"""AC-04: existing offline component tests only; not full AC acceptance."""
from focused_support import execute, make_suite
SELECTORS = ['test_U11_sentry_policy', 'test_U11_sentry_model']
EXPECTED = 15
def load_tests(loader, tests, pattern):
    raise RuntimeError('Discovery disabled: use strict direct entrypoint; skips cannot be validated by unittest discovery')
if __name__ == '__main__':
    execute(SELECTORS, EXPECTED)
