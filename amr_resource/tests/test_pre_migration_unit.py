"""Offline checks for the pre-migration guard; real upgrade tests remain separate."""
import importlib.util
from pathlib import Path
import unittest


PATH = (Path(__file__).resolve().parents[1] / 'migrations' / '13.0.1.1.0'
        / 'pre-check-issuer-duplicates.py')
spec = importlib.util.spec_from_file_location('pre_migration_guard', str(PATH))
assert spec is not None and spec.loader is not None
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


class Cursor:
    def __init__(self, results):
        self.results = iter(results)
        self.queries = []

    def execute(self, query):
        self.queries.append(query)

    def fetchone(self):
        return (next(self.results),)


class PreMigrationGuardTests(unittest.TestCase):
    def test_unknown_schema_stops_before_data_query(self):
        cr = Cursor([False])
        with self.assertRaisesRegex(RuntimeError, 'schema unavailable'):
            guard.migrate(cr, '13.0.1.0.0')
        self.assertEqual(len(cr.queries), 1)

    def test_duplicate_stops_without_value_in_diagnostic(self):
        cr = Cursor([True, True])
        with self.assertRaisesRegex(RuntimeError, '^Duplicate issuer registry entries; upgrade stopped$'):
            guard.migrate(cr, '13.0.1.0.0')
        self.assertEqual(len(cr.queries), 2)

    def test_invalid_issuer_stops_upgrade_without_disclosing_values(self):
        # The third result represents an invalid stored issuer, after schema
        # and duplicate checks have passed.
        cr = Cursor([True, False, True])
        with self.assertRaisesRegex(RuntimeError, '^Invalid issuer registry entries; upgrade stopped$'):
            guard.migrate(cr, '13.0.1.0.0')

    def test_distinct_rows_allow_upgrade(self):
        cr = Cursor([True, False, False])
        guard.migrate(cr, '13.0.1.0.0')
        self.assertEqual(len(cr.queries), 3)


if __name__ == '__main__':
    unittest.main()
