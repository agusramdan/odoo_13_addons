"""Additional isolated coverage for ExternalDataSync utility and mapping paths."""
import importlib.util
import pathlib
import types
import unittest
from unittest.mock import Mock


_HELPER = pathlib.Path(__file__).with_name("test_sync_core.py")
_spec = importlib.util.spec_from_file_location("sync_more7_core_helpers", _HELPER)
_helpers = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_helpers)
ExternalDataSync, _utils = _helpers.load_sync_model()


class SyncMoreSevenTest(unittest.TestCase):
    def model(self, **values):
        record = ExternalDataSync()
        for name, value in values.items():
            setattr(record, name, value)
        return record

    def test_ensure_external_data_normalizes_supported_shapes(self):
        record = self.model()
        self.assertEqual(record.ensure_external_data({"id": 4, "name": "Ada"}),
                         {"id": 4, "name": "Ada"})
        self.assertEqual(record.ensure_external_data([5, "Grace"]),
                         {"id": 5, "display_name": "Grace"})
        self.assertEqual(record.ensure_external_data([6, "Grace", "ignored"]),
                         {"id": 6})
        self.assertEqual(record.ensure_external_data(7), {"id": 7})
        self.assertEqual(record.ensure_external_data(None), {})

    def test_get_internal_object_browses_including_archived_record(self):
        internal = _helpers.FakeModelBase()
        internal.with_context = Mock()
        internal.with_context.return_value.browse.return_value.exists.return_value = "record"
        strategy = types.SimpleNamespace(internal_model_object=Mock(return_value=internal))
        record = self.model(sync_strategy_id=strategy, internal_odoo_id=42)

        result = record.get_internal_object()

        self.assertEqual(result, "record")
        internal.with_context.assert_called_once_with(active_test=False)
        internal.with_context.return_value.browse.assert_called_once_with(42)

    def test_reverse_mapping_returns_empty_for_empty_input(self):
        record = self.model()
        self.assertEqual(record.reverse_mapping(False), ([], []))

    def test_reverse_mapping_rejects_non_recordset_when_requested(self):
        record = self.model()
        with self.assertRaisesRegex(ValueError, "Internal Object must"):
            record.reverse_mapping([1], raise_not_found_exception=True)

    def test_reverse_mapping_returns_unmapped_ids_when_errors_suppressed(self):
        internal = _helpers.FakeModelBase()
        internal._name = "res.partner"
        internal.ids = [3, 8]
        search_read = Mock(return_value=[
            {"internal_odoo_id": 3, "external_odoo_id": 30},
            {"internal_odoo_id": 3, "external_odoo_id": 31},
            {"internal_odoo_id": 8, "external_odoo_id": 80},
        ])
        record = self.model(search_read=search_read)
        result = record.reverse_mapping(
            internal, external_app_name="ERP", external_model="res.partner",
            raise_not_found_exception=False,
        )
        self.assertEqual(result, ({3: [30, 31], 8: [80]}, set()))
        self.assertEqual(search_read.call_args[0][0], [
            ("internal_odoo_id", "in", [8, 3]),
            ("internal_model", "=", "res.partner"),
            ("external_app_name", "=", "ERP"),
            ("external_model", "=", "res.partner"),
        ])


if __name__ == "__main__":
    unittest.main()
