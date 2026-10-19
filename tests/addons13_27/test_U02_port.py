"""Offline source-layout/provenance integrity checks for U02."""
from support import *
import ast
import hashlib
import json
import subprocess

REPORTS = pathlib.Path('/home/ubuntu/docs/reports/ADDONS13-27')
SECURITY = REPORTS / 'security-read-only-20261019T095501Z/security-review.json'
BASE_SHA = 'd195390ffc1e5fd6fdb18d4bcd10e7fb1c10be59'


def local_git(*args):
    env = {
        'PATH': '/usr/bin:/bin',
        'HOME': str(ROOT),
        'LANG': 'C',
        'GIT_CONFIG_NOSYSTEM': '1',
        'GIT_CONFIG_GLOBAL': '/dev/null',
        'GIT_NO_LAZY_FETCH': '1',
        'GIT_TERMINAL_PROMPT': '0',
        'GIT_OPTIONAL_LOCKS': '0',
    }
    return subprocess.run(['git', '-c', 'core.fsmonitor=false', *args], cwd=ROOT,
                          env=env, capture_output=True, text=True, timeout=20)


class Port(OfflineCase):
    def test_manifest_dependencies_and_all_declared_files_are_local(self):
        manifest = ast.literal_eval((ADDON / '__manifest__.py').read_text())
        self.assertEqual(manifest['version'], '13.0.0.1.0')
        self.assertTrue({'base', 'web', 'base_setup', 'amr_resource'} <= set(manifest['depends']))
        self.assertIn('pyjwt', manifest['external_dependencies']['python'])
        self.assertTrue(manifest['data'])
        for relative in manifest['data']:
            target = (ADDON / relative).resolve()
            self.assertTrue(ADDON.resolve() in target.parents, relative)
            self.assertTrue(target.is_file(), relative)
        self.assertNotIn('demo', manifest)
        self.assertFalse(any('service-client-demo.json' in item for item in manifest['data']))

    def test_import_graph_maps_to_local_modules_and_duplicate_is_inactive(self):
        root_init = (ADDON / '__init__.py').read_text()
        model_init = (ADDON / 'models/__init__.py').read_text()
        service_init = (ADDON / 'services/__init__.py').read_text()
        wizard_init = (ADDON / 'wizards/__init__.py').read_text()
        self.assertIn('models', root_init)
        self.assertIn('services', root_init)
        self.assertIn('wizards', root_init)
        for module in ('service_credential', 'service_endpoint', 'service_client',
                       'service_client_log', 'actions_server'):
            self.assertIn(module, model_init)
            self.assertTrue((ADDON / 'models' / f'{module}.py').is_file())
        for module in ('credential_loader', 'auth_factory', 'providers', 'token_cache'):
            self.assertIn(module, service_init)
            self.assertTrue((ADDON / 'services' / f'{module}.py').is_file())
        self.assertIn('service_credential', wizard_init)
        self.assertIn('service_endpoint_test', wizard_init)
        self.assertTrue((ADDON / 'services/service_client.py').is_file())
        self.assertNotIn('service_client', [line.strip() for line in service_init.splitlines()
                                           if line.strip() and not line.lstrip().startswith('#')])

    def test_reviewed_26_file_source_manifest_is_unchanged(self):
        # Allowlist is exactly the regular Python/XML/CSV addon surface in the
        # prior read-only security review; no credentials/config files included.
        files = sorted(p for p in ADDON.rglob('*')
                       if p.is_file() and p.suffix in {'.py', '.xml', '.csv'})
        self.assertEqual(len(files), 26)
        mapping = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                   for p in files}
        compact = json.dumps(mapping, sort_keys=True, separators=(',', ':')).encode()
        actual = hashlib.sha256(compact).hexdigest()
        review = json.loads(SECURITY.read_text())
        self.assertEqual(review['source_manifest']['file_count'], 26)
        self.assertTrue(review['source_manifest']['match'])
        self.assertEqual(actual, review['source_manifest']['expected_sha256'])
        self.assertIsNone(review['identity']['candidate_commit_sha'])

    def test_amr_resource_matches_local_task_base_without_fetch(self):
        object_check = local_git('cat-file', '-e', f'{BASE_SHA}^{{commit}}')
        if object_check.returncode != 0:
            self.skipTest('task base object unavailable locally; lazy/network fetch disabled')
        diff = local_git('diff', '--quiet', BASE_SHA, '--', 'amr_resource/')
        self.assertEqual(diff.returncode, 0, 'tracked amr_resource bytes differ from task base')
        status = local_git('status', '--porcelain', '--', 'amr_resource/')
        self.assertEqual(status.returncode, 0, status.stderr)
        self.assertEqual(status.stdout.strip(), '', 'untracked or modified amr_resource paths')
