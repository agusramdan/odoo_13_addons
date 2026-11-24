"""Behavioral coverage for remaining strategy lookup, input, and callback paths."""
import importlib.util
import pathlib
import types
import unittest
from unittest.mock import Mock, call, patch


UNIT_DIR = pathlib.Path(__file__).resolve().parent
_helper_spec = importlib.util.spec_from_file_location(
    "strategy_remaining_support", UNIT_DIR / "test_sync_strategy.py")
_helper = importlib.util.module_from_spec(_helper_spec)
_helper_spec.loader.exec_module(_helper)


def field(name, kind="char", required=False, compute=False, related=False):
    return types.SimpleNamespace(name=name, type=kind, required=required,
                                 compute=compute, related=related)


class Savepoint(object):
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False


class Environment(dict):
    def __init__(self, values):
        dict.__init__(self, values)
        self.cr = types.SimpleNamespace(savepoint=Savepoint)
        self.context = {"lang": "en_US"}


class Recordset(_helper.FakeModel):
    def __init__(self, ids):
        self.ids = ids


class StrategyRemainingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.strategy_class, _ = _helper.load_strategy_class()

    def strategy(self, **values):
        strategy = self.strategy_class()
        strategy.__dict__.update(values)
        strategy.ensure_one = lambda: strategy
        return strategy

    def test_lookup_strategy_tries_parent_then_server_then_application_scope(self):
        server_result = object()

        class Strategies(object):
            def __init__(self):
                self.domains = []

            def browse(self):
                return False

            def search(self, domain, limit=None):
                self.domains.append(domain)
                return server_result if len(self.domains) == 2 else False

        strategies = Strategies()
        server = types.SimpleNamespace(
            id=7, get_application_name=lambda: "resolved-app")
        parent = types.SimpleNamespace(id=31, get_server_sync=lambda: server)
        strategy = self.strategy()
        strategy.search = strategies.search
        self.assertIs(strategy.lookup_strategy(
            "local.item", parent_sync_strategy=parent, server_sync=None,
            external_app_name="supplied-app", external_model="remote.item"), server_result)
        self.assertEqual(strategies.domains, [[
            ("external_model", "=", "remote.item"),
            ("internal_model", "=", "local.item"),
            ("parent_sync_strategy_id", "=", 31)], [
            ("external_model", "=", "remote.item"),
            ("internal_model", "=", "local.item"),
            ("server_sync_id", "=", 7)]])
        self.assertEqual(parent.get_server_sync().id, server.id)

    def test_lookup_strategy_falls_back_to_exact_then_application_model(self):
        class Strategies(object):
            def __init__(self):
                self.domains = []

            def browse(self):
                return False

            def search(self, domain, limit=None):
                self.domains.append(domain)
                return "app-wide" if len(self.domains) == 2 else False

        strategies = Strategies()
        strategy = self.strategy()
        strategy.search = strategies.search
        strategy.browse = lambda: False
        self.assertEqual(strategy.lookup_strategy(
            "local.item", external_app_name="app", external_model="remote.item"),
            "app-wide")
        self.assertEqual(strategies.domains, [
            [("external_model", "=", "remote.item"),
             ("internal_model", "=", "local.item"), ("external_app_name", "=", "app")],
            [("internal_model", "=", "local.item"), ("external_app_name", "=", "app")],
        ])

    def test_prepare_input_filters_fields_applies_script_and_parent_relation(self):
        fields = {
            "name": field("name"), "active": field("active", "boolean"),
            "computed": field("computed", compute=True),
            "optional_id": field("optional_id", "many2one", required=False),
            "after_id": field("after_id", "many2one", required=True),
            "ignored": field("ignored"),
        }
        model = types.SimpleNamespace(
            _fields=fields,
            check_field_access_rights=lambda mode, names: ["name", "active", "computed",
                                                           "optional_id", "after_id"])
        parent = types.SimpleNamespace(
            company_id=False,
            get_related_data=Mock(side_effect=lambda f, value: value + "-resolved"))
        env = Environment({"local.item": model})
        strategy = self.strategy(
            internal_model="local.item", env=env, exclude_fields="ignored",
            relation_field_ignore=True, after_create_fields="after_id", eval_script="",
            external_fields="")
        strategy.get_include_fields = lambda: []
        strategy.get_exclude_fields = lambda: ["ignored"]
        strategy.get_mapping_fields = lambda: {}
        strategy.get_after_create_fields = lambda: ["after_id"]

        actual = strategy.prepare_input_external(parent, {
            "name": "Item", "active": "", "computed": "forged",
            "optional_id": "optional", "after_id": "deferred", "ignored": "no",
            "unknown": "no",
        })

        self.assertEqual(actual, {"name": "Item", "active": False})
        self.assertEqual(parent.get_related_data.call_args_list, [
            call(fields["after_id"], "deferred")])

    def test_prepare_input_mapping_eval_and_model_hook_compose_in_order(self):
        fields = {"name": field("name"), "status": field("status")}
        model = types.SimpleNamespace(
            _fields=fields,
            check_field_access_rights=lambda mode, names: ["name", "status"],
            prepare_input_dict=Mock(side_effect=lambda item, input_dict: {"hook": input_dict["status"]}))
        mapping = types.SimpleNamespace(key_name="remote_status",
                                        mapping_data=Mock(return_value="mapped"))
        strategy = self.strategy(
            internal_model="local.item", env=Environment({"local.item": model}),
            exclude_fields="", relation_field_ignore=False, after_create_fields="",
            eval_script="input_dict['scripted'] = external_data['name']",
            external_fields="")
        strategy.get_include_fields = lambda: []
        strategy.get_exclude_fields = lambda: []
        strategy.get_mapping_fields = lambda: {"status": mapping}
        strategy.get_after_create_fields = lambda: []
        item = {"name": "Widget", "status": "raw", "remote_status": "x"}

        self.assertEqual(strategy.prepare_input_external(
            types.SimpleNamespace(company_id=False), item), {
                "name": "Widget", "status": "mapped", "scripted": "Widget", "hook": "mapped"})
        mapping.mapping_data.assert_called_once_with(
            item, model=model, parent_data_sync=unittest.mock.ANY, field=fields["status"])
        model.prepare_input_dict.assert_called_once()

    def test_ensure_internal_context_merges_config_and_default_company(self):
        strategy = self.strategy(env=Environment({}), internal_context="{'active_test': False}",
                                 company_ids=False)
        def with_context(**context):
            clone = self.strategy_class()
            clone.__dict__.update(strategy.__dict__)
            clone.env = types.SimpleNamespace(context=context)
            return clone
        strategy.with_context = with_context
        result = strategy.ensure_internal_context(default_company_id=17)
        self.assertIsNot(result, strategy)
        self.assertEqual(result.env.context, {
            "lang": "en_US", "default_company_id": 17, "active_test": False})
        unchanged = self.strategy(env=Environment({}), internal_context="", company_ids=False)
        self.assertIs(unchanged.ensure_internal_context(), unchanged)

    def test_reverse_mapping_groups_external_ids_and_reports_missing_ids(self):
        internal = Recordset([4, 5, 6])
        strategy = self.strategy(id=9)
        strategy.search_read = Mock(return_value=[
            {"internal_odoo_id": 4, "external_odoo_id": "a"},
            {"internal_odoo_id": 4, "external_odoo_id": "b"},
            {"internal_odoo_id": 5, "external_odoo_id": False},
        ])
        result, missing = strategy.reverse_mapping(internal, raise_not_found_exception=False)
        self.assertEqual(result, {4: ["a", "b"]})
        self.assertEqual(missing, set([5, 6]))
        strategy.search_read.assert_called_once_with(
            [("internal_odoo_id", "in", [4, 5, 6]), ("sync_strategy_id", "=", 9)],
            fields=["internal_odoo_id", "external_odoo_id"])

    def test_reverse_mapping_rejects_missing_mapping_by_default_and_accepts_empty_input(self):
        strategy = self.strategy(id=9)
        self.assertEqual(strategy.reverse_mapping([]), ([], []))
        strategy.search_read = Mock(return_value=[])
        with self.assertRaisesRegex(ValueError, r"found not mapped data \[\{2\}\]"):
            strategy.reverse_mapping(Recordset([2]))
        with self.assertRaisesRegex(ValueError, "Internal Object must"):
            strategy.reverse_mapping([2])
        self.assertEqual(strategy.reverse_mapping([2], raise_not_found_exception=False), ([], []))

    def test_internal_method_and_completion_events_use_configured_arguments(self):
        record = Recordset([42])
        record.process = Mock(return_value={"next": True})
        strategy = self.strategy(internal_process_method="process",
                                 internal_event_sync_done="done",
                                 internal_event_archived_done="archived")
        item, values, sync = {"id": 42}, {"name": "x"}, object()
        self.assertEqual(strategy.call_internal_process_method(record, item, values, sync),
                         {"next": True})
        record.process.assert_called_once_with(data_external=item, data_update=values,
                                              sync_strategy=strategy, data_sync=sync)
        event_globals = strategy.event_external_data_sync_done.__func__.__globals__
        with patch.dict(event_globals, {"call_with_savepoint": Mock(return_value="event-result")}):
            call = event_globals["call_with_savepoint"]
            self.assertEqual(strategy.event_external_data_sync_done(record, item, values),
                             "event-result")
            self.assertEqual(strategy.event_external_archived_done(record, item, values),
                             "event-result")
            self.assertEqual(call.call_count, 2)
            self.assertEqual(call.call_args_list[0][0][1], "done")
            self.assertEqual(call.call_args_list[1][0][1], "archived")
            self.assertEqual(call.call_args_list[1][1]["kwargs"], {
                "data_external": item, "data_update": values})

    def test_internal_process_and_events_leave_non_record_inputs_unchanged(self):
        strategy = self.strategy(internal_process_method="process",
                                 internal_event_sync_done="done",
                                 internal_event_archived_done="archived")
        values = {"name": "x"}
        self.assertIs(strategy.call_internal_process_method(None, {}, values, None), values)
        self.assertIs(strategy.event_external_data_sync_done(None, {}, values), None)
        self.assertIs(strategy.event_external_archived_done(None, {}, values), None)


if __name__ == "__main__":
    unittest.main()
