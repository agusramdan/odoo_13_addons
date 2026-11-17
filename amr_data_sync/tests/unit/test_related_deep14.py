"""Offline behavioral tests for relation resolution and cron synchronization."""
import datetime
import importlib.util
import pathlib
import sys
import types
import unittest
from unittest.mock import Mock

ADDON = pathlib.Path(__file__).resolve().parents[2]


class ModelBase(object):
    def write(self, values):
        self.writes.append(dict(values))
        self.__dict__.update(values)
        return True


def load_module(filename, name):
    odoo = types.ModuleType("odoo")
    odoo.SUPERUSER_ID = 1
    odoo.api = types.SimpleNamespace(
        Environment=Mock(), model=lambda fn: fn,
        model_create_multi=lambda fn: fn,
        returns=lambda *a, **k: (lambda fn: fn))
    fixed_now = datetime.datetime(2024, 1, 1, 12, 0)
    odoo.fields = types.SimpleNamespace(
        Boolean=lambda *a, **k: None, Char=lambda *a, **k: None,
        Datetime=type("Datetime", (), {"now": staticmethod(lambda: fixed_now)}),
        Many2one=lambda *a, **k: None, Selection=lambda *a, **k: None,
        Text=lambda *a, **k: None)
    odoo.models = types.SimpleNamespace(Model=ModelBase)
    tools = types.ModuleType("odoo.tools")
    tools.date_utils = types.SimpleNamespace(json_default=lambda value: str(value))
    package = types.ModuleType("amr_data_sync")
    package.__path__ = [str(ADDON)]
    models = types.ModuleType("amr_data_sync.models")
    models.__path__ = [str(ADDON / "models")]
    utility_package = types.ModuleType("amr_data_sync.tools")
    utility_package.__path__ = [str(ADDON / "tools")]
    utils = types.ModuleType("amr_data_sync.tools.utils")
    utils.is_callable_method = lambda model, method: callable(getattr(model, method, None))
    modules = {"odoo": odoo, "odoo.tools": tools, "amr_data_sync": package,
               "amr_data_sync.models": models, "amr_data_sync.tools": utility_package,
               "amr_data_sync.tools.utils": utils}
    names = tuple(modules) + (name,)
    previous = {key: sys.modules.get(key) for key in names}
    sys.modules.update(modules)
    try:
        spec = importlib.util.spec_from_file_location(name, ADDON / "models" / filename)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        return module
    finally:
        for key, old in previous.items():
            if old is None:
                sys.modules.pop(key, None)
            else:
                sys.modules[key] = old


class RelatedDeep14Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.related_class = load_module(
            "data_sync_related.py", "amr_data_sync.models.data_sync_related").ExternalDataSyncRelated

    def model(self, **values):
        instance = self.related_class()
        instance.__dict__.update(values)
        return instance

    def test_internal_lookup_fallback_uses_sudo_and_strategy_when_lookup_misses(self):
        result = types.SimpleNamespace(id=74)
        lookup = types.SimpleNamespace(lookup_internal=Mock(return_value=False))
        strategy = object()
        resolver = types.SimpleNamespace(lookup_internal_from_external_data=Mock(return_value=result))
        elevated = types.SimpleNamespace(lookup_internal_from_external_data=resolver.lookup_internal_from_external_data)
        resolver.sudo = Mock(return_value=elevated)
        related_sync = types.SimpleNamespace(sync_strategy_id=strategy)
        relation = self.model(
            env={"external.data.lookup": lookup, "res.partner": resolver},
            internal_model="res.partner", external_app_name="erp",
            related_external_data_sync_id=related_sync)

        found = relation.internal_lookup({"id": 12, "display_name": "Twelve"})

        self.assertIs(found, result)
        lookup.lookup_internal.assert_called_once_with(
            "erp", "res.partner", "res.partner", external_id=12, display_name="Twelve")
        resolver.sudo.assert_called_once_with()
        resolver.lookup_internal_from_external_data.assert_called_once_with(
            {"id": 12, "display_name": "Twelve"}, sync_strategy=strategy)

    def test_internal_lookup_returns_none_when_fallback_method_is_not_callable(self):
        lookup = types.SimpleNamespace(lookup_internal=Mock(return_value=None))
        resolver = types.SimpleNamespace(sudo=Mock(return_value=object()))
        relation = self.model(env={"external.data.lookup": lookup, "res.partner": resolver},
                              internal_model="res.partner", external_app_name="erp")

        self.assertIsNone(relation.internal_lookup([5, "Five"]))
        resolver.sudo.assert_called_once_with()
        lookup.lookup_internal.assert_called_once_with(
            "erp", "res.partner", "res.partner", external_id=5, display_name="Five")

    def test_create_or_get_related_uses_many2one_factory_for_different_model(self):
        strategy = type("Strategy", (), {"__int__": lambda self: 11})()
        strategy.id = 11
        strategy.internal_model = "res.user"
        parent = type("Parent", (), {"__int__": lambda self: 3})()
        parent.id = 3
        parent.internal_model = "res.partner"
        relation_model = self.model(search=Mock(return_value=False),
                                    create_many2one=Mock(return_value="created relation"))

        result = relation_model.create_or_get_related(
            parent, "owner_id", "many2one", related_external_data_sync_id=strategy,
            internal_model="res.user", value={"id": 8})

        self.assertEqual(result, "created relation")
        relation_model.create_many2one.assert_called_once_with(
            "owner_id", parent, {"id": 8}, strategy)
        relation_model.search.assert_called_once_with(
            [("external_data_sync_id", "=", 3), ("name", "=", "owner_id")], limit=1)

    def test_process_data_resolves_all_integer_many2many_ids_and_state(self):
        strategy = types.SimpleNamespace(
            internal_id_same_as_external=False,
            get_or_create_relation_from_external=Mock(return_value=[
                types.SimpleNamespace(internal_odoo_id=4, state="done"),
                types.SimpleNamespace(internal_odoo_id=9, state="done")]))
        relation = self.model(data_json='["a", "b"]', field_type="many2many",
                              sync_strategy_id=strategy, writes=[])

        relation.process_data()

        self.assertEqual(relation.writes, [{"state": "done", "internal_data_eval": "[4, 9]"}])
        strategy.get_or_create_relation_from_external.assert_called_once_with(["a", "b"], relation)


class CronDeep14Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cron_class = load_module(
            "data_sync_cron.py", "amr_data_sync.models.data_sync_cron").ExternalDataSyncCron

    def test_write_active_propagates_to_strategy_only_when_not_cron_originated(self):
        strategy = types.SimpleNamespace(sync_cron=False, write=Mock())
        record = types.SimpleNamespace(active=True, sync_strategy_id=strategy)
        cron_class = self.cron_class
        recordset = cron_class()
        recordset._context = {}
        recordset.writes = []
        recordset.with_context = Mock(return_value=[record])

        self.assertTrue(recordset.write({"active": True}))
        self.assertEqual(recordset.writes, [{"active": True}])

        strategy.write.reset_mock()
        recordset._context = {"__from_sync_cron": True}
        self.assertTrue(recordset.write({"active": False}))
        strategy.write.assert_not_called()
        self.assertEqual(recordset.with_context.call_count, 1)

    def test_action_sync_now_delegates_to_strategy(self):
        strategy = types.SimpleNamespace(action_sync_now=Mock())
        recordset = self.cron_class()
        recordset.sync_strategy_id = strategy

        recordset.action_sync_now()

        strategy.action_sync_now.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
