"""Behavioral coverage for relation processing and exclusion configuration."""
import importlib.util
import pathlib
import sys
import types
import unittest
from unittest.mock import Mock

ADDON = pathlib.Path(__file__).resolve().parents[2]


class ModelBase(object):
    def write(self, values):
        self.writes.append(dict(values))
        self.__dict__.update(values)
        return True


class NullContext(object):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def load_model(filename, module_name):
    odoo = types.ModuleType("odoo")
    odoo.SUPERUSER_ID = 1
    odoo.api = types.SimpleNamespace(Environment=Mock())
    odoo.fields = types.SimpleNamespace(
        Boolean=lambda *a, **k: None, Char=lambda *a, **k: None,
        Datetime=lambda *a, **k: None,
        Many2one=lambda *a, **k: None, Selection=lambda *a, **k: None,
        Text=lambda *a, **k: None)
    odoo.models = types.SimpleNamespace(Model=ModelBase)
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
               "amr_data_sync.tools.utils": utils, module_name: None}
    previous = {key: sys.modules.get(key) for key in modules}
    sys.modules.update({key: value for key, value in modules.items() if value is not None})
    try:
        spec = importlib.util.spec_from_file_location(
            module_name, ADDON / "models" / filename)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module
    finally:
        for key, value in previous.items():
            if value is None:
                sys.modules.pop(key, None)
            else:
                sys.modules[key] = value


class RelatedProcessingDeep15Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model_class = load_model(
            "data_sync_related.py", "amr_data_sync.models.data_sync_related").ExternalDataSyncRelated

    def make(self, **values):
        record = self.model_class()
        record.__dict__.update(values)
        return record

    def test_try_process_data_sets_recursion_context_and_skips_recursive_entry(self):
        env = types.SimpleNamespace(context={})
        child = self.make(process_data=Mock())
        record = self.make(env=env, with_context=Mock(return_value=[child]))

        record.try_process_data()

        record.with_context.assert_called_once_with(
            __process_relation=True, __try_process_relation=True)
        child.process_data.assert_called_once_with()
        recursive = self.make(env=types.SimpleNamespace(context={"__try_process_relation": True}),
                              with_context=Mock())
        self.assertIsNone(recursive.try_process_data())
        recursive.with_context.assert_not_called()

    def test_after_create_processing_is_suppressed_in_both_recursive_contexts(self):
        for context in ({"__process_relation": True}, {"__process_field_after_create": True}):
            record = self.make(env=types.SimpleNamespace(context=context),
                               with_context=Mock())
            self.assertIsNone(record.process_field_after_create())
            record.with_context.assert_not_called()
        process = self.make(env=types.SimpleNamespace(context={}),
                            with_context=Mock(return_value=types.SimpleNamespace(process_data=Mock())))
        delegated = process.with_context.return_value
        process.process_field_after_create()
        process.with_context.assert_called_once_with(
            __process_relation=True, __process_field_after_create=True)
        delegated.process_data.assert_called_once_with()

    def test_matching_external_ids_convert_dict_list_and_integer_by_offset(self):
        strategy = types.SimpleNamespace(internal_id_same_as_external=True, internal_id_offset=10)
        for encoded, expected in (( '{"id": 3}', "13"), ('[4, "Four"]', "14"), ('5', "15")):
            record = self.make(data_json=encoded, field_type="many2one",
                               sync_strategy_id=strategy, state="process")
            record.process_data()
            self.assertEqual(record.internal_data_eval, expected)
            self.assertEqual(record.state, "done")

    def test_matching_many2many_ids_apply_positive_offset(self):
        record = self.make(data_json='[2, 7]', field_type="many2many",
                           sync_strategy_id=types.SimpleNamespace(
                               internal_id_same_as_external=True, internal_id_offset=3))
        record.process_data()
        self.assertEqual(record.internal_data_eval, "[5, 10]")
        self.assertEqual(record.state, "done")

    def test_empty_parent_value_returns_without_creating_a_relation(self):
        record = self.make(data_json='null', field_type="many2one",
                           sync_strategy_id=types.SimpleNamespace(
                               internal_id_same_as_external=False, internal_id_offset=0),
                           related_external_data_sync_id=False, state="process")
        record.process_data()
        self.assertEqual(record.state, "process")
        self.assertFalse(record.related_external_data_sync_id)

    def test_relation_resolution_links_related_record_and_keeps_need_resolve_state(self):
        related = types.SimpleNamespace(state="process", internal_odoo_id=42, process_data=Mock())
        record = self.make(data_json='{"id": 8}', field_type="many2one",
                           sync_strategy_id=types.SimpleNamespace(
                               internal_id_same_as_external=False, internal_id_offset=0),
                           related_external_data_sync_id=related, field_after_create=False,
                           env=types.SimpleNamespace(context={"__process_relation": True},
                               cr=types.SimpleNamespace(savepoint=NullContext)), writes=[])
        record.process_data()
        related.process_data.assert_called_once_with()
        self.assertEqual(record.writes, [{"state": "need_resolve", "internal_data_eval": "42"}])


