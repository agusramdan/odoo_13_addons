"""Behavior-focused offline tests for real ExternalDataSync methods.

The production model class is imported from its source; deliberately small
recordset/ORM boundary doubles model only the contracts these paths use.
"""
import importlib.util
import json
import pathlib
import sys
import types
import unittest
from unittest.mock import Mock

ADDON = pathlib.Path(__file__).resolve().parents[2]


class FakeBaseModel(object):
    def create(self, values):
        return values

    def write(self, values):
        return values


class Record(object):
    def __init__(self, **values):
        self.__dict__.update(values)
        self.writes = []

    def __bool__(self):
        return True
    __nonzero__ = __bool__

    def write(self, values):
        self.writes.append(dict(values))
        self.__dict__.update(values)
        return True

    def reset_related(self):
        self.reset_count = getattr(self, 'reset_count', 0) + 1


class Records(object):
    def __init__(self, rows=()):
        self.rows = list(rows)

    def __bool__(self):
        return bool(self.rows)
    __nonzero__ = __bool__

    def __getitem__(self, index):
        return self.rows[index]

    def __iter__(self):
        return iter(self.rows)

    def __getattr__(self, name):
        if len(self.rows) == 1:
            return getattr(self.rows[0], name)
        raise AttributeError(name)


class Search(object):
    def __init__(self, result=None):
        self.result = result or Records()
        self.calls = []

    def __call__(self, domain, limit=None):
        self.calls.append((domain, limit))
        return self.result


def load_sync_class():
    odoo = types.ModuleType('odoo')
    odoo.SUPERUSER_ID = 1
    odoo._ = lambda text: text
    odoo.api = types.SimpleNamespace(model=lambda fn: fn)

    def datetime_field(**kwargs):
        return None
    datetime_field.now = lambda: 'now'
    datetime_field.to_datetime = lambda value: 'parsed:' + value
    odoo.fields = types.SimpleNamespace(
        Boolean=lambda **kwargs: None, Char=lambda **kwargs: None,
        Datetime=datetime_field, Integer=lambda **kwargs: None,
        Many2one=lambda *args, **kwargs: None,
        One2many=lambda *args, **kwargs: None,
        Selection=lambda *args, **kwargs: None, Text=lambda **kwargs: None)
    odoo.models = types.SimpleNamespace(Model=FakeBaseModel, BaseModel=FakeBaseModel)
    exceptions = types.ModuleType('odoo.exceptions')
    class UserError(Exception):
        pass
    exceptions.UserError = UserError
    tools = types.ModuleType('odoo.tools')
    tools.date_utils = types.SimpleNamespace(json_default=lambda value: str(value))
    addon = types.ModuleType('amr_data_sync')
    addon.__path__ = [str(ADDON)]
    models_package = types.ModuleType('amr_data_sync.models')
    models_package.__path__ = [str(ADDON / 'models')]
    tools_package = types.ModuleType('amr_data_sync.tools')
    tools_package.__path__ = [str(ADDON / 'tools')]
    utility = types.ModuleType('amr_data_sync.tools.utils')
    utility.convert_from_external_data = lambda value: value
    utility.insert_data_sql = Mock()
    modules = {'odoo': odoo, 'odoo.exceptions': exceptions, 'odoo.tools': tools,
               'amr_data_sync': addon, 'amr_data_sync.models': models_package,
               'amr_data_sync.tools': tools_package,
               'amr_data_sync.tools.utils': utility}
    names = list(modules) + ['amr_data_sync.models.data_sync']
    prior = {name: sys.modules.get(name) for name in names}
    sys.modules.update(modules)
    try:
        name = 'amr_data_sync.models.data_sync'
        spec = importlib.util.spec_from_file_location(name, ADDON / 'models' / 'data_sync.py')
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        return module.ExternalDataSync
    finally:
        for name, value in prior.items():
            if value is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = value


class DataSyncExtraTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model_class = load_sync_class()

    def test_create_derives_mapping_metadata_and_defaults_state_and_name(self):
        strategy = Record(external_model='remote.item', external_app_name='remote',
                          internal_model='local.item', get_external_application_name=Mock(return_value='app'))
        strategy.get_external_application_name.return_value = 'app'
        model = self.model_class()
        model.env = {'external.data.sync.strategy': types.SimpleNamespace(browse=lambda _id: strategy)}
        values = [{'sync_strategy_id': 14, 'external_odoo_id': 7},
                  {'display_name': 'Named', 'state': 'done'}]
        result = model.create(values)
        self.assertIs(result, values)
        self.assertEqual(values[0], {'sync_strategy_id': 14, 'external_odoo_id': 7,
                                     'external_model': 'remote.item', 'external_app_name': 'app',
                                     'internal_model': 'local.item', 'state': 'draft', 'name': 'ID 7'})
        self.assertEqual(values[1]['state'], 'done')
        self.assertEqual(values[1]['name'], 'Named')

    def test_data_from_external_updates_newer_mapping_and_resets_related(self):
        existing = Record(external_last_update='2026-01-01', internal_odoo_id=8,
                          updateable=True, reset_count=0)
        existing.is_update_able_from_external = lambda: True
        search = Search(Records([existing]))
        model = self.model_class()
        model.search = search
        strategy = Record(id=3)
        result = model.data_from_external({'id': 21, 'display_name': 'Latest',
                                           'write_date': '2026-01-02'}, strategy)
        self.assertIs(result, search.result)
        self.assertEqual(search.calls, [([('external_odoo_id', '=', 21),
                                          ('sync_strategy_id', '=', 3)], 1)])
        self.assertEqual(existing.writes, [{'display_name': 'Latest',
                                            'data_json': '[21, "Latest"]',
                                            'need_get_data_json': True,
                                            'external_last_update': 'parsed:2026-01-02',
                                            'state': 'process'}])
        self.assertEqual(existing.reset_count, 1)

    def test_data_from_external_does_not_overwrite_when_timestamps_equal(self):
        existing = Record(external_last_update='parsed:2026-01-02', internal_odoo_id=8)
        search = Search(Records([existing]))
        model = self.model_class()
        model.search = search
        result = model.data_from_external({'id': 21, 'display_name': 'Old',
                                           'write_date': '2026-01-02'}, Record(id=3))
        self.assertIs(result, search.result)
        self.assertEqual(existing.writes, [])
        self.assertEqual(getattr(existing, 'reset_count', 0), 0)

    def test_get_json_data_fetches_and_persists_timestamp_inside_savepoint(self):
        events = []
        class Savepoint(object):
            def __enter__(self): events.append('enter')
            def __exit__(self, kind, value, tb): events.append('rollback' if kind else 'commit')
        row = self.model_class()
        row.need_get_data_json = True
        row.get_external_one_data = Mock(return_value={'id': 4, 'write_date': '2026-03-04 05:06:07'})
        row.env = types.SimpleNamespace(cr=types.SimpleNamespace(savepoint=Savepoint))
        row.write = Mock()
        data = row.get_json_data_for_create()
        self.assertEqual(data, {'id': 4, 'write_date': '2026-03-04 05:06:07'})
        row.get_external_one_data.assert_called_once_with()
        row.write.assert_called_once_with({'need_get_data_json': False,
                                           'data_json': json.dumps(data),
                                           'external_last_update': 'parsed:2026-03-04 05:06:07'})
        self.assertEqual(events, ['enter', 'commit'])

    def test_get_json_data_returns_inactive_marker_when_external_item_missing(self):
        row = self.model_class()
        row.need_get_data_json = True
        row.get_external_one_data = Mock(return_value=False)
        row.write = Mock()
        self.assertEqual(row.get_json_data_for_create(), {'active': False})
        row.write.assert_called_once_with({'need_get_data_json': False, 'data_json': 'false'})


if __name__ == '__main__':
    unittest.main()
