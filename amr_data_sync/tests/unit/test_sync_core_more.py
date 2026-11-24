"""Additional offline behavior tests for ExternalDataSync methods.

The production model is loaded directly; fakes stand in only for Odoo's
recordset, environment, and cursor boundaries. No ORM/database behavior is
claimed.
"""
import importlib.util
import pathlib
import types
import unittest
from unittest.mock import Mock


CORE_TEST = pathlib.Path(__file__).with_name("test_sync_core.py")
_spec = importlib.util.spec_from_file_location("sync_core_test_helpers", CORE_TEST)
_helpers = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_helpers)
ExternalDataSync, _utils = _helpers.load_sync_model()


class Records(object):
    def __init__(self, records=()):
        self.records = list(records)

    def __iter__(self):
        return iter(self.records)

    def __bool__(self):
        return bool(self.records)

    __nonzero__ = __bool__


class ExternalDataSyncMoreTest(unittest.TestCase):
    def model(self, **values):
        instance = ExternalDataSync()
        for name, value in values.items():
            setattr(instance, name, value)
        return instance

    def test_ensure_external_data_normalizes_supported_shapes(self):
        normalize = ExternalDataSync.ensure_external_data

        self.assertEqual(normalize(self.model(), {"id": 8, "name": "A"}),
                         {"id": 8, "name": "A"})
        self.assertEqual(normalize(self.model(), [8, "A"]),
                         {"id": 8, "display_name": "A"})
        self.assertEqual(normalize(self.model(), [8, "A", "ignored"]), {"id": 8})
        self.assertEqual(normalize(self.model(), [8]), {"id": 8})
        self.assertEqual(normalize(self.model(), 8), {"id": 8})
        self.assertEqual(normalize(self.model(), "8"), {})

    def test_get_json_data_for_create_returns_cached_dict_without_fetch(self):
        instance = self.model(need_get_data_json=False, data_json='{"id": 17}')
        instance.get_external_one_data = Mock(side_effect=AssertionError("unexpected fetch"))

        self.assertEqual(instance.get_json_data_for_create(), {"id": 17})
        instance.get_external_one_data.assert_not_called()

    def test_get_json_data_for_create_records_empty_fetch_as_inactive(self):
        instance = self.model(need_get_data_json=True,
                              get_external_one_data=Mock(return_value=None),
                              write=Mock())

        result = instance.get_json_data_for_create()

        self.assertEqual(result, {"active": False})
        instance.write.assert_called_once_with({
            "need_get_data_json": False, "data_json": "null"})

    def test_is_all_related_done_requires_every_related_record_done(self):
        complete = self.model(related_ids=Records([
            types.SimpleNamespace(state="done"),
            types.SimpleNamespace(state="need_resolve"),
        ]))
        incomplete = self.model(related_ids=Records([
            types.SimpleNamespace(state="done"),
            types.SimpleNamespace(state="process", name="address"),
        ]))

        self.assertTrue(complete.is_all_related_done())
        self.assertFalse(incomplete.is_all_related_done())

    def test_get_internal_object_returns_existing_inactive_record_with_context_disabled(self):
        internal = types.SimpleNamespace(with_context=Mock())
        browsed = types.SimpleNamespace(exists=Mock(return_value=internal))
        internal.with_context.return_value.browse.return_value = browsed
        model_object = _helpers.FakeModelBase()
        model_object.with_context = Mock(return_value=types.SimpleNamespace(
            browse=Mock(return_value=browsed)))
        strategy = types.SimpleNamespace(internal_model_object=Mock(return_value=model_object))
        instance = self.model(sync_strategy_id=strategy, internal_odoo_id=23)

        result = instance.get_internal_object()

        self.assertIs(result, internal)
        model_object.with_context.assert_called_once_with(active_test=False)
        model_object.with_context.return_value.browse.assert_called_once_with(23)
        browsed.exists.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
