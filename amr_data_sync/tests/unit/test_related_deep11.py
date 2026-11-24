"""Focused offline tests for relational resolution and failure handling."""
import importlib.util
import pathlib
import sys
import types
import unittest
from unittest.mock import Mock

ADDON = pathlib.Path(__file__).resolve().parents[2]


class Record(object):
    def __init__(self, **values):
        self.__dict__.update(values)

    def __bool__(self):
        return bool(getattr(self, "ids", [True]))

    __nonzero__ = __bool__

    def __int__(self):
        return self.id

    def write(self, values):
        self.writes.append(dict(values))
        for key, value in values.items():
            setattr(self, key, value)
        return True


class ModelBase(object):
    def write(self, values):
        self.writes.append(dict(values))
        self.__dict__.update(values)
        return True


def load_model():
    odoo = types.ModuleType("odoo")
    odoo.SUPERUSER_ID = 1
    odoo.api = types.SimpleNamespace(Environment=Mock())
    odoo.fields = types.SimpleNamespace(
        Boolean=lambda *a, **k: None, Char=lambda *a, **k: None,
        Datetime=type("Datetime", (), {"now": staticmethod(lambda: "now")}),
        Many2one=lambda *a, **k: None, Selection=lambda *a, **k: None,
        Text=lambda *a, **k: None)
    odoo.models = types.SimpleNamespace(Model=ModelBase)
    tools = types.ModuleType("odoo.tools")
    tools.date_utils = types.SimpleNamespace(json_default=lambda value: str(value))
    package = types.ModuleType("amr_data_sync")
    package.__path__ = [str(ADDON)]
    models_package = types.ModuleType("amr_data_sync.models")
    models_package.__path__ = [str(ADDON / "models")]
    tool_package = types.ModuleType("amr_data_sync.tools")
    tool_package.__path__ = [str(ADDON / "tools")]
    utils = types.ModuleType("amr_data_sync.tools.utils")
    utils.is_callable_method = lambda model, name: callable(getattr(model, name, None))
    names = ("odoo", "odoo.tools", "amr_data_sync", "amr_data_sync.models",
             "amr_data_sync.tools", "amr_data_sync.tools.utils",
             "amr_data_sync.models.data_sync_related")
    previous = {name: sys.modules.get(name) for name in names}
    sys.modules.update({"odoo": odoo, "odoo.tools": tools, "amr_data_sync": package,
                        "amr_data_sync.models": models_package,
                        "amr_data_sync.tools": tool_package,
                        "amr_data_sync.tools.utils": utils})
    try:
        name = "amr_data_sync.models.data_sync_related"
        spec = importlib.util.spec_from_file_location(name, ADDON / "models" / "data_sync_related.py")
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        return module.ExternalDataSyncRelated
    finally:
        for name, old in previous.items():
            if old is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = old


class RelatedDeep11Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model_class = load_model()

    def model(self, **values):
        result = self.model_class()
        result.__dict__.update(values)
        return result

    def test_parent_resolution_uses_existing_link_internal_id(self):
        linked = Record(internal_odoo_id=73, state="done", process_data=Mock())
        related = self.model(
            data_json='{"id": 8}', field_type="parent", state="draft",
            field_after_create=False, related_external_data_sync_id=linked,
            sync_strategy_id=Record(internal_id_same_as_external=False),
            env=types.SimpleNamespace(context={}, cr=None), writes=[])

        related.process_data()

        linked.process_data.assert_not_called()
        self.assertEqual(related.writes, [{"state": "need_resolve", "internal_data_eval": "73"}])

    def test_existing_relation_uses_internal_id(self):
        linked = Record(internal_odoo_id=91, state="done")
        external_sync = Record(state="done", internal_odoo_id=91)
        related = self.model(
            data_json='{"id": 12, "display_name": "A"}', field_type="many2one",
            state="draft", related_external_data_sync_id=external_sync,
            internal_data_eval=None, writes=[],
            sync_strategy_id=Record(internal_id_same_as_external=False))

        related.process_data()

        self.assertIs(related.related_external_data_sync_id, external_sync)
        self.assertEqual(related.internal_data_eval, "91")
        self.assertEqual(related.state, "need_resolve")

    def test_internal_lookup_uses_model_fallback_when_lookup_table_misses(self):
        fallback = Mock(return_value=Record(id=18))
        model = Record(lookup_internal_from_external_data=fallback)
        model.sudo = Mock(return_value=model)
        lookup = Record(lookup_internal=Mock(return_value=False))
        related = self.model(env={"external.data.lookup": lookup, "res.partner": model},
                             internal_model="res.partner", external_app_name="crm",
                             related_external_data_sync_id=Record(sync_strategy_id="strategy"))

        result = related.internal_lookup([4, "Ada"])

        self.assertEqual(result.id, 18)
        lookup.lookup_internal.assert_called_once_with(
            "crm", "res.partner", "res.partner", external_id=4, display_name="Ada")
        model.sudo.assert_called_once_with()
        fallback.assert_called_once_with([4, "Ada"], sync_strategy="strategy")

    def test_internal_lookup_returns_none_without_fallback_method(self):
        model = Record(sudo=Mock(return_value=Record()))
        related = self.model(env={"external.data.lookup": Record(
            lookup_internal=Mock(return_value=False)), "res.partner": model},
            internal_model="res.partner", external_app_name="crm",
            related_external_data_sync_id=False)

        self.assertIsNone(related.internal_lookup(27))

    def test_many2many_resolution_records_ids_and_unresolved_state(self):
        strategy = Record(internal_id_same_as_external=False,
                          get_or_create_relation_from_external=Mock(return_value=[
                              Record(internal_odoo_id=20, state="done"),
                              Record(internal_odoo_id=21, state="process")]))
        related = self.model(data_json='[{"id": 1}, {"id": 2}]',
                             field_type="many2many", sync_strategy_id=strategy,
                             writes=[], state="draft")

        related.process_data()

        self.assertEqual(related.writes, [{"state": "need_resolve", "internal_data_eval": "[20, 21]"}])
        strategy.get_or_create_relation_from_external.assert_called_once_with(
            [{"id": 1}, {"id": 2}], related)

    def test_many2many_resolution_with_missing_internal_id_clears_evaluation(self):
        strategy = Record(internal_id_same_as_external=False,
                          get_or_create_relation_from_external=Mock(return_value=[
                              Record(internal_odoo_id=20, state="done"),
                              Record(internal_odoo_id=False, state="process")]))
        related = self.model(data_json='[1, 2]', field_type="one2many",
                             sync_strategy_id=strategy, writes=[], state="draft")

        related.process_data()

        self.assertEqual(related.writes, [{"state": "process", "internal_data_eval": None}])

    def test_invalid_relation_json_sets_error_and_reraises(self):
        related = self.model(data_json="not-json", field_type="many2one",
                             sync_strategy_id=Record(internal_id_same_as_external=False),
                             write_error_safe=Mock())

        with self.assertRaises(ValueError):
            related.process_data()

        related.write_error_safe.assert_called_once_with(
            {"state": "error", "internal_data_eval": None})


if __name__ == "__main__":
    unittest.main()
