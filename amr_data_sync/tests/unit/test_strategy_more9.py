"""Behavioral tests for additional data-sync strategy model methods."""
import importlib.util
import pathlib
import types
import unittest
from unittest.mock import Mock


UNIT_DIR = pathlib.Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location(
    "strategy_more9_support", UNIT_DIR / "test_sync_strategy.py")
_support = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_support)


class StrategyMore9Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.strategy_class, _ = _support.load_strategy_class()

    def strategy(self, **values):
        strategy = self.strategy_class()
        strategy.__dict__.update(values)
        strategy.ensure_one = lambda: strategy
        return strategy

    def test_get_external_one_data_returns_first_read_record(self):
        remote = Mock()
        remote.read.return_value = [{"id": 5, "name": "Five"}, {"id": 6}]

        class RemoteContext(object):
            def __enter__(self):
                return remote
            def __exit__(self, *args):
                return False

        server = types.SimpleNamespace(create_remote_model=Mock(return_value=RemoteContext()))
        strategy = self.strategy(server_sync_id=server, external_model="remote.item")
        config = {"fields": ["name"], "domain": []}
        strategy.prepare_sync_one_dict = Mock(return_value=config)

        self.assertEqual(strategy.get_external_one_data(5), {"id": 5, "name": "Five"})
        strategy.prepare_sync_one_dict.assert_called_once_with()
        server.create_remote_model.assert_called_once_with("remote.item", **config)
        remote.read.assert_called_once_with([5])

    def test_get_external_one_data_preserves_empty_and_nonlist_results(self):
        for result in ([], {"error": "not found"}, False):
            remote = Mock()
            remote.read.return_value = result

            class RemoteContext(object):
                def __enter__(self):
                    return remote
                def __exit__(self, *args):
                    return False

            strategy = self.strategy(server_sync_id=types.SimpleNamespace(
                create_remote_model=lambda *args, **kwargs: RemoteContext()))
            strategy.prepare_sync_one_dict = lambda: {}
            self.assertEqual(strategy.get_external_one_data(2), result)

    def test_method_call_sync_invokes_configured_internal_method(self):
        expected = {"processed": True}
        method = Mock(return_value=expected)
        model = types.SimpleNamespace(run_sync=method)
        strategy = self.strategy(internal_model="local.item", internal_call_method="run_sync",
                                 env={"local.item": model})

        self.assertIs(strategy.method_call_sync_from_application_server(), expected)
        method.assert_called_once_with(strategy)

    def test_reverse_mapping_groups_external_ids_and_reports_unmapped(self):
        internal = _support.FakeModel()
        internal.ids = [10, 20, 30]
        rows = [
            {"internal_odoo_id": 10, "external_odoo_id": "a"},
            {"internal_odoo_id": 10, "external_odoo_id": "b"},
            {"internal_odoo_id": 20, "external_odoo_id": False},
        ]
        strategy = self.strategy(id=7, search_read=Mock(return_value=rows))

        mapping, missing = strategy.reverse_mapping(internal, raise_not_found_exception=False)

        self.assertEqual(mapping, {10: ["a", "b"]})
        self.assertEqual(missing, set([20, 30]))
        strategy.search_read.assert_called_once_with(
            [("internal_odoo_id", "in", [10, 20, 30]), ("sync_strategy_id", "=", 7)],
            fields=["internal_odoo_id", "external_odoo_id"])

    def test_reverse_mapping_raises_for_unmapped_ids_by_default(self):
        internal = _support.FakeModel()
        internal.ids = [12]
        strategy = self.strategy(id=3, search_read=Mock(return_value=[]))

        with self.assertRaisesRegex(ValueError, "found not mapped data \[\{12\}\]"):
            strategy.reverse_mapping(internal)

    def test_reverse_mapping_rejects_non_recordset_or_returns_empty_when_permitted(self):
        strategy = self.strategy(id=3, search_read=Mock())
        with self.assertRaisesRegex(ValueError, "Internal Object must"):
            strategy.reverse_mapping(object())
        self.assertEqual(strategy.reverse_mapping(object(), raise_not_found_exception=False), ([], []))
        strategy.search_read.assert_not_called()

    def test_lookup_company_delegates_effective_server_and_application(self):
        company_lookup = Mock(return_value=42)
        server = object()
        strategy = self.strategy(env={"external.data.company": types.SimpleNamespace(
            lookup_company=company_lookup)}, server_sync_id=server,
            external_app_name="configured")
        strategy.get_server_sync = Mock(return_value=server)
        strategy.get_external_application_name = Mock(return_value="effective")

        self.assertEqual(strategy.lookup_company({"id": "remote-company"}), 42)
        company_lookup.assert_called_once_with(
            {"id": "remote-company"}, server_sync=server, external_app_name="effective")
        self.assertIsNone(strategy.lookup_company(False))
        self.assertEqual(company_lookup.call_count, 1)


if __name__ == "__main__":
    unittest.main()
