"""Guard addon ownership and Odoo/offline test discovery boundaries."""
import ast
import os
from pathlib import Path
import re
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]

# Fixed baseline from the 53 legacy contract cases; additions remain allowed.
LEGACY_CONTRACTS = frozenset({
    'test_active_file_rejects_each_missing_safety_key (test_U11_sentry_safe_file.SafeFileProfilePresenceTest)',
    'test_all_mode_initializes_only_sdk_options_and_reports_both_outcomes (test_U11_sentry_policy.SentryPolicyTests)',
    'test_call_pre_response_failure_returns_none_without_masking (test_U11_sentry_behavior.SentryReporting)',
    'test_capture_failures_are_swallowed (test_U11_sentry_policy.SentryPolicyTests)',
    'test_configuration_mechanism_and_policy_are_documented (test_U11_sentry_docs.SentryDocs)',
    'test_core_packaging_no_longer_declares_sentry_dependencies (test_U11_sentry_bootstrap.SentryPackagingContractTest)',
    'test_create_log_accepts_service_client_integer_id (test_U11_sentry_behavior.SentryReporting)',
    'test_delegates_fixed_arguments_without_importing_sentry_sdk (test_U11_sentry_bridge.TestSentryBridge)',
    'test_disabled_policy_never_initializes_or_captures (test_U11_sentry_policy.SentryPolicyTests)',
    'test_dispatch_success_log_failure_uses_baseline_error_log_path (test_U11_sentry_behavior.SentryReporting)',
    'test_dsn_must_be_null_or_string_even_when_disabled (test_U11_sentry_safe_file.SafeFileProfilePresenceTest)',
    'test_each_present_safety_value_has_exact_type_and_value (test_U11_sentry_safe_file.SafeFileProfilePresenceTest)',
    'test_empty_environment_uses_default_path (test_U11_sentry_config.TestSentryConfig)',
    'test_error_mode_reports_only_errors (test_U11_sentry_policy.SentryPolicyTests)',
    'test_exception_reports_failure_without_forwarding_private_arguments (test_U11_sentry_model.TestOptionalSentryModelHook)',
    'test_guides_document_target_and_test_only_dependency_boundary (test_U11_sentry_docs.SentryDocs)',
    'test_hook_failure_does_not_escape (test_U11_sentry_bridge.TestSentryBridge)',
    'test_import_initializes_once_with_sentry_namespace_only (test_U11_sentry_bootstrap.SentryBootstrapContractTest)',
    'test_init_failure_disables_reporter_without_exposing_exception (test_U11_sentry_policy.SentryPolicyTests)',
    'test_invalid_override_is_nonfatal_and_warns_without_secrets (test_U11_sentry_bootstrap.SentryBootstrapContractTest)',
    'test_invalid_service_client_policy_is_rejected (test_U11_sentry_config.TestSentryConfig)',
    'test_json_override_maps_configuration (test_U11_sentry_config.TestSentryConfig)',
    'test_legacy_global_sentry_settings_are_removed_from_core (test_U11_sentry_settings.TestSentrySettingsRemoval)',
    'test_metadata_must_be_strings_when_present (test_U11_sentry_safe_file.SafeFileProfilePresenceTest)',
    'test_missing_dsn_never_initializes_or_captures (test_U11_sentry_policy.SentryPolicyTests)',
    'test_missing_service_client_uses_core_hook_default (test_U11_sentry_model.TestOptionalSentryModelHook)',
    'test_modes_gate_reporting_and_selected_requires_opt_in (test_U11_sentry_behavior.SentryReporting)',
    'test_none_mode_never_initializes_or_captures (test_U11_sentry_policy.SentryPolicyTests)',
    'test_operator_discloses_original_exception_residual_risk (test_U11_sentry_docs.SentryDocs)',
    'test_operator_guides_and_entry_point_links_exist (test_U11_sentry_docs.SentryDocs)',
    'test_optional_addon_declares_dependencies_and_exact_pins (test_U11_sentry_bootstrap.SentryPackagingContractTest)',
    'test_per_client_sentry_opt_in_remains_declared_and_visible (test_U11_sentry_settings.TestSentrySettingsRemoval)',
    'test_real_dispatch_send_success_and_failure_reporting_are_best_effort (test_U11_sentry_behavior.SentryReporting)',
    'test_real_log_send_reporter_failure_preserves_log_outcome (test_U11_sentry_behavior.SentryReporting)',
    'test_real_log_send_reports_http_failure_and_preserves_logged_error (test_U11_sentry_behavior.SentryReporting)',
    'test_real_log_send_reports_success (test_U11_sentry_behavior.SentryReporting)',
    'test_real_service_client_call_outcomes_privacy_and_transport_semantics (test_U11_sentry_behavior.SentryReporting)',
    'test_rejects_non_allowlisted_sentry_options_even_when_disabled (test_U11_sentry_safe_file.SafeFileProfilePresenceTest)',
    'test_reporter_failure_does_not_escape_hook (test_U11_sentry_model.TestOptionalSentryModelHook)',
    'test_root_addon_index_lists_optional_addon (test_U11_sentry_docs.SentryDocs)',
    'test_run_action_call_exception_is_not_reported_twice (test_U11_sentry_behavior.SentryReporting)',
    'test_run_action_handler_exception_is_reported_once_with_valid_keywords (test_U11_sentry_behavior.SentryReporting)',
    'test_run_action_reporter_failure_logs_only_safe_diagnostics (test_U11_sentry_behavior.SentryReporting)',
    'test_schema_and_inactive_cases_do_not_initialize_or_capture (test_U11_sentry_bootstrap.SentryBootstrapContractTest)',
    'test_selected_dispatch_bound_opted_in_singleton_reports_once (test_U11_sentry_model.TestOptionalSentryModelHook)',
    'test_selected_dispatch_suppresses_opted_out_and_empty_recordsets (test_U11_sentry_model.TestOptionalSentryModelHook)',
    'test_selected_explicit_client_takes_precedence_over_bound_client (test_U11_sentry_model.TestOptionalSentryModelHook)',
    'test_selected_mode_requires_opt_in_and_reports_both (test_U11_sentry_policy.SentryPolicyTests)',
    'test_sentry_failure_is_best_effort (test_U11_sentry_behavior.SentryReporting)',
    'test_success_reports_once_with_exact_service_client (test_U11_sentry_model.TestOptionalSentryModelHook)',
    'test_yaml_and_json_examples_load_when_activated (test_U11_sentry_docs.ActivatedOperatorExamples)',
    'test_yaml_example_is_valid_and_safe_by_default (test_U11_sentry_docs.SentryDocs)',
    'test_yaml_override_maps_sentry_kwargs_and_policy (test_U11_sentry_config.TestSentryConfig)',
})


