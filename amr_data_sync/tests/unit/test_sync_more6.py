"""Focused tests for remaining ExternalDataSync relation and retry paths.

These exercise model decisions with recordset doubles; they do not claim ORM
persistence or transaction behavior.
"""
import importlib.util
import pathlib
import types
import unittest
from unittest.mock import Mock


_HELPER = pathlib.Path(__file__).with_name("test_sync_core.py")
_spec = importlib.util.spec_from_file_location("sync_more6_core_helpers", _HELPER)
_helpers = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_helpers)
ExternalDataSync, _utils = _helpers.load_sync_model()


class SyncMoreSixTest(unittest.TestCase):
    def model(self, **values):
        record = ExternalDataSync()
        for name, value in values.items():
            setattr(record, name, value)
        return record

    def test_relation_from_external_creates_mapping_using_related_strategy(self):
        created = _helpers.FakeRecords([_helpers.FakeRecordset(id=31)])
        create = Mock(return_value=created)
        search = _helpers.FakeSearchModel()
        parent = types.SimpleNamespace(external_app_name="ERP")
        strategy = types.SimpleNamespace(id=8)
        related = types.SimpleNamespace(
            external_data_sync_id=parent,
            internal_model="res.partner",
            external_app_name="ERP",
            sync_strategy_id=strategy,
        )
        result = self.model(search=search.search, create=create).relation_from_external(
            {"id": "12", "name": "Ada"}, related
        )
        self.assertIs(result, created[0])
        self.assertEqual(search.calls, [([
            ("external_odoo_id", "=", 12),
            ("external_app_name", "=", "ERP"),
            ("internal_model", "=", "res.partner"),
        ], 1)])
        self.assertEqual(create.call_args[0][0][0], {
            "display_name": "Ada", "data_json": '[12, "Ada"]',
            "external_odoo_id": 12, "external_model": "res.partner",
            "internal_model": "res.partner", "sync_strategy_id": 8,
            "external_app_name": "ERP",
        })

    def test_relation_from_external_dispatches_existing_unfinished_mapping(self):
        existing = _helpers.FakeRecordset(
            state="process", updateable=True, dispatch_process=Mock()
        )
        search = _helpers.FakeSearchModel(_helpers.FakeRecords([existing]))
        create = Mock(side_effect=AssertionError("existing mapping must not be created"))
        result = self.model(search=search.search, create=create).relation_from_external(
            {"id": 12, "display_name": "Ada"},
            types.SimpleNamespace(
                external_data_sync_id=types.SimpleNamespace(external_app_name="ERP"),
                internal_model="res.partner", external_app_name="ERP",
                sync_strategy_id=None,
            ),
        )
        self.assertIs(result, search.result)
        existing.dispatch_process.assert_called_once_with()
        create.assert_not_called()

    def test_force_update_requests_refetch_and_dispatches_only_done_record(self):
        dispatch = Mock()
        done = self.model(state="done", dispatch_process=dispatch)
        pending = self.model(state="process", dispatch_process=Mock())
        done.force_update_from_external()
        pending.force_update_from_external()
        self.assertIs(done.need_get_data_json, True)
        self.assertIs(pending.need_get_data_json, True)
        self.assertEqual(done.request_datetime, "now")
        self.assertEqual(pending.request_datetime, "now")
        dispatch.assert_called_once_with()
        pending.dispatch_process.assert_not_called()


if __name__ == "__main__":
    unittest.main()
