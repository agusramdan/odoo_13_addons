"""State-branch coverage for the real ExternalDataSync.process_data method.

Fakes isolate Odoo recordset/environment boundaries; this is not ORM evidence.
"""
import datetime
import importlib.util
import pathlib
import types
import unittest
from unittest.mock import Mock


_helper_path = pathlib.Path(__file__).with_name("test_sync_core.py")
_spec = importlib.util.spec_from_file_location("sync_extra2_helpers", _helper_path)
_helpers = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_helpers)
ExternalDataSync, _utils = _helpers.load_sync_model()


class SyncProcessStateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.datetime_now = ExternalDataSync.process_data.__globals__["fields"].Datetime.now

    def setUp(self):
        ExternalDataSync.process_data.__globals__["fields"].Datetime.now = (
            lambda: datetime.datetime(2025, 1, 1))

    def tearDown(self):
        ExternalDataSync.process_data.__globals__["fields"].Datetime.now = self.datetime_now

    def model(self, **values):
        result = ExternalDataSync()
        for key, value in values.items():
            setattr(result, key, value)
        return result

    def test_missing_strategy_marks_record_for_resolution_and_returns(self):
        writes = []
        sync = self.model(get_json_data_for_create=Mock(return_value={"id": 3}),
                          get_sync_strategy=Mock(return_value=None),
                          write=lambda vals: writes.append(dict(vals)))

        self.assertIsNone(sync.process_data())
        self.assertEqual(len(writes), 1)
        self.assertEqual(writes[0]["state"], "need_resolve")
        self.assertEqual(writes[0]["error_info"], "Without Strategy")
        self.assertIn("last_error", writes[0])
        self.assertIn("next_processing_datetime", writes[0])

    def test_inactive_payload_archives_and_notifies_without_creating(self):
        strategy = types.SimpleNamespace(
            ensure_internal_context=Mock(return_value=None),
            internal_model_object=Mock(),
            event_external_data_sync_done=Mock(),
        )
        existing = object()
        writes = []
        sync = self.model(
            get_json_data_for_create=Mock(return_value={"id": 4, "active": False}),
            get_sync_strategy=Mock(return_value=strategy), company_id=None,
            internal_odoo_id=4, get_internal_object=Mock(return_value=existing),
            action_archive_internal_odoo=Mock(),
            write=lambda vals: writes.append(dict(vals)),
        )

        self.assertIsNone(sync.process_data())
        sync.action_archive_internal_odoo.assert_called_once_with(existing, {"id": 4, "active": False}, {})
        strategy.event_external_data_sync_done.assert_called_once_with(
            existing, {"id": 4, "active": False}, {})
        strategy.internal_model_object.assert_called_once_with()
        self.assertEqual(writes, [])

    def test_existing_record_with_creation_and_update_disabled_is_marked_done(self):
        strategy = types.SimpleNamespace(
            ensure_internal_context=Mock(return_value=None),
            internal_model_object=Mock(return_value="model"),
            lookup_company=Mock(return_value=None),
        )
        existing = object()
        sync = self.model(
            get_json_data_for_create=Mock(return_value={"id": 7}),
            get_sync_strategy=Mock(return_value=strategy), company_id=None,
            get_internal_object=Mock(return_value=existing),
            is_create_able_from_external=Mock(return_value=False),
            is_update_able_from_external=Mock(return_value=False),
            write_done_internal_odoo=Mock(), write=Mock(),
        )

        self.assertIsNone(sync.process_data())
        sync.write_done_internal_odoo.assert_called_once_with(existing)
        sync.write.assert_not_called()

    def test_no_existing_record_with_both_permissions_disabled_needs_resolution(self):
        strategy = types.SimpleNamespace(
            ensure_internal_context=Mock(return_value=None),
            internal_model_object=Mock(return_value="model"),
            lookup_company=Mock(return_value=None),
            internal_lookup=Mock(return_value=None),
        )
        writes = []
        sync = self.model(
            get_json_data_for_create=Mock(return_value={"id": 8}),
            get_sync_strategy=Mock(return_value=strategy), company_id=None,
            get_internal_object=Mock(return_value=None),
            is_create_able_from_external=Mock(return_value=False),
            is_update_able_from_external=Mock(return_value=False),
            write=lambda vals: writes.append(dict(vals)),
        )

        self.assertIsNone(sync.process_data())
        self.assertEqual(writes[0]["state"], "need_resolve")
        self.assertEqual(writes[0]["error_info"], "Cannot update and create")
        self.assertIn("next_processing_datetime", writes[0])

    def test_incomplete_related_records_override_done_state_to_need_resolve(self):
        internal = types.SimpleNamespace(id=19)
        strategy = types.SimpleNamespace(
            ensure_internal_context=Mock(return_value=None),
            internal_model_object=Mock(return_value="model"),
            lookup_company=Mock(return_value=None),
            internal_lookup=Mock(return_value=internal),
            call_internal_process_method=Mock(return_value={"name": "Mapped"}),
            event_external_data_sync_done=Mock(),
        )
        related = [types.SimpleNamespace(state="process", name="partner")]
        sync = self.model(
            get_json_data_for_create=Mock(return_value={"id": 9}),
            get_sync_strategy=Mock(return_value=strategy), company_id=None,
            get_internal_object=Mock(return_value=None),
            is_create_able_from_external=Mock(return_value=True),
            is_update_able_from_external=Mock(return_value=True),
            prepare_input_external=Mock(return_value={"name": "Mapped"}),
            save_data=Mock(return_value=internal), related_ids=related,
            process_field_after_create=Mock(return_value={}),
            write_done_internal_odoo=Mock(), write=Mock(),
        )

        self.assertIsNone(sync.process_data())
        sync.write_done_internal_odoo.assert_called_once_with(internal, {"name": "Mapped"})
        sync.write.assert_called_once_with({"state": "need_resolve", "error_info": "need_resolve"})
        strategy.event_external_data_sync_done.assert_not_called()


if __name__ == "__main__":
    unittest.main()
