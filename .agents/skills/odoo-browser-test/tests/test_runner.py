import pathlib
import subprocess
import sys
import unittest
import importlib.util
import tempfile
from unittest.mock import patch
from types import SimpleNamespace

RUNNER = pathlib.Path(__file__).resolve().parents[1] / 'scripts' / 'run.py'
spec = importlib.util.spec_from_file_location('browser_runner', RUNNER)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)

class RunnerTest(unittest.TestCase):
    def test_cleanup_failure_forces_nonzero_after_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            addon = pathlib.Path(tmp) / 'sample'
            addon.mkdir()
            (addon / '__manifest__.py').write_text("{'depends': []}")
            (addon / 'tests' / 'browser').mkdir(parents=True)
            (addon / 'tests' / 'browser' / 'test_browser.py').write_text('class Class:\n    def test_ok(self): pass\n')
            def docker(args, **kwargs):
                if args[1:3] == ['network', 'ls']:
                    raise subprocess.CalledProcessError(1, args)
                output = 'odoo.addons.sample.tests.browser.test_browser: Starting Class.test_ok\n in browser\nRan 1 test\n' if args[1:3] == ['start', '-a'] else ''
                return SimpleNamespace(returncode=0, stdout=output)
            with patch.object(sys, 'argv', ['run', '--addon', str(addon), '--test', 'Class.test_ok']), patch.object(runner.subprocess, 'run', side_effect=docker):
                self.assertNotEqual(runner.main(), 0)

    def test_timeout_recovery_reconciles_late_resources(self):
        for stage in ('build', 'create'):
            with self.subTest(stage=stage), tempfile.TemporaryDirectory() as tmp:
                addon = pathlib.Path(tmp) / 'sample'
                (addon / 'tests' / 'browser').mkdir(parents=True)
                (addon / '__manifest__.py').write_text("{'depends': []}")
                (addon / 'tests' / 'browser' / 'test_browser.py').write_text('class Class:\n    def test_ok(self): pass\n')
                calls = []
                late = [False]
                visible = [False]
                def docker(args, **kwargs):
                    calls.append(args)
                    if args[1] == stage and not late[0]:
                        late[0] = True
                        raise subprocess.TimeoutExpired(args, 1)
                    if args[1:3] == ['image', 'ls'] and visible[0]:
                        return SimpleNamespace(returncode=0, stdout='lateimage\n')
                    if args[1:3] == ['ps', '-aq'] and visible[0] and stage == 'create':
                        return SimpleNamespace(returncode=0, stdout='latecontainer\n')
                    return SimpleNamespace(returncode=0, stdout='')
                run = 'a' * 32
                with patch.object(sys, 'argv', ['run', '--addon', str(addon), '--test', 'Class.test_ok']), patch.object(runner.uuid, 'uuid4', return_value=SimpleNamespace(hex=run)), patch.object(runner.subprocess, 'run', side_effect=docker):
                    self.assertEqual(runner.main(), 1)
                    self.assertNotIn(['docker', 'image', 'rm', '-f', 'lateimage'], calls)
                    visible[0] = True
                    self.assertTrue(runner.cleanup(run))
                self.assertIn(['docker', 'image', 'rm', '-f', 'lateimage'], calls)
                self.assertIn('--label', next(c for c in calls if c[1] == 'build'))
                self.assertTrue(all('label=odoo.browser.run=' + run in c for c in calls if c[1:3] in (['ps', '-aq'], ['network', 'ls'], ['image', 'ls'])))
                if stage == 'create':
                    self.assertIn(['docker', 'rm', '-f', 'latecontainer'], calls)

    def test_spoofed_log_is_not_independent_evidence(self):
        forged = 'odoo.addons.sample.tests.browser.test_browser: Starting Class.test_ok\n in browser\nRan 1 test\n'
        self.assertTrue(runner.browser_test_started(forged, 'sample', 'Class.test_ok'))
        self.assertIn('never independent proof', (RUNNER.parents[1] / 'SKILL.md').read_text())

    def test_browser_evidence_requires_browser_module(self):
        log = 'odoo.addons.sample.tests.test_browser: Starting Class.test_ok ...'
        self.assertFalse(runner.browser_test_started(log, 'sample', 'Class.test_ok'))
        log = 'odoo.addons.sample.tests.browser.test_browser: Starting Class.test_ok ...'
        self.assertTrue(runner.browser_test_started(log, 'sample', 'Class.test_ok'))

    def test_rejects_symlinked_addon_argument(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            addon = root / 'real'
            addon.mkdir()
            (addon / '__manifest__.py').write_text("{'depends': []}")
            (addon / 'tests' / 'browser').mkdir(parents=True)
            (root / 'alias').symlink_to(addon)
            result = subprocess.run([sys.executable, str(RUNNER), '--addon', str(root / 'alias'), '--test', 'Class.test_ok'], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('symlink', result.stderr)

    def test_selector_must_be_defined_in_browser_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            addon = pathlib.Path(tmp) / 'sample'
            (addon / 'tests' / 'browser').mkdir(parents=True)
            (addon / '__manifest__.py').write_text("{'depends': []}")
            result = subprocess.run([sys.executable, str(RUNNER), '--addon', str(addon), '--test', 'Class.test_ok'], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('selector', result.stderr)

    def test_local_dependencies_are_discovered_transitively(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            for name, deps in [('sample', ['local_dep', 'base']), ('local_dep', ['nested']), ('nested', [])]:
                addon = root / name
                addon.mkdir()
                (addon / '__manifest__.py').write_text(repr({'depends': deps}))
            self.assertEqual({p.name for p in runner.local_addons(root / 'sample')}, {'sample', 'local_dep', 'nested'})

    def test_rejects_symlinked_dependency(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            addon = root / 'sample'
            addon.mkdir()
            (addon / '__manifest__.py').write_text("{'depends': ['local_dep']}")
            (root / 'local_dep').symlink_to(root / 'elsewhere')
            with self.assertRaisesRegex(ValueError, 'symlink'):
                runner.local_addons(addon)

    def test_rejects_addon_without_browser_test_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            addon = pathlib.Path(tmp) / 'sample'
            addon.mkdir()
            (addon / '__manifest__.py').write_text("{'depends': []}")
            result = subprocess.run([sys.executable, str(RUNNER), '--addon', str(addon), '--test', 'Class.test_ok'], capture_output=True, text=True)
            self.assertIn('tests/browser', result.stderr)
            self.assertNotEqual(result.returncode, 0)

    def test_requires_explicit_addon_and_selector(self):
        result = subprocess.run([sys.executable, str(RUNNER)], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('--addon', result.stderr)

if __name__ == '__main__':
    unittest.main()
