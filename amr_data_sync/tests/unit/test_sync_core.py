"""Offline tests of core ExternalDataSync model behavior.

Odoo's registry and recordsets are boundary fakes; production model methods are
loaded directly. These tests do not claim ORM or persistence integration.
"""
import importlib.util
import pathlib
import sys
import types
import unittest
from unittest.mock import Mock


ADDON = pathlib.Path(__file__).resolve().parents[2]


class FakeModelBase(object):
    def create(self, values):
        return values

    def write(self, values):
        return values


class FakeRecordset(object):
    def __init__(self, **values):
        self.__dict__.update(values)

    def __bool__(self):
        return bool(getattr(self, "ids", [True]))

    __nonzero__ = __bool__

    def write(self, values):
        self.writes.append(dict(values))
        for key, value in values.items():
            setattr(self, key, value)
        return True

    def reset_related(self):
        self.reset_count += 1

    def is_update_able_from_external(self):
        return self.updateable


class FakeRecords(object):
    def __init__(self, records=()):
        self.records = list(records)

    def __bool__(self):
        return bool(self.records)

    __nonzero__ = __bool__

    def __getitem__(self, index):
        return self.records[index]

    def __iter__(self):
        return iter(self.records)

    def __getattr__(self, name):
        if len(self.records) == 1:
            return getattr(self.records[0], name)
        raise AttributeError(name)


class FakeSearchModel(object):
    def __init__(self, result=None):
        self.result = result or FakeRecords()
        self.calls = []

    def search(self, domain, limit=None):
        self.calls.append((domain, limit))
        return self.result


def load_sync_model():
    odoo = types.ModuleType("odoo")
    odoo.SUPERUSER_ID = 1
    odoo._ = lambda value: value
    odoo.api = types.SimpleNamespace(model=lambda fn: fn)
    datetime_field = lambda **kwargs: None
    datetime_field.to_datetime = lambda value: "parsed:" + value
    datetime_field.now = lambda: "now"
    odoo.fields = types.SimpleNamespace(
        Boolean=lambda **kwargs: None,
        Char=lambda **kwargs: None,
        Datetime=datetime_field,
        Integer=lambda **kwargs: None,
        Many2one=lambda *args, **kwargs: None,
        One2many=lambda *args, **kwargs: None,
        Selection=lambda *args, **kwargs: None,
        Text=lambda **kwargs: None,
    )
    odoo.models = types.SimpleNamespace(Model=FakeModelBase, BaseModel=FakeModelBase)
    exceptions = types.ModuleType("odoo.exceptions")

    class UserError(Exception):
        pass

    exceptions.UserError = UserError
    tools = types.ModuleType("odoo.tools")
    tools.date_utils = types.SimpleNamespace(json_default=lambda value: str(value))
    addon = types.ModuleType("amr_data_sync")
    addon.__path__ = [str(ADDON)]
    models_package = types.ModuleType("amr_data_sync.models")
    models_package.__path__ = [str(ADDON / "models")]
    tools_package = types.ModuleType("amr_data_sync.tools")
    tools_package.__path__ = [str(ADDON / "tools")]
    utils = types.ModuleType("amr_data_sync.tools.utils")
    utils.convert_from_external_data = lambda value: value
    utils.insert_data_sql = Mock()

    names = ("odoo", "odoo.exceptions", "odoo.tools", "amr_data_sync",
             "amr_data_sync.models", "amr_data_sync.tools",
             "amr_data_sync.tools.utils", "amr_data_sync.models.data_sync")
    previous = dict((name, sys.modules.get(name)) for name in names)
    replacements = {
        "odoo": odoo, "odoo.exceptions": exceptions, "odoo.tools": tools,
        "amr_data_sync": addon, "amr_data_sync.models": models_package,
        "amr_data_sync.tools": tools_package,
        "amr_data_sync.tools.utils": utils,
    }
    sys.modules.update(replacements)
    try:
        name = "amr_data_sync.models.data_sync"
        spec = importlib.util.spec_from_file_location(name, ADDON / "models" / "data_sync.py")
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        return module.ExternalDataSync, utils
    finally:
        for name, old in previous.items():
            if old is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = old


class ExternalDataSyncCoreTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model_class, cls.utils = load_sync_model()

    def model(self, **values):
        instance = self.model_class()
        for name, value in values.items():
            setattr(instance, name, value)
        return instance

    def test_data_from_external_creates_and_maps_new_record(self):
        search = FakeSearchModel()
        created = FakeRecords([FakeRecordset(id=81)])
        strategy = FakeRecordset(id=12, internal_lookup=Mock(return_value=FakeRecordset(id=44)))
        model = self.model(search=search.search, create=Mock(return_value=created))

        result = model.data_from_external(
            {"id": 9, "display_name": "Widget", "write_date": "2026-01-02 03:04:05"},
            strategy, need_get_data_json=False)

        self.assertIs(result, created[0])
        domain, limit = search.calls[0]
        self.assertEqual(domain, [("external_odoo_id", "=", 9), ("sync_strategy_id", "=", 12)])
        self.assertEqual(limit, 1)
        vals = model.create.call_args[0][0][0]
        self.assertEqual(vals["external_odoo_id"], 9)
        self.assertEqual(vals["display_name"], "Widget")
        self.assertEqual(vals["data_json"], '{"id": 9, "display_name": "Widget", "write_date": "2026-01-02 03:04:05"}')
        self.assertNotIn("external_last_update", vals)
        self.assertEqual(vals["internal_odoo_id"], 44)
        self.assertEqual(vals["state"], "done")
        strategy.internal_lookup.assert_called_once_with({
            "id": 9, "display_name": "Widget", "write_date": "2026-01-02 03:04:05"})

    def test_data_from_external_ignores_stale_or_equal_update_for_mapped_record(self):
        existing = FakeRecordset(external_last_update="parsed:2026-01-03", internal_odoo_id=5,
                                 writes=[], reset_count=0, updateable=True)
        search = FakeSearchModel(FakeRecords([existing]))
        model = self.model(search=search.search, create=Mock())
        strategy = FakeRecordset(id=12)

        result = model.data_from_external(
            {"id": 9, "display_name": "Older", "write_date": "2026-01-02"}, strategy)

        self.assertIs(result, search.result)
        self.assertEqual(existing.writes, [])
        self.assertEqual(existing.reset_count, 0)
        model.create.assert_not_called()

    def test_data_from_external_updates_existing_and_resets_related_when_newer(self):
        existing = FakeRecordset(external_last_update="2026-01-01", internal_odoo_id=5,
                                 writes=[], reset_count=0, updateable=True)
        search = FakeSearchModel(FakeRecords([existing]))
        model = self.model(search=search.search)
        strategy = FakeRecordset(id=12)

        result = model.data_from_external(
            {"id": 9, "display_name": "New", "write_date": "2026-01-02"}, strategy)

        self.assertIs(result, search.result)
        self.assertEqual(existing.writes[0]["state"], "process")
        self.assertEqual(existing.writes[0]["display_name"], "New")
        self.assertEqual(existing.writes[0]["external_last_update"], "parsed:2026-01-02")
        self.assertEqual(existing.reset_count, 1)

    def test_get_json_data_for_create_uses_cached_object_and_fetches_when_requested(self):
        cached = self.model(need_get_data_json=False, data_json='{"id": 3}')
        self.assertEqual(cached.get_json_data_for_create(), {"id": 3})

        fetched = self.model(need_get_data_json=True, get_external_one_data=Mock(
            return_value={"id": 4, "write_date": "2026-02-03"}),
            env=types.SimpleNamespace(cr=types.SimpleNamespace(savepoint=lambda: _NullContext())))
        fetched.write = Mock()
        result = fetched.get_json_data_for_create()

        self.assertEqual(result, {"id": 4, "write_date": "2026-02-03"})
        self.assertEqual(fetched.write.call_args[0][0]["need_get_data_json"], False)
        self.assertEqual(fetched.write.call_args[0][0]["external_last_update"], "parsed:2026-02-03")


class _NullContext(object):
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, tb):
        return False


if __name__ == "__main__":
    unittest.main()
