"""Offline behavioral coverage for sync record access and cache paths."""
import importlib.util
import json
import pathlib
import types
import unittest
from unittest.mock import Mock

_HELPER = pathlib.Path(__file__).with_name("test_sync_core.py")
_SPEC = importlib.util.spec_from_file_location("sync_deep14_core_helpers", _HELPER)
_HELPERS = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_HELPERS)
ExternalDataSync, _utils = _HELPERS.load_sync_model()


class SyncDeepFourteenTest(unittest.TestCase):
    def model(self, **values):
        record = ExternalDataSync()
        for name, value in values.items():
            setattr(record, name, value)
        return record

    def test_cached_create_data_returns_dict_without_fetch_or_write(self):
        record = self.model(need_get_data_json=False,
                            data_json='{"name": "Cached", "active": true}',
                            get_external_one_data=Mock(), write=Mock())

        result = record.get_json_data_for_create()

        self.assertEqual(result, {"name": "Cached", "active": True})
        record.get_external_one_data.assert_not_called()
        record.write.assert_not_called()

    def test_external_create_data_persists_payload_and_parses_write_date(self):
        context = _Context()
        record = self.model(need_get_data_json=True,
                            get_external_one_data=Mock(return_value={
                                "id": 9, "write_date": "2026-04-05 06:07:08"}),
                            env=types.SimpleNamespace(cr=types.SimpleNamespace(
                                savepoint=Mock(return_value=context))),
                            write=Mock())
        datetime_field = ExternalDataSync.get_json_data_for_create.__globals__["fields"].Datetime
        old_parser = datetime_field.to_datetime
        datetime_field.to_datetime = lambda value: ("parsed", value)
        try:
            result = record.get_json_data_for_create()
        finally:
            datetime_field.to_datetime = old_parser

        self.assertEqual(result, {"id": 9, "write_date": "2026-04-05 06:07:08"})
        record.env.cr.savepoint.assert_called_once_with()
        record.write.assert_called_once_with({
            "need_get_data_json": False,
            "data_json": json.dumps(result),
            "external_last_update": ("parsed", "2026-04-05 06:07:08")})

    def test_external_absence_is_cached_and_returns_inactive_marker(self):
        record = self.model(need_get_data_json=True,
                            get_external_one_data=Mock(return_value=False), write=Mock())

        result = record.get_json_data_for_create()

        self.assertEqual(result, {"active": False})
        record.write.assert_called_once_with({"need_get_data_json": False, "data_json": "false"})

    def test_internal_object_browses_inactive_record_and_returns_existing(self):
        existing = object()
        browsed = _HELPERS.FakeModelBase()
        browsed.with_context = Mock(return_value=types.SimpleNamespace(
            browse=Mock(return_value=types.SimpleNamespace(exists=Mock(return_value=existing)))))
        strategy = types.SimpleNamespace(internal_model_object=Mock(return_value=browsed))
        record = self.model(sync_strategy_id=strategy, internal_odoo_id=23)

        result = record.get_internal_object()

        self.assertIs(result, existing)
        browsed.with_context.assert_called_once_with(active_test=False)
        browsed.with_context.return_value.browse.assert_called_once_with(23)

    def test_open_internal_action_uses_model_and_record_identity(self):
        record = self.model(internal_model="res.partner", internal_odoo_id=71,
                            ensure_one=Mock())

        self.assertEqual(record.action_open_internal(), {
            "name": "Internal Data", "type": "ir.actions.act_window",
            "res_model": "res.partner", "res_id": 71, "view_mode": "form"})


class _Context(object):
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False


if __name__ == "__main__":
    unittest.main()
