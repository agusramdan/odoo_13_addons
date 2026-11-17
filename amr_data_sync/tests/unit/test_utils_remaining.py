"""Focused coverage for lower-level SQL creation helpers in tools/utils.py."""
import importlib.util
import pathlib
import sys
import types
import unittest
from unittest.mock import Mock


UTILS_PATH = pathlib.Path(__file__).resolve().parents[2] / "tools" / "utils.py"


def load_utils():
    odoo = types.ModuleType("odoo")
    odoo.SUPERUSER_ID = 1
    odoo._ = lambda value: value

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

    replacements = {
        "odoo": odoo,
        "odoo.exceptions": exceptions,
        "odoo.tools": tools,
        "psycopg2": psycopg2,
        "psycopg2._psycopg": psycopg2_inner,
    }
    previous = {name: sys.modules.get(name) for name in replacements}
    sys.modules.update(replacements)
    try:
        spec = importlib.util.spec_from_file_location("utils_remaining_under_test", UTILS_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        for name, old_module in previous.items():
            if old_module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = old_module


class UtilsRemainingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.utils = load_utils()

    def test_insert_data_sql_partitions_fields_and_ignores_protected_columns(self):
        class Field(types.SimpleNamespace):
            __hash__ = object.__hash__

        stored = Field(store=True, inherited=False, inverse=False,
                       company_dependent=False, compute=None, readonly=True)
        inverse = Field(store=False, inherited=False, inverse=True,
                        company_dependent=False, compute=None, readonly=True)
        inherited = Field(store=True, inherited=True, inverse=False,
                          company_dependent=False,
                          related_field=types.SimpleNamespace(model_name="parent"),
                          compute=None, readonly=True)
        model = types.SimpleNamespace(
            _log_access=True, _fields={"name": stored, "alias": inverse,
                                       "parent_name": inherited,
                                       "defaulted": stored},
            _field_computed={}, _name="demo.model",
        )
        model.env = types.SimpleNamespace(
            uid=7, pool=types.SimpleNamespace(ready=True),
        )
        model._add_missing_default_values = lambda vals: dict(vals, defaulted=True)
        delegated = Mock(return_value="created")
        self.utils.insert_sql = delegated

        result = self.utils.insert_data_sql(model, [{
            "name": "record", "alias": "display", "parent_name": "inherited",
            "create_uid": 99, "parent_path": "ignored",
        }])

        self.assertEqual(result, "created")
        delegated.assert_called_once()
        data_list = delegated.call_args[0][1]
        self.assertEqual(len(data_list), 1)
        data = data_list[0]
        self.assertEqual(data["stored"], {"name": "record", "parent_name": "inherited",
                                         "defaulted": True})
        self.assertEqual(data["inversed"], {"alias": "display"})
        self.assertEqual(data["inherited"], {"parent": {"parent_name": "inherited"}})
        self.assertEqual(data["protected"], set())

    def test_insert_data_sql_rejects_unknown_fields_before_inserting(self):
        model = types.SimpleNamespace(
            _log_access=False, _fields={}, _field_computed={}, _name="demo.model",
            env=types.SimpleNamespace(uid=7, pool=types.SimpleNamespace(ready=True)),
            _add_missing_default_values=lambda vals: vals,
        )
        with self.assertRaisesRegex(ValueError, "Invalid field 'unknown'"):
            self.utils.insert_data_sql(model, [{"unknown": 1}])

if __name__ == "__main__":
    unittest.main()
