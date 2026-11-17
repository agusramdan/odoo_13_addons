"""Offline behavioral coverage for utility methods used by data sync."""
import importlib.util
import pathlib
import sys
import types
import unittest
from unittest.mock import Mock


def load_utils():
    """Load the production file with only its Odoo/PostgreSQL imports stubbed."""
    psycopg = types.ModuleType("psycopg2")
    psycopg_impl = types.ModuleType("psycopg2._psycopg")
    psycopg_impl.AsIs = lambda value: value
    odoo = types.ModuleType("odoo")
    odoo.SUPERUSER_ID = 1
    odoo._ = lambda message: message
    odoo.models = types.SimpleNamespace(BaseModel=type("BaseModel", (), {}))
    exceptions = types.ModuleType("odoo.exceptions")
    exceptions.UserError = type("UserError", (Exception,), {})
    tools = types.ModuleType("odoo.tools")
    tools.attrgetter = lambda name: lambda value: getattr(value, name)
    tools.clean_context = lambda context: dict(context)
    prior = {name: sys.modules.get(name) for name in
             ("psycopg2", "psycopg2._psycopg", "odoo", "odoo.exceptions", "odoo.tools")}
    sys.modules.update({"psycopg2": psycopg, "psycopg2._psycopg": psycopg_impl,
                        "odoo": odoo, "odoo.exceptions": exceptions, "odoo.tools": tools})
    path = pathlib.Path(__file__).parents[2] / "tools" / "utils.py"
    spec = importlib.util.spec_from_file_location("amr_data_sync_utils_tested", str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for name, value in prior.items():
        if value is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = value
    return module


utils = load_utils()


class UtilsExtraBehaviorTest(unittest.TestCase):
    def test_safe_call_method_maps_positional_named_and_keyword_only_arguments(self):
        class Receiver(utils.models.BaseModel):
            def combine(self, first, second=2, *, flag, **extra):
                return first, second, flag, extra

        receiver = Receiver()
        result = utils.safe_call_method(
            receiver, "combine", args=["A"],
            kwargs={"flag": True, "trace": "kept", "unused": "discarded"})
        self.assertEqual(result, ("A", 2, True, {"trace": "kept", "unused": "discarded"}))

    def test_safe_call_method_reports_missing_required_and_rejects_non_model(self):
        class Receiver(utils.models.BaseModel):
            def run(self, required):
                return required

        with self.assertRaisesRegex(TypeError, "Missing required argument: required"):
            utils.safe_call_method(Receiver(), "run")
        with self.assertRaisesRegex(AttributeError, "Method run not found"):
            utils.safe_call_method(object(), "run")

    def test_safe_call_method_rethrows_method_failures_unchanged(self):
        error = RuntimeError("operation failed")
        class Receiver(utils.models.BaseModel):
            def run(self):
                raise error
        with self.assertRaises(RuntimeError) as caught:
            utils.safe_call_method(Receiver(), "run")
        self.assertIs(caught.exception, error)

    def test_callable_helpers_distinguish_missing_noncallable_and_descriptor_failure(self):
        class Broken(object):
            @property
            def explode(self):
                raise RuntimeError("descriptor")
        self.assertTrue(utils.get_callable_method(types.SimpleNamespace(run=lambda: None), "run"))
        self.assertFalse(utils.is_callable_method(types.SimpleNamespace(run=3), "run"))
        self.assertFalse(utils.get_callable_method(Broken(), "explode"))

    def test_has_kwargs_inspects_real_callable_signature(self):
        def flexible(value, **options):
            return value, options
        def fixed(value, option=None):
            return value, option
        self.assertTrue(utils.has_kwargs(flexible))
        self.assertFalse(utils.has_kwargs(fixed))

    def test_convert_external_data_handles_supported_shapes_without_copying_dict(self):
        original = {"id": 9, "display_name": "kept", "extra": "value"}
        self.assertEqual(utils.convert_from_external_data(12), {"id": 12})
        self.assertEqual(utils.convert_from_external_data([]), {})
        self.assertEqual(utils.convert_from_external_data([4]), {"id": 4})
        self.assertEqual(utils.convert_from_external_data([4, "Four", "ignored"]),
                         {"id": 4, "display_name": "Four"})
        self.assertIs(utils.convert_from_external_data(original), original)
        self.assertEqual(utils.convert_from_external_data("unsupported"), {})

    def test_ensure_external_fields_creates_only_missing_metadata_fields(self):
        model = types.SimpleNamespace(id=31)
        ir_model = types.SimpleNamespace(search=Mock(return_value=model))
        existing = types.SimpleNamespace(id=100)
        ir_fields = types.SimpleNamespace(
            search=Mock(side_effect=[existing, False, False]), create=Mock(side_effect=lambda vals: dict(vals)))
        created = utils.ensure_external_fields(types.SimpleNamespace(env={
            "ir.model": ir_model, "ir.model.fields": ir_fields}), "res.partner")
        self.assertEqual(len(created), 2)
        self.assertEqual([field["name"] for field in created],
                         ["x_external_model", "x_external_odoo_id"])
        self.assertEqual(ir_fields.create.call_args_list[0][0][0]["model_id"], 31)
        self.assertEqual(ir_fields.create.call_args_list[1][0][0]["state"], "manual")
        ir_model.search.assert_called_once_with([("model", "=", "res.partner")], limit=1)

    def test_ensure_external_fields_raises_for_unknown_model(self):
        with self.assertRaisesRegex(utils.UserError, "Model missing.model not found"):
            utils.ensure_external_fields(types.SimpleNamespace(env={
                "ir.model": types.SimpleNamespace(search=Mock(return_value=False)),
                "ir.model.fields": Mock()}), "missing.model")

    def test_call_with_savepoint_swallows_or_reraises_and_logs_failure(self):
        events = []
        class Context(object):
            def __enter__(self):
                events.append("enter")
            def __exit__(self, kind, value, tb):
                events.append("rollback" if kind else "commit")
                return False
        failure = ValueError("bad call")
        target = utils.models.BaseModel()
        target.env = types.SimpleNamespace(cr=types.SimpleNamespace(savepoint=Context))
        target.run = Mock(side_effect=failure)
        logger = Mock()
        self.assertIsNone(utils.call_with_savepoint(target, "run", logger=logger))
        self.assertEqual(events, ["enter", "rollback"])
        logger.warning.assert_called_once()
        with self.assertRaises(ValueError) as caught:
            utils.call_with_savepoint(target, "run", logger=logger, rethrow=True)
        self.assertIs(caught.exception, failure)
        self.assertEqual(events, ["enter", "rollback", "enter", "rollback"])


if __name__ == "__main__":
    unittest.main()
