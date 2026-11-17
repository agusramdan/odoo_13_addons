"""Behavior-focused coverage for related conversion and cron retry paths."""
import datetime
import importlib.util
import pathlib
import sys
import types
import unittest
from unittest.mock import Mock

ADDON = pathlib.Path(__file__).resolve().parents[2]


class BaseModel(object):
    def write(self, values):
        self.writes.append(dict(values))
        self.__dict__.update(values)
        return True


def load_production(path, module_name, extra=None):
    odoo = types.ModuleType("odoo")
    odoo.SUPERUSER_ID = 1
    odoo.api = types.SimpleNamespace(
        Environment=Mock(), model=lambda fn: fn,
        model_create_multi=lambda fn: fn,
        returns=lambda *a, **k: (lambda fn: fn))
    now = datetime.datetime(2024, 1, 1, 12, 0)
    odoo.fields = types.SimpleNamespace(
        Boolean=lambda *a, **k: None, Char=lambda *a, **k: None,
        Datetime=type("Datetime", (), {"now": staticmethod(lambda: now)}),
        Many2one=lambda *a, **k: None, Selection=lambda *a, **k: None,
        Text=lambda *a, **k: None)
    odoo.models = types.SimpleNamespace(Model=BaseModel)
    tools = types.ModuleType("odoo.tools")
    tools.date_utils = types.SimpleNamespace(json_default=lambda value: str(value))
    package = types.ModuleType("amr_data_sync")
    package.__path__ = [str(ADDON)]
    models = types.ModuleType("amr_data_sync.models")
    models.__path__ = [str(ADDON / "models")]
    tool_package = types.ModuleType("amr_data_sync.tools")
    tool_package.__path__ = [str(ADDON / "tools")]
    utils = types.ModuleType("amr_data_sync.tools.utils")
    utils.is_callable_method = lambda model, name: callable(getattr(model, name, None))
    modules = {"odoo": odoo, "odoo.tools": tools, "amr_data_sync": package,
               "amr_data_sync.models": models, "amr_data_sync.tools": tool_package,
               "amr_data_sync.tools.utils": utils}
    if extra:
        modules.update(extra)
    names = tuple(modules) + (module_name,)
    previous = dict((name, sys.modules.get(name)) for name in names)
    sys.modules.update(modules)
    try:
        spec = importlib.util.spec_from_file_location(module_name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module
    finally:
        for name, old in previous.items():
            if old is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = old


def load_related():
    return load_production(ADDON / "models" / "data_sync_related.py",
                           "amr_data_sync.models.data_sync_related").ExternalDataSyncRelated


def load_cron():
    return load_production(ADDON / "models" / "data_sync_cron.py",
                           "amr_data_sync.models.data_sync_cron").ExternalDataSyncCron


class RelatedDeep13Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model_class = load_related()

    def make(self, **values):
        model = self.model_class()
        model.__dict__.update(values)
        return model

    def test_all_relation_collects_only_truthy_values_under_recursion_context(self):
        done = self.make(name="done", get_data_relation=Mock(return_value=[4, 8]))
        empty = self.make(name="empty", get_data_relation=Mock(return_value=None))
        source = self.make(env=types.SimpleNamespace(context={}),
                           with_context=Mock(return_value=[done, empty]))

        self.assertEqual(source.get_All_data_relation(), {"done": [4, 8]})
        source.with_context.assert_called_once_with(__try_process_relation=True)
        done.get_data_relation.assert_called_once_with()
        empty.get_data_relation.assert_called_once_with()

    def test_many2many_partial_resolution_preserves_retry_state_without_partial_ids(self):
        resolved = types.SimpleNamespace(internal_odoo_id=17, state="done")
        unresolved = types.SimpleNamespace(internal_odoo_id=False, state="process")
        strategy = types.SimpleNamespace(
            internal_id_same_as_external=False,
            get_or_create_relation_from_external=Mock(return_value=[resolved, unresolved]))
        relation = self.make(data_json='["a", "b"]', field_type="many2many",
                             sync_strategy_id=strategy, writes=[])

        relation.process_data()

        self.assertEqual(relation.writes, [{"state": "process", "internal_data_eval": None}])
        strategy.get_or_create_relation_from_external.assert_called_once_with(["a", "b"], relation)

    def test_write_error_safe_uses_savepoint_and_persists_error_fields(self):
        class Savepoint(object):
            def __init__(self):
                self.entered = False
                self.exited = False
            def __enter__(self):
                self.entered = True
            def __exit__(self, *args):
                self.exited = True
                return False
        savepoint = Savepoint()
        relation = self.make(env=types.SimpleNamespace(cr=types.SimpleNamespace(
            savepoint=lambda: savepoint)), writes=[])

        relation.write_error_safe({"state": "error", "internal_data_eval": None})

        self.assertEqual(relation.writes, [{"state": "error", "internal_data_eval": None}])
        self.assertTrue(savepoint.entered)
        self.assertTrue(savepoint.exited)


class CronDeep13Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model_class = load_cron()

    def make(self, **values):
        model = self.model_class()
        model.__dict__.update(values)
        return model

    def test_sync_failure_still_records_attempt_and_one_hour_retry(self):
        strategy = types.SimpleNamespace(
            sync_from_application_server=Mock(side_effect=RuntimeError("temporary")),
            is_delete_able_from_external=Mock(return_value=False))
        sync = self.make(sync_strategy_id=strategy, external_app_name="erp",
                         external_model="res.partner", writes=[], _context={})
        sync.write = lambda values: (sync.writes.append(dict(values)), sync.__dict__.update(values), True)[-1]
        runner_class = type("CronRecordset", (self.model_class,), {
            "__iter__": lambda self: iter([sync]), "__bool__": lambda self: True})
        runner = runner_class()
        runner.env = types.SimpleNamespace(context={}, cr=Mock())

        runner.cron_sync_from_server()

        self.assertEqual(sync.writes, [{
            "last_sync_datetime": datetime.datetime(2024, 1, 1, 12, 0),
            "next_sync_datetime": datetime.datetime(2024, 1, 1, 13, 0)}])
        strategy.sync_from_application_server.assert_called_once_with()
        strategy.is_delete_able_from_external.assert_called_once_with()

    def test_delete_validation_exception_is_retried_and_does_not_abort_cron(self):
        strategy = types.SimpleNamespace(
            sync_from_application_server=Mock(), is_delete_able_from_external=Mock(return_value=True), id=9)
        sync = self.make(sync_strategy_id=strategy, external_app_name="erp",
                         external_model="res.partner", writes=[], _context={})
        sync.write = lambda values: (sync.writes.append(dict(values)), sync.__dict__.update(values), True)[-1]
        bad = self.make(validate_json_data_for_delete=Mock(side_effect=ValueError("bad payload")),
                        external_model="res.partner", writes=[])
        good = self.make(validate_json_data_for_delete=Mock(return_value=True),
                         external_model="res.partner", writes=[])
        bad.write = lambda values: (bad.writes.append(dict(values)), bad.__dict__.update(values), True)[-1]
        good.write = lambda values: (good.writes.append(dict(values)), good.__dict__.update(values), True)[-1]
        search = Mock(return_value=[bad, good])
        env = type("FakeEnvironment", (dict,), {})({
            "external.data.sync": types.SimpleNamespace(search=search)})
        class Savepoint(object):
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False
        runner_class = type("CronRecordset", (self.model_class,), {
            "__iter__": lambda self: iter([sync]), "__bool__": lambda self: True})
        runner = runner_class()
        runner.env = env
        runner.env.cr = types.SimpleNamespace(savepoint=lambda: Savepoint())

        runner.cron_sync_from_server()

        search.assert_called_once_with([
            ("state", "=", "done"), ("external_deleted", "=", False),
            ("external_archived", "=", False), ("sync_strategy_id", "=", 9)],
            limit=1000, order="next_processing_datetime")
        self.assertEqual(bad.writes, [{
            "last_processing_datetime": datetime.datetime(2024, 1, 1, 12, 0),
            "next_processing_datetime": datetime.datetime(2024, 1, 1, 13, 0)}])
        self.assertEqual(good.writes, [])
        good.validate_json_data_for_delete.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
