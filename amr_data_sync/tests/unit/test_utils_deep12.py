"""Focused SQL construction and field-partition tests for tools/utils.py."""
import importlib.util
import pathlib
import sys
import types
import unittest
from collections import defaultdict

ADDON = pathlib.Path(__file__).resolve().parents[2]
UTILS_PATH = ADDON / "tools" / "utils.py"


def load_utils():
    odoo = types.ModuleType("odoo")
    odoo.SUPERUSER_ID = 1
    odoo._ = lambda value: value
    odoo.models = types.SimpleNamespace(BaseModel=type("BaseModel", (), {}))
    exceptions = types.ModuleType("odoo.exceptions")
    exceptions.UserError = type("UserError", (Exception,), {})
    tools = types.ModuleType("odoo.tools")
    tools.attrgetter = lambda name: lambda obj: getattr(obj, name)
    tools.clean_context = lambda context: dict(context)
    psycopg2 = types.ModuleType("psycopg2")
    psycopg2.__path__ = []
    psycopg2_inner = types.ModuleType("psycopg2._psycopg")
    class AsIs(object):
        def __init__(self, value):
            self.value = value
        def __str__(self):
            return self.value
    psycopg2_inner.AsIs = AsIs
    replacements = {"odoo": odoo, "odoo.exceptions": exceptions,
                    "odoo.tools": tools, "psycopg2": psycopg2,
                    "psycopg2._psycopg": psycopg2_inner}
    previous = {key: sys.modules.get(key) for key in replacements}
    sys.modules.update(replacements)
    try:
        spec = importlib.util.spec_from_file_location("utils_deep12_under_test", UTILS_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        for key, value in previous.items():
            if value is None:
                sys.modules.pop(key, None)
            else:
                sys.modules[key] = value


class Cursor(object):
    def __init__(self, ids):
        self.ids = iter(ids)
        self.calls = []
    def execute(self, query, params):
        self.calls.append((query, params))
    def fetchone(self):
        return (next(self.ids),)


class Field(object):
    def __init__(self, name, fmt="%s", translate=False, column_type=True):
        self.name = name
        self.store = True
        self.column_type = column_type
        self.column_format = fmt
        self.translate = translate
        self.type = "char"
        self.related = False
        self.compute = False
        self.company_dependent = False
        self.inherited = False
        self.inverse = False
        self.related_field = types.SimpleNamespace(model_name="demo.item")
    def convert_to_column(self, value, model, stored):
        return "db:" + str(value)
    def convert_to_cache(self, value, record):
        return value


class Record(object):
    def __init__(self, record_id):
        self.id = record_id
        self._field_inverses = {}


class Records(list):
    def _parent_store_create(self):
        pass
    def modified(self, fields, create=False):
        pass
    def _validate_fields(self, fields):
        self.validated = set(fields)
    def check_access_rule(self, operation):
        self.checked_operation = operation


class Model(object):
    _log_access = False
    _uid = 23
    _name = "demo.item"
    _table = "demo_item"
    _context = {}
    _fields = {}
    CONCURRENCY_CHECK_FIELD = "__last_update"
    def __init__(self, ids):
        self.env = types.SimpleNamespace(cr=Cursor(ids), cache=types.SimpleNamespace(
            set=lambda *args: None, contains=lambda *args: False), lang="en_US",
            protecting=lambda protected: _null_context())
    def browse(self, ids):
        return Records(Record(value) for value in ids)


from contextlib import contextmanager
@contextmanager
def _null_context():
    yield


class UtilsDeep12Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.utils = load_utils()

    def test_insert_sql_quotes_table_columns_sorts_values_and_returns_ids(self):
        model = Model([41, 42])
        model._fields = {name: Field(name) for name in ("zeta", "alpha")}
        result = self.utils.insert_sql(model, [
            {"stored": {"zeta": "last", "alpha": "first"}, "inherited": {}, "protected": set()},
            {"stored": {"alpha": "second"}, "inherited": {}, "protected": set()},
        ])
        self.assertEqual([record.id for record in result], [41, 42])
        self.assertEqual(model.env.cr.calls, [
            ('INSERT INTO "demo_item" ("alpha", "zeta") VALUES (%s, %s) RETURNING id',
             ["db:first", "db:last"]),
            ('INSERT INTO "demo_item" ("alpha") VALUES (%s) RETURNING id', ["db:second"]),
        ])

    def test_insert_sql_adds_log_access_sql_expression_as_parameter(self):
        model = Model([9])
        model._log_access = True
        model._fields = {"name": Field("name")}
        self.utils.insert_sql(model, [{"stored": {"name": "item"}, "inherited": {}, "protected": set()}])
        query, params = model.env.cr.calls[0]
        self.assertEqual(query, 'INSERT INTO "demo_item" ("create_uid", "create_date", "write_uid", "write_date", "name") VALUES (%s, %s, %s, %s, %s) RETURNING id')
        self.assertEqual(params[0], 23)
        self.assertEqual(str(params[1]), "(now() at time zone 'UTC')")
        self.assertEqual(params[2], 23)
        self.assertEqual(str(params[3]), "(now() at time zone 'UTC')")
        self.assertEqual(params[4], "db:item")

    def test_insert_sql_omits_explicit_log_access_values_from_automatic_columns(self):
        model = Model([5])
        model._log_access = True
        model._fields = {"name": Field("name"), "create_uid": Field("create_uid")}
        self.utils.insert_sql(model, [{"stored": {"name": "x", "create_uid": 77}, "inherited": {}, "protected": set()}])
        query, params = model.env.cr.calls[0]
        self.assertEqual(query, 'INSERT INTO "demo_item" ("create_date", "write_uid", "write_date", "create_uid", "name") VALUES (%s, %s, %s, %s, %s) RETURNING id')
        self.assertEqual(str(params[0]), "(now() at time zone 'UTC')")
        self.assertEqual(params[1], 23)
        self.assertEqual(str(params[2]), "(now() at time zone 'UTC')")
        self.assertEqual(params[3:], ["db:77", "db:x"])

    def test_insert_data_sql_filters_parent_path_and_constructs_stored_columns(self):
        model = Model([18])
        model._fields = {"name": Field("name")}
        model._add_missing_default_values = lambda vals: dict(vals)
        result = self.utils.insert_data_sql(model, [{"parent_path": "ignored", "name": "chosen"}])
        self.assertEqual([record.id for record in result], [18])
        self.assertEqual(model.env.cr.calls, [
            ('INSERT INTO "demo_item" ("name") VALUES (%s) RETURNING id', ["db:chosen"])
        ])

    def test_insert_data_sql_rejects_unknown_field_before_any_sql(self):
        model = Model([1])
        model._add_missing_default_values = lambda vals: dict(vals)
        with self.assertRaisesRegex(ValueError, "Invalid field 'missing' on model 'demo.item'"):
            self.utils.insert_data_sql(model, [{"missing": "value"}])
        self.assertEqual(model.env.cr.calls, [])


if __name__ == "__main__":
    unittest.main()
