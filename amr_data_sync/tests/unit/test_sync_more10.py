"""Behavioral tests for post-create relation resolution edge cases."""
import importlib.util
import pathlib
import types
import unittest
from unittest.mock import Mock


_HELPER = pathlib.Path(__file__).with_name("test_sync_core.py")
_SPEC = importlib.util.spec_from_file_location("sync_more10_core_helpers", _HELPER)
_HELPERS = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_HELPERS)
ExternalDataSync, _utils = _HELPERS.load_sync_model()


class SyncMoreTenTest(unittest.TestCase):
    def model(self, **values):
        record = ExternalDataSync()
        for name, value in values.items():
            setattr(record, name, value)
        return record

    def test_post_create_applies_resolved_many2one_and_defers_unresolved_relation(self):
        resolved = types.SimpleNamespace(
            field_after_create=False, state="done", field_type="many2one",
            name="country_id", get_data_relation=Mock(return_value=42),
            process_field_after_create=Mock())
        pending = types.SimpleNamespace(
            field_after_create=True, state="process", field_type="one2many",
            name="line_ids", get_data_relation=Mock(return_value=False),
            process_field_after_create=Mock())
        record = self.model(related_ids=[resolved, pending], write_error_safe=Mock())
        internal = types.SimpleNamespace(write=Mock())

        original_now = ExternalDataSync.process_field_after_create.__globals__["fields"].Datetime.now
        ExternalDataSync.process_field_after_create.__globals__["fields"].Datetime.now = Mock(return_value="now")
        original_timedelta = ExternalDataSync.process_field_after_create.__globals__["datetime"].timedelta
        ExternalDataSync.process_field_after_create.__globals__["datetime"].timedelta = lambda **kwargs: " + one hour"
        try:
            result = record.process_field_after_create(internal)
        finally:
            ExternalDataSync.process_field_after_create.__globals__["fields"].Datetime.now = original_now
            ExternalDataSync.process_field_after_create.__globals__["datetime"].timedelta = original_timedelta

        self.assertEqual(result, {"country_id": 42})
        internal.write.assert_called_once_with({"country_id": 42})
        resolved.process_field_after_create.assert_not_called()
        pending.process_field_after_create.assert_called_once_with()
        record.write_error_safe.assert_called_once_with({
            "error_info": "Issue Process Field After Create",
            "state": "need_resolve",
            "next_processing_datetime": "now + one hour",
        })

    def test_post_create_does_not_write_empty_relations_or_mark_resolved_records_pending(self):
        relation = types.SimpleNamespace(
            field_after_create=False, state="done", field_type="many2one",
            name="parent_id", get_data_relation=Mock(return_value=False),
            process_field_after_create=Mock())
        record = self.model(related_ids=[relation], write_error_safe=Mock())
        internal = types.SimpleNamespace(write=Mock())

        result = record.process_field_after_create(internal)

        self.assertEqual(result, {})
        internal.write.assert_not_called()
        record.write_error_safe.assert_not_called()
        relation.process_field_after_create.assert_not_called()


if __name__ == "__main__":
    unittest.main()
