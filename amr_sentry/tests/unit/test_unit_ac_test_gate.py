"""Tests for the addon-owned fail-closed component test gate."""
import unittest

from unit.ac_test_gate import evaluate


class TestFocusedGate(unittest.TestCase):
    def evaluate(self, expected=1, selected=None, **outcomes):
        return evaluate(expected, ['case.a'] if selected is None else selected, **outcomes)

    def test_positive_counts_pass(self):
        verdict = self.evaluate(executed=1)
        self.assertTrue(verdict['passed'])
        self.assertEqual((verdict['expected'], verdict['selected'], verdict['distinct'], verdict['executed']),
                         (1, 1, 1, 1))

    def test_count_mismatch_fails(self):
        verdict = self.evaluate(expected=2, executed=1)
        self.assertFalse(verdict['passed'])
        self.assertEqual((verdict['expected'], verdict['selected'], verdict['distinct'], verdict['executed']),
                         (2, 1, 1, 1))

    def test_duplicate_selected_id_fails(self):
        verdict = self.evaluate(expected=2, selected=['case.a', 'case.a'], executed=2)
        self.assertFalse(verdict['passed'])
        self.assertEqual((verdict['expected'], verdict['selected'], verdict['distinct'], verdict['executed']),
                         (2, 2, 1, 2))

    def test_missing_selected_case_fails(self):
        verdict = self.evaluate(expected=2, selected=['case.a'], executed=1)
        self.assertFalse(verdict['passed'])
        self.assertEqual((verdict['expected'], verdict['selected'], verdict['distinct'], verdict['executed']),
                         (2, 1, 1, 1))

    def test_zero_expected_count_fails(self):
        verdict = self.evaluate(expected=0, selected=[], executed=0)
        self.assertFalse(verdict['passed'])
        self.assertEqual((verdict['expected'], verdict['selected'], verdict['distinct'], verdict['executed']),
                         (0, 0, 0, 0))

    def test_skip_fails(self):
        verdict = self.evaluate(executed=1, skipped=1)
        self.assertFalse(verdict['passed'])
        self.assertEqual(verdict['skipped'], 1)

    def test_expected_failure_fails(self):
        verdict = self.evaluate(executed=1, expected_failures=1)
        self.assertFalse(verdict['passed'])
        self.assertEqual(verdict['expected_failures'], 1)

    def test_unexpected_success_fails(self):
        verdict = self.evaluate(executed=1, unexpected_successes=1)
        self.assertFalse(verdict['passed'])
        self.assertEqual(verdict['unexpected_successes'], 1)

    def test_failure_or_error_fails(self):
        for outcomes in ({'failures': 1}, {'errors': 1}):
            with self.subTest(outcomes=outcomes):
                verdict = self.evaluate(executed=1, **outcomes)
                self.assertFalse(verdict['passed'])
                self.assertEqual((verdict['failures'], verdict['errors']),
                                 (outcomes.get('failures', 0), outcomes.get('errors', 0)))