class ExclusionDeep15Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model_class = load_model(
            "data_sync_exclude.py", "amr_data_sync.models.data_sync_exclude").ExternalDataSyncExclude

    def setUp(self):
        self.model = self.model_class()

    def test_abstract_all_fields_are_collected_and_abstract_model_errors_are_skipped(self):
        abstract = types.SimpleNamespace(_abstract=True, _fields={"name": 1, "parent_id": 1})
        env = {"abstract.mixin": abstract}
        rows = [types.SimpleNamespace(model="abstract.mixin"),
                types.SimpleNamespace(model="broken.mixin")]
        self.model.env = dict(env, **{"broken.mixin": object()})
        self.model.search = Mock(return_value=rows)
        with self.assertLogs("amr_data_sync.models.data_sync_exclude", level="ERROR") as logs:
            result = self.model.get_exclude_all_fields()
        self.assertCountEqual(result, ["name", "parent_id"])
        self.assertEqual(len(logs.output), 1)
        self.assertIn("_abstract", logs.output[0])
        self.model.search.assert_called_once_with([
            ("exclude", "=", "all_fields"), ("active", "=", True)])

    def test_field_exclusions_merge_all_model_fields_and_comma_separated_names(self):
        env = {"abstract.mixin": types.SimpleNamespace(_fields={"shared": 1, "active": 1}),
               "res.partner": object(), "broken.mixin": object()}
        rows_all = [types.SimpleNamespace(model="abstract.mixin"),
                    types.SimpleNamespace(model="broken.mixin")]
        rows_specific = [types.SimpleNamespace(model="res.partner", fields="secret,email")]
        self.model.env = env
        self.model.search = Mock(side_effect=[rows_all, rows_specific])
        with self.assertLogs("amr_data_sync.models.data_sync_exclude", level="ERROR") as logs:
            result = self.model.get_exclude_fields("res.partner")
        self.assertCountEqual(result, ["shared", "active", "secret", "email"])
        self.assertEqual(len(logs.output), 1)
        self.assertIn("_fields", logs.output[0])
        self.assertEqual(self.model.search.call_args_list, [
            unittest.mock.call([("exclude", "=", "all_fields"), ("active", "=", True)]),
            unittest.mock.call([("exclude", "=", "fields"), ("model", "=", "res.partner"),
                                ("active", "=", True)])])

    def test_inactive_or_empty_specific_field_rows_do_not_add_names(self):
        self.model.env = {"res.partner": object()}
        self.model.search = Mock(side_effect=[[], [
            types.SimpleNamespace(model="res.partner", fields="")]])
        self.assertEqual(self.model.get_exclude_fields("res.partner"), [])

    def test_model_exclusion_is_true_only_when_active_match_exists(self):
        self.model.search = Mock(return_value=[object()])
        self.assertTrue(self.model.is_exclude_model("res.partner"))
        self.model.search.assert_called_once_with(
            [("exclude", "=", "model"), ("model", "=", "res.partner"),
             ("active", "=", True)], limit=1)
        self.model.search = Mock(return_value=[])
        self.assertFalse(self.model.is_exclude_model("res.partner"))


if __name__ == "__main__":
    unittest.main()
