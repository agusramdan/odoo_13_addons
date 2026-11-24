"""Offline unit tests for the real ExternalDataMapping methods.

The Odoo ORM is intentionally replaced only at import time; mapping_data itself
is loaded from the production source file and exercised directly.
"""
import importlib.util
import pathlib
import sys
import types
import unittest
from datetime import date, datetime
from unittest.mock import Mock


ADDON = pathlib.Path(__file__).resolve().parents[2]


def load_mapping_class():
    """Load production data_mapping.py with minimal Odoo import stand-ins."""
    odoo = types.ModuleType("odoo")
    odoo.__path__ = []
    odoo._ = lambda value: value

    class Field(object):
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs

    fields = types.SimpleNamespace(
        Boolean=Field, Integer=Field, Many2one=Field, Char=Field,
        Text=Field, Selection=Field,
    )
    odoo.fields = fields

    class Model(object):
        pass

    odoo.models = types.SimpleNamespace(Model=Model)
    safe_eval_module = types.ModuleType("odoo.tools.safe_eval")
    safe_eval_module.safe_eval = lambda script, context, mode=None, nocopy=None: exec(script, context)
    tools_module = types.ModuleType("odoo.tools")
    tools_module.safe_eval = safe_eval_module.safe_eval

    addon_name = "amr_data_sync"
    models_name = addon_name + ".models"
    tools_name = addon_name + ".tools"
    utils_module = types.ModuleType(tools_name + ".utils")
    utils_module.has_kwargs = lambda func: any(
        parameter.kind == parameter.VAR_KEYWORD
        for parameter in __import__("inspect").signature(func).parameters.values()
    )
    utils_module.is_callable_method = lambda obj, name: callable(getattr(obj, name, None))

    previous = {name: sys.modules.get(name) for name in (
        "odoo", "odoo.tools", "odoo.tools.safe_eval", addon_name,
        models_name, tools_name, tools_name + ".utils",
    )}
    packages = {}
    for name, path in ((addon_name, ADDON), (models_name, ADDON / "models"),
                       (tools_name, ADDON / "tools")):
        package = types.ModuleType(name)
        package.__path__ = [str(path)]
        packages[name] = package
    sys.modules.update(packages)
    sys.modules.update({
        "odoo": odoo, "odoo.tools": tools_module,
        "odoo.tools.safe_eval": safe_eval_module,
        tools_name + ".utils": utils_module,
    })
    try:
        module_name = models_name + ".data_mapping"
        spec = importlib.util.spec_from_file_location(module_name, ADDON / "models" / "data_mapping.py")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module.ExternalDataMapping
    finally:
        for name, old_module in previous.items():
            if old_module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = old_module


class MappingLogicTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mapping_class = load_mapping_class()

    def mapping(self, **values):
        mapping = self.mapping_class()
        mapping.__dict__.update(values)
        return mapping

    def test_field_mapping_uses_configured_key_and_returns_falsey_values(self):
        mapping = self.mapping(mapping_strategy="field_mapping", key_name="remote",
                               internal_field="local")
        self.assertEqual(mapping.mapping_data({"remote": False}), False)
        self.assertEqual(mapping.mapping_data({"remote": 0}), 0)
        self.assertIsNone(mapping.mapping_data({}))

    def test_field_mapping_falls_back_to_internal_field_when_key_is_empty(self):
        mapping = self.mapping(mapping_strategy="field_mapping", key_name=False,
                               internal_field="source")
        self.assertEqual(mapping.mapping_data({"source": "value"}), "value")

    def test_constant_mapping_converts_supported_scalar_types(self):
        cases = (("None", "ignored", None), ("False", "ignored", False),
                 ("True", "ignored", True), ("empty_array", "ignored", []),
                 ("empty_dict", "ignored", {}), ("empty_string", "ignored", ""),
                 ("string", "text", "text"), ("integer", "-12", -12),
                 ("float", "2.5", 2.5), ("boolean", "", False),
                 ("date", "2024-02-29", date(2024, 2, 29)),
                 ("datetime", "2024-02-29 13:14:15", datetime(2024, 2, 29, 13, 14, 15)))
        for kind, raw, expected in cases:
            with self.subTest(kind=kind):
                mapping = self.mapping(mapping_strategy="constant",
                                       constant_value_type=kind, constant_value=raw)
                self.assertEqual(mapping.mapping_data({}), expected)

    def test_function_mapping_passes_sync_context_when_callable_accepts_kwargs(self):
        receiver = types.SimpleNamespace()
        receiver.transform = Mock(return_value={"mapped": True})
        mapping = self.mapping(mapping_strategy="function", function_name="transform",
                               env={}, sync_strategy_id="strategy")
        external = {"id": 17}
        self.assertEqual(mapping.mapping_data(external, model=receiver,
                                                  field=types.SimpleNamespace(relational=False,
                                                                              comodel_name=None)), {"mapped": True})
        receiver.transform.assert_called_once_with(external_data=external,
                                                   sync_strategy="strategy")

    def test_function_mapping_calls_zero_argument_method_without_kwargs(self):
        receiver = types.SimpleNamespace()
        calls = []

        def transform():
            calls.append("called")
            return 42

        receiver.transform = transform
        mapping = self.mapping(mapping_strategy="function", function_name="transform",
                               env={}, sync_strategy_id="strategy")
        self.assertEqual(mapping.mapping_data({}, model=receiver,
                                                  field=types.SimpleNamespace(relational=False,
                                                                              comodel_name=None)), 42)
        self.assertEqual(calls, ["called"])

    def test_eval_mapping_returns_value_from_script_context(self):
        mapping = self.mapping(mapping_strategy="eval_script",
                               eval_script="value = external_data['amount'] * 2",
                               env={}, sync_strategy_id="strategy")
        self.assertEqual(mapping.mapping_data({"amount": 21}), 42)

    def test_blank_eval_script_returns_none(self):
        mapping = self.mapping(mapping_strategy="eval_script", eval_script="  \n", env={})
        self.assertIsNone(mapping.mapping_data({}))

    def test_eval_script_errors_are_reported_as_value_error(self):
        mapping = self.mapping(mapping_strategy="eval_script", eval_script="value = missing_name",
                               env={})
        with self.assertRaisesRegex(ValueError, "Error evaluating script"):
            mapping.mapping_data({})

    def test_unknown_strategy_is_rejected(self):
        mapping = self.mapping(mapping_strategy="unsupported")
        with self.assertRaisesRegex(ValueError, "Invalid mapping strategy"):
            mapping.mapping_data({})


if __name__ == "__main__":
    unittest.main()
