"""Additional behavioral coverage for field processing and sync failures."""
import importlib.util
import pathlib
import types
import unittest
from unittest.mock import Mock


UNIT = pathlib.Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location(
    "strategy_extra4_helpers", UNIT / "test_sync_strategy.py")
_helpers = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_helpers)


def field(name, kind="char", required=False, compute=False, related=False):
    return types.SimpleNamespace(name=name, type=kind, required=required,
                                 compute=compute, related=related)


class Environment(dict):
    def __init__(self, values):
        dict.__init__(self, values)
        self.cr = types.SimpleNamespace(savepoint=Savepoint)


class Savepoint(object):
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False


class StrategyExtra4Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.strategy_class, _ = _helpers.load_strategy_class()

    def strategy(self, **values):
        obj = self.strategy_class()
        obj.__dict__.update(values)
        obj.ensure_one = lambda: None
        return obj

    def environment(self, model):
        return Environment({
            "res.partner": model,
            "mail.thread": types.SimpleNamespace(_fields={"message_ids": None}),
            "mail.activity.mixin": types.SimpleNamespace(_fields={"activity_ids": None}),
            "mail.blacklist": types.SimpleNamespace(_fields={"is_blacklisted": None}),
            "external.data.sync.exclude": types.SimpleNamespace(
                get_exclude_all_fields=lambda: ["globally_hidden"]),
        })

    def test_prepare_input_coerces_boolean_integer_and_company_and_overrides_parent_company(self):
        fields = {name: field(name, kind) for name, kind in (
            ("enabled", "boolean"), ("quantity", "integer"),
            ("company_id", "many2one"), ("title", "char"))}
        model = types.SimpleNamespace(
            _fields=fields, check_field_access_rights=lambda mode, names: list(fields))
        strategy = self.strategy(internal_model="res.partner", env=self.environment(model),
                                 exclude_fields="", external_fields="", relation_field_ignore=False,
                                 after_create_fields="", eval_script="")
        strategy.get_mapping_fields = lambda: {}
        strategy.lookup_company = Mock(return_value="17")
        parent = types.SimpleNamespace(company_id=types.SimpleNamespace(id=23))

        result = strategy.prepare_input_external(parent, {
            "enabled": "", "quantity": [8, "Eight"], "company_id": "Remote Co",
            "title": "Member", "globally_hidden": "discard",
        })

        self.assertEqual(result, {"enabled": False, "quantity": 8, "company_id": 23,
                                  "title": "Member"})
        strategy.lookup_company.assert_called_once_with("Remote Co")

    def test_prepare_input_honors_mapping_even_when_source_key_is_excluded(self):
        mapping = types.SimpleNamespace(key_name="remote_status",
                                        mapping_data=Mock(return_value="active"))
        fields = {"status": field("status"), "name": field("name")}
        model = types.SimpleNamespace(
            _fields=fields, check_field_access_rights=lambda mode, names: list(fields))
        strategy = self.strategy(internal_model="res.partner", env=self.environment(model),
                                 exclude_fields="", external_fields="", relation_field_ignore=False,
                                 after_create_fields="", eval_script="")
        strategy.get_mapping_fields = lambda: {"status": mapping}
        parent = types.SimpleNamespace(company_id=False)
        item = {"name": "A", "status": "raw", "remote_status": "enabled"}

        result = strategy.prepare_input_external(parent, item)

        self.assertEqual(result, {"name": "A", "status": "active"})
        mapping.mapping_data.assert_called_once_with(
            item, model=model, parent_data_sync=parent,
            field=fields["status"])

    def test_mapping_failure_propagates_from_savepoint_without_partial_result(self):
        mapping_error = RuntimeError("mapping unavailable")
        mapping = types.SimpleNamespace(key_name="remote", mapping_data=Mock(side_effect=mapping_error))
        fields = {"status": field("status")}
        model = types.SimpleNamespace(
            _fields=fields, check_field_access_rights=lambda mode, names: list(fields))
        strategy = self.strategy(internal_model="res.partner", env=self.environment(model),
                                 exclude_fields="", external_fields="", relation_field_ignore=False,
                                 after_create_fields="", eval_script="")
        strategy.get_mapping_fields = lambda: {"status": mapping}
        with self.assertRaisesRegex(RuntimeError, "mapping unavailable"):
            strategy.prepare_input_external(types.SimpleNamespace(company_id=False),
                                            {"status": "raw", "remote": "x"})
        mapping.mapping_data.assert_called_once()

    def test_remote_read_returns_first_record_and_preserves_remote_errors(self):
        strategy = self.strategy(external_model="remote.item", server_sync_id=None)
        strategy.prepare_sync_one_dict = Mock(return_value={"fields": ["name"]})
        model = types.SimpleNamespace(read=Mock(return_value=[{"id": 4, "name": "A"}]))

        class RemoteContext(object):
            def __enter__(self):
                return model
            def __exit__(self, exc_type, exc_value, traceback):
                return False

        server = types.SimpleNamespace(create_remote_model=Mock(return_value=RemoteContext()))
        strategy.server_sync_id = server
        self.assertEqual(strategy.get_external_one_data(4), {"id": 4, "name": "A"})
        server.create_remote_model.assert_called_once_with("remote.item", fields=["name"])
        model.read.assert_called_once_with([4])

        failure = ValueError("remote unavailable")
        model.read.side_effect = failure
        with self.assertRaisesRegex(ValueError, "remote unavailable"):
            strategy.get_external_one_data(9)
        model.read.assert_called_with([9])

    def test_method_call_sync_propagates_configured_method_result_and_errors(self):
        strategy = self.strategy(internal_model="res.partner", internal_call_method="sync_now")
        method = Mock(return_value={"synced": 3})
        model = types.SimpleNamespace(sync_now=method)
        strategy.env = {"res.partner": model}
        self.assertEqual(strategy.method_call_sync_from_application_server(), {"synced": 3})
        method.assert_called_once_with(strategy)
        method.side_effect = RuntimeError("sync failed")
        with self.assertRaisesRegex(RuntimeError, "sync failed"):
            strategy.method_call_sync_from_application_server()


if __name__ == "__main__":
    unittest.main()
