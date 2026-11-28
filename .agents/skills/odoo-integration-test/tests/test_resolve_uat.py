import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import unittest
from unittest import mock

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location('resolve_uat', SCRIPTS / 'resolve_uat.py')
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)


class ResolverTests(unittest.TestCase):
    def setUp(self):
        self.profile = {'task_id': 'task-1', 'database': 'uat_task_1', 'runtime': 'python3.8', 'max_runs': 2, 'profile': 'uat-native', 'data': 'synthetic', 'egress': 'denied', 'host_ports': 'disabled', 'database_lifecycle': 'disposable', 'cleanup': 'exact-run-owned-only', 'password': 'DO_NOT_PRINT'}
        self.raw = json.dumps(self.profile).encode()
        self.inv = {'head': 'abc123', 'changes': []}

    def invoke(self, expected=None, inventories=None):
        def git(repo, *args):
            if args[0] == 'rev-parse': return b'/synthetic-repo\n'
            if args[0] == 'ls-tree': return b'100644 blob abc\tprofile.json\0'
            if args[0] == 'show': return self.raw
            raise AssertionError(args)
        with mock.patch.object(r.planner, 'git', side_effect=git), mock.patch.object(r.planner, 'inventory', side_effect=inventories or [self.inv, self.inv]), mock.patch('subprocess.run', side_effect=AssertionError('subprocess forbidden')):
            return r.resolve('/synthetic-repo', 'task-1', 'profile.json', expected or hashlib.sha256(self.raw).hexdigest())

    def test_proposal_is_not_authorization_and_hides_secrets(self):
        result = self.invoke()
        self.assertFalse(result['execution_authorized'])
        self.assertFalse(result['execution_implemented'])
        self.assertEqual(result['config_proposal']['database'], 'uat_task_1')
        self.assertEqual(result['profile_artifact']['acceptance'], 'unverified')
        self.assertNotIn('DO_NOT_PRINT', json.dumps(result))
        self.assertTrue(result['blockers']['isolation'])

    def test_hash_mismatch_fails_closed(self):
        with self.assertRaisesRegex(ValueError, 'hash mismatch'): self.invoke('0' * 64)

    def test_unsafe_values_not_copied(self):
        self.profile.update(database='production', egress='allowed', max_runs=True)
        self.raw = json.dumps(self.profile).encode()
        result = self.invoke()
        self.assertNotIn('database', result['config_proposal'])
        self.assertNotIn('egress', result['config_proposal'])
        self.assertIn('missing_or_invalid_max_runs', result['blockers']['profile'])

    def test_unstable_inventory_has_no_candidate_identity(self):
        result = self.invoke(inventories=[self.inv, {'head': 'different', 'changes': []}])
        self.assertIsNone(result['candidate']['inventory_sha256'])

    def test_duplicate_json_rejected(self):
        self.raw = b'{"task_id":"task-1","task_id":"task-1"}'
        with self.assertRaisesRegex(ValueError, 'duplicate'): self.invoke()

    def test_path_traversal_rejected_before_git(self):
        with mock.patch.object(r.planner, 'git', return_value=b'/synthetic-repo\n'):
            with self.assertRaises(ValueError): r.resolve('/synthetic-repo', 'task-1', '../secret', '0' * 64)


if __name__ == '__main__': unittest.main()
