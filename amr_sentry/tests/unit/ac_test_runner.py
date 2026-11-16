"""Run reviewed AC selectors and derive verdicts from pytest's live reports."""
import argparse
import os
import sys
from pathlib import Path
from types import MappingProxyType

import pytest


_ADDON = Path(__file__).resolve().parents[2]
_ROOT = _ADDON.parent


def _selection_root(selectors):
    paths = {Path(selector.split('::', 1)[0]).resolve().parent for selector in selectors}
    if len(paths) != 1:
        raise ValueError('Reviewed selectors must share one unit-test directory')
    return next(iter(paths))


def _ids(path, names):
    return tuple(str(_ADDON / 'tests' / 'unit' / path) + '::' + name for name in names)


BASELINE = MappingProxyType({
    'AC01': tuple(str(_ROOT / 'amr_service_client/tests/unit/test_unit_sentry_bridge.py') +
                  '::TestSentryBridge::' + name for name in (
                      'test_delegates_fixed_arguments_without_importing_sentry_sdk',
                      'test_hook_failure_does_not_escape')),
    'AC02': _ids('test_unit_sentry_config.py', (
        'TestSentryConfig::test_yaml_override_maps_sentry_kwargs_and_policy',
        'TestSentryConfig::test_json_override_maps_configuration',
        'TestSentryConfig::test_empty_environment_uses_default_path',
        'TestSentryConfig::test_invalid_service_client_policy_is_rejected')),
    'AC03': _ids('test_unit_sentry_safe_file.py', (
        'SafeFileProfilePresenceTest::test_active_file_rejects_each_missing_safety_key',
        'SafeFileProfilePresenceTest::test_each_present_safety_value_has_exact_type_and_value',
        'SafeFileProfilePresenceTest::test_rejects_non_allowlisted_sentry_options_even_when_disabled',
        'SafeFileProfilePresenceTest::test_metadata_must_be_strings_when_present',
        'SafeFileProfilePresenceTest::test_dsn_must_be_null_or_string_even_when_disabled')),
    'AC04': _ids('test_unit_sentry_policy.py', (
        'SentryPolicyTests::test_disabled_policy_never_initializes_or_captures',
        'SentryPolicyTests::test_none_mode_never_initializes_or_captures',
        'SentryPolicyTests::test_missing_dsn_never_initializes_or_captures',
        'SentryPolicyTests::test_all_mode_initializes_only_sdk_options_and_reports_both_outcomes',
        'SentryPolicyTests::test_error_mode_reports_only_errors',
        'SentryPolicyTests::test_selected_mode_requires_opt_in_and_reports_both',
        'SentryPolicyTests::test_init_failure_disables_reporter_without_exposing_exception',
        'SentryPolicyTests::test_capture_failures_are_swallowed')) + _ids('test_unit_sentry_model.py', (
        'TestOptionalSentryModelHook::test_selected_dispatch_bound_opted_in_singleton_reports_once',
        'TestOptionalSentryModelHook::test_selected_dispatch_suppresses_opted_out_and_empty_recordsets',
        'TestOptionalSentryModelHook::test_selected_explicit_client_takes_precedence_over_bound_client',
        'TestOptionalSentryModelHook::test_success_reports_once_with_exact_service_client',
        'TestOptionalSentryModelHook::test_missing_service_client_uses_core_hook_default',
        'TestOptionalSentryModelHook::test_exception_reports_failure_without_forwarding_private_arguments',
        'TestOptionalSentryModelHook::test_reporter_failure_does_not_escape_hook')),
    'AC05': (),
    'AC06': _ids('test_unit_sentry_bootstrap.py', (
        'SentryBootstrapContractTest::test_invalid_override_is_nonfatal_and_warns_without_secrets',)) +
        _ids('test_unit_sentry_behavior.py', (
        'SentryReporting::test_run_action_reporter_failure_logs_only_safe_diagnostics',)),
    'AC07': _ids('test_unit_sentry_behavior.py', (
        'SentryReporting::test_real_service_client_call_outcomes_privacy_and_transport_semantics',
        'SentryReporting::test_call_pre_response_failure_returns_none_without_masking',
        'SentryReporting::test_real_dispatch_send_success_and_failure_reporting_are_best_effort',
        'SentryReporting::test_dispatch_success_log_failure_uses_baseline_error_log_path',
        'SentryReporting::test_create_log_accepts_service_client_integer_id',
        'SentryReporting::test_real_log_send_reports_http_failure_and_preserves_logged_error',
        'SentryReporting::test_real_log_send_reports_success',
        'SentryReporting::test_real_log_send_reporter_failure_preserves_log_outcome',
        'SentryReporting::test_call_failure_counts_and_sdk_failure_preserve_original_outcomes',
        'SentryReporting::test_call_http_counts_and_sdk_failure_preserve_original_outcomes',
        'SentryReporting::test_dispatch_success_without_active_log_reports_one_outcome',
        'SentryReporting::test_dispatch_error_logging_matrix_component')),
    'AC08': _ids('test_unit_sentry_behavior.py', (
        'SentryReporting::test_run_action_call_exception_is_not_reported_twice',
        'SentryReporting::test_run_action_handler_exception_is_reported_once_with_valid_keywords',
        'SentryReporting::test_run_action_success_then_next_action_failure_are_distinct')),
    'AC09': _ids('test_unit_sentry_bootstrap.py', (
        'SentryBootstrapContractTest::test_import_initializes_once_with_sentry_namespace_only',)),
    'AC10': _ids('test_unit_sentry_bootstrap.py', (
        'SentryPackagingContractTest::test_optional_addon_declares_dependencies_and_exact_pins',
        'SentryPackagingContractTest::test_core_packaging_no_longer_declares_sentry_dependencies')),
    'AC11': _ids('test_unit_sentry_docs.py', (
        'SentryDocs::test_operator_guides_and_entry_point_links_exist',
        'SentryDocs::test_root_addon_index_lists_optional_addon',
        'SentryDocs::test_configuration_mechanism_and_policy_are_documented',
        'SentryDocs::test_guides_document_target_and_test_only_dependency_boundary',
        'SentryDocs::test_operator_discloses_original_exception_residual_risk',
        'SentryDocs::test_yaml_example_is_valid_and_safe_by_default',
        'ActivatedOperatorExamples::test_yaml_and_json_examples_load_when_activated')),
    'AC12': (),
})


