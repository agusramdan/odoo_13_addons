"""Offline unit coverage for the production tools/utils.py helpers.

Odoo and psycopg2 are minimal import-time stand-ins; every tested helper is
executed from the real production source file.
"""
import importlib.util
import pathlib
import sys
import types
import unittest
from contextlib import contextmanager
from unittest.mock import Mock


ADDON = pathlib.Path(__file__).resolve().parents[2]
UTILS_PATH = ADDON / "tools" / "utils.py"


def load_utils():
    odoo = types.ModuleType("odoo")
    odoo.SUPERUSER_ID = 1
    odoo._ = lambda value: value

    class BaseModel(object):
        pass

    odoo.models = types.SimpleNamespace(BaseModel=BaseModel)
    exceptions = types.ModuleType("odoo.exceptions")

    class UserError(Exception):
        pass

    exceptions.UserError = UserError
    tools = types.ModuleType("odoo.tools")
    tools.attrgetter = lambda name: lambda obj: getattr(obj, name)
    tools.clean_context = lambda context: dict(context)
    psycopg2 = types.ModuleType("psycopg2")
    psycopg2.__path__ = []
    psycopg2_inner = types.ModuleType("psycopg2._psycopg")
    psycopg2_inner.AsIs = lambda value: value

    names = ("odoo", "odoo.exceptions", "odoo.tools", "psycopg2",
             "psycopg2._psycopg")
    previous = {name: sys.modules.get(name) for name in names}
    sys.modules.update({"odoo": odoo, "odoo.exceptions": exceptions,
                        "odoo.tools": tools, "psycopg2": psycopg2,
                        "psycopg2._psycopg": psycopg2_inner})
    try:
        spec = importlib.util.spec_from_file_location("utils_under_test", UTILS_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        for name, old_module in previous.items():
            if old_module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = old_module


class UtilsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.utils = load_utils()

    def test_safe_call_method_binds_positional_keywords_and_defaults(self):
        class Receiver(object):
            def combine(self, first, second=2, *, suffix="!"):
                return "{}:{}:{}".format(first, second, suffix)

        self.assertEqual(self.utils.safe_call_method(
            Receiver(), "combine", args=["a"], kwargs={"second": 3, "suffix": "?"}),
            "a:3:?")
        self.assertEqual(self.utils.safe_call_method(Receiver(), "combine", args=["a"]), "a:2:!")

    def test_safe_call_method_handles_variadic_arguments(self):
        class Receiver(object):
            def collect(self, first, *items, **options):
                return first, items, options

        self.assertEqual(self.utils.safe_call_method(
            Receiver(), "collect", args=[1, 2, 3], kwargs={"flag": True}),
            (1, (2, 3), {"flag": True}))

    def test_safe_call_method_reports_missing_required_argument(self):
        class Receiver(object):
            def run(self, required):
                return required

        with self.assertRaisesRegex(TypeError, "Missing required argument: required"):
            self.utils.safe_call_method(Receiver(), "run")

    def test_safe_call_method_rejects_missing_method_parameter(self):
        with self.assertRaisesRegex(AttributeError, "No Method parameter"):
            self.utils.safe_call_method(object(), None)

    def test_safe_call_method_returns_none_for_ineligible_object(self):
        self.assertIsNone(self.utils.safe_call_method(None, "run"))

    def test_get_callable_method_is_false_for_absent_or_noncallable_attribute(self):
        receiver = types.SimpleNamespace(value=4)
        self.assertFalse(self.utils.get_callable_method(receiver, "absent"))
        self.assertFalse(self.utils.get_callable_method(receiver, "value"))
        self.assertTrue(self.utils.get_callable_method(receiver, "__str__"))
        self.assertFalse(self.utils.get_callable_method(None, "bad"))

    def test_is_callable_method_delegates_to_callable_lookup(self):
        receiver = types.SimpleNamespace(run=lambda: 1)
        self.assertTrue(self.utils.is_callable_method(receiver, "run"))
        self.assertFalse(self.utils.is_callable_method(receiver, "missing"))

    def test_has_kwargs_detects_only_arbitrary_keyword_parameter(self):
        def ordinary(value):
            return value

        def arbitrary(**kwargs):
            return kwargs

        self.assertFalse(self.utils.has_kwargs(ordinary))
        self.assertTrue(self.utils.has_kwargs(arbitrary))

    def test_convert_external_data_normalizes_supported_shapes(self):
        source = {"id": 8, "name": "same"}
        self.assertEqual(self.utils.convert_from_external_data(12), {"id": 12})
        self.assertEqual(self.utils.convert_from_external_data([]), {})
        self.assertEqual(self.utils.convert_from_external_data([7]), {"id": 7})
        self.assertEqual(self.utils.convert_from_external_data([7, "Seven", "ignored"]),
                         {"id": 7, "display_name": "Seven"})
        self.assertIs(self.utils.convert_from_external_data(source), source)
        self.assertEqual(self.utils.convert_from_external_data("unsupported"), {})

    def test_call_with_savepoint_returns_successful_result(self):
        class Cursor(object):
            @contextmanager
            def savepoint(self):
                yield

        receiver = types.SimpleNamespace(env=types.SimpleNamespace(cr=Cursor(), uid=1))
        receiver.run = lambda value: value * 2
        self.assertEqual(self.utils.call_with_savepoint(receiver, "run", args=[6]), 12)

    def test_call_with_savepoint_logs_and_swallows_failure_by_default(self):
        class Cursor(object):
            @contextmanager
            def savepoint(self):
                yield

        receiver = types.SimpleNamespace(env=types.SimpleNamespace(cr=Cursor(), uid=1))
        receiver.run = Mock(side_effect=ValueError("broken"))
        logger = Mock()
        self.assertIsNone(self.utils.call_with_savepoint(receiver, "run", logger=logger))
        logger.warning.assert_called_once()
        receiver.run.assert_called_once_with()

    def test_call_with_savepoint_rethrows_when_requested(self):
        class Cursor(object):
            @contextmanager
            def savepoint(self):
                yield

        receiver = types.SimpleNamespace(env=types.SimpleNamespace(cr=Cursor(), uid=1))
        receiver.run = Mock(side_effect=ValueError("broken"))
        with self.assertRaisesRegex(ValueError, "broken"):
            self.utils.call_with_savepoint(receiver, "run", logger=Mock(), rethrow=True)


if __name__ == "__main__":
    unittest.main()
