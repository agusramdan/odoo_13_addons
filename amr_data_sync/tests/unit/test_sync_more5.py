"""Additional branch coverage for production ExternalDataSync behavior.

The model is loaded directly with the established offline Odoo fixture; these
cases exercise Python decisions and mocked boundaries, not ORM persistence.
"""
import importlib.util
import json
import pathlib
import types
import unittest
from unittest.mock import Mock


_HELPER = pathlib.Path(__file__).with_name("test_sync_core.py")
_spec = importlib.util.spec_from_file_location("sync_more5_core_helpers", _HELPER)
_helpers = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_helpers)
ExternalDataSync, _utils = _helpers.load_sync_model()


class _NoopContext(object):
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False


class SyncMoreFiveTest(unittest.TestCase):
    def model(self, **values):
        record = ExternalDataSync()
        for name, value in values.items():
            setattr(record, name, value)
        return record

    def test_get_json_cached_non_mapping_refetches_and_persists_empty_payload(self):
        record = self.model(
            need_get_data_json=False,
            data_json='["not", "a", "mapping"]',
            get_external_one_data=Mock(return_value=None),
            write=Mock(),
        )
        with self.assertLogs(ExternalDataSync.get_json_data_for_create.__globals__["_logger"],
                             level="INFO") as captured:
            result = record.get_json_data_for_create()
        self.assertEqual(result, {"active": False})
        record.get_external_one_data.assert_called_once_with()
        values = record.write.call_args[0][0]
        self.assertIs(values["need_get_data_json"], False)
        self.assertEqual(json.loads(values["data_json"]), None)
        self.assertTrue(any("Data Json not dict" in message for message in captured.output))

    def test_get_json_fetch_string_write_date_converts_before_savepoint_write(self):
        record = self.model(
            need_get_data_json=True,
            get_external_one_data=Mock(return_value={"id": 8, "write_date": "2026-02-03"}),
            env=types.SimpleNamespace(cr=types.SimpleNamespace(savepoint=_NoopContext)),
            write=Mock(),
        )
        self.assertEqual(record.get_json_data_for_create(), {"id": 8, "write_date": "2026-02-03"})
        values = record.write.call_args[0][0]
        self.assertEqual(values["external_last_update"], "parsed:2026-02-03")
        self.assertEqual(json.loads(values["data_json"]), {"id": 8, "write_date": "2026-02-03"})

    def test_get_internal_object_uses_model_name_when_no_strategy_and_no_explicit_model(self):
        target = object()
        record = self.model(internal_model="res.partner", env={"res.partner": target})
        self.assertIs(record.get_internal_object(), target)

    def test_get_internal_object_browses_including_inactive_and_returns_existing(self):
        browsed = types.SimpleNamespace(exists=Mock(return_value="row"))
        contextual = types.SimpleNamespace(browse=Mock(return_value=browsed))
        contextual.with_context = Mock(return_value=contextual)
        strategy_model = _helpers.FakeModelBase()
        strategy_model.with_context = contextual.with_context
        strategy_model.browse = contextual.browse
        strategy_model._name = "res.partner"
        record = self.model(internal_odoo_id=17)
        result = record.get_internal_object(strategy_model)
        self.assertEqual(result, "row")
        contextual.with_context.assert_called_once_with(active_test=False)
        contextual.browse.assert_called_once_with(17)

    def test_get_internal_object_returns_model_without_browsing_when_mapping_is_absent(self):
        model = _helpers.FakeModelBase()
        record = self.model(internal_odoo_id=False)
        self.assertIs(record.get_internal_object(model), model)

    def test_data_from_external_returns_existing_when_update_is_disallowed(self):
        existing = _helpers.FakeRecordset(updateable=False, writes=[], reset_count=0)
        search = _helpers.FakeSearchModel(_helpers.FakeRecords([existing]))
        record = self.model(search=search.search, create=Mock())
        strategy = _helpers.FakeRecordset(id=3)
        result = record.data_from_external({"id": 4, "display_name": "Kept"}, strategy)
        self.assertIs(result, search.result)
        self.assertEqual(existing.writes, [])
        self.assertEqual(existing.reset_count, 0)
        record.create.assert_not_called()

    def test_data_from_external_does_not_create_when_create_flag_is_false(self):
        search = _helpers.FakeSearchModel()
        create = Mock(side_effect=AssertionError("creation must be disabled"))
        record = self.model(search=search.search, create=create)
        self.assertFalse(record.data_from_external({"id": 5}, _helpers.FakeRecordset(id=7),
                                                  create_when_not_found=False))
        create.assert_not_called()

    def test_data_from_external_maps_internal_match_on_new_sync_record(self):
        created = _helpers.FakeRecords([_helpers.FakeRecordset(id=50)])
        create = Mock(return_value=created)
        record = self.model(search=_helpers.FakeSearchModel().search, create=create)
        internal = _helpers.FakeRecordset(id=81)
        strategy = _helpers.FakeRecordset(id=9, internal_lookup=Mock(return_value=internal))
        result = record.data_from_external({"id": 12}, strategy)
        self.assertIs(result, created[0])
        values = create.call_args[0][0][0]
        self.assertEqual(values["internal_odoo_id"], 81)
        self.assertEqual(values["state"], "done")
        self.assertIn("last_success", values)

    def test_action_open_internal_returns_window_action_for_current_mapping(self):
        record = self.model(internal_model="res.partner", internal_odoo_id=23,
                            ensure_one=Mock())
        action = record.action_open_internal()
        self.assertEqual(action, {
            "name": "Internal Data", "type": "ir.actions.act_window",
            "res_model": "res.partner", "res_id": 23, "view_mode": "form",
        })
        record.ensure_one.assert_called_once_with()

    def test_dispatch_marks_process_and_only_runs_immediately_when_requested(self):
        record = self.model(write=Mock(), process_with_handel_error=Mock())
        self.assertIsNone(record.dispatch_process())
        record.write.assert_called_once_with({"state": "process"})
        record.process_with_handel_error.assert_not_called()
        record.dispatch_process(run_immediate=True)
        record.process_with_handel_error.assert_called_once_with()

    def test_ensure_external_data_normalizes_supported_shapes_and_integer_subclass(self):
        normalize = ExternalDataSync.ensure_external_data
        self.assertEqual(normalize(ExternalDataSync(), [6, "six", "ignored"]), {"id": 6})
        self.assertEqual(normalize(ExternalDataSync(), [6, "six"]), {"id": 6, "display_name": "six"})
        self.assertEqual(normalize(ExternalDataSync(), 11), {"id": 11})


if __name__ == "__main__":
    unittest.main()
