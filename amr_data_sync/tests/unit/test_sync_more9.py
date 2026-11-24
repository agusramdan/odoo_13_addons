"""Behavioral coverage for additional ExternalDataSync branches."""
import importlib.util
import pathlib
import types
import unittest
from unittest.mock import Mock

_HELPER = pathlib.Path(__file__).with_name("test_sync_core.py")
_SPEC = importlib.util.spec_from_file_location("sync_more9_core_helpers", _HELPER)
_HELPERS = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_HELPERS)
ExternalDataSync, _utils = _HELPERS.load_sync_model()


class SyncMoreNineTest(unittest.TestCase):
    def model(self, **values):
        record = ExternalDataSync()
        for name, value in values.items():
            setattr(record, name, value)
        return record

    def test_ensure_external_data_normalizes_supported_input_shapes(self):
        ensure = self.model().ensure_external_data
        self.assertEqual(ensure({"id": 4, "name": "A"}), {"id": 4, "name": "A"})
        self.assertEqual(ensure([4, "A"]), {"id": 4, "display_name": "A"})
        self.assertEqual(ensure([4, "A", "ignored"]), {"id": 4})
        self.assertEqual(ensure([]), {})
        self.assertEqual(ensure(9), {"id": 9})
        self.assertEqual(ensure("9"), {})

    def test_get_internal_object_browses_including_archived_record(self):
        recordset = type("Record", (_HELPERS.FakeRecordset,), {"exists": Mock(return_value="found")})()
        model_object = type("Model", (_HELPERS.FakeModelBase,), {})()
        model_object.with_context = Mock(return_value=types.SimpleNamespace(browse=Mock(return_value=recordset)))
        strategy = types.SimpleNamespace(internal_model_object=Mock(return_value=model_object))
        record = self.model(sync_strategy_id=strategy, internal_odoo_id=23)

        result = record.get_internal_object()

        self.assertEqual(result, "found")
        model_object.with_context.assert_called_once_with(active_test=False)
        model_object.with_context.return_value.browse.assert_called_once_with(23)
        recordset.exists.assert_called_once_with()

    def test_get_internal_object_returns_model_when_no_internal_id(self):
        model_object = types.SimpleNamespace()
        strategy = types.SimpleNamespace(internal_model_object=Mock(return_value=model_object))
        record = self.model(sync_strategy_id=strategy, internal_odoo_id=False)

        self.assertIs(record.get_internal_object(), model_object)

    def test_get_internal_object_uses_internal_model_environment_fallback(self):
        model_object = types.SimpleNamespace()
        record = self.model(sync_strategy_id=False, internal_model="res.partner",
                            env={"res.partner": model_object}, internal_odoo_id=False)

        self.assertIs(record.get_internal_object(), model_object)

    def test_write_error_persists_error_schedule_and_json_payload(self):
        record = self.model(write_error_safe=Mock())
        original_timedelta = ExternalDataSync.write_error.__globals__["datetime"].timedelta
        ExternalDataSync.write_error.__globals__["datetime"].timedelta = lambda **kwargs: "later"
        try:
            record.write_error("traceback text", {"name": "bad"})
        finally:
            ExternalDataSync.write_error.__globals__["datetime"].timedelta = original_timedelta

        values = record.write_error_safe.call_args[0][0]
        self.assertEqual(values["error_info"], "traceback text")
        self.assertEqual(values["state"], "error")
        self.assertEqual(values["last_error"], "now")
        self.assertEqual(values["last_processing_datetime"], "now")
        self.assertEqual(values["next_processing_datetime"], "nowlater")
        self.assertEqual(values["payload_json"], '{"name": "bad"}')


if __name__ == "__main__":
    unittest.main()
