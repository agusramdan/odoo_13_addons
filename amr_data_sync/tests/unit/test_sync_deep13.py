"""Behavioral coverage for sync metadata and recovery paths."""
import importlib.util
import pathlib
import types
import unittest
from unittest.mock import Mock

_HELPER = pathlib.Path(__file__).with_name("test_sync_core.py")
_SPEC = importlib.util.spec_from_file_location("sync_deep13_core_helpers", _HELPER)
_HELPERS = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_HELPERS)
ExternalDataSync, _utils = _HELPERS.load_sync_model()


class SyncDeepThirteenTest(unittest.TestCase):
    def model(self, **values):
        record = ExternalDataSync()
        for key, value in values.items():
            setattr(record, key, value)
        return record

    def test_write_strategy_refreshes_model_identity_and_rejects_missing_strategy(self):
        strategy = types.SimpleNamespace(external_model="RemoteContact", external_app_name="crm",
                                         internal_model="res.partner")
        env_model = types.SimpleNamespace(browse=Mock(return_value=strategy))
        record = self.model(env={"external.data.sync.strategy": env_model})

        written = record.write({"sync_strategy_id": 17, "name": "Contact"})
        self.assertEqual(written, {
            "sync_strategy_id": 17, "name": "Contact", "external_model": "RemoteContact",
            "external_app_name": "crm", "internal_model": "res.partner"})
        env_model.browse.return_value = False
        with self.assertRaises(Exception) as raised:
            record.write({"sync_strategy_id": 404})
        self.assertEqual(type(raised.exception).__name__, "UserError")
        self.assertIn("404", str(raised.exception))

    def test_related_completion_requires_mandatory_and_optional_rows_resolved(self):
        mandatory = types.SimpleNamespace(name="country_id", mandatory_before_create=True, state="process")
        optional = types.SimpleNamespace(name="note", mandatory_before_create=False, state="process")
        record = self.model(related_ids=[mandatory, optional])
        self.assertFalse(record.is_mandatory_related_done())
        self.assertFalse(record.is_all_related_done())
        mandatory.state = "need_resolve"
        self.assertTrue(record.is_mandatory_related_done())
        self.assertFalse(record.is_all_related_done())
        optional.state = "done"
        self.assertTrue(record.is_all_related_done())

    def test_archived_write_records_done_state_and_json_payload_and_returns_object(self):
        now_values = iter(["archived-at", "success-at", "processed-at"])
        sync = self.model(write=Mock(return_value=True))
        sync_fields = ExternalDataSync.write_archived_internal_odoo.__globals__["fields"]
        original_now = sync_fields.Datetime.now
        sync_fields.Datetime.now = lambda: next(now_values)
        internal = types.SimpleNamespace(id=27)
        try:
            self.assertIs(sync.write_archived_internal_odoo(internal, {"reason": "remote-delete"}), internal)
        finally:
            sync_fields.Datetime.now = original_now
        written = sync.write.call_args[0][0]
        self.assertEqual(written["state"], "done")
        self.assertTrue(written["external_archived"])
        self.assertEqual(written["archived_datetime"], "archived-at")
        self.assertEqual(written["last_success"], "success-at")
        self.assertEqual(written["last_processing_datetime"], "processed-at")
        self.assertEqual(written["payload_json"], '{"reason": "remote-delete"}')

    def test_error_safe_uses_savepoint_for_normal_write_and_pool_environment_for_recovery(self):
        record = self.model(env=types.SimpleNamespace(
            cr=types.SimpleNamespace(savepoint=Mock(return_value=_Context()))),
            pool=types.SimpleNamespace(cursor=Mock(return_value=_Context())),
            with_env=Mock(return_value=types.SimpleNamespace(write=Mock())))
        record.write = Mock(return_value=True)
        payload = {"state": "error", "error_info": "failed"}
        record.write_error_safe(payload)
        record.env.cr.savepoint.assert_called_once_with()
        record.write.assert_called_once_with(payload)

        cursor = _Context()
        record.pool.cursor.return_value = cursor
        elevated = types.SimpleNamespace(write=Mock(return_value=True))
        record.with_env.return_value = elevated
        record.env.context = {"lang": "en_US"}
        api = ExternalDataSync.write_error_safe.__globals__["api"]
        original_environment = getattr(api, "Environment", None)
        api.Environment = lambda cr, uid, context: types.SimpleNamespace(cr=cr, uid=uid, context=context)
        try:
            record.write_error_safe(payload, using_pool=True)
        finally:
            if original_environment is None:
                del api.Environment
            else:
                api.Environment = original_environment
        self.assertEqual(record.with_env.call_args[0][0].uid, 1)
        self.assertIs(record.with_env.call_args[0][0].cr, cursor)
        self.assertEqual(record.with_env.call_args[0][0].context, {"lang": "en_US"})
        elevated.write.assert_called_once_with(payload)


class _Context(object):
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False


if __name__ == "__main__":
    unittest.main()
