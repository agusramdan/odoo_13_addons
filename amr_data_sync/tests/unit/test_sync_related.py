"""Offline behavior tests for the actual ExternalDataSyncRelated model methods."""
import importlib.util
import json
import pathlib
import sys
import types
import unittest
from unittest.mock import Mock

ADDON = pathlib.Path(__file__).resolve().parents[2]


class FakeRecordset(object):
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


class FakeModelBase(object):
    def write(self, values):
        self.writes.append(dict(values))
        for key, value in values.items():
            setattr(self, key, value)
        return True


def load_model():
    """Load the production file with only its Odoo boundary stubbed."""
    odoo = types.ModuleType("odoo")
    odoo.SUPERUSER_ID = 1
    odoo.api = types.SimpleNamespace(Environment=Mock())
    odoo.fields = types.SimpleNamespace(
        Boolean=lambda *a, **k: None, Char=lambda *a, **k: None,
        Datetime=lambda *a, **k: None,
        Many2one=lambda *a, **k: None, Selection=lambda *a, **k: None,
        Text=lambda *a, **k: None)
    odoo.models = types.SimpleNamespace(Model=FakeModelBase)
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
    previous = dict((name, sys.modules.get(name)) for name in names)
    sys.modules.update({"odoo": odoo, "odoo.tools": tools,
                        "amr_data_sync": package, "amr_data_sync.models": models_package,
                        "amr_data_sync.tools": tool_package,
                        "amr_data_sync.tools.utils": utils})
    try:
        module_name = "amr_data_sync.models.data_sync_related"
        spec = importlib.util.spec_from_file_location(
            module_name, ADDON / "models" / "data_sync_related.py")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module.ExternalDataSyncRelated
    finally:
        for name, old in previous.items():
            if old is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = old


class SyncRelatedUnitTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model_class = load_model()

    def model(self, **values):
        instance = self.model_class()
        for name, value in values.items():
            setattr(instance, name, value)
        return instance

    def test_process_data_maps_parent_id_with_configured_offset(self):
        related = self.model(data_json='{"id": 12}', field_type="parent",
                             sync_strategy_id=FakeRecordset(
                                 internal_id_same_as_external=True, internal_id_offset=100),
                             state="draft")

        related.process_data()

        self.assertEqual(related.internal_data_eval, "112")
        self.assertEqual(related.state, "done")

    def test_process_data_maps_many2many_ids_and_offset(self):
        related = self.model(data_json="[1, 4]", field_type="many2many",
                             sync_strategy_id=FakeRecordset(
                                 internal_id_same_as_external=True, internal_id_offset=5),
                             state="draft")

        related.process_data()

        self.assertEqual(related.internal_data_eval, "[6, 9]")
        self.assertEqual(related.state, "done")

    def test_process_data_resolves_relation_ids_and_need_resolve_state(self):
        linked = FakeRecordset(internal_odoo_id=53, state="process")
        related = self.model(data_json='{"id": 9}', field_type="many2one",
                             sync_strategy_id=FakeRecordset(internal_id_same_as_external=False),
                             related_external_data_sync_id=linked, state="draft",
                             env=types.SimpleNamespace(context={}),
                             writes=[])

        related.process_data()

        self.assertEqual(related.writes, [{"state": "need_resolve", "internal_data_eval": "53"}])

    def test_process_data_records_failure_then_reraises(self):
        related = self.model(data_json="not json", field_type="many2one",
                             write_error_safe=Mock())

        with self.assertRaises(ValueError):
            related.process_data()

        related.write_error_safe.assert_called_once_with(
            {"state": "error", "internal_data_eval": None})

    def test_create_or_get_related_updates_existing_record(self):
        existing = FakeRecordset(writes=[])
        related = self.model(search=Mock(return_value=existing))
        parent = FakeRecordset(id=8, internal_model="res.partner")
        strategy = FakeRecordset(id=4, internal_model="res.partner")

        result = related.create_or_get_related(
            parent, "partner_ids", "one2many", inverse_field="parent_id",
            related_sync_strategy_id=strategy, value=[1, 2])

        self.assertIs(result, existing)
        self.assertEqual(existing.writes, [{
            "field_after_create": True, "field_type": "one2many",
            "sync_strategy_id": (4,), "internal_model": "res.partner",
            "inverse_field": "parent_id", "data_json": "[1, 2]"}])
        self.assertEqual(related.search.call_args[0][0], [
            ("external_data_sync_id", "=", 8), ("name", "=", "partner_ids")])

    def test_get_data_relation_returns_literal_value_only_when_done(self):
        ready = self.model(state="done", field_type="many2many", internal_data_eval="[3, 7]")
        pending = self.model(state="process", field_type="many2many", internal_data_eval="[3, 7]",
                             try_process_data=Mock())

        self.assertEqual(ready.get_data_relation(), [3, 7])
        self.assertIsNone(pending.get_data_relation())
        pending.try_process_data.assert_called_once_with()

    def test_recursion_context_prevents_processing(self):
        related = self.model(env=types.SimpleNamespace(context={"__try_process_relation": True}),
                             process_data=Mock())
        related.with_context = Mock(return_value=related)

        related.try_process_data()

        related.process_data.assert_not_called()
        related.with_context.assert_not_called()


if __name__ == "__main__":
    unittest.main()
