"""Offline unit tests for the real ExternalDataUpdate model methods.

The Odoo registry/recordset boundary is stubbed; production methods are loaded
from models/data_update.py and called directly. This does not test ORM behavior.
"""
import importlib.util
import json
import pathlib
import sys
import types
import unittest
from contextlib import contextmanager
from datetime import datetime


ADDON = pathlib.Path(__file__).resolve().parents[2]


class FakeModel(object):
    pass


class FakeDatetime(object):
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    @staticmethod
    def now():
        return "now"

    @staticmethod
    def to_datetime(value):
        if isinstance(value, datetime):
            return value
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")


def load_update_class():
    odoo = types.ModuleType("odoo")
    odoo.__path__ = []

    class Field(object):
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs

    class API(object):
        @staticmethod
        def model(method):
            return method

    odoo.api = API
    odoo.fields = types.SimpleNamespace(
        Char=Field, Datetime=FakeDatetime, Integer=Field, Many2one=Field,
        Selection=Field, Text=Field)
    odoo.models = types.SimpleNamespace(Model=FakeModel)

    old_odoo = sys.modules.get("odoo")
    sys.modules["odoo"] = odoo
    try:
        name = "amr_data_sync_test_data_update"
        spec = importlib.util.spec_from_file_location(
            name, ADDON / "models" / "data_update.py")
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        return module.ExternalDataUpdate
    finally:
        sys.modules.pop("amr_data_sync_test_data_update", None)
        if old_odoo is None:
            sys.modules.pop("odoo", None)
        else:
            sys.modules["odoo"] = old_odoo


class FakeRecord(object):
    def __init__(self, **values):
        self.__dict__.update(values)
        self.writes = []

    def write(self, values):
        self.writes.append(dict(values))
        self.__dict__.update(values)
        return True

    def dispatch_process(self):
        self.dispatched = True


class FakeCursor(object):
    @contextmanager
    def savepoint(self):
        yield


class FakeRecordset(FakeRecord):
    def __init__(self, **values):
        FakeRecord.__init__(self, **values)
        self.env = types.SimpleNamespace(cr=FakeCursor())

    def ensure_one(self):
        return True


class FakeDataModel(object):
    def __init__(self, result=None):
        self.result = result
        self.domains = []
        self.writes = []

    def search(self, domain):
        self.domains.append(domain)
        return self.result

    def data_from_external(self, item, strategy, **kwargs):
        self.received = (item, strategy, kwargs)
        return self.result

    def write(self, values):
        self.writes.append(dict(values))
        return True

    def dispatch_process(self):
        self.dispatched = True


class UpdateModelTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model_class = load_update_class()

    def test_prepare_data_update_normalizes_upsert_and_preserves_raw_payload(self):
        instance = self.model_class()
        payload = {"res_model": "res.partner", "res_id": 13,
                   "name": "Ada", "data": {"email": "a@example.test"}}
        raw_payload = json.dumps(payload)

        values = instance.prepare_data_update(payload)

        self.assertEqual(values["name"], "Ada")
        self.assertEqual(values["res_id"], 13)
        self.assertEqual(values["res_model"], "res.partner")
        self.assertEqual(values["operation"], "upsert")
        self.assertEqual(values["raw_payload"], raw_payload)
        self.assertEqual(json.loads(values["data_payload"]), {
            "email": "a@example.test", "id": 13, "display_name": "Ada"})


    def test_prepare_data_update_prefers_top_level_fields_and_unlink(self):
        instance = self.model_class()
        values = instance.prepare_data_update({
            "res_model": "res.partner", "res_id": 21, "display_name": "Top",
            "operation": "unlink", "event_datetime": "2024-01-02 03:04:05",
            "data": {"id": 99, "display_name": "Nested", "value": 1}})

        self.assertEqual(values["operation"], "unlink")
        self.assertEqual(values["name"], "Top")
        self.assertEqual(values["event_datetime"], "2024-01-02 03:04:05")
        self.assertEqual(json.loads(values["data_payload"]), {
            "id": 21, "display_name": "Top", "value": 1})

    def test_process_upsert_dispatches_and_marks_done(self):
        strategy = FakeRecord(id=6)
        data = FakeDataModel(result=FakeRecord(id=42, external_last_update=False))
        row = FakeRecordset(data_payload=json.dumps({"id": 19}), operation="upsert",
                            data_id=data, strategy_id=strategy, company_id=False,
                            res_id=19, event_datetime=False)

        self.model_class.process_data(row)

        self.assertEqual(data.received, ({"id": 19}, strategy, {
            "create_when_not_found": True, "need_get_data_json": False}))
        self.assertTrue(data.result.dispatched)
        self.assertEqual(row.writes, [{"state": "done", "data_id": 42,
                                      "error_message": False}])

    def test_process_unlink_searches_scoped_record_and_applies_company(self):
        strategy = FakeRecord(id=8)
        target = FakeRecord(id=31)
        data = FakeDataModel(result=target)
        row = FakeRecordset(data_payload="{}", operation="unlink", data_id=data,
                            strategy_id=strategy, company_id=FakeRecord(id=3),
                            res_id=31, event_datetime="2024-02-03")

        self.model_class.process_data(row)

        self.assertEqual(data.domains, [[("external_odoo_id", "=", 31),
                                        ("sync_strategy_id", "=", 8)]])
        self.assertEqual(target.writes, [{"external_deleted": True,
                                         "deleted_datetime": "2024-02-03",
                                         "company_id": 3}])
        self.assertTrue(data.result.dispatched)
        self.assertEqual(row.writes[0]["state"], "done")

    def test_process_upsert_converts_write_date_and_sets_company(self):
        data = FakeDataModel(result=FakeRecord(id=11, external_last_update=False))
        row = FakeRecordset(data_payload=json.dumps({"id": 7,
                                  "write_date": "2024-03-04 05:06:07"}),
                            operation="upsert", data_id=data,
                            strategy_id=FakeRecord(id=2), company_id=FakeRecord(id=5),
                            res_id=7, event_datetime=False)

        self.model_class.process_data(row)

        self.assertEqual(data.result.writes, [
            {"company_id": 5}, {"external_last_update": datetime(2024, 3, 4, 5, 6, 7)}])
        self.assertTrue(data.result.dispatched)
        self.assertEqual(row.writes[0]["state"], "done")

    def test_process_older_event_marks_out_of_date_without_dispatch(self):
        later = datetime(2024, 3, 4, 5, 6, 8)
        data = FakeDataModel(result=FakeRecord(id=11, external_last_update=later))
        row = FakeRecordset(data_payload=json.dumps({"write_date": "2024-03-04 05:06:07"}),
                            operation="upsert", data_id=data,
                            strategy_id=FakeRecord(id=2), company_id=False,
                            res_id=7, event_datetime=False)

        self.model_class.process_data(row)

        self.assertFalse(hasattr(data, "dispatched"))
        self.assertEqual(row.writes[0]["state"], "out_off_date")
        self.assertEqual(row.writes[0]["data_id"], 11)
        self.assertIn("Data out off date", row.writes[0]["error_message"])

    def test_process_failure_is_recorded_as_error(self):
        row = FakeRecordset(data_payload="not-json", operation="upsert",
                            data_id=FakeDataModel(), strategy_id=False,
                            company_id=False, res_id=1, event_datetime=False)

        self.model_class.process_data(row)

        self.assertEqual(row.writes[0]["state"], "error")
        self.assertIn("JSONDecodeError", row.writes[0]["error_message"])

    def test_action_process_enforces_singleton_and_delegates(self):
        row = FakeRecordset()
        called = []
        row.process_data = lambda: called.append(True)

        self.model_class.action_process(row)

        self.assertEqual(called, [True])
        self.assertTrue(row.ensure_one())


if __name__ == "__main__":
    unittest.main()
