"""Additional behavior tests for ExternalDataSync process/get-data paths."""
import datetime
import unittest
from unittest.mock import Mock

import importlib.util
from pathlib import Path
_spec = importlib.util.spec_from_file_location('sync_extra3_helpers', str(Path(__file__).with_name('test_sync_extra3.py')))
_helpers = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_helpers)
Record, Records, load_sync_class = _helpers.Record, _helpers.Records, _helpers.load_sync_class


class SyncExtra4Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model_class = load_sync_class()
        cls.model_class.process_data.__globals__['fields'].Datetime.now = lambda: datetime.datetime(2026, 1, 1)

    def test_get_json_uses_cached_dict_without_fetching(self):
        row = self.model_class()
        row.need_get_data_json = False
        row.data_json = '{"id": 12, "active": true}'
        row.get_external_one_data = Mock(side_effect=AssertionError('unexpected fetch'))
        self.assertEqual(row.get_json_data_for_create(), {'id': 12, 'active': True})
        row.get_external_one_data.assert_not_called()

    def test_process_data_without_strategy_records_need_resolve_and_returns(self):
        row = self.model_class()
        row.get_json_data_for_create = Mock(return_value={'id': 5})
        row.get_sync_strategy = Mock(return_value=False)
        row.write = Mock()
        row.process_data()
        values = row.write.call_args[0][0]
        self.assertEqual(values['error_info'], 'Without Strategy')
        self.assertEqual(values['state'], 'need_resolve')
        self.assertEqual(values['last_error'], datetime.datetime(2026, 1, 1))
        self.assertEqual(values['last_processing_datetime'], datetime.datetime(2026, 1, 1))
        self.assertEqual(values['next_processing_datetime'], datetime.datetime(2026, 1, 2))

    def test_process_data_inactive_item_archives_and_notifies_strategy(self):
        row = self.model_class()
        item = {'id': 8, 'active': False}
        strategy = Record()
        strategy.internal_model_object = Mock(return_value=Records())
        strategy.ensure_internal_context = Mock(return_value=strategy)
        strategy.event_external_data_sync_done = Mock()
        row.get_json_data_for_create = Mock(return_value=item)
        row.get_sync_strategy = Mock(return_value=strategy)
        row.company_id = False
        row.internal_model = 'res.partner'
        row.sync_strategy_id = strategy
        row.get_internal_object = Mock(return_value=False)
        row.write = Mock()
        row.action_archive_internal_odoo = Mock()
        row.process_data()
        row.action_archive_internal_odoo.assert_called_once_with(False, item, {})
        strategy.event_external_data_sync_done.assert_called_once_with(False, item, {})
        self.assertEqual(row.write.call_args[0][0], {'error_info': 'Not data active'})

    def test_process_data_disallowed_create_and_update_marks_need_resolve(self):
        row = self.model_class()
        strategy = Record()
        strategy.internal_model_object = Mock(return_value=Records())
        strategy.ensure_internal_context = Mock(return_value=strategy)
        strategy.lookup_company = Mock(return_value=False)
        strategy.internal_lookup = Mock(return_value=False)
        row.get_json_data_for_create = Mock(return_value={'id': 1})
        row.get_sync_strategy = Mock(return_value=strategy)
        row.company_id = False
        row.sync_strategy_id = strategy
        row.get_internal_object = Mock(return_value=False)
        row.is_create_able_from_external = Mock(return_value=False)
        row.is_update_able_from_external = Mock(return_value=False)
        row.write = Mock()
        row.process_data()
        values = row.write.call_args[0][0]
        self.assertEqual(values['error_info'], 'Cannot update and create')
        self.assertEqual(values['state'], 'need_resolve')
        self.assertEqual(values['last_processing_datetime'], datetime.datetime(2026, 1, 1))
        self.assertEqual(values['next_processing_datetime'], datetime.datetime(2026, 1, 2))

    def test_process_data_failure_persists_error_payload_then_reraises(self):
        row = self.model_class()
        row.get_json_data_for_create = Mock(side_effect=ValueError('broken input'))
        row.write_error = Mock()
        with self.assertRaises(ValueError):
            row.process_data()
        args = row.write_error.call_args[0]
        self.assertIn('ValueError: broken input', args[0])
        self.assertEqual(args[1], {})


if __name__ == '__main__':
    unittest.main()
