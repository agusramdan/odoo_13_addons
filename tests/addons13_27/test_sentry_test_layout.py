"""Guard addon ownership and Odoo/offline test discovery boundaries."""
import ast
import os
from pathlib import Path
import re
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]


class SentryTestLayout(unittest.TestCase):
    def test_sentry_test_files_live_with_their_owners(self):
        sentry = {'behavior', 'bootstrap', 'config', 'docs', 'model', 'policy', 'safe_file'}
        core = {'bridge', 'settings'}
        for owner, names in (('amr_sentry', sentry), ('amr_service_client', core)):
            for name in names:
                self.assertTrue((ROOT / owner / 'tests' / ('test_U11_sentry_%s.py' % name)).is_file(), name)

    def test_legacy_selector_runs_each_owned_contract_once(self):
        def run(directory, pythonpath):
            env = os.environ.copy()
            env['PYTHONPATH'] = pythonpath
            result = subprocess.run(
                [sys.executable, '-B', '-m', 'unittest', 'discover', '-s', directory,
                 '-p', 'test_U11_sentry_*.py', '-v'],
                cwd=str(ROOT), env=env, stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, universal_newlines=True)
            self.assertEqual(result.returncode, 0, result.stdout)
            matches = re.findall(r'^(test_\S+ \([^\n]+?\)) \.\.\.', result.stdout, re.MULTILINE)
            self.assertRegex(result.stdout, r'Ran %d tests? in ' % len(matches))
            self.assertRegex(result.stdout, r'\nOK\s*$')
            self.assertEqual(len(matches), len(set(matches)), result.stdout)
            return matches, result.stdout

        sentry, _ = run('amr_sentry/tests', 'tests/addons13_27:amr_sentry/tests:.')
        core, _ = run('amr_service_client/tests', 'tests/addons13_27:.')
        legacy, output = run('tests/addons13_27', '.')
        self.assertEqual(len(sentry) + len(core), 51)
        self.assertEqual(len(legacy), 51, output)
        self.assertEqual(set(legacy), set(sentry + core))

    def test_legacy_discovery_preserves_external_modules_and_search_path(self):
        code = '''
import os, sys, types, unittest
names = ('requests', 'requests.exceptions', 'jwt')
originals = {name: types.ModuleType(name) for name in names}
sys.modules.update(originals)
sys.path.insert(0, os.path.abspath('tests/addons13_27'))
path = list(sys.path)
unittest.TestLoader().discover('tests/addons13_27', pattern='test_U11_sentry_*.py')
assert all(sys.modules.get(name) is module for name, module in originals.items()), 'external modules replaced during discovery'
assert sys.path == path, 'discovery changed module search path'
'''
        result = subprocess.run([sys.executable, '-B', '-c', code], cwd=str(ROOT),
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                universal_newlines=True)
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_orm_hook_registered_without_importing_offline_tests(self):
        integration = ROOT / 'amr_sentry/integration_tests/test_service_client_hook.py'
        self.assertTrue(integration.is_file())
        init = (ROOT / 'amr_sentry/tests/__init__.py').read_text()
        self.assertIn('from ..integration_tests import test_service_client_hook', init)
        self.assertNotIn('test_U11_sentry_', init)
        package = ast.parse((ROOT / 'amr_sentry/__init__.py').read_text())
        self.assertFalse(any(isinstance(n, ast.ImportFrom) and any(a.name == 'tests' for a in n.names) for n in ast.walk(package)))

if __name__ == '__main__':
    unittest.main()
