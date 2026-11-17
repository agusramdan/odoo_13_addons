"""Additional behavioral coverage for tools/utils.py without an Odoo runtime."""
import importlib.util
import pathlib
import sys
import types
import unittest
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
        spec = importlib.util.spec_from_file_location("utils_extra4_under_test", UTILS_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        for name, old_module in previous.items():
            if old_module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = old_module


class UtilsExtra4Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.utils = load_utils()

    def test_safe_call_method_accepts_callable_and_uses_keyword_for_positional_parameter(self):
        def target(value, optional="default"):
            return value, optional

        self.assertEqual(self.utils.safe_call_method(
            object(), target, kwargs={"value": "provided"}), ("provided", "default"))

    def test_safe_call_method_raises_for_missing_attribute_and_returns_none_for_noncallable(self):
        receiver = types.SimpleNamespace(value=7)
        with self.assertRaisesRegex(AttributeError, "Method missing not found"):
            self.utils.safe_call_method(receiver, "missing")
        self.assertIsNone(self.utils.safe_call_method(receiver, "value"))

    def test_safe_call_method_requires_keyword_only_argument(self):
        class Receiver(object):
            def run(self, *, required):
                return required

        with self.assertRaisesRegex(TypeError, "Missing keyword-only argument: required"):
            self.utils.safe_call_method(Receiver(), "run")

    def test_safe_call_method_routes_extra_keywords_to_var_keyword_parameter(self):
        class Receiver(object):
            def run(self, **options):
                return options

        self.assertEqual(self.utils.safe_call_method(
            Receiver(), "run", kwargs={"mode": "safe", "count": 2}),
            {"mode": "safe", "count": 2})

    def test_ensure_external_fields_creates_only_missing_field_definitions(self):
        model = types.SimpleNamespace(id=23)
        created = []

        class ModelCatalog(object):
            def search(self, domain, limit=None):
                self.domain = domain
                self.limit = limit
                return model

        class FieldCatalog(object):
            def search(self, domain, limit=None):
                return types.SimpleNamespace() if domain[0][2] == "x_external_model" else None

            def create(self, values):
                created.append(dict(values))
                return types.SimpleNamespace(**values)

        env = {"ir.model": ModelCatalog(), "ir.model.fields": FieldCatalog()}
        result = self.utils.ensure_external_fields(types.SimpleNamespace(env=env), "res.partner")

        self.assertEqual(len(result), 2)
        self.assertEqual([item["name"] for item in created],
                         ["x_external_app_name", "x_external_odoo_id"])
        for values in created:
            self.assertEqual(values["model_id"], 23)
            self.assertEqual(values["state"], "manual")
            self.assertTrue(values["store"])

    def test_ensure_external_fields_raises_when_model_is_unknown(self):
        class ModelCatalog(object):
            def search(self, domain, limit=None):
                return None

        env = {"ir.model": ModelCatalog(), "ir.model.fields": Mock()}
        with self.assertRaisesRegex(self.utils.UserError, "Model missing.model not found"):
            self.utils.ensure_external_fields(types.SimpleNamespace(env=env), "missing.model")

    def test_ensure_external_fields_creates_nothing_when_all_fields_exist(self):
        model = types.SimpleNamespace(id=4)

        class Catalog(object):
            def search(self, domain, limit=None):
                return model if domain[0][0] == "model" else types.SimpleNamespace()

            def create(self, values):
                self.fail("create must not run when every external field exists")

        result = self.utils.ensure_external_fields(
            types.SimpleNamespace(env={"ir.model": Catalog(), "ir.model.fields": Catalog()}),
            "res.partner")
        self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main()
