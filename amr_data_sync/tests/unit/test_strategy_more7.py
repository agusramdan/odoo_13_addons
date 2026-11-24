"""Mock-focused coverage for additional strategy production branches."""
import importlib.util
import pathlib
import types
import unittest
from unittest.mock import Mock

UNIT_DIR = pathlib.Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location(
    "strategy_more7_support", UNIT_DIR / "test_sync_strategy.py")
_support = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_support)


class StrategyMore7Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.strategy_class, _ = _support.load_strategy_class()

    def strategy(self, **values):
        result = self.strategy_class()
        result.__dict__.update(values)
        result.ensure_one = lambda: result
        return result

    def test_get_internal_id_uses_same_id_offset_after_both_mapping_misses(self):
        sync = Mock()
        sync.search.side_effect = [
            types.SimpleNamespace(internal_odoo_id=False),
            types.SimpleNamespace(internal_odoo_id=False),
        ]
        strategy = self.strategy(
            id=17, external_app_name="source", external_model="remote.item",
            internal_model="local.item", internal_id_same_as_external=True,
            internal_id_offset=30, env={"external.data.sync": sync})

        self.assertEqual(strategy.get_internal_id_from_external_id(12), 42)
        self.assertEqual(sync.search.call_count, 2)
        self.assertEqual(sync.search.call_args_list[0][0][0], [
            ("sync_strategy_id", "=", 17), ("external_odoo_id", "=", 12)])
        self.assertEqual(sync.search.call_args_list[1][0][0], [
            ("external_app_name", "=", "source"),
            ("external_model", "=", "remote.item"),
            ("internal_model", "=", "local.item"),
            ("external_odoo_id", "=", 12), ("sync_strategy_id", "=", False)])

    def test_lookup_strategy_falls_back_in_order_and_prefers_parent_server(self):
        parent_server = types.SimpleNamespace(id=8, get_application_name=lambda: "parent-app")
        parent = types.SimpleNamespace(id=4, get_server_sync=lambda: parent_server)
        model = self.strategy()
        model.search = Mock(side_effect=[False, False, False, "app-any-model"])
        model.browse = Mock(return_value=False)

        # Parent lookup hits the final generic-by-app fallback after its specific misses.
        found = model.lookup_strategy(
            "local.item", parent_sync_strategy=parent, server_sync=object(),
            external_app_name="caller-app", external_model="remote.item")

        self.assertEqual(found, "app-any-model")
        self.assertEqual(model.search.call_count, 4)
        self.assertEqual(model.search.call_args_list[0][0][0], [
            ("external_model", "=", "remote.item"),
            ("internal_model", "=", "local.item"),
            ("parent_sync_strategy_id", "=", 4)])
        self.assertEqual(model.search.call_args_list[1][0][0], [
            ("external_model", "=", "remote.item"),
            ("internal_model", "=", "local.item"), ("server_sync_id", "=", 8)])
        self.assertEqual(model.search.call_args_list[2][0][0], [
            ("external_model", "=", "remote.item"),
            ("internal_model", "=", "local.item"),
            ("external_app_name", "=", "parent-app")])
        self.assertEqual(model.search.call_args_list[3][0][0], [
            ("internal_model", "=", "local.item"),
            ("external_app_name", "=", "parent-app")])

    def test_prepare_sync_list_combines_company_mapping_and_last_sync(self):
        company_model = Mock()
        company_model.reverse_mapping.return_value = ({6: ["remote-6"]}, {9})
        last_sync = types.SimpleNamespace(strftime=lambda fmt: "2024-03-04 05:06:07")
        sync_model = Mock()
        sync_model.get_last_sync_datetime.return_value = last_sync
        companies = [types.SimpleNamespace(id=6, name="Mapped"),
                     types.SimpleNamespace(id=9, name="Unmapped")]
        server = types.SimpleNamespace(id=3)
        strategy = self.strategy(
            external_context="{'lang': 'en_US'}", external_model="remote.item",
            external_app_name="app", server_sync_id=server, company_ids=companies,
            external_domain="[]", internal_lookup_fields="sku, barcode", filter_last_update=True,
            env={"external.data.company": company_model,
                 "external.data.sync": sync_model})
        strategy.get_external_application_name = Mock(return_value="effective-app")

        config = strategy.prepare_sync_list_dict()

        self.assertEqual(config, {
            "fields": ["display_name", "name", "write_date", "id", "sku", "barcode"],
            "context": {"lang": "en_US"},
            "domain": [
                ("write_date", ">=", "2024-03-04 05:06:07"), "|",
                ("company_id", "in", ["remote-6"]),
                ("company_id.name", "in", ["Unmapped"])]})
        company_model.reverse_mapping.assert_called_once_with(
            companies, external_app_name="effective-app", server_sync=server)
        sync_model.get_last_sync_datetime.assert_called_once_with(strategy)

    def test_prepare_input_converts_simple_types_and_applies_relation_rules(self):
        class Field(object):
            def __init__(self, name, field_type, compute=False, related=False,
                         required=False):
                self.name = name
                self.type = field_type
                self.compute = compute
                self.related = related
                self.required = required

        field_defs = {
            "active": Field("active", "boolean"),
            "count": Field("count", "integer"),
            "computed": Field("computed", "char", compute=True),
            "related": Field("related", "char", related=True),
            "parent_id": Field("parent_id", "many2one", required=True),
            "optional_id": Field("optional_id", "many2one"),
            "name": Field("name", "char"),
        }
        model = Mock()
        model.prepare_input_dict = None
        model._fields = field_defs
        model.check_field_access_rights.return_value = list(field_defs)
        parent = Mock()
        parent.company_id = False
        parent.get_related_data.return_value = 29
        env = {"local.item": model}
        exclusion_model = types.SimpleNamespace(_fields={})
        exclusion_registry = Mock()
        exclusion_registry.get_exclude_all_fields.return_value = []
        env.update({"mail.thread": exclusion_model,
                    "mail.activity.mixin": exclusion_model,
                    "mail.blacklist": exclusion_model,
                    "external.data.sync.exclude": exclusion_registry})
        class Env(dict):
            def __init__(self, *args, **kwargs):
                dict.__init__(self, *args, **kwargs)
                self.cr = Mock()
        env = Env(env)
        mappings = types.SimpleNamespace(filtered=lambda predicate: [])
        strategy = self.strategy(
            internal_model="local.item", external_fields="parent_id",
            relation_field_ignore=True, after_create_fields="parent_id",
            exclude_fields="name", eval_script=False, line_mapping_ids=mappings, env=env)
        strategy.env.cr.savepoint.return_value.__enter__ = Mock(return_value=None)
        strategy.env.cr.savepoint.return_value.__exit__ = Mock(return_value=False)

        result = strategy.prepare_input_external(parent, {
            "active": 0, "count": [5, "label"], "computed": "discard",
            "related": "discard", "parent_id": 22, "optional_id": 23,
            "name": "excluded", "unknown": "discard"})

        self.assertEqual(result, {"active": False, "count": 5})
        parent.get_related_data.assert_called_once_with(field_defs["parent_id"], 22)
        model.check_field_access_rights.assert_called_once_with("write", None)

    def test_internal_lookup_uses_inactive_id_recordset_when_mapping_exists(self):
        inactive_model = Mock()
        inactive_model.search.return_value = "inactive-record"
        scoped_model = Mock()
        scoped_model.with_context.return_value = inactive_model
        base_model = Mock()
        base_model.sudo.return_value = scoped_model
        strategy = self.strategy(
            internal_model="local.item", internal_lookup_method="find",
            env={"local.item": base_model})
        strategy.get_internal_id_from_external_id = Mock(return_value=71)

        self.assertEqual(strategy.internal_lookup({"id": 12}), "inactive-record")
        base_model.sudo.assert_called_once_with()
        scoped_model.with_context.assert_called_once_with(active_test=False)
        inactive_model.search.assert_called_once_with([("id", "=", 71)])


if __name__ == "__main__":
    unittest.main()
