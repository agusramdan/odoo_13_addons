"""Deep behavioral tests for signature dispatch in production tools/utils.py."""
import importlib.util
import pathlib
import sys
import types
import unittest

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
        spec = importlib.util.spec_from_file_location("utils_deep11_under_test", UTILS_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        for name, old_module in previous.items():
            if old_module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = old_module


class UtilsDeep11Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.utils = load_utils()

    def test_safe_call_method_consumes_positional_args_before_named_values(self):
        class Receiver(object):
            def build(self, first, second="default", *, mode="normal"):
                return first, second, mode

        receiver = Receiver()
        self.assertEqual(
            self.utils.safe_call_method(receiver, "build", args=["arg-first"],
                                        kwargs={"first": "ignored", "mode": "fast"}),
            ("arg-first", "default", "fast"))

    def test_safe_call_method_routes_remaining_args_and_keywords_to_variadics(self):
        class Receiver(object):
            def collect(self, fixed, *items, label="unset", **options):
                return fixed, items, label, options

        self.assertEqual(
            self.utils.safe_call_method(
                Receiver(), "collect", args=[1, 2, 3],
                kwargs={"label": "chosen", "enabled": True}),
            (1, (2, 3), "chosen", {"enabled": True}))

    def test_safe_call_method_uses_default_for_omitted_required_position(self):
        class Receiver(object):
            def render(self, prefix, count=3, *, uppercase=False):
                value = prefix * count
                return value.upper() if uppercase else value

        self.assertEqual(self.utils.safe_call_method(
            Receiver(), "render", kwargs={"prefix": "x", "uppercase": True}), "XXX")

    def test_safe_call_method_does_not_forward_extra_arguments_without_variadics(self):
        class Receiver(object):
            def one(self, value):
                return value

        self.assertEqual(self.utils.safe_call_method(Receiver(), "one", args=[7, 8]), 7)
        self.assertEqual(self.utils.safe_call_method(
            Receiver(), "one", args=[7], kwargs={"unused": "discarded"}), 7)

    def test_callable_lookup_handles_attribute_access_errors(self):
        class Hostile(object):
            @property
            def action(self):
                raise RuntimeError("descriptor failed")

        self.assertFalse(self.utils.get_callable_method(Hostile(), "action"))
        self.assertFalse(self.utils.is_callable_method(Hostile(), "action"))

    def test_convert_external_data_preserves_mapping_and_ignores_non_supported_shapes(self):
        original = {"id": 0, "display_name": "Zero", "extra": 5}
        self.assertIs(self.utils.convert_from_external_data(original), original)
        self.assertEqual(self.utils.convert_from_external_data((4, "tuple")), {})
        self.assertEqual(self.utils.convert_from_external_data(None), {})
        self.assertEqual(self.utils.convert_from_external_data([None, "No ID"]),
                         {"id": None, "display_name": "No ID"})


if __name__ == "__main__":
    unittest.main()
