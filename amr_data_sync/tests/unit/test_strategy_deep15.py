"""Behavioral regression tests for strategy configuration edge paths."""
import importlib.util
import pathlib
import types
import unittest
from unittest.mock import Mock

UNIT_DIR = pathlib.Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("strategy_deep15_support", UNIT_DIR / "test_sync_strategy.py")
_support = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_support)


class _Env(dict):
    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)
        self.cr = types.SimpleNamespace(savepoint=lambda: _NullContext())


class StrategyDeep15Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.strategy_class, _ = _support.load_strategy_class()

    def strategy(self, **values):
        strategy = self.strategy_class()
        strategy.__dict__.update(values)
        strategy.ensure_one = lambda: strategy
        return strategy

    def test_internal_model_object_resolves_configured_model_only(self):
        model = object()
        strategy = self.strategy(internal_model="res.partner", env={"res.partner": model})
        self.assertIs(strategy.internal_model_object(), model)
        strategy.internal_model = False
        self.assertIsNone(strategy.internal_model_object())

    def test_company_mapping_branches_build_expected_external_domain(self):
        for mapped, unmapped, expected in (
                ({4: [21, 22]}, [], [("company_id", "in", [21, 22])]),
                ({}, [4], [("company_id.name", "in", ["Acme"])])):
            strategy = self.strategy(
                external_domain="[]", external_context="{}", company_ids=[types.SimpleNamespace(id=4, name="Acme")],
                server_sync_id=types.SimpleNamespace(get_application_name=lambda: "test-app"), filter_last_update=False,
                internal_lookup_fields="",
                env=_Env({"external.data.company": types.SimpleNamespace(
                    reverse_mapping=Mock(return_value=(mapped, unmapped)))}))
            config = strategy.prepare_sync_list_dict()
            self.assertEqual(config["domain"], expected)

    def test_prepare_input_skips_empty_values_and_defers_relations(self):
        class Field(object):
            def __init__(self, name, kind="char", required=False):
                self.name, self.type, self.required = name, kind, required
                self.compute = self.related = False
        class Model(object):
            _fields = {"name": Field("name"), "parent_id": Field("parent_id", "many2one")}
            def check_field_access_rights(self, mode, fields):
                return list(self._fields)
        relation = object()
        related = Mock(return_value=17)
        parent = types.SimpleNamespace(company_id=False, get_related_data=related)
        strategy = self.strategy(internal_model="x", relation_field_ignore=False, eval_script=False,
                                 env=_Env({"x": Model()}),
                                 get_include_fields=lambda: [], get_exclude_fields=lambda: [],
                                 get_mapping_fields=lambda: {}, get_after_create_fields=lambda: [])
        strategy.env.cr = types.SimpleNamespace(savepoint=lambda: _NullContext())
        result = strategy.prepare_input_external(parent, {"name": "", "parent_id": relation})
        self.assertEqual(result, {"parent_id": 17})
        related.assert_called_once_with(Model._fields["parent_id"], relation)

    def test_relation_deferred_when_field_is_after_create(self):
        class Field(object):
            name, type, required, compute, related = "parent_id", "many2one", False, False, False
        class Model(object):
            _fields = {"parent_id": Field()}
            def check_field_access_rights(self, mode, fields): return ["parent_id"]
        relation = {"id": 3}
        related = Mock(return_value=44)
        strategy = self.strategy(internal_model="x", relation_field_ignore=False, eval_script=False,
                                 env=_Env({"x": Model()}),
                                 get_include_fields=lambda: [], get_exclude_fields=lambda: [],
                                 get_mapping_fields=lambda: {}, get_after_create_fields=lambda: ["parent_id"])
        strategy.env.cr = types.SimpleNamespace(savepoint=lambda: _NullContext())
        result = strategy.prepare_input_external(types.SimpleNamespace(company_id=False, get_related_data=related),
                                                 {"parent_id": relation})
        self.assertEqual(result, {})
        related.assert_called_once()


class _NullContext(object):
    def __enter__(self): return self
    def __exit__(self, *exc): return False


if __name__ == "__main__":
    unittest.main()
