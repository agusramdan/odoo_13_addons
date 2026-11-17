"""Additional offline coverage for real strategy preparation and callbacks."""
import importlib.util
import pathlib
import types
import unittest
from unittest.mock import Mock


UNIT = pathlib.Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location(
    "strategy_extra2_helpers", UNIT / "test_sync_strategy.py")
_helpers = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_helpers)
Strategy = _helpers.StrategyTest


class Savepoint(object):
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False


class Environment(dict):
    def __init__(self, values):
        super(Environment, self).__init__(values)
        self.cr = types.SimpleNamespace(savepoint=Savepoint)


def field(name, kind="char", compute=False, related=False, required=False):
    return types.SimpleNamespace(name=name, type=kind, compute=compute,
                                 related=related, required=required)


class StrategyExtraTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Strategy.setUpClass()
        cls.strategy_class = Strategy.strategy_class
        cls.FakeModel = _helpers.FakeModel

    def strategy(self, **values):
        strategy = self.strategy_class()
        strategy.__dict__.update(values)
        strategy.ensure_one = lambda: None
        return strategy

    def test_prepare_input_filters_unwritable_computed_and_excluded_and_converts_scalars(self):
        fields = {
            "name": field("name"), "enabled": field("enabled", "boolean"),
            "count": field("count", "integer"), "computed": field("computed", compute=True),
            "related": field("related", related=True), "secret": field("secret"),
        }
        model = types.SimpleNamespace(_fields=fields,
                                     check_field_access_rights=lambda mode, names: list(fields))
        strategy = self.strategy(
            internal_model="res.partner", env=Environment({"res.partner": model, "mail.thread": types.SimpleNamespace(_fields={}),
            "mail.activity.mixin": types.SimpleNamespace(_fields={}),
            "mail.blacklist": types.SimpleNamespace(_fields={}),
            "external.data.sync.exclude": types.SimpleNamespace(get_exclude_all_fields=lambda: [])}),
            external_fields=False, exclude_fields="secret", line_mapping_ids=False,
            after_create_fields="", relation_field_ignore=False, eval_script="")
        strategy.get_mapping_fields = lambda: {}
        parent = types.SimpleNamespace(company_id=False)

        actual = strategy.prepare_input_external(parent, {
            "name": "Ada", "enabled": 0, "count": [7, "Seven"],
            "computed": "ignored", "related": "ignored", "secret": "hidden",
            "unknown": "ignored", "empty": "",
        })

        self.assertEqual(actual, {"name": "Ada", "enabled": False, "count": 7})

    def test_prepare_input_maps_fields_runs_script_relations_and_model_hook(self):
        mapping_field = field("mapped")
        relation_field = field("category_id", "many2one", required=False)
        fields = {"name": field("name"), "mapped": mapping_field,
                  "category_id": relation_field}
        model = types.SimpleNamespace(_fields=fields,
                                     check_field_access_rights=lambda mode, names: list(fields),
                                     prepare_input_dict=Mock(return_value={"hooked": True}))
        mapping = types.SimpleNamespace(key_name="remote_value",
            mapping_data=Mock(return_value="resolved"))
        strategy = self.strategy(
            internal_model="res.partner", env=Environment({"res.partner": model, "mail.thread": types.SimpleNamespace(_fields={}),
            "mail.activity.mixin": types.SimpleNamespace(_fields={}),
            "mail.blacklist": types.SimpleNamespace(_fields={}),
            "external.data.sync.exclude": types.SimpleNamespace(get_exclude_all_fields=lambda: [])}),
            external_fields="category_id", exclude_fields="", line_mapping_ids=False,
            after_create_fields="category_id", relation_field_ignore=False,
            eval_script="input_dict['scripted'] = external_data['name'].upper()")
        strategy.get_mapping_fields = lambda: {"mapped": mapping}
        relation_value = [12]
        parent = types.SimpleNamespace(company_id=False,
            get_related_data=Mock(return_value=relation_value))
        item = {"name": "Ada", "remote_value": "raw", "category_id": {"id": 12}}

        result = strategy.prepare_input_external(parent, item)

        self.assertEqual(result, {"name": "Ada", "mapped": "resolved",
                                 "scripted": "ADA", "hooked": True})
        mapping.mapping_data.assert_called_once_with(
            item, model=model, parent_data_sync=parent, field=mapping_field)
        parent.get_related_data.assert_called_once_with(relation_field, item["category_id"])
        model.prepare_input_dict.assert_called_once_with(item, input_dict={
            "name": "Ada", "mapped": "resolved", "scripted": "ADA", "hooked": True})

    def test_sync_callbacks_dispatch_real_strategy_method_to_sync_consumer(self):
        strategy = self.strategy()
        strategy.ensure_internal_context = Mock(return_value=strategy)
        strategy.prepare_sync_list_dict = Mock(return_value={"fields": ["id"]})
        callback = Mock()
        remote_model = types.SimpleNamespace(external_data_callback=Mock())

        class RemoteContext(object):
            def __enter__(self):
                return remote_model
            def __exit__(self, exc_type, exc_value, traceback):
                return False

        server = types.SimpleNamespace(create_remote_model=Mock(return_value=RemoteContext()))
        strategy.server_sync_id = server
        strategy.external_model = "remote.partner"
        strategy.env = {"external.data.sync": types.SimpleNamespace(data_from_external=callback)}

        strategy.sync_list_model_object()

        server.create_remote_model.assert_called_once_with("remote.partner", fields=["id"])
        remote_model.external_data_callback.assert_called_once()
        delivered = remote_model.external_data_callback.call_args[0][0]
        payload = {"id": 18, "name": "Ada"}
        delivered(payload, source="remote")
        callback.assert_called_once_with(payload, strategy)
        strategy.ensure_internal_context.assert_called_once_with()

    def test_sync_completion_callbacks_pass_production_kwargs_and_preserve_result(self):
        strategy = self.strategy(internal_event_sync_done="on_done",
                                 internal_event_archived_done="on_archived")
        existing = self.FakeModel()
        item = {"id": 5}
        values = {"name": "Ada"}
        invocations = []
        strategy_globals = self.strategy_class.event_external_data_sync_done.__globals__
        original = strategy_globals["call_with_savepoint"]
        strategy_globals["call_with_savepoint"] = lambda record, method, kwargs=None: (
            invocations.append((record, method, kwargs)) or "callback result")
        try:
            self.assertEqual(strategy.event_external_data_sync_done(existing, item, values),
                             "callback result")
            self.assertEqual(strategy.event_external_archived_done(existing, item, values),
                             "callback result")
        finally:
            strategy_globals["call_with_savepoint"] = original
        self.assertEqual(invocations, [
            (existing, "on_done", {"data_external": item, "data_update": values}),
            (existing, "on_archived", {"data_external": item, "data_update": values}),
        ])

    def test_sync_callbacks_skip_non_recordsets_or_unconfigured_events(self):
        strategy = self.strategy(internal_event_sync_done="", internal_event_archived_done="")
        existing = object()
        self.assertIs(strategy.event_external_data_sync_done(existing, {}, {}), existing)
        self.assertIsNone(strategy.event_external_archived_done(None, {}, {}))
        self.assertEqual(strategy.call_internal_process_method(object(), {}, {"x": 1}, None), {"x": 1})

    def test_internal_process_callback_receives_exact_sync_context(self):
        strategy = self.strategy(internal_process_method="before_write")
        existing = self.FakeModel()
        method = Mock(return_value={"adjusted": True})
        existing.before_write = method
        item, values, sync = {"id": 9}, {"name": "Ada"}, object()
        result = strategy.call_internal_process_method(existing, item, values, sync)
        self.assertEqual(result, {"adjusted": True})
        method.assert_called_once_with(data_external=item, data_update=values,
                                       sync_strategy=strategy, data_sync=sync)


if __name__ == "__main__":
    unittest.main()
