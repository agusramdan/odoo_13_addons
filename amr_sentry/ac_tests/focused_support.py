"""Strict unittest execution for component-only focused suites."""
import json
import sys
import unittest

def make_suite(loader, selectors):
    return unittest.TestSuite(loader.loadTestsFromName(name) for name in selectors)

def test_ids(suite):
    for test in suite:
        if isinstance(test, unittest.TestSuite):
            yield from test_ids(test)
        else:
            yield test.id()

def execute(selectors, expected):
    suite = make_suite(unittest.defaultTestLoader, selectors)
    selected = suite.countTestCases()
    ids = list(test_ids(suite))
    distinct = len(set(ids))
    result = unittest.TextTestRunner(stream=sys.stdout, verbosity=2).run(suite)
    data = dict(expected=expected, selected=selected, distinct=distinct, ran=result.testsRun,
                failures=len(result.failures), errors=len(result.errors),
                skipped=len(result.skipped), expected_failures=len(result.expectedFailures),
                unexpected_successes=len(result.unexpectedSuccesses))
    good = (expected > 0 and selected == expected and distinct == expected and result.testsRun == expected
            and result.wasSuccessful() and not result.skipped and not result.expectedFailures
            and not result.unexpectedSuccesses)
    data['status'] = 'COMPONENT PASS' if good else 'FAIL/INVALID'
    print('FOCUSED_RESULT=' + json.dumps(data, sort_keys=True), flush=True)
    sys.exit(0 if good else 1)
