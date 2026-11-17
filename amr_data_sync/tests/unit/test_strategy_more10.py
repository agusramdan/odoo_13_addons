"""Behavioral tests for additional strategy configuration edge cases."""
import importlib.util
import pathlib
import types
import unittest
from unittest.mock import Mock


UNIT_DIR = pathlib.Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location(
    "strategy_more10_support", UNIT_DIR / "test_sync_strategy.py")
_support = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_support)


class StrategyMore10Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.strategy_class, _ = _support.load_strategy_class()

    def strategy(self, **values):
        strategy = self.strategy_class()
        strategy.__dict__.update(values)
        strategy.ensure_one = lambda: strategy
        return strategy

    def test_sync_list_config_combines_cursor_domain_context_and_lookup_fields(self):
        last_sync = types.SimpleNamespace(strftime=lambda fmt: "2024-03-04 05:06:07")
        sync_model = types.SimpleNamespace(get_last_sync_datetime=Mock(return_value=last_sync))
        strategy = self.strategy(
            env={"external.data.sync": sync_model}, external_context="{'lang': 'fr_FR'}",
            external_domain="[('active', '=', True)]", internal_lookup_fields="code, ref",
            filter_last_update=True, company_ids=False)
        strategy.get_internal_lookup_fields = lambda: ["code", "ref"]

        self.assertEqual(strategy.prepare_sync_list_dict(), {
            "fields": ["display_name", "name", "write_date", "id", "code", "ref"],
            "context": {"lang": "fr_FR"},
            "domain": [("write_date", ">=", "2024-03-04 05:06:07"),
                       ("active", "=", True)],
        })
        sync_model.get_last_sync_datetime.assert_called_once_with(strategy)

    def test_sync_list_config_does_not_add_cursor_without_previous_sync(self):
        sync_model = types.SimpleNamespace(get_last_sync_datetime=Mock(return_value=False))
        strategy = self.strategy(env={"external.data.sync": sync_model}, external_context="",
                                 external_domain="", internal_lookup_fields="", filter_last_update=True,
                                 company_ids=False)
        strategy.get_internal_lookup_fields = lambda: []

        self.assertEqual(strategy.prepare_sync_list_dict(), {
            "fields": ["display_name", "name", "write_date", "id"],
            "context": {}, "domain": []})

    def test_internal_id_lookup_uses_unscoped_mapping_before_offset_fallback(self):
        rows = [types.SimpleNamespace(internal_odoo_id=False),
                types.SimpleNamespace(internal_odoo_id=73)]

        class SyncModel(object):
            def __init__(self):
                self.domains = []

            def search(self, domain, limit=None):
                self.domains.append(domain)
                return rows[len(self.domains) - 1]

        sync = SyncModel()
        strategy = self.strategy(id=8, external_app_name="app", external_model="remote.item",
                                 internal_model="local.item", internal_id_same_as_external=True,
                                 internal_id_offset=200, env={"external.data.sync": sync})
        self.assertEqual(strategy.get_internal_id_from_external_id(11), 73)
        self.assertEqual(sync.domains, [
            [("sync_strategy_id", "=", 8), ("external_odoo_id", "=", 11)],
            [("external_app_name", "=", "app"), ("external_model", "=", "remote.item"),
             ("internal_model", "=", "local.item"), ("external_odoo_id", "=", 11),
             ("sync_strategy_id", "=", False)],
        ])

    def test_internal_id_lookup_offset_is_only_used_after_both_mappings_miss(self):
        class SyncModel(object):
            def search(self, domain, limit=None):
                return types.SimpleNamespace(internal_odoo_id=False)

        strategy = self.strategy(id=8, external_app_name="app", external_model="remote.item",
                                 internal_model="local.item", internal_id_same_as_external=True,
                                 internal_id_offset=200, env={"external.data.sync": SyncModel()})
        self.assertEqual(strategy.get_internal_id_from_external_id(11), 211)


if __name__ == "__main__":
    unittest.main()
