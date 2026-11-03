"""AC-08: existing offline component tests only; not full AC acceptance."""
from focused_support import execute, make_suite
SELECTORS = ['test_U11_sentry_behavior.SentryReporting.test_run_action_call_exception_is_not_reported_twice', 'test_U11_sentry_behavior.SentryReporting.test_run_action_handler_exception_is_reported_once_with_valid_keywords']
EXPECTED = 2
def load_tests(loader, tests, pattern):
    raise RuntimeError('Discovery disabled: use strict direct entrypoint; skips cannot be validated by unittest discovery')
if __name__ == '__main__':
    execute(SELECTORS, EXPECTED)
