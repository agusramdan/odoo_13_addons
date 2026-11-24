"""Behavioral coverage for additional data-sync strategy branches."""
import importlib.util
import pathlib
import types
import unittest
from unittest.mock import Mock


UNIT_DIR = pathlib.Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location(
    "strategy_more8_support", UNIT_DIR / "test_sync_strategy.py")
_support = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_support)


class StrategyMore8Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.strategy_class, _ = _support.load_strategy_class()

    def strategy(self, **values):
        result = self.strategy_class()
        result.__dict__.update(values)
        result.ensure_one = lambda: result
        return result

    def test_get_server_sync_prefers_related_record_then_searches_by_app(self):
        direct = object()
        strategy = self.strategy(server_sync_id=direct)
        self.assertIs(strategy.get_server_sync(), direct)

        searched = Mock()
        class EmptyServerSet(object):
            def __bool__(self):
                return False

            def search(self, domain, limit=None):
                self.request = (domain, limit)
                return searched

        server_model = EmptyServerSet()
        strategy = self.strategy(server_sync_id=server_model, external_app_name="source")
        self.assertIs(strategy.get_server_sync(), searched)
        self.assertEqual(server_model.request, ([ ("app_name", "=", "source")], 1))

    def test_get_external_application_name_falls_back_to_configured_name(self):
        server = types.SimpleNamespace(get_application_name=lambda: False)
        strategy = self.strategy(server_sync_id=server, external_app_name="configured-app")
        self.assertEqual(strategy.get_external_application_name(), "configured-app")

    def test_internal_context_overlays_env_context_and_company_filter(self):
        strategy = self.strategy(
            env=types.SimpleNamespace(context={"lang": "en_US", "timezone": "UTC"}),
            internal_context="{'lang': 'id_ID', 'active_test': False}",
            company_ids=types.SimpleNamespace(ids=[3, 7]))
        self.assertEqual(strategy.get_internal_context(), {
            "lang": "id_ID", "active_test": False, "allowed_company_ids": [3, 7]})

        contextualized = Mock()
        strategy.with_context = Mock(return_value=contextualized)
        self.assertIs(strategy.ensure_internal_context(default_company_id=3), contextualized)
        strategy.with_context.assert_called_once_with(
            lang="id_ID", timezone="UTC", default_company_id=3,
            active_test=False, allowed_company_ids=[3, 7])

    def test_prepare_sync_one_adds_write_date_and_company_for_requested_fields(self):
        strategy = self.strategy(
            external_context="{'lang': 'en_US'}", external_domain="[('active', '=', True)]",
            external_fields="name, company_id", company_ids=[object()])
        self.assertEqual(strategy.prepare_sync_one_dict(), {
            "fields": ["name", "company_id", "write_date"],
            "context": {"lang": "en_US"},
            "domain": [("active", "=", True)]})

    def test_prepare_eval_returns_reassigned_prepare_value(self):
        strategy = self.strategy(
            eval_script="prepare = {'result': external_data['id']}",
            internal_model="local.item", env={"local.item": object()})
        self.assertEqual(strategy.execute_prepare_eval({"id": 14}, {"old": True}),
                         {"result": 14})

    def test_prepare_eval_wraps_script_failure_with_original_message(self):
        strategy = self.strategy(eval_script="raise RuntimeError('broken transform')",
                                 internal_model="local.item", env={"local.item": object()})
        with self.assertRaisesRegex(ValueError, "Error evaluating script: broken transform"):
            strategy.execute_prepare_eval({}, {})

if __name__ == "__main__":
    unittest.main()
