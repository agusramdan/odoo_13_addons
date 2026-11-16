"""Exercise the addon-owned AC runner against real temporary pytest cases."""
import ast
import tempfile
import unittest
from pathlib import Path
from types import MappingProxyType

from unit.ac_test_runner import run_selection


class TestAcTestRunner(unittest.TestCase):
    def run_files(self, cases):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            selectors = []
            for filename, source in cases.items():
                path = root / filename
                path.write_text(source)
                selectors.extend('{}::{}'.format(path, node.name) for node in ast.parse(source).body
                                 if isinstance(node, ast.FunctionDef) and node.name.startswith('test_'))
            return run_selection(selectors, root=str(root))

    def test_real_pytest_pass_is_counted_from_reports(self):
        result = self.run_files({'test_pass.py': 'def test_one(): pass\ndef test_two(): pass\n'})
        self.assertTrue(result['passed'], result)
        self.assertEqual((result['selected'], result['distinct'], result['executed']), (2, 2, 2))

    def test_missing_case_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'test_missing.py'
            path.write_text('value = 1\n')
            result = run_selection([str(path) + '::test_expected'], root=directory)
        self.assertFalse(result['passed'])
        self.assertEqual((result['selected'], result['executed']), (0, 0))

    def test_duplicate_selection_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'test_one.py'
            path.write_text('def test_one(): pass\n')
            selector = str(path) + '::test_one'
            result = run_selection([selector, selector], root=directory)
        self.assertFalse(result['passed'])
        self.assertEqual((result['selected'], result['distinct']), (1, 1))

    def test_skip_xfail_xpass_and_failure_do_not_pass(self):
        cases = {
            'test_bad.py': (
                'import pytest\n'
                'def test_skip(): pytest.skip("unavailable")\n'
                '@pytest.mark.xfail(reason="expected")\ndef test_xfail(): assert False\n'
                '@pytest.mark.xfail(reason="expected")\ndef test_xpass(): assert True\n'
                'def test_fail(): assert False\n'
            )
        }
        result = self.run_files(cases)
        self.assertFalse(result['passed'], result)
        self.assertEqual(result['executed'], 4)
        self.assertEqual((result['skipped'], result['expected_failures'],
                          result['unexpected_successes'], result['failures']), (1, 1, 1, 1))

    def test_reviewed_selectors_use_their_unit_directory_as_pytest_root(self):
        from unit.ac_test_runner import BASELINE, _selection_root
        for ac in ('AC01', 'AC04', 'AC07'):
            with self.subTest(ac=ac):
                root = _selection_root(BASELINE[ac])
                self.assertEqual(root.name, 'unit')
                self.assertTrue(all(Path(selector.split('::', 1)[0]).parent == root
                                    for selector in BASELINE[ac]))

    def test_inventory_is_reviewed_and_cannot_be_overridden_by_cli(self):
        from unit import ac_test_runner
        self.assertIn('AC02', ac_test_runner.BASELINE)
        self.assertIsInstance(ac_test_runner.BASELINE, type(MappingProxyType({})))
        with self.assertRaises((AttributeError, TypeError)):
            ac_test_runner.BASELINE['AC02'] = ('test_unreviewed.py::test_case',)

    def test_arbitrary_pass_counts_are_not_an_entrypoint_input(self):
        from unit import ac_test_runner
        self.assertFalse(hasattr(ac_test_runner, 'evaluate'))
        self.assertTrue(callable(ac_test_runner.main))


if __name__ == '__main__':
    unittest.main()
