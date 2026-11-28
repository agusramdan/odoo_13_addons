import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from io import StringIO
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'plan_uat.py'
spec = importlib.util.spec_from_file_location('planner', SCRIPT)
planner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(planner)

class PlannerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=os.environ.get('TMPDIR'))
        self.repo = Path(self.tmp.name) / 'repo'
        self.repo.mkdir()
        self.git('init', '-q')
        self.git('config', 'user.email', 'test@example.invalid')
        self.git('config', 'user.name', 'Test')
        (self.repo / 'base').write_text('original')
        self.git('add', 'base')
        self.git('commit', '-qm', 'initial')

    def tearDown(self):
        self.tmp.cleanup()

    def git(self, *args):
        return subprocess.run(['git', '-C', str(self.repo), *args], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def plan(self, *args):
        out, err = StringIO(), StringIO()
        real = subprocess.run
        def only_git(command, *a, **kw):
            self.assertEqual(command[0], 'git')
            return real(command, *a, **kw)
        with patch.object(planner.subprocess, 'run', side_effect=only_git), redirect_stdout(out), redirect_stderr(err):
            rc = planner.main(['--repo', str(self.repo), '--task-id', 'test', *args])
        return rc, out.getvalue(), err.getvalue()

    def test_clean_and_dirty_hashes(self):
        rc, out, _ = self.plan()
        clean = json.loads(out)
        self.assertEqual(rc, 0)
        self.assertFalse(clean['execution_authorized'])
        self.assertEqual(clean['source']['changes'], [])
        (self.repo / 'base').write_text('staged')
        self.git('add', 'base')
        (self.repo / 'base').write_text('unstaged')
        (self.repo / 'new').write_text('untracked')
        dirty = json.loads(self.plan()[1])
        entry = dirty['source']['changes'][0]
        self.assertTrue(entry['staged'] and entry['unstaged'])
        self.assertTrue(entry['index_sha256'])
        self.assertNotEqual(entry['index_sha256'][0]['sha256'], entry['worktree']['sha256'])
        self.assertNotEqual(clean['source']['candidate_sha256'], dirty['source']['candidate_sha256'])
        self.assertEqual(dirty['source']['candidate_sha256'], json.loads(self.plan()[1])['source']['candidate_sha256'])
        self.assertTrue(dirty['proposed']['resource_names_are_unchecked'])
        self.assertIsNone(dirty['bindings']['runtime'])
        self.assertTrue(dirty['blockers']['authorization'])

    def test_hidden_index_flags_block_candidate(self):
        for flag in ('--assume-unchanged', '--skip-worktree'):
            with self.subTest(flag=flag):
                self.git('update-index', flag, 'base')
                (self.repo / 'base').write_text('hidden modification')
                rc, out, err = self.plan()
                self.assertTrue(rc != 0 or json.loads(out)['blockers']['candidate'])
                self.git('update-index', '--no-assume-unchanged', '--no-skip-worktree', 'base')
                (self.repo / 'base').write_text('original')

    def test_symlink_parent_never_reads_external_file(self):
        import hashlib
        directory = self.repo / 'nested'
        directory.mkdir()
        (directory / 'tracked').write_text('tracked')
        self.git('add', 'nested/tracked')
        self.git('commit', '-qm', 'tracked directory')
        (directory / 'tracked').unlink()
        directory.rmdir()
        outside = Path(self.tmp.name) / 'outside'
        outside.mkdir()
        secret = b'synthetic-external-content-marker'
        (outside / 'tracked').write_bytes(secret)
        directory.symlink_to(outside, target_is_directory=True)
        rc, out, err = self.plan()
        self.assertEqual(rc, 0)
        data = json.loads(out)
        change = next(x for x in data['source']['changes'] if x['path'] == 'nested/tracked')
        self.assertEqual(change['worktree']['kind'], 'unsupported')
        self.assertTrue(data['blockers']['candidate'])
        self.assertNotIn(secret.decode(), out + err)
        self.assertNotIn(hashlib.sha256(secret).hexdigest(), out + err)

    def test_literal_staged_path(self):
        for name in ('[abc]', 'a'):
            (self.repo / name).write_text(name)
        self.git('add', '--', '[abc]', 'a')
        changes = {x['path']: x for x in json.loads(self.plan()[1])['source']['changes']}
        self.assertEqual(len(changes['[abc]']['index_entries']), 1)
        self.assertTrue(changes['[abc]']['index_entries'][0].endswith('\t[abc]'))

    def test_freeform_arguments_never_echoed(self):
        marker = 'synthetic-password-UNIQUE'
        rc, out, err = self.plan('--image-metadata', marker, '--odoo-bin', '/tmp/' + marker,
                                 '--addon', 'demo', '--database', 'test_db', '--mode', 'install')
        self.assertNotIn(marker, out + err)
        if rc == 0:
            self.assertTrue(json.loads(out)['blockers']['lock_image_qualification'])
            self.assertIsNone(json.loads(out)['draft_helper_dry_run_argv'])

    def test_deletion_and_rename(self):
        self.git('mv', 'base', 'renamed')
        changes = {x['path']: x for x in json.loads(self.plan()[1])['source']['changes']}
        self.assertEqual(changes['base']['worktree']['kind'], 'deleted')
        self.assertTrue(changes['renamed']['index_sha256'])

    def test_sensitive_withheld(self):
        (self.repo / '.env').write_text('secret value')
        rc, out, err = self.plan()
        self.assertEqual(rc, 2)
        self.assertNotIn('secret value', out + err)
        self.assertNotIn('.env', out + err)

    def test_scope_and_ledger_never_reset(self):
        ledger = Path(self.tmp.name) / 'ledger'
        ledger.write_text('5')
        rc, out, _ = self.plan('--ledger', str(ledger), '--authorization', 'accepted', '--runtime', 'python3', '--postgres-image', 'postgres:10', '--image-metadata', 'unverified')
        data = json.loads(out)
        self.assertEqual(rc, 0)
        self.assertFalse(data['execution_authorized'])
        self.assertEqual(ledger.read_text(), '5')
        self.assertTrue(data['blockers']['authorization'])
        self.assertTrue(data['blockers']['lock_image_qualification'])
        self.assertTrue(data['proposed']['resource_names_are_unchecked'])

if __name__ == '__main__':
    unittest.main()
