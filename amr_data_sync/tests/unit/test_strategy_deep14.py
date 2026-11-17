"""Offline behavioral tests for strategy lookup and configuration paths."""
import importlib.util
import pathlib
import types
import unittest
from unittest.mock import Mock

UNIT_DIR = pathlib.Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location(
    "strategy_deep14_support", UNIT_DIR / "test_sync_strategy.py")
_support = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_support)


class StrategyDeep14Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.strategy_class, _ = _support.load_strategy_class()

    def strategy(self, **values):
        strategy = self.strategy_class()
        strategy.__dict__.update(values)
        strategy.ensure_one = lambda: strategy
        return strategy

    def test_external_id_lookup_uses_strategy_mapping_before_global_mapping(self):
        strategy = self.strategy(id=12, external_app_name="app", external_model="remote.item",
                                 internal_model="local.item", internal_id_same_as_external=False)
        rows = [types.SimpleNamespace(internal_odoo_id=False),
                types.SimpleNamespace(internal_odoo_id=88)]
        sync = types.SimpleNamespace(search=Mock(side_effect=rows))
        strategy.env = {"external.data.sync": sync}

        self.assertEqual(strategy.get_internal_id_from_external_id(9), 88)
        self.assertEqual(sync.search.call_args_list[0][0][0], [
            ("sync_strategy_id", "=", 12), ("external_odoo_id", "=", 9)])
        self.assertEqual(sync.search.call_args_list[1][0][0], [
            ("external_app_name", "=", "app"), ("external_model", "=", "remote.item"),
            ("internal_model", "=", "local.item"), ("external_odoo_id", "=", 9),
            ("sync_strategy_id", "=", False)])

    def test_external_id_lookup_returns_global_mapping_or_configured_offset(self):
        strategy = self.strategy(id=12, external_app_name="app", external_model="remote.item",
                                 internal_model="local.item", internal_id_same_as_external=True,
                                 internal_id_offset=100)
        sync = types.SimpleNamespace(search=Mock(side_effect=[
            types.SimpleNamespace(internal_odoo_id=False),
            types.SimpleNamespace(internal_odoo_id=41)]))
        strategy.env = {"external.data.sync": sync}
        self.assertEqual(strategy.get_internal_id_from_external_id(9), 41)

        sync.search.side_effect = [types.SimpleNamespace(internal_odoo_id=False)] * 2
        self.assertEqual(strategy.get_internal_id_from_external_id(9), 109)
        self.assertIsNone(strategy.get_internal_id_from_external_id(0))

    def test_internal_id_mapping_handles_list_and_dict_input(self):
        strategy = self.strategy(internal_id_offset=5, internal_id_same_as_external=True)
        self.assertEqual(strategy.get_internal_id_same_as_external([7, "Seven"]), 12)
        self.assertEqual(strategy.get_internal_id_same_as_external({"id": 8}), 13)

    def test_sync_context_includes_company_scope_without_mutating_parsed_context(self):
        company_ids = types.SimpleNamespace(ids=[3, 8])
        strategy = self.strategy(internal_context="{'lang': 'id_ID'}", company_ids=company_ids)
        self.assertEqual(strategy.get_internal_context(), {
            "lang": "id_ID", "allowed_company_ids": [3, 8]})
        self.assertEqual(strategy.get_internal_context(), {
            "lang": "id_ID", "allowed_company_ids": [3, 8]})

    def test_external_one_data_preserves_empty_or_non_list_remote_result(self):
        strategy = self.strategy(external_model="remote.item")
        strategy.prepare_sync_one_dict = Mock(return_value={"context": {}})
        model = types.SimpleNamespace(read=Mock(side_effect=[[], {"id": 2}]))

        class RemoteContext(object):
            def __enter__(self):
                return model
            def __exit__(self, exc_type, exc_value, traceback):
                return False

        server = types.SimpleNamespace(create_remote_model=Mock(return_value=RemoteContext()))
        strategy.server_sync_id = server
        self.assertEqual(strategy.get_external_one_data(1), [])
        self.assertEqual(strategy.get_external_one_data(2), {"id": 2})
        self.assertEqual(model.read.call_args_list[0][0][0], [1])
        self.assertEqual(model.read.call_args_list[1][0][0], [2])


if __name__ == "__main__":
    unittest.main()
