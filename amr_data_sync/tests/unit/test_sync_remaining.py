"""Behavior coverage for remaining ExternalDataSync mapping methods.

The model and its Odoo boundaries are loaded with the established offline
fixture; this does not claim ORM or database integration.
"""
import importlib.util
import pathlib
import types
import unittest
from unittest.mock import Mock


_HELPER = pathlib.Path(__file__).with_name("test_sync_core.py")
_spec = importlib.util.spec_from_file_location("sync_remaining_core_helpers", _HELPER)
_helpers = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_helpers)
ExternalDataSync, _utils = _helpers.load_sync_model()


class SyncRemainingTest(unittest.TestCase):
    def test_reverse_mapping_combines_sync_rows_and_reverse_lookups(self):
        model = ExternalDataSync()
        model.env = {"external.data.lookup": types.SimpleNamespace(search_read=Mock(
            return_value=[{"internal_id": 2, "external_id": "lookup-2"},
                          {"internal_id": 3, "external_id": "lookup-3"}]))}
        model.search_read = Mock(return_value=[
            {"internal_odoo_id": 1, "external_odoo_id": "sync-1"},
        ])
        internal = _helpers.FakeModelBase()
        internal._name, internal.ids = "res.partner", [1, 2, 3]

        mapped, missing = model.reverse_mapping(
            internal, external_app_name="remote", external_model="Contact",
            raise_not_found_exception=False)

        self.assertEqual(mapped, {1: ["sync-1"], 2: ["lookup-2"], 3: ["lookup-3"]})
        # The current method does not subtract fallback lookup IDs from its
        # not_mapped_ids set; preserve that observed return contract here.
        self.assertEqual(missing, {2, 3})
        self.assertEqual(model.search_read.call_args[0][0], [
            ("internal_odoo_id", "in", [1, 2, 3]), ("internal_model", "=", "res.partner"),
            ("external_app_name", "=", "remote"), ("external_model", "=", "Contact")])
        lookup_search = model.env["external.data.lookup"].search_read
        self.assertEqual(lookup_search.call_args[0][0], [
            ("internal_id", "in", [2, 3]), ("internal_model", "=", "res.partner"),
            ("external_app_name", "=", "remote"), ("external_model", "=", "Contact"),
            ("reverse_able", "=", True)])

    def test_reverse_mapping_reports_unmapped_ids_when_nonraising(self):
        model = ExternalDataSync()
        model.search_read = Mock(return_value=[])
        model.env = {"external.data.lookup": types.SimpleNamespace(search_read=Mock(return_value=[]))}
        internal = _helpers.FakeModelBase()
        internal._name, internal.ids = "res.partner", [7]

        mapped, missing = model.reverse_mapping(
            internal, external_app_name="remote", external_model="Contact",
            raise_not_found_exception=False)

        self.assertEqual(mapped, {})
        self.assertEqual(missing, {7})

    def test_reverse_mapping_rejects_non_recordset_or_missing_application(self):
        model = ExternalDataSync()
        self.assertEqual(model.reverse_mapping(False), ([], []))
        self.assertEqual(model.reverse_mapping(object(), raise_not_found_exception=False), ([], []))
        internal = _helpers.FakeModelBase()
        internal._name, internal.ids = "res.partner", [1]
        with self.assertRaisesRegex(ValueError, "external_app_name not set"):
            model.reverse_mapping(internal)

    def test_get_or_create_reuses_existing_mapping_before_creating(self):
        model = ExternalDataSync()
        existing = object()
        model.search = Mock(return_value=existing)
        model.data_from_external = Mock(side_effect=AssertionError("must reuse existing"))
        strategy = types.SimpleNamespace(id=42)

        result = model.get_or_create({"id": 13}, strategy)

        self.assertIs(result, existing)
        self.assertEqual(model.search.call_args[0][0], [
            ("external_odoo_id", "=", 13), ("sync_strategy_id", "=", 42)])
        model.data_from_external.assert_not_called()

    def test_ensure_external_data_preserves_empty_and_unsupported_inputs_as_empty(self):
        normalize = ExternalDataSync.ensure_external_data
        self.assertEqual(normalize(ExternalDataSync(), []), {})
        self.assertEqual(normalize(ExternalDataSync(), None), {})
        self.assertEqual(normalize(ExternalDataSync(), "13"), {})


if __name__ == "__main__":
    unittest.main()
