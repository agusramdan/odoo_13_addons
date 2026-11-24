"""Behavioral coverage for strategy metadata, dispatch, and utility calls."""
import importlib.util
import pathlib
import types
import unittest
from unittest.mock import Mock

UNIT_DIR = pathlib.Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location(
    "strategy_deep13_support", UNIT_DIR / "test_sync_strategy.py")
_support = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_support)


class StrategyDeep13Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.strategy_class, cls.UserError = _support.load_strategy_class()

    def strategy(self, **values):
        strategy = self.strategy_class()
        strategy.__dict__.update(values)
        strategy.ensure_one = lambda: strategy
        return strategy

    def test_compute_app_name_updates_only_when_server_is_configured(self):
        strategy = self.strategy(external_app_name="manual", server_sync_id=False)
        class Recordset(self.strategy_class):
            def __iter__(self):
                return iter((strategy,))
        recordset = Recordset()
        recordset._compute_external_app_name()
        self.assertEqual(strategy.external_app_name, "manual")

        strategy.server_sync_id = types.SimpleNamespace(app_name="server-app")
        recordset._compute_external_app_name()
        self.assertEqual(strategy.external_app_name, "server-app")

    def test_name_get_formats_each_strategy_with_effective_application_name(self):
        app = types.SimpleNamespace(get_application_name=lambda: "")
        first = self.strategy_class()
        first.id, first.server_sync_id = 3, app
        first.external_app_name = "fallback"
        first.external_model, first.internal_model = "remote.item", "local.item"
        first.get_external_application_name = lambda: "fallback"
        second = self.strategy_class()
        second.id, second.server_sync_id = 9, app
        second.external_model, second.internal_model = "remote.user", "res.users"
        second.get_external_application_name = lambda: "server-app"

        class Recordset(self.strategy_class):
            def __iter__(self):
                return iter((first, second))
        recordset = Recordset()
        self.assertEqual(recordset.name_get(), [
            (3, "(3) [fallback] remote.item -> local.item"),
            (9, "(9) [server-app] remote.user -> res.users"),
        ])

    def test_sync_dispatch_uses_method_call_only_for_that_transport(self):
        strategy = self.strategy(external_sync="method_call")
        strategy.method_call_sync_from_application_server = Mock(return_value="called")
        strategy.sync_list_model_object = Mock(return_value="listed")
        self.assertIsNone(strategy.sync_from_application_server())
        strategy.method_call_sync_from_application_server.assert_called_once_with()
        strategy.sync_list_model_object.assert_not_called()

        strategy.external_sync = "jsonrpc"
        strategy.sync_from_application_server()
        strategy.sync_list_model_object.assert_called_once_with()
        strategy.method_call_sync_from_application_server.assert_called_once_with()

    def test_endpoint_url_delegates_to_selected_server(self):
        server = types.SimpleNamespace(get_endpoint_url=Mock(return_value="https://sync.invalid/api"))
        strategy = self.strategy(server_sync_id=server)
        self.assertEqual(strategy.get_endpoint_url(), "https://sync.invalid/api")
        server.get_endpoint_url.assert_called_once_with()

    def test_strategy_name_get_uses_one_record_per_returned_pair(self):
        strategy = self.strategy(id=5, external_model="remote", internal_model="local",
                                 get_external_application_name=lambda: "app")
        class Recordset(self.strategy_class):
            def __iter__(self):
                return iter((strategy,))
        self.assertEqual(Recordset().name_get(), [(5, "(5) [app] remote -> local")])


class SafeCallDeep13Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Load real utilities with narrow Odoo/psycopg2 import doubles.
        path = pathlib.Path(__file__).resolve().parents[2] / "tools" / "utils.py"
        odoo = types.ModuleType("odoo")
        odoo.SUPERUSER_ID, odoo._ = 1, lambda value: value
        class BaseModel(object):
            pass
        odoo.models = types.SimpleNamespace(BaseModel=BaseModel)
        exceptions = types.ModuleType("odoo.exceptions")
        exceptions.UserError = type("UserError", (Exception,), {})
        tools = types.ModuleType("odoo.tools")
        tools.attrgetter = lambda name: lambda obj: getattr(obj, name)
        tools.clean_context = lambda context: dict(context)
        psycopg2 = types.ModuleType("psycopg2")
        psycopg2.__path__ = []
        psycopg2_inner = types.ModuleType("psycopg2._psycopg")
        psycopg2_inner.AsIs = lambda value: value
        modules = {"odoo": odoo, "odoo.exceptions": exceptions, "odoo.tools": tools,
                   "psycopg2": psycopg2, "psycopg2._psycopg": psycopg2_inner}
        previous = dict((name, __import__("sys").modules.get(name)) for name in modules)
        __import__("sys").modules.update(modules)
        try:
            spec = importlib.util.spec_from_file_location("utils_deep13_under_test", path)
            cls.utils = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(cls.utils)
        finally:
            sys_modules = __import__("sys").modules
            for name, old in previous.items():
                if old is None:
                    sys_modules.pop(name, None)
                else:
                    sys_modules[name] = old
        cls.BaseModel = BaseModel

    def test_safe_call_supports_callable_and_filters_unmatched_kwargs(self):
        class Receiver(self.BaseModel):
            def run(self, required, optional="default"):
                return required, optional
        receiver = Receiver()
        self.assertEqual(self.utils.safe_call_method(
            receiver, lambda required, optional="default": (required, optional),
            args=["positional"], kwargs={"required": "ignored", "unused": 7}),
            ("positional", "default"))
        self.assertEqual(self.utils.safe_call_method(
            receiver, "run", kwargs={"required": "named", "unused": 7}),
            ("named", "default"))

    def test_safe_call_distinguishes_missing_method_and_missing_required_argument(self):
        receiver = self.BaseModel()
        with self.assertRaisesRegex(AttributeError, "Method missing not found"):
            self.utils.safe_call_method(receiver, "missing")
        with self.assertRaisesRegex(TypeError, "Missing required argument: value"):
            self.utils.safe_call_method(receiver, lambda value: value)
        with self.assertRaisesRegex(AttributeError, "No Method parameter"):
            self.utils.safe_call_method(receiver, None)


if __name__ == "__main__":
    unittest.main()
