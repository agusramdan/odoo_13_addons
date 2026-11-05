"""AC-06: existing offline component tests only; not full AC acceptance."""
from focused_support import execute, make_suite
SELECTORS = ['test_U11_sentry_bootstrap.SentryBootstrapContractTest.test_invalid_override_is_nonfatal_and_warns_without_secrets', 'test_U11_sentry_behavior.SentryReporting.test_run_action_reporter_failure_logs_only_safe_diagnostics']
EXPECTED = 2
def load_tests(loader, tests, pattern):
    raise RuntimeError('Discovery disabled: use strict direct entrypoint; skips cannot be validated by unittest discovery')
if __name__ == '__main__':
    execute(SELECTORS, EXPECTED)
