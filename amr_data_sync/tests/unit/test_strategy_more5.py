"""Additional behavioral tests for uncovered strategy branches."""
import importlib.util
import pathlib
import types
import unittest
from unittest.mock import Mock

UNIT_DIR = pathlib.Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location(
    "strategy_more5_support", UNIT_DIR / "test_sync_strategy.py")
_support = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_support)


class StrategyMoreCoverageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.strategy_class, _ = _support.load_strategy_class()

    def strategy(self, **values):
        result = self.strategy_class()
        result.__dict__.update(values)
        result.ensure_one = lambda: result
        return result

    def test_external_id_lookup_returns_direct_mapping_and_fallback_mapping(self):
        class SyncRecords(object):
            def __init__(self):
                self.calls = []

            def search(self, domain, limit=None):
                self.calls.append((domain, limit))
                return types.SimpleNamespace(internal_odoo_id=88 if len(self.calls) == 2 else False)

        records = SyncRecords()
        strategy = self.strategy(id=5, external_app_name="app", external_model="remote",
                                 internal_model="local", env={"external.data.sync": records})
        self.assertEqual(strategy.get_internal_id_from_external_id("x"), 88)
        self.assertEqual(records.calls[0], ([('sync_strategy_id', '=', 5),
                                             ('external_odoo_id', '=', 'x')], 1))
        self.assertEqual(records.calls[1][0], [
            ('external_app_name', '=', 'app'), ('external_model', '=', 'remote'),
            ('internal_model', '=', 'local'), ('external_odoo_id', '=', 'x'),
            ('sync_strategy_id', '=', False)])

    def test_external_id_lookup_applies_offset_only_when_configured(self):
        strategy = self.strategy(id=5, external_app_name="app", external_model="remote",
                                 internal_model="local", internal_id_same_as_external=True,
                                 internal_id_offset=100)
        strategy.env = {"external.data.sync": types.SimpleNamespace(
            search=lambda *args, **kwargs: types.SimpleNamespace(internal_odoo_id=False))}
        self.assertEqual(strategy.get_internal_id_from_external_id(7), 107)
        self.assertIsNone(strategy.get_internal_id_from_external_id(None))

    def test_external_context_literal_and_empty_values(self):
        self.assertEqual(self.strategy(external_context="{'lang': 'id_ID'}").get_external_context(),
                         {'lang': 'id_ID'})
        self.assertEqual(self.strategy(external_context="").get_external_context(), {})

    def test_internal_context_adds_allowed_company_ids(self):
        strategy = self.strategy(internal_context="{'active_test': False}",
                                 company_ids=types.SimpleNamespace(ids=[3, 9]))
        self.assertEqual(strategy.get_internal_context(), {
            'active_test': False, 'allowed_company_ids': [3, 9]})

    def test_prepare_sync_one_dict_adds_required_fields_and_company(self):
        strategy = self.strategy(external_context="{'lang': 'en_US'}",
                                 external_domain="[('active', '=', True)]",
                                 external_fields="name, code", company_ids=[object()])
        config = strategy.prepare_sync_one_dict()
        self.assertEqual(config, {'fields': ['name', 'code', 'write_date', 'company_id'],
                                  'context': {'lang': 'en_US'},
                                  'domain': [('active', '=', True)]})

    def test_prepare_sync_one_dict_preserves_unspecified_fields(self):
        strategy = self.strategy(external_context="", external_domain="", external_fields="")
        self.assertEqual(strategy.prepare_sync_one_dict(),
                         {'fields': None, 'context': {}, 'domain': []})

    def test_eval_prepare_script_returns_mutated_prepare_and_wraps_errors(self):
        strategy = self.strategy(eval_script="prepare['ok'] = external_data['value']",
                                 internal_model='local', env={'local': object()})
        self.assertEqual(strategy.execute_prepare_eval({'value': 4}, {}), {'ok': 4})
        broken = self.strategy(eval_script="raise RuntimeError('bad')", internal_model='local',
                               env={'local': object()})
        with self.assertRaisesRegex(ValueError, 'Error evaluating script: bad'):
            broken.execute_prepare_eval({}, {})

    def test_get_internal_id_same_as_external_handles_pair_and_dict_inputs(self):
        strategy = self.strategy(internal_id_offset=2, internal_id_same_as_external=True)
        self.assertEqual(strategy.get_internal_id_same_as_external([5, 'five']), 7)
        self.assertEqual(strategy.get_internal_id_same_as_external({'id': 8}), 10)
        without_offset = self.strategy(internal_id_offset=0, internal_id_same_as_external=True)
        self.assertEqual(without_offset.get_internal_id_same_as_external({'id': 8}), 8)
        self.assertIsNone(without_offset.get_internal_id_same_as_external({'name': 'missing'}))

    def test_call_internal_process_skips_missing_method_or_nonrecord(self):
        strategy = self.strategy(internal_process_method='process')
        values = {'x': 1}
        self.assertIs(strategy.call_internal_process_method(object(), {}, values, object()), values)
        strategy.internal_process_method = False
        self.assertIs(strategy.call_internal_process_method(object(), {}, values, object()), values)

    def test_get_or_create_relation_delegates_each_relation(self):
        sync = Mock()
        records = types.SimpleNamespace(relation_from_external=Mock(side_effect=[21, 22]))
        strategy = self.strategy(env={'external.data.sync': records})
        self.assertEqual(strategy.get_or_create_relation_from_external([1, {'id': 2}], sync), [21, 22])
        self.assertEqual(records.relation_from_external.call_count, 2)

    def test_capability_flags_for_unrecognized_strategy_are_false(self):
        strategy = self.strategy(strategy='local_lookup')
        self.assertFalse(strategy.is_delete_able_from_external())
        self.assertFalse(strategy.is_update_able_from_external())
        self.assertFalse(strategy.is_update_only_from_external())
        self.assertFalse(strategy.is_create_able_from_external())


if __name__ == '__main__':
    unittest.main()