class SentryTestLayout(unittest.TestCase):
    def test_policy_bodies_are_canonical_in_unit_directory(self):
        path = ROOT / 'amr_sentry/tests/unit/test_unit_sentry_policy.py'
        tree = ast.parse(path.read_text())
        classes = [n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'SentryPolicyTests']
        self.assertEqual(len(classes), 1, 'policy test bodies must live in unit')
        self.assertEqual(len([n for n in classes[0].body if isinstance(n, ast.FunctionDef) and n.name.startswith('test_')]), 8)
        # Every addon-owned legacy class must contain its actual test bodies here,
        # not merely import them from an old adapter.
        inventory = {
            'behavior': {'SentryReporting': 17},
            'bootstrap': {'SentryBootstrapContractTest': 3, 'SentryPackagingContractTest': 2},
            'config': {'TestSentryConfig': 4},
            'docs': {'SentryDocs': 6, 'ActivatedOperatorExamples': 1},
            'model': {'TestOptionalSentryModelHook': 7},
            'safe_file': {'SafeFileProfilePresenceTest': 5},
        }
        for name, expected in inventory.items():
            tree = ast.parse((ROOT / 'amr_sentry/tests/unit' / ('test_unit_sentry_%s.py' % name)).read_text())
            legacy_imports = [n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)
                              and n.module and 'test_U11_sentry_' in n.module]
            self.assertFalse(legacy_imports, 'canonical unit depends on legacy adapters: %s' % legacy_imports)
            found = {n.name: n for n in tree.body if isinstance(n, ast.ClassDef)}
            for class_name, count in expected.items():
                self.assertIn(class_name, found, name)
                methods = [n for n in found[class_name].body if isinstance(n, ast.FunctionDef) and n.name.startswith('test_')]
                self.assertEqual(len(methods), count, class_name)

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
            if directory == 'tests/addons13_27':
                command = [sys.executable, '-B', '-m', 'unittest', 'discover', '-s', directory,
                           '-p', 'test_U11_sentry_*.py', '-v']
            else:
                inventory = sorted((ROOT / directory).glob('test_U11_sentry_*.py'))
                self.assertTrue(inventory, directory)
                command = [sys.executable, '-B', '-m', 'unittest', '-v'] + [p.stem for p in inventory]
            result = subprocess.run(
                command,
                cwd=str(ROOT), env=env, stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, universal_newlines=True)
            self.assertEqual(result.returncode, 0, result.stdout)
            matches = re.findall(r'^(test_\S+ \([^\n]+?\)) \.\.\.', result.stdout, re.MULTILINE)
            self.assertRegex(result.stdout, r'Ran %d tests? in ' % len(matches))
            self.assertRegex(result.stdout, r'\nOK\s*$')
            self.assertEqual(len(matches), len(set(matches)), result.stdout)
            # Python 3.12 includes the method twice in unittest's verbose label;
            # Python 3.7 omits the final component. Normalize across runtimes.
            identities = []
            for match in matches:
                name, qualified = match[:-1].split(' (', 1)
                if qualified.endswith('.' + name):
                    qualified = qualified[:-(len(name) + 1)]
                identities.append('%s (%s)' % (name, qualified))
            return identities, result.stdout

        sentry, _ = run('amr_sentry/tests', 'tests/addons13_27:amr_sentry/tests:.')
        core, _ = run('amr_service_client/tests', 'tests/addons13_27:amr_service_client/tests:.')
        legacy, output = run('tests/addons13_27', '.')
        self.assertTrue(sentry)
        self.assertTrue(core)
        self.assertEqual(len(legacy), len(sentry) + len(core), output)
        self.assertEqual(len(sentry + core), len(set(sentry + core)))
        self.assertEqual(set(legacy), set(sentry + core))
        self.assertFalse(LEGACY_CONTRACTS - set(legacy),
                         "Missing legacy contracts: %s" % sorted(LEGACY_CONTRACTS - set(legacy)))

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
assert 'integration' not in sys.modules, 'offline discovery imported Odoo integration'
assert 'odoo.tests.common' not in sys.modules, 'offline discovery imported Odoo tests'
'''
        result = subprocess.run([sys.executable, '-B', '-c', code], cwd=str(ROOT),
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                universal_newlines=True)
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_orm_hook_registered_without_importing_offline_tests(self):
        integration = ROOT / 'amr_sentry/integration_tests/test_service_client_hook.py'
        self.assertTrue(integration.is_file())
        init = (ROOT / 'amr_sentry/tests/__init__.py').read_text()
        self.assertIn('from . import integration', init)
        self.assertIn('from .integration import test_service_client_hook', init)
        integration_init = (ROOT / 'amr_sentry/tests/integration/__init__.py').read_text()
        self.assertIn('from . import test_service_client_hook', integration_init)
        self.assertNotIn('test_U11_sentry_', init)
        package = ast.parse((ROOT / 'amr_sentry/__init__.py').read_text())
        self.assertFalse(any(isinstance(n, ast.ImportFrom) and any(a.name == 'tests' for a in n.names) for n in ast.walk(package)))

if __name__ == '__main__':
    unittest.main()