class _Results:
    def __init__(self):
        self.items = []
        self.reports = []
        self.errors = 0

    def pytest_collectreport(self, report):
        if report.failed:
            self.errors += 1

    def pytest_collection_finish(self, session):
        self.items = [item.nodeid for item in session.items]

    def pytest_runtest_logreport(self, report):
        if report.when == 'call':
            self.reports.append(report)


def run_selection(selectors, root=None):
    """Execute exact pytest selectors; counts only come from collection/reports."""
    unique = len(set(selectors))
    plugin = _Results()
    args = ['-q', '-p', 'no:cacheprovider', '--import-mode=importlib']
    if root:
        args.extend(['--rootdir=' + root, '--confcutdir=' + root])
    args.extend(selectors)
    exit_code = pytest.main(args, plugins=[plugin])
    selected, executed = len(plugin.items), len(plugin.reports)
    failures = sum(report.failed and not hasattr(report, 'wasxfail') for report in plugin.reports)
    errors = plugin.errors + sum(report.when in ('setup', 'teardown') and report.failed
                                 for report in plugin.reports)
    skipped = sum(report.skipped and not hasattr(report, 'wasxfail') for report in plugin.reports)
    expected_failures = sum(report.skipped and hasattr(report, 'wasxfail') for report in plugin.reports)
    unexpected_successes = sum(report.passed and hasattr(report, 'wasxfail') for report in plugin.reports)
    expected_ids = [os.path.relpath(selector.split('::', 1)[0], root or os.getcwd()) +
                    ('::' + selector.split('::', 1)[1] if '::' in selector else '')
                    for selector in selectors]
    passed = bool(selectors) and unique == len(selectors) and selected == len(selectors) and \
        len(set(plugin.items)) == selected and set(plugin.items) == set(expected_ids) and executed == selected and not failures and not errors and \
        not skipped and not expected_failures and not unexpected_successes and exit_code == 0
    return {'expected': len(selectors), 'selected': selected, 'distinct': len(set(plugin.items)),
            'executed': executed, 'ids': tuple(plugin.items), 'failures': failures, 'errors': errors, 'skipped': skipped,
            'expected_failures': expected_failures, 'unexpected_successes': unexpected_successes,
            'passed': passed}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('ac', choices=tuple(BASELINE))
    args = parser.parse_args(argv)
    selectors = BASELINE[args.ac]
    if not selectors:
        print('{} NOT RUN: real SDK/telemetry oracle unavailable'.format(args.ac)
              if args.ac == 'AC05' else '{} NOT RUN: monitoring/restore oracle unavailable'.format(args.ac))
        return 2
    scripts = str(_ROOT / 'skills' / 'odoo-unit-test' / 'scripts')
    sys.path.insert(0, scripts)
    from isolation import install, self_check
    install()
    self_check()
    result = run_selection(selectors, root=str(_selection_root(selectors)))
    print('{} {}'.format(args.ac, result))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
