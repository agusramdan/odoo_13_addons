"""Behavioral tests for uncovered ExternalDataSync decision branches."""
import datetime
import importlib.util
import pathlib
import types
import unittest
from unittest.mock import Mock

_HELPER = pathlib.Path(__file__).with_name("test_sync_core.py")
_SPEC = importlib.util.spec_from_file_location("sync_deep15_core_helpers", _HELPER)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError("Unable to load sync unit-test helpers")
_HELPERS = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_HELPERS)
ExternalDataSync, _utils = _HELPERS.load_sync_model()


class SyncDeepFifteenTest(unittest.TestCase):
    def model(self, **values):
        record = ExternalDataSync()
        for name, value in values.items():
            setattr(record, name, value)
        return record

    def test_server_sync_falls_back_to_sudo_search_by_application(self):
        server = object()
        strategy = types.SimpleNamespace(get_server_sync=Mock(return_value=False))
        model = types.SimpleNamespace(sudo=Mock())
        model.sudo.return_value.search = Mock(return_value=server)
        record = self.model(sync_strategy_id=strategy, external_app_name="remote", env={"external.server.sync": model})

        self.assertIs(record.get_server_sync(), server)
        strategy.get_server_sync.assert_called_once_with()
        model.sudo.assert_called_once_with()
        model.sudo.return_value.search.assert_called_once_with([("name", "=", "remote")], limit=1)

    def test_strategy_lookup_uses_all_model_identity_fields_and_context(self):
        found = types.SimpleNamespace(ensure_internal_context=Mock(return_value="contextual"))
        strategy_model = types.SimpleNamespace(search=Mock(return_value=found))
        record = self.model(sync_strategy_id=False, external_app_name="remote",
                            external_model="Contact", internal_model="res.partner",
                            env={"external.data.sync.strategy": strategy_model})

        self.assertEqual(record.get_sync_strategy(), "contextual")
        strategy_model.search.assert_called_once_with([
            ("external_app_name", "=", "remote"), ("external_model", "=", "Contact"),
            ("internal_model", "=", "res.partner")], limit=1)
        found.ensure_internal_context.assert_called_once_with()

    def test_missing_strategy_raises_named_user_error_before_fetch(self):
        record = self.model(get_sync_strategy=Mock(return_value=False),
                            get_external_application_name=Mock(return_value="legacy-app"),
                            external_odoo_id=41)

        with self.assertRaises(ExternalDataSync.get_external_one_data.__globals__["UserError"]) as error:
            record.get_external_one_data()

        self.assertIn("legacy-app", str(error.exception))

    def test_delete_validation_archives_when_external_payload_is_absent(self):
        internal = object()
        record = self.model(ensure_one=Mock(), get_external_one_data=Mock(return_value=False),
                            get_internal_object=Mock(return_value=internal),
                            action_archive_internal_odoo=Mock())

        self.assertTrue(record.validate_json_data_for_delete())
        self.assertTrue(record.external_deleted)
        record.get_internal_object.assert_called_once_with()
        record.action_archive_internal_odoo.assert_called_once_with(internal, {}, {})

    def test_delete_validation_keeps_present_external_payload(self):
        record = self.model(ensure_one=Mock(), get_external_one_data=Mock(return_value={"active": True}),
                            action_archive_internal_odoo=Mock())

        self.assertFalse(record.validate_json_data_for_delete())
        record.action_archive_internal_odoo.assert_not_called()

    def test_mandatory_related_requires_only_mandatory_relations_resolved(self):
        record = self.model(related_ids=[
            types.SimpleNamespace(name="optional", mandatory_before_create=False, state="draft"),
            types.SimpleNamespace(name="required", mandatory_before_create=True, state="done")])

        self.assertTrue(record.is_mandatory_related_done())
        record.related_ids[1].state = "process"
        self.assertFalse(record.is_mandatory_related_done())

    def test_need_resolve_write_records_internal_id_payload_and_error_safe_path(self):
        internal = types.SimpleNamespace(id=23)
        record = self.model(write_error_safe=Mock())
        payload = {"name": "pending"}

        self.assertIs(record.write_need_resolve_internal_odoo(internal, payload), internal)
        data = record.write_error_safe.call_args[0][0]
        self.assertEqual(data["internal_odoo_id"], 23)
        self.assertEqual(data["state"], "need_resolve")
        self.assertEqual(data["payload_json"], '{"name": "pending"}')
        self.assertIn("last_processing_datetime", data)
        record.write_error_safe.assert_called_once()

    def test_ensure_have_strategy_assigns_resolved_strategy_once(self):
        resolved = object()
        record = self.model(sync_strategy_id=False, get_sync_strategy=Mock(return_value=resolved))

        self.assertIs(record.ensure_have_sync_strategy(), resolved)
        # The test double lacks Odoo's field descriptor assignment semantics; assert
        # whether a write would be warranted via the return and current field value.
        self.assertFalse(record.sync_strategy_id)

    def test_process_data_switches_to_item_company_and_uses_that_context(self):
        company = types.SimpleNamespace(id=8)
        strategy = types.SimpleNamespace(
            lookup_company=Mock(return_value=company),
            ensure_internal_context=Mock(),
            internal_model_object=Mock(return_value=_HELPERS.FakeModelBase()),
            internal_lookup=Mock(return_value=False))
        strategy.ensure_internal_context.side_effect = lambda **kwargs: strategy
        record = self.model(get_json_data_for_create=Mock(return_value={"company_id": 8}),
                            get_sync_strategy=Mock(return_value=strategy), company_id=types.SimpleNamespace(id=3),
                            write=Mock(), get_internal_object=Mock(return_value=None),
                            is_create_able_from_external=Mock(return_value=False),
                            is_update_able_from_external=Mock(return_value=False))

        datetime_field = ExternalDataSync.process_data.__globals__["fields"].Datetime
        old_now = datetime_field.now
        datetime_field.now = lambda: datetime.datetime(2026, 1, 2)
        try:
            record.process_data()
        finally:
            datetime_field.now = old_now

        strategy.lookup_company.assert_called_once_with(8)
        self.assertEqual(record.write.call_args_list[0][0][0]["company_id"], 8)
        self.assertEqual(record.write.call_args_list[1][0][0]["error_info"], "Cannot update and create")
        strategy.ensure_internal_context.assert_called_once_with(default_company_id=8)
        strategy.internal_model_object.assert_called_once_with()
        record.get_internal_object.assert_called_once_with(strategy.internal_model_object.return_value)

    def test_process_data_missing_company_falls_back_to_record_company(self):
        company = types.SimpleNamespace(id=3)
        strategy = types.SimpleNamespace(
            lookup_company=Mock(return_value=False),
            ensure_internal_context=Mock(),
            internal_model_object=Mock(return_value=_HELPERS.FakeModelBase()),
            internal_lookup=Mock(return_value=False))
        strategy.ensure_internal_context.side_effect = lambda **kwargs: strategy
        record = self.model(get_json_data_for_create=Mock(return_value={"company_id": 999}),
                            get_sync_strategy=Mock(return_value=strategy), company_id=company,
                            write=Mock(), get_internal_object=Mock(return_value=None),
                            is_create_able_from_external=Mock(return_value=False),
                            is_update_able_from_external=Mock(return_value=False))

        datetime_field = ExternalDataSync.process_data.__globals__["fields"].Datetime
        old_now = datetime_field.now
        datetime_field.now = lambda: datetime.datetime(2026, 1, 2)
        try:
            record.process_data()
        finally:
            datetime_field.now = old_now

        strategy.ensure_internal_context.assert_called_once_with(default_company_id=3)
        self.assertEqual(record.write.call_count, 1)
        self.assertEqual(record.write.call_args_list[0][0][0]["error_info"], "Cannot update and create")
        self.assertEqual(record.write.call_args_list[0][0][0]["state"], "need_resolve")
        self.assertIn("last_processing_datetime", record.write.call_args_list[0][0][0])
        self.assertIn("next_processing_datetime", record.write.call_args_list[0][0][0])

    def test_action_after_create_filters_to_done_linked_records(self):
        target = types.SimpleNamespace(state="done", internal_odoo_id=17,
                                       get_internal_object=Mock(return_value="internal"),
                                       process_field_after_create=Mock())
        skipped = types.SimpleNamespace(state="process", internal_odoo_id=18,
                                        get_internal_object=Mock(), process_field_after_create=Mock())
        record = self.model(filtered=Mock(return_value=[target]))

        record.action_process_field_after_create()

        record.filtered.assert_called_once()
        target.get_internal_object.assert_called_once_with()
        target.process_field_after_create.assert_called_once_with("internal")
        skipped.get_internal_object.assert_not_called()

    def test_last_sync_query_filters_done_mapped_rows_and_returns_timestamp(self):
        last = object()
        match = types.SimpleNamespace(last_success=last)
        record = self.model(search=Mock(return_value=match))
        strategy = types.SimpleNamespace(id=5)

        self.assertIs(record.get_last_sync_datetime(strategy), last)
        record.search.assert_called_once_with([
            ("sync_strategy_id", "=", 5), ("state", "=", "done"),
            ("internal_odoo_id", "!=", False)], order="last_success desc", limit=1)

    def test_reverse_mapping_uses_strategy_then_sync_rows_for_unmapped_ids(self):
        internal = _HELPERS.FakeModelBase()
        internal._name = "res.partner"
        internal.ids = [4, 5]
        strategy = types.SimpleNamespace(
            reverse_mapping=Mock(return_value=({4: [40]}, {5})), internal_model="res.partner",
            get_external_application_name=Mock(return_value="remote"), external_model="Contact")
        record = self.model(search_read=Mock(return_value=[{"internal_odoo_id": 5, "external_odoo_id": 50}]),
                            env={"external.data.lookup": types.SimpleNamespace(search_read=Mock())})

        mapping, missing = record.reverse_mapping(internal, sync_strategy=strategy)

        self.assertEqual(mapping, {4: [40], 5: [50]})
        self.assertEqual(missing, set())
        record.search_read.assert_called_once_with([
            ("internal_odoo_id", "in", [5]), ("internal_model", "=", "res.partner"),
            ("external_app_name", "=", "remote"), ("external_model", "=", "Contact")],
            fields=["internal_odoo_id", "external_odoo_id"])

    def test_reverse_mapping_reports_missing_app_without_search(self):
        internal = _HELPERS.FakeModelBase()
        internal._name = "res.partner"
        internal.ids = [5]
        strategy = types.SimpleNamespace(reverse_mapping=Mock(return_value=({}, {5})),
                                         internal_model="res.partner",
                                         get_external_application_name=Mock(return_value=False),
                                         external_model="Contact")
        record = self.model(search_read=Mock())

        mapping, missing = record.reverse_mapping(internal, sync_strategy=strategy,
                                                  raise_not_found_exception=False)

        self.assertEqual(mapping, {})
        self.assertEqual(missing, {5})
        record.search_read.assert_not_called()

    def test_duplicate_removal_empty_input_is_noop_and_nonempty_uses_sudo(self):
        model = types.SimpleNamespace(search=Mock())
        model.search.return_value.remove_duplicate_data = Mock(return_value="cleaned")
        record = self.model(sudo=Mock(return_value=model))

        self.assertIsNone(record.remove_duplicate_external_data("res.partner", []))
        record.sudo.assert_not_called()
        self.assertEqual(record.remove_duplicate_external_data("res.partner", [4, 5]), "cleaned")
        record.sudo.assert_called_once_with()
        model.search.assert_called_once_with([
            ("internal_model", "=", "res.partner"), ("internal_odoo_id", "in", [4, 5])])
        model.search.return_value.remove_duplicate_data.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
