"""Additional behavioral coverage for production utility and mapping helpers.

Only import-time Odoo/PostgreSQL APIs are represented by small stand-ins; the
functions and mapping method under test are loaded from the addon's real files.
"""
import importlib.util
import pathlib
import sys
import types
import unittest
from unittest.mock import Mock

ADDON = pathlib.Path(__file__).resolve().parents[2]


def _load_utils():
    psycopg = types.ModuleType("psycopg2")
    psycopg.__path__ = []
    psycopg_impl = types.ModuleType("psycopg2._psycopg")
    psycopg_impl.AsIs = lambda value: value
    odoo = types.ModuleType("odoo")
    odoo.SUPERUSER_ID = 1
    odoo._ = lambda message: message
    odoo.models = types.SimpleNamespace(BaseModel=type("BaseModel", (), {}))
    exceptions = types.ModuleType("odoo.exceptions")
    exceptions.UserError = type("UserError", (Exception,), {})
    tools = types.ModuleType("odoo.tools")
    tools.attrgetter = lambda name: lambda obj: getattr(obj, name)
    tools.clean_context = lambda context: dict(context)
    names = ("psycopg2", "psycopg2._psycopg", "odoo", "odoo.exceptions", "odoo.tools")
    old = dict((name, sys.modules.get(name)) for name in names)
    sys.modules.update({"psycopg2": psycopg, "psycopg2._psycopg": psycopg_impl,
                        "odoo": odoo, "odoo.exceptions": exceptions, "odoo.tools": tools})
    try:
        spec = importlib.util.spec_from_file_location("misc_extra3_utils", ADDON / "tools" / "utils.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        for name, module in old.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module


def _load_mapping_class():
    odoo = types.ModuleType("odoo")
    odoo.__path__ = []
    odoo._ = lambda value: value

    class Field(object):
        def __init__(self, *args, **kwargs):
            pass

    odoo.fields = types.SimpleNamespace(Boolean=Field, Integer=Field, Many2one=Field,
                                        Char=Field, Text=Field, Selection=Field)
    odoo.models = types.SimpleNamespace(Model=type("Model", (), {}))
    safe_eval_module = types.ModuleType("odoo.tools.safe_eval")
    safe_eval_module.safe_eval = lambda script, context, mode=None, nocopy=None: exec(script, context)
    tools_module = types.ModuleType("odoo.tools")
    tools_module.safe_eval = safe_eval_module.safe_eval
    addon_name = "amr_data_sync"
    models_name, tools_name = addon_name + ".models", addon_name + ".tools"
    utils_name = tools_name + ".utils"
    utils_module = types.ModuleType(utils_name)

    def has_kwargs(func):
        import inspect
        return any(p.kind == p.VAR_KEYWORD for p in inspect.signature(func).parameters.values())

    utils_module.has_kwargs = has_kwargs
    utils_module.is_callable_method = lambda obj, name: callable(getattr(obj, name, None))
    names = ("odoo", "odoo.tools", "odoo.tools.safe_eval", addon_name, models_name,
             tools_name, utils_name, models_name + ".data_mapping")
    old = dict((name, sys.modules.get(name)) for name in names)
    for name, path in ((addon_name, ADDON), (models_name, ADDON / "models"),
                       (tools_name, ADDON / "tools")):
        package = types.ModuleType(name)
        package.__path__ = [str(path)]
        sys.modules[name] = package
    sys.modules.update({"odoo": odoo, "odoo.tools": tools_module,
                        "odoo.tools.safe_eval": safe_eval_module, utils_name: utils_module})
    try:
        module_name = models_name + ".data_mapping"
        spec = importlib.util.spec_from_file_location(module_name, ADDON / "models" / "data_mapping.py")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module.ExternalDataMapping
    finally:
        for name, module in old.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module


class UtilityExtra3Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.utils = _load_utils()

    def test_ensure_external_fields_creates_missing_fields_with_complete_metadata(self):
        model = types.SimpleNamespace(id=23)
        ir_model = types.SimpleNamespace(search=Mock(return_value=model))
        fields_model = types.SimpleNamespace(search=Mock(side_effect=[False, True, False]),
                                             create=Mock(side_effect=lambda vals: dict(vals)))
        created = self.utils.ensure_external_fields(
            types.SimpleNamespace(env={"ir.model": ir_model, "ir.model.fields": fields_model}),
            "res.partner")
        self.assertEqual([item["name"] for item in created],
                         ["x_external_app_name", "x_external_odoo_id"])
        self.assertEqual(created[0], {"name": "x_external_app_name", "field_description": "External App Name",
                                      "ttype": "char", "model_id": 23, "state": "manual", "store": True})
        self.assertEqual(created[1]["ttype"], "integer")
        self.assertEqual(created[1]["model_id"], 23)
        self.assertEqual(fields_model.create.call_count, 2)
        self.assertEqual(fields_model.search.call_count, 3)

    def test_safe_call_method_accepts_callable_and_preserves_keyword_only_binding(self):
        def combine(left, *, right):
            return left + right
        self.assertEqual(self.utils.safe_call_method(object(), combine,
                                                     args=["left"], kwargs={"right": "-right"}),
                         "left-right")

    def test_safe_call_method_rejects_missing_required_keyword_only_argument(self):
        class Receiver(object):
            def combine(self, *, right):
                return right
        with self.assertRaisesRegex(TypeError, "Missing keyword-only argument: right"):
            self.utils.safe_call_method(Receiver(), "combine")


class MappingExtra3Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mapping_class = _load_mapping_class()

    def mapping(self, **attrs):
        record = self.mapping_class()
        record.__dict__.update(attrs)
        return record

    def test_parent_mapping_updates_changed_payload_and_marks_empty_payload_done(self):
        related = types.SimpleNamespace(data_json='{"old": 1}', write=Mock(),
                                        get_data_relation=Mock(return_value="relation"))
        related_model = types.SimpleNamespace(get_relation_data=Mock(return_value=related))
        mapping = self.mapping(mapping_strategy="parent", key_name="remote", internal_field="local",
                               env={"external.data.sync.related": related_model})
        self.assertEqual(mapping.mapping_data({"remote": {"new": 2}}, parent_data_sync="parent"), "relation")
        related.write.assert_called_once_with({"data_json": '{"new": 2}'})
        related_model.get_relation_data.assert_called_once_with("local", "parent")
        related.write.reset_mock()
        related.data_json = "null"
        self.assertEqual(mapping.mapping_data({"remote": None}, parent_data_sync="parent"), "relation")
        related.write.assert_called_once_with({"state": "done"})

    def test_many2one_mapping_creates_relation_and_completes_when_source_is_falsey(self):
        related = types.SimpleNamespace(write=Mock(), get_data_relation=Mock(return_value=False))
        related_model = types.SimpleNamespace(get_relation_data=Mock(return_value=False),
                                             create_many2one=Mock(return_value=related))
        mapping = self.mapping(mapping_strategy="many2one", key_name="remote", internal_field="local",
                               env={"external.data.sync.related": related_model},
                               relation_strategy_id="strategy")
        self.assertFalse(mapping.mapping_data({"remote": []}, parent_data_sync="parent"))
        related_model.create_many2one.assert_called_once_with("local", "parent", [], "strategy")
        related.write.assert_called_once_with({"state": "done"})

    def test_many2many_mapping_persists_changed_json_and_returns_relation_value(self):
        related = types.SimpleNamespace(data_json='[1]', write=Mock(),
                                        get_data_relation=Mock(return_value=[1, 2]))
        related_model = types.SimpleNamespace(get_relation_data=Mock(return_value=related))
        mapping = self.mapping(mapping_strategy="many2many", key_name="items", internal_field="item_ids",
                               env={"external.data.sync.related": related_model},
                               relation_strategy_id="strategy")
        self.assertEqual(mapping.mapping_data({"items": [1, 2]}, parent_data_sync=9), [1, 2])
        related.write.assert_called_once_with({"data_json": "[1, 2]"})
        related_model.get_relation_data.assert_called_once_with("item_ids", 9)

    def test_function_mapping_prefers_relational_comodel_method(self):
        transform = Mock(return_value="from comodel")
        comodel = types.SimpleNamespace(transform=transform)
        mapping = self.mapping(mapping_strategy="function", function_name="transform",
                               env={"res.partner": comodel}, sync_strategy_id="strategy")
        field = types.SimpleNamespace(relational=True, comodel_name="res.partner")
        self.assertEqual(mapping.mapping_data({"id": 4}, model=object(), field=field), "from comodel")
        transform.assert_called_once_with(external_data={"id": 4}, sync_strategy="strategy")
