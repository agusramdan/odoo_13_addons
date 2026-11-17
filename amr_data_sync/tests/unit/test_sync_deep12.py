"""Behavioral edge coverage for ExternalDataSync mapping utilities."""
import importlib.util
import pathlib
import types
import unittest
from unittest.mock import Mock

_HELPER = pathlib.Path(__file__).with_name("test_sync_core.py")
_SPEC = importlib.util.spec_from_file_location("sync_deep12_core_helpers", _HELPER)
_HELPERS = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_HELPERS)
ExternalDataSync, _utils = _HELPERS.load_sync_model()


class SyncDeepTwelveTest(unittest.TestCase):
    def model(self, **values):
        record = ExternalDataSync()
        for name, value in values.items():
            setattr(record, name, value)
        return record

    def test_ensure_external_data_normalizes_supported_shapes_and_rejects_others(self):
        record = self.model()
        values = {"id": 4, "display_name": "Four"}
        self.assertIs(record.ensure_external_data(values), values)
        self.assertEqual(record.ensure_external_data([4, "Four"]),
                         {"id": 4, "display_name": "Four"})
        self.assertEqual(record.ensure_external_data([4, "Four", "ignored"]), {"id": 4})
        self.assertEqual(record.ensure_external_data(4), {"id": 4})
        self.assertEqual(record.ensure_external_data("4"), {})
        self.assertEqual(record.ensure_external_data(None), {})

    def test_reverse_mapping_collects_multiple_sync_rows_and_subtracts_mapped_ids(self):
        internal = _HELPERS.FakeModelBase()
        internal._name, internal.ids = "res.partner", [3, 8]
        lookup = types.SimpleNamespace(search_read=Mock(return_value=[]))
        record = self.model(search_read=Mock(return_value=[
            {"internal_odoo_id": 3, "external_odoo_id": 30},
            {"internal_odoo_id": 3, "external_odoo_id": 31},
        ]), env={"external.data.lookup": lookup})

        mapping, missing = record.reverse_mapping(
            internal, external_app_name="remote", external_model="Contact",
            raise_not_found_exception=False)

        self.assertEqual(mapping, {3: [30, 31]})
        self.assertEqual(missing, {8})
        self.assertEqual(set(record.search_read.call_args[0][0][0][2]), {3, 8})
        self.assertEqual(record.search_read.call_args[0][0][1:], [
            ("internal_model", "=", "res.partner"),
            ("external_app_name", "=", "remote"), ("external_model", "=", "Contact")])
        self.assertEqual(lookup.search_read.call_args[0][0], [
            ("internal_id", "in", [8]), ("internal_model", "=", "res.partner"),
            ("external_app_name", "=", "remote"), ("external_model", "=", "Contact"),
            ("reverse_able", "=", True)])

    def test_reverse_mapping_uses_reverse_enabled_lookup_and_deduplicates_missing(self):
        internal = _HELPERS.FakeModelBase()
        internal._name, internal.ids = "res.partner", [3, 8]
        lookup = types.SimpleNamespace(search_read=Mock(return_value=[
            {"internal_id": 8, "external_id": 80},
        ]))
        record = self.model(search_read=Mock(return_value=[
            {"internal_odoo_id": 3, "external_odoo_id": 30},
        ]), env={"external.data.lookup": lookup})

        mapping, missing = record.reverse_mapping(
            internal, external_app_name="remote", raise_not_found_exception=False)

        self.assertEqual(mapping, {3: [30], 8: [80]})
        self.assertEqual(missing, {8})
        self.assertEqual(lookup.search_read.call_args[1]["fields"], ["internal_id", "external_id"])

    def test_reverse_mapping_rejects_non_model_input_or_returns_empty_when_optional(self):
        record = self.model()
        with self.assertRaisesRegex(ValueError, "Internal Object must"):
            record.reverse_mapping([3], external_app_name="remote")
        self.assertEqual(record.reverse_mapping(
            [3], external_app_name="remote", raise_not_found_exception=False), ([], []))

    def test_reverse_mapping_reports_unmapped_ids_when_exception_disabled(self):
        internal = _HELPERS.FakeModelBase()
        internal._name, internal.ids = "res.partner", [6]
        lookup = types.SimpleNamespace(search_read=Mock(return_value=[]))
        record = self.model(search_read=Mock(return_value=[]), env={"external.data.lookup": lookup})

        mapping, missing = record.reverse_mapping(
            internal, external_app_name="remote", raise_not_found_exception=False)

        self.assertEqual(mapping, {})
        self.assertEqual(missing, {6})

    def test_reverse_mapping_raises_for_unmapped_ids(self):
        internal = _HELPERS.FakeModelBase()
        internal._name, internal.ids = "res.partner", [6]
        lookup = types.SimpleNamespace(search_read=Mock(return_value=[]))
        record = self.model(search_read=Mock(return_value=[]), env={"external.data.lookup": lookup})

        with self.assertRaisesRegex(ValueError, "found not mapped data"):
            record.reverse_mapping(internal, external_app_name="remote")


if __name__ == "__main__":
    unittest.main()
