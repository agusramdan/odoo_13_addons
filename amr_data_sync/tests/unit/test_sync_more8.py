"""Behavioral unit coverage for additional ExternalDataSync methods."""
import importlib.util
import pathlib
import types
import unittest
from unittest.mock import Mock


_HELPER = pathlib.Path(__file__).with_name("test_sync_core.py")
_spec = importlib.util.spec_from_file_location("sync_more8_core_helpers", _HELPER)
_helpers = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_helpers)
ExternalDataSync, _utils = _helpers.load_sync_model()


class SyncMoreEightTest(unittest.TestCase):
    def model(self, **values):
        record = ExternalDataSync()
        for name, value in values.items():
            setattr(record, name, value)
        return record

    def test_is_update_create_and_update_only_delegate_to_strategy(self):
        strategy = types.SimpleNamespace(
            is_update_able_from_external=Mock(return_value=True),
            is_create_able_from_external=Mock(return_value=False),
            is_update_only_from_external=Mock(return_value=True),
        )
        record = self.model(sync_strategy_id=strategy)

        self.assertTrue(record.is_update_able_from_external())
        self.assertFalse(record.is_create_able_from_external())
        self.assertTrue(record.is_update_only_from_external())
        strategy.is_update_able_from_external.assert_called_once_with()
        strategy.is_create_able_from_external.assert_called_once_with()
        strategy.is_update_only_from_external.assert_called_once_with()

    def test_get_external_application_name_prefers_record_value_then_server(self):
        record = self.model(external_app_name="cached", server_sync_id=Mock())
        self.assertEqual(record.get_external_application_name(), "cached")
        record.external_app_name = False
        record.server_sync_id.get_application_name.return_value = "from-server"
        self.assertEqual(record.get_external_application_name(), "from-server")
        record.server_sync_id = False
        self.assertIsNone(record.get_external_application_name())

    def test_action_open_internal_returns_window_for_current_mapping(self):
        record = self.model(internal_model="res.partner", internal_odoo_id=27,
                           ensure_one=Mock())

        action = record.action_open_internal()

        self.assertEqual(action, {
            "name": "Internal Data", "type": "ir.actions.act_window",
            "res_model": "res.partner", "res_id": 27, "view_mode": "form",
        })
        record.ensure_one.assert_called_once_with()

    def test_write_done_internal_odoo_persists_payload_and_mapping(self):
        internal = types.SimpleNamespace(id=17)
        record = self.model(sudo=Mock())
        elevated = types.SimpleNamespace(write=Mock(return_value=True))
        record.sudo.return_value = elevated

        result = record.write_done_internal_odoo(internal, {"name": "Updated"})

        self.assertIs(result, internal)
        values = elevated.write.call_args[0][0]
        self.assertEqual(values["state"], "done")
        self.assertEqual(values["internal_odoo_id"], 17)
        self.assertEqual(values["error_info"], "Done")
        self.assertEqual(values["payload_json"], '{"name": "Updated"}')
        self.assertEqual(values["last_success"], "now")

    def test_write_done_internal_odoo_without_internal_record_does_not_write(self):
        record = self.model(sudo=Mock())

        self.assertIs(record.write_done_internal_odoo(False, {"name": "unused"}), False)
        record.sudo.assert_not_called()


if __name__ == "__main__":
    unittest.main()
