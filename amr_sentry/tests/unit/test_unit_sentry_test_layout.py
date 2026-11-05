"""Guard addon ownership and Odoo/offline test discovery boundaries."""
import ast
from pathlib import Path
import unittest

ADDON_ROOT = Path(__file__).resolve().parents[2]
ROOT = ADDON_ROOT.parent


class SentryTestLayout(unittest.TestCase):
    def test_pytest_docker_template_is_in_repository_tests_directory(self):
        tests_root = ROOT / 'tests'
        dockerfile = tests_root / 'Dockerfile.pytest'
        requirements = tests_root / 'requirements-pytest.txt'
        dockerignore = tests_root / 'Dockerfile.pytest.dockerignore'
        self.assertTrue(dockerfile.is_file(), str(dockerfile))
        self.assertTrue(requirements.is_file(), str(requirements))
        self.assertTrue(dockerignore.is_file(), str(dockerignore))
        self.assertFalse((ROOT / 'Dockerfile.pytest').exists())
        self.assertFalse((ROOT / 'requirements-pytest.txt').exists())
        self.assertIn('pytest==7.4.4', requirements.read_text())
        self.assertEqual(['**', '!Dockerfile.pytest', '!requirements-pytest.txt'],
                         dockerignore.read_text().splitlines())

    def test_policy_bodies_are_canonical_in_unit_directory(self):
        path = ADDON_ROOT / 'tests/unit/test_unit_sentry_policy.py'
        tree = ast.parse(path.read_text())
        classes = [node for node in tree.body
                   if isinstance(node, ast.ClassDef) and node.name == 'SentryPolicyTests']
        self.assertEqual(len(classes), 1, 'policy test bodies must live in unit')
        methods = [node for node in classes[0].body
                   if isinstance(node, ast.FunctionDef) and node.name.startswith('test_')]
        self.assertEqual(len(methods), 8)

    def test_canonical_unit_files_do_not_import_legacy_adapters(self):
        inventory = {
            'behavior': {'SentryReporting': 18},
            'bootstrap': {'SentryBootstrapContractTest': 3, 'SentryPackagingContractTest': 2},
            'config': {'TestSentryConfig': 4},
            'docs': {'SentryDocs': 6, 'ActivatedOperatorExamples': 1},
            'model': {'TestOptionalSentryModelHook': 7},
            'safe_file': {'SafeFileProfilePresenceTest': 5},
        }
        unit = ADDON_ROOT / 'tests/unit'
        for name, expected in inventory.items():
            tree = ast.parse((unit / ('test_unit_sentry_%s.py' % name)).read_text())
            legacy_imports = [node.module for node in ast.walk(tree)
                             if isinstance(node, ast.ImportFrom) and node.module
                             and 'test_U11_sentry_' in node.module]
            self.assertFalse(legacy_imports, 'canonical unit imports adapters: %s' % legacy_imports)
            found = {node.name: node for node in tree.body if isinstance(node, ast.ClassDef)}
            for class_name, count in expected.items():
                self.assertIn(class_name, found, name)
                methods = [node for node in found[class_name].body
                           if isinstance(node, ast.FunctionDef) and node.name.startswith('test_')]
                self.assertEqual(len(methods), count, class_name)

    def test_sentry_test_files_live_with_their_addon_owners(self):
        sentry = {'behavior', 'bootstrap', 'config', 'docs', 'model', 'policy', 'safe_file'}
        core = {'bridge', 'settings'}
        for owner, names in (('amr_sentry', sentry), ('amr_service_client', core)):
            for name in names:
                path = ROOT / owner / 'tests' / ('test_U11_sentry_%s.py' % name)
                self.assertTrue(path.is_file(), str(path))
                if owner == 'amr_service_client':
                    canonical = ROOT / owner / 'tests/unit' / ('test_unit_sentry_%s.py' % name)
                    self.assertTrue(canonical.is_file(), str(canonical))

    def test_no_sentry_tests_or_selector_remain_in_shared_legacy_directory(self):
        legacy = ROOT / 'tests/addons13_27'
        sentry_tests = sorted(path.name for path in legacy.glob('test_*.py')
                              if 'sentry' in path.stem.lower())
        self.assertEqual([], sentry_tests)
        self.assertFalse((legacy / 'test_U11_sentry_legacy.py').exists())
        self.assertFalse((legacy / 'orm_68_probe.py').exists())
        self.assertTrue((ADDON_ROOT / 'tests/orm_68_probe.py').is_file())
        # Keep fixtures used by unrelated legacy suites.
        self.assertTrue((legacy / 'support.py').is_file())

    def test_orm_hook_is_registered_without_importing_offline_tests(self):
        init = (ADDON_ROOT / 'tests/__init__.py').read_text()
        self.assertIn('from . import integration', init)
        self.assertIn('from .integration import test_service_client_hook', init)
        integration_init = (ADDON_ROOT / 'tests/integration/__init__.py').read_text()
        self.assertIn('from . import test_service_client_hook', integration_init)
        self.assertNotIn('test_U11_sentry_', init)
        package = ast.parse((ADDON_ROOT / '__init__.py').read_text())
        imports_tests = any(isinstance(node, ast.ImportFrom)
                            and any(alias.name == 'tests' for alias in node.names)
                            for node in ast.walk(package))
        self.assertFalse(imports_tests)


if __name__ == '__main__':
    unittest.main()
