"""AC-07: existing offline component tests only; not full AC acceptance."""
from focused_support import execute, make_suite
SELECTORS = ['test_U11_sentry_behavior.SentryReporting.test_real_service_client_call_outcomes_privacy_and_transport_semantics', 'test_U11_sentry_behavior.SentryReporting.test_call_pre_response_failure_returns_none_without_masking', 'test_U11_sentry_behavior.SentryReporting.test_real_dispatch_send_success_and_failure_reporting_are_best_effort', 'test_U11_sentry_behavior.SentryReporting.test_dispatch_success_log_failure_uses_baseline_error_log_path', 'test_U11_sentry_behavior.SentryReporting.test_create_log_accepts_service_client_integer_id', 'test_U11_sentry_behavior.SentryReporting.test_real_log_send_reports_http_failure_and_preserves_logged_error', 'test_U11_sentry_behavior.SentryReporting.test_real_log_send_reports_success', 'test_U11_sentry_behavior.SentryReporting.test_real_log_send_reporter_failure_preserves_log_outcome', 'test_new_n3']
EXPECTED = 9
def load_tests(loader, tests, pattern):
    raise RuntimeError('Discovery disabled: use strict direct entrypoint; skips cannot be validated by unittest discovery')
if __name__ == '__main__':
    execute(SELECTORS, EXPECTED)
