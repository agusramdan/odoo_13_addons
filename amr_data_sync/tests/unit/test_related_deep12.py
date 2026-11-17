"""Behavioral coverage for less-traveled related-data synchronization paths."""
import datetime
import importlib.util
import json
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
        self.__dict__.update(values)
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
        Datetime=type("Datetime", (), {
            "now": staticmethod(lambda: datetime.datetime(2024, 1, 1, 12, 0))}),
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
        spec = importlib.util.spec_from_file_location(
            name, ADDON / "models" / "data_sync_related.py")
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


class RelatedDeep12Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model_class = load_model()

    def model(self, **values):
        result = self.model_class()
        result.__dict__.update(values)
        return result

    def test_create_factories_preserve_parent_and_strategy_metadata(self):
        created = []
        model = self.model(create=lambda vals: created.append(vals) or vals)
        strategy = Record(id=6, internal_model="res.partner")
        sync = Record(id=17, sync_strategy_id=strategy)

        parent = model.create_parent("parent_id", sync, {"id": 3})
        many2one = model.create_many2one("owner_id", sync, [4, "Ada"], strategy)
        many2many = model.create_many2many("member_ids", sync, [1, 2], strategy)

        self.assertEqual(parent["field_type"], "parent")
        self.assertEqual(parent["sync_strategy_id"], 6)
        self.assertEqual(parent["internal_model"], "res.partner")
        self.assertEqual(json.loads(parent["data_json"]), {"id": 3})
        self.assertEqual(many2one["field_type"], "many2one")
        self.assertEqual(many2one["external_data_sync_id"], 17)
        self.assertEqual(json.loads(many2one["data_json"]), [4, "Ada"])
        self.assertEqual(many2many["field_type"], "many2many")
        self.assertNotIn("internal_model", many2many)
        self.assertEqual(json.loads(many2many["data_json"]), [1, 2])
        self.assertEqual(len(created), 3)

    def test_create_or_get_required_field_overrides_deferred_create(self):
        created = []
        model = self.model(search=Mock(return_value=False),
                           create=Mock(side_effect=lambda vals: created.append(vals) or ["new"]))
        parent = Record(id=31, internal_model="res.partner")
        strategy = Record(id=5, internal_model="res.user")

        result = model.create_or_get_related(
            parent, "partner_id", "many2one", field_required=True,
            inverse_field="company_id", related_sync_strategy_id=strategy,
            value={"id": 7})

        self.assertEqual(result, "new")
        values = created[0][0]
        self.assertEqual(values["state"], "draft")
        self.assertTrue(values["mandatory_before_create"])
        self.assertFalse(values["field_after_create"])
        self.assertEqual(values["inverse_field"], "company_id")
        self.assertEqual(json.loads(values["data_json"]), {"id": 7})
        model.search.assert_called_once_with(
            [("external_data_sync_id", "=", 31), ("name", "=", "partner_id")], limit=1)

    def test_create_or_get_selects_parent_factory_for_same_internal_model(self):
        model = self.model(search=Mock(return_value=False), create_parent=Mock(return_value="parent"))
        parent = Record(id=9, internal_model="res.partner")

        result = model.create_or_get_related(
            parent, "parent_id", "many2one", related_external_data_sync_id=88,
            internal_model="res.partner", value={"id": 2})

        self.assertEqual(result, "parent")
        model.create_parent.assert_called_once_with("parent_id", parent, {"id": 2})

    def test_create_or_get_updates_existing_and_encodes_datetime_value(self):
        existing = Record(writes=[])
        model = self.model(search=Mock(return_value=existing))
        strategy = Record(id=3, internal_model="res.partner")
        value = datetime.date(2024, 1, 2)

        self.assertIs(model.create_or_get_related(
            Record(id=12, internal_model="res.partner"), "members", "many2many",
            related_sync_strategy_id=strategy, value=value), existing)
        written = existing.writes[0]
        self.assertEqual(written["data_json"], '"2024-01-02"')
        self.assertEqual(written["sync_strategy_id"], (3,))
        self.assertTrue(written["field_after_create"])

    def test_lookup_dict_and_integer_extract_expected_lookup_keys(self):
        lookup = Record(lookup_internal=Mock(return_value=Record(id=41)))
        model = self.model(env={"external.data.lookup": lookup}, internal_model="res.partner",
                           external_app_name="crm")

        self.assertEqual(model.internal_lookup({"id": 7, "display_name": "Seven"}).id, 41)
        lookup.lookup_internal.assert_called_once_with(
            "crm", "res.partner", "res.partner", external_id=7, display_name="Seven")
        lookup.lookup_internal.reset_mock()
        model.internal_lookup(9)
        lookup.lookup_internal.assert_called_once_with(
            "crm", "res.partner", "res.partner", external_id=9, display_name=None)

    def test_direct_internal_lookup_result_does_not_call_model_fallback(self):
        result = Record(id=52)
        lookup = Record(lookup_internal=Mock(return_value=result))
        model_record = Record(sudo=Mock())
        related = self.model(env={"external.data.lookup": lookup, "res.partner": model_record},
                             internal_model="res.partner", external_app_name="erp")

        self.assertIs(related.internal_lookup([2, "Two"]), result)
        model_record.sudo.assert_not_called()

    def test_get_data_relation_prefers_related_many2one_internal_id(self):
        related = self.model(state="done", field_type="many2one", internal_data_eval="99",
                             related_external_data_sync_id=Record(internal_odoo_id=24))
        self.assertEqual(related.get_data_relation(), 24)
        related.related_external_data_sync_id.internal_odoo_id = False
        self.assertIsNone(related.get_data_relation())

    def test_get_all_data_relation_respects_recursion_guard(self):
        relation = self.model(env=types.SimpleNamespace(context={"__try_process_relation": True}),
                              with_context=Mock(), name="x")
        self.assertIsNone(relation.get_All_data_relation())
        relation.with_context.assert_not_called()

    def test_dispatch_sets_processing_state_and_runs_only_when_immediate(self):
        relation = self.model(writes=[], process_with_handel_error=Mock())
        relation.dispatch_process()
        self.assertEqual(relation.writes, [{"state": "process"}])
        relation.process_with_handel_error.assert_not_called()

        relation.dispatch_process(run_immediate=True)
        self.assertEqual(relation.writes[-1], {"state": "process"})
        relation.process_with_handel_error.assert_called_once_with()

    def test_process_error_handler_records_traceback_and_retry_time(self):
        savepoint = Mock()
        class Savepoint(object):
            def __enter__(self):
                return self
            def __exit__(self, exc_type, exc, tb):
                return False
        savepoint.return_value = Savepoint()
        relation = self.model(env=types.SimpleNamespace(cr=Record(savepoint=savepoint)),
                              process_data=Mock(side_effect=RuntimeError("failure")),
                              write_error_safe=Mock())

        relation.process_with_handel_error()

        error = relation.write_error_safe.call_args[0][0]
        self.assertEqual(error["state"], "error")
        self.assertIn("RuntimeError: failure", error["error_info"])
        self.assertEqual(error["last_error"], datetime.datetime(2024, 1, 1, 12, 0))
        self.assertEqual(error["next_processing_datetime"], datetime.datetime(2024, 1, 1, 13, 0))
        savepoint.assert_called_once_with()

    def test_create_or_get_related_parent_defaults_without_strategy(self):
        created = []
        model = self.model(search=Mock(return_value=False),
                           create=Mock(side_effect=lambda vals: created.append(vals) or ["created"]))
        parent = Record(id=6, internal_model="res.company")

        model.create_or_get_related(parent, "children", "one2many", inverse_field="company_id",
                                    internal_model="res.partner")

        values = created[0][0]
        self.assertTrue(values["field_after_create"])
        self.assertEqual(values["internal_model"], "res.partner")
        self.assertEqual(values["inverse_field"], "company_id")
        self.assertFalse(values["mandatory_before_create"] if "mandatory_before_create" in values else False)


if __name__ == "__main__":
    unittest.main()
