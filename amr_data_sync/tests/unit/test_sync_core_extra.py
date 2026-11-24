"""Failure-path coverage for real ExternalDataSync methods with offline ORM fakes."""
import datetime
import importlib.util
import pathlib
import types
import unittest
from unittest.mock import Mock


CORE_TEST = pathlib.Path(__file__).with_name("test_sync_core.py")
_spec = importlib.util.spec_from_file_location("sync_core_extra_helpers", CORE_TEST)
_helpers = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_helpers)
ExternalDataSync, _utils = _helpers.load_sync_model()


class NullContext(object):
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, tb):
        return False


class SyncCoreFailureTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model_globals = ExternalDataSync.process_data.__globals__
        cls.original_now = cls.model_globals["fields"].Datetime.now

    def setUp(self):
        self.model_globals["fields"].Datetime.now = lambda: datetime.datetime(2025, 1, 1)

    def tearDown(self):
        self.model_globals["fields"].Datetime.now = self.original_now

    def model(self, **values):
        instance = ExternalDataSync()
        for name, value in values.items():
            setattr(instance, name, value)
        return instance

    def test_process_data_records_failure_state_and_reraises_original_error(self):
        failure = ValueError("bad external payload")
        writes = []
        instance = self.model(
            get_json_data_for_create=Mock(side_effect=failure),
            write_error_safe=lambda values: writes.append(dict(values)),
        )

        with self.assertRaises(ValueError) as raised:
            instance.process_data()

        self.assertIs(raised.exception, failure)
        self.assertEqual(len(writes), 1)
        self.assertEqual(writes[0]["state"], "error")
        self.assertIn("ValueError: bad external payload", writes[0]["error_info"])
        self.assertNotIn("payload_json", writes[0])
        self.assertIn("last_error", writes[0])
        self.assertIn("last_processing_datetime", writes[0])
        self.assertIn("next_processing_datetime", writes[0])

    def test_process_with_handel_error_persists_error_state_without_leaking_exception(self):
        writes = []
        instance = self.model(
            env=types.SimpleNamespace(cr=types.SimpleNamespace(savepoint=NullContext)),
            process_data=Mock(side_effect=RuntimeError("sync failed")),
            write_error_safe=lambda values: writes.append(dict(values)),
        )

        result = instance.process_with_handel_error()

        self.assertIsNone(result)
        instance.process_data.assert_called_once_with()
        self.assertEqual(len(writes), 1)
        self.assertEqual(writes[0]["state"], "error")
        self.assertIn("RuntimeError: sync failed", writes[0]["error_info"])
        self.assertIn("last_error", writes[0])
        self.assertIn("next_processing_datetime", writes[0])

    def test_cron_processes_due_sync_and_related_records_through_real_dispatch(self):
        seen = []
        first = types.SimpleNamespace(dispatch_process=lambda immediate: seen.append(("first", immediate)))
        second = types.SimpleNamespace(dispatch_process=lambda immediate: seen.append(("second", immediate)))
        related = types.SimpleNamespace(dispatch_process=lambda immediate: seen.append(("related", immediate)))
        call_count = [0]

        def search(domain, **kwargs):
            call_count[0] += 1
            return [first] if call_count[0] == 1 else [second]

        related_model = types.SimpleNamespace(search=Mock(return_value=[related]))
        instance = self.model(
            search=search,
            env=types.SimpleNamespace(__getitem__=lambda self, key: related_model),
        )
        # Python special-method lookup is on the class, so provide an ordinary mapping instead.
        instance.env = {"external.data.sync.related": related_model}

        result = instance.cron_process_data(limit=7)

        self.assertTrue(result)
        self.assertEqual(call_count[0], 2)
        self.assertEqual(seen, [("first", True), ("second", True), ("related", True)])
        self.assertEqual(related_model.search.call_args[0][0][0], ("state", "!=", "done"))
        self.assertEqual(related_model.search.call_args[1]["limit"], 7)


if __name__ == "__main__":
    unittest.main()
