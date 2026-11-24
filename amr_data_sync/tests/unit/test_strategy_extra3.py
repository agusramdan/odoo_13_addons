"""Additional contract tests for the real sync-strategy model methods."""
import importlib.util
import pathlib
import sys
import types
import unittest


UNIT_DIR = pathlib.Path(__file__).resolve().parent
_helper_spec = importlib.util.spec_from_file_location(
    "strategy_test_support", UNIT_DIR / "test_sync_strategy.py")
_helper = importlib.util.module_from_spec(_helper_spec)
_helper_spec.loader.exec_module(_helper)


class SyncListConfigurationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.strategy_class, _ = _helper.load_strategy_class()

    def test_sync_list_config_combines_literal_context_domain_and_lookup_fields(self):
        strategy = self.strategy_class()
        strategy.__dict__.update({
            "external_context": "{'lang': 'id_ID', 'active_test': False}",
            "external_domain": "[('active', '=', True)]",
            "internal_lookup_fields": " sku, barcode ",
            "company_ids": False,
            "filter_last_update": False,
        })

        self.assertEqual(strategy.prepare_sync_list_dict(), {
            "fields": ["display_name", "name", "write_date", "id", "sku", "barcode"],
            "context": {"lang": "id_ID", "active_test": False},
            "domain": [("active", "=", True)],
        })

    def test_sync_list_adds_write_date_filter_when_last_sync_exists(self):
        class SyncRows(object):
            def get_last_sync_datetime(self, strategy):
                return types.SimpleNamespace(strftime=lambda fmt: "2024-02-03 04:05:06")

        strategy = self.strategy_class()
        strategy.__dict__.update({
            "external_context": "",
            "external_domain": "[('state', '=', 'ready')]",
            "internal_lookup_fields": "code",
            "company_ids": False,
            "filter_last_update": True,
            "env": {"external.data.sync": SyncRows()},
        })

        self.assertEqual(strategy.prepare_sync_list_dict(), {
            "fields": ["display_name", "name", "write_date", "id", "code"],
            "context": {},
            "domain": [
                ("write_date", ">=", "2024-02-03 04:05:06"),
                ("state", "=", "ready"),
            ],
        })

    def test_secondary_unscoped_external_mapping_is_used_before_id_offset(self):
        class SyncRows(object):
            def __init__(self):
                self.domains = []

            def search(self, domain, limit=None):
                self.domains.append(domain)
                if len(self.domains) == 2:
                    return types.SimpleNamespace(internal_odoo_id=73)
                return types.SimpleNamespace(internal_odoo_id=False)

        strategy = self.strategy_class()
        strategy.__dict__.update({
            "id": 8,
            "ensure_one": lambda: None,
            "external_app_name": "legacy-app",
            "external_model": "remote.item",
            "internal_model": "local.item",
            "internal_id_same_as_external": True,
            "internal_id_offset": 100,
            "env": {"external.data.sync": SyncRows()},
        })

        self.assertEqual(strategy.get_internal_id_from_external_id(12), 73)
        self.assertEqual(strategy.env["external.data.sync"].domains, [
            [("sync_strategy_id", "=", 8), ("external_odoo_id", "=", 12)],
            [("external_app_name", "=", "legacy-app"),
             ("external_model", "=", "remote.item"),
             ("internal_model", "=", "local.item"),
             ("external_odoo_id", "=", 12), ("sync_strategy_id", "=", False)],
        ])


if __name__ == "__main__":
    unittest.main()
