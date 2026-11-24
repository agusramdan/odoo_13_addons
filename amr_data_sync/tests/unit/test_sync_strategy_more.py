"""Additional isolated coverage for real sync-strategy methods."""
import importlib.util
import pathlib
import types
import unittest


UNIT = pathlib.Path(__file__).resolve().parent
_existing_spec = importlib.util.spec_from_file_location(
    "sync_strategy_test_fixtures", UNIT / "test_sync_strategy.py")
_existing = importlib.util.module_from_spec(_existing_spec)
_existing_spec.loader.exec_module(_existing)
Strategy = _existing.StrategyTest


class MoreStrategyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Strategy.setUpClass()
        cls.strategy_class = Strategy.strategy_class

    def strategy(self, **values):
        strategy = self.strategy_class()
        strategy.__dict__.update(values)
        strategy.ensure_one = lambda: None
        return strategy

    def test_prepare_sync_list_uses_literal_config_and_lookup_fields(self):
        strategy = self.strategy(
            external_context="{'lang': 'en_US'}",
            external_domain="[('active', '=', True)]",
            internal_lookup_fields=" code, sku ",
            company_ids=False,
            filter_last_update=False)
        config = strategy.prepare_sync_list_dict()
        self.assertEqual(config, {
            "fields": ["display_name", "name", "write_date", "id", "code", "sku"],
            "context": {"lang": "en_US"},
            "domain": [("active", "=", True)],
        })

    def test_prepare_sync_list_adds_last_sync_filter_before_configured_domain(self):
        last_sync = types.SimpleNamespace(strftime=lambda fmt: "2024-03-05 06:07:08")

        class SyncModel(object):
            def get_last_sync_datetime(self, strategy):
                return last_sync

        strategy = self.strategy(external_context="", external_domain="[('state', '=', 'ok')]",
                                 internal_lookup_fields="", company_ids=False,
                                 filter_last_update=True,
                                 env={"external.data.sync": SyncModel()})
        self.assertEqual(strategy.prepare_sync_list_dict()["domain"], [
            ("write_date", ">=", "2024-03-05 06:07:08"), ("state", "=", "ok")])

    def test_get_internal_id_uses_unscoped_mapping_before_same_id_fallback(self):
        class SyncModel(object):
            def __init__(self):
                self.results = [types.SimpleNamespace(internal_odoo_id=False),
                                types.SimpleNamespace(internal_odoo_id=73)]
                self.domains = []

            def search(self, domain, limit=None):
                self.domains.append(domain)
                return self.results.pop(0)

        sync_model = SyncModel()
        strategy = self.strategy(id=9, external_app_name="legacy_app",
                                 external_model="remote.partner", internal_model="res.partner",
                                 internal_id_same_as_external=True, internal_id_offset=100,
                                 env={"external.data.sync": sync_model})
        self.assertEqual(strategy.get_internal_id_from_external_id(12), 73)
        self.assertEqual(sync_model.domains[1], [
            ("external_app_name", "=", "legacy_app"),
            ("external_model", "=", "remote.partner"),
            ("internal_model", "=", "res.partner"),
            ("external_odoo_id", "=", 12),
            ("sync_strategy_id", "=", False)])

    def test_reverse_mapping_returns_mapped_ids_and_unmapped_set(self):
        class StrategyModel(object):
            def search_read(self, domain, fields):
                self.request = (domain, fields)
                return [{"internal_odoo_id": 4, "external_odoo_id": 21},
                        {"internal_odoo_id": 4, "external_odoo_id": False}]

        strategy = self.strategy(id=6)
        strategy.search_read = StrategyModel().search_read
        strategy.ensure_one = lambda: strategy
        # Real method validates the recordset type; use the fixture's concrete
        # FakeModel subclass for the Odoo BaseModel boundary.
        records = _existing.FakeModel()
        records.ids = [4, 5]
        mapping, unmapped = strategy.reverse_mapping(records, raise_not_found_exception=False)
        self.assertEqual(mapping, {4: [21]})
        self.assertEqual(unmapped, {5})

    def test_reverse_mapping_rejects_non_recordset_when_requested(self):
        strategy = self.strategy()
        with self.assertRaisesRegex(ValueError, "Internal Object must"):
            strategy.reverse_mapping([1], raise_not_found_exception=True)


if __name__ == "__main__":
    unittest.main()
