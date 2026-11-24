"""Offline unit tests for real ExternalDataSyncStrategy behavior.

Only Odoo's import/recordset boundary and utility dependencies are faked;
production strategy methods are loaded and invoked directly.
"""
import importlib.util
import pathlib
import sys
import types
import unittest


ADDON = pathlib.Path(__file__).resolve().parents[2]


class FakeModel(object):
    pass


def load_strategy_class():
    odoo = types.ModuleType("odoo")
    odoo.__path__ = []
    odoo._ = lambda value: value

    class Field(object):
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs

    class API(object):
        @staticmethod
        def depends(*args):
            return lambda method: method

        @staticmethod
        def model(method):
            return method

        @staticmethod
        def model_create_multi(method):
            return method

        @staticmethod
        def returns(*args, **kwargs):
            return lambda method: method

    odoo.api = API
    odoo.fields = types.SimpleNamespace(
        Boolean=Field, Char=Field, Datetime=Field, Integer=Field,
        Many2many=Field, Many2one=Field, One2many=Field,
        Selection=Field, Text=Field,
    )
    odoo.models = types.SimpleNamespace(Model=FakeModel, BaseModel=FakeModel)
    exceptions = types.ModuleType("odoo.exceptions")

    class UserError(Exception):
        pass

    exceptions.UserError = UserError
    tools = types.ModuleType("odoo.tools")
    safe_eval_module = types.ModuleType("odoo.tools.safe_eval")

    def safe_eval(script, context, mode=None, nocopy=None):
        exec(script, context)

    safe_eval_module.safe_eval = safe_eval
    tools.safe_eval = safe_eval
    addon_name = "amr_data_sync"
    models_name = addon_name + ".models"
    tools_name = addon_name + ".tools"
    utils_name = tools_name + ".utils"
    utils = types.ModuleType(utils_name)
    utils.call_with_savepoint = lambda *args, **kwargs: None
    utils.convert_from_external_data = lambda data: data
    utils.get_callable_method = lambda obj, name: getattr(obj, name)
    utils.is_callable_method = lambda obj, name: callable(getattr(obj, name, None))
    utils.safe_call_method = lambda obj, name, kwargs=None: getattr(obj, name)(**(kwargs or {}))

    names = ("odoo", "odoo.exceptions", "odoo.tools", "odoo.tools.safe_eval",
             addon_name, models_name, tools_name, utils_name)
    previous = dict((name, sys.modules.get(name)) for name in names)
    for name, path in ((addon_name, ADDON), (models_name, ADDON / "models"),
                       (tools_name, ADDON / "tools")):
        package = types.ModuleType(name)
        package.__path__ = [str(path)]
        sys.modules[name] = package
    sys.modules.update({"odoo": odoo, "odoo.exceptions": exceptions,
                        "odoo.tools": tools, "odoo.tools.safe_eval": safe_eval_module,
                        utils_name: utils})
    try:
        module_name = models_name + ".data_sync_strategy"
        spec = importlib.util.spec_from_file_location(
            module_name, ADDON / "models" / "data_sync_strategy.py")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module.ExternalDataSyncStrategy, UserError
    finally:
        sys.modules.pop(models_name + ".data_sync_strategy", None)
        for name, old in previous.items():
            if old is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = old


class StrategyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.strategy_class, cls.UserError = load_strategy_class()

    def strategy(self, **values):
        strategy = self.strategy_class()
        strategy.__dict__.update(values)
        strategy.ensure_one = lambda: None
        return strategy

    def test_relation_ignore_helpers_are_cumulative(self):
        cases = {
            "ignore": (True, True, True, True),
            "to_many_ignore": (False, True, True, True),
            "parent_ignore": (False, False, True, True),
            "to_one_ignore": (False, False, False, True),
            "all_process": (False, False, False, False),
        }
        for mode, expected in cases.items():
            with self.subTest(mode=mode):
                strategy = self.strategy(relation_strategy=mode)
                self.assertEqual((strategy.is_relation_ignore(),
                                  strategy.is_relation_to_many_ignore(),
                                  strategy.is_relation_parent_ignore(),
                                  strategy.is_relation_to_one_ignore()), expected)

    def test_field_list_helpers_trim_entries_and_handle_empty_values(self):
        strategy = self.strategy(external_fields=" name, code ,, ",
                                 internal_lookup_fields=" sku, barcode ",
                                 after_create_fields=" parent_id, child_ids ")
        self.assertEqual(strategy.get_include_fields(), ["name", "code", "", ""])
        self.assertEqual(strategy.get_external_fields(), ["name", "code", "", ""])
        self.assertEqual(strategy.get_internal_lookup_fields(), ["sku", "barcode"])
        self.assertEqual(strategy.get_after_create_fields(), ["parent_id", "child_ids"])
        empty = self.strategy(external_fields=False, internal_lookup_fields=None,
                              after_create_fields="")
        self.assertEqual(empty.get_include_fields(), [])
        self.assertEqual(empty.get_external_fields(), [])
        self.assertEqual(empty.get_internal_lookup_fields(), [])
        self.assertEqual(empty.get_after_create_fields(), [])

    def test_sync_capability_predicates_match_each_strategy(self):
        expected = {
            "external_event": (True, True, True, True),
            "external_push": (True, True, True, True),
            "external_cud": (True, True, False, True),
            "external_cu": (False, True, False, True),
            "external_create": (False, False, False, True),
            "external_update": (False, True, True, False),
            "local_lookup": (False, False, False, False),
        }
        for mode, capabilities in expected.items():
            with self.subTest(mode=mode):
                strategy = self.strategy(strategy=mode)
                self.assertEqual((strategy.is_delete_able_from_external(),
                                  strategy.is_update_able_from_external(),
                                  strategy.is_update_only_from_external(),
                                  strategy.is_create_able_from_external()), capabilities)

    def test_external_context_and_sync_config_parse_configured_literals(self):
        strategy = self.strategy(external_context="{'lang': 'id_ID'}",
                                 external_domain="[('active', '=', True)]",
                                 external_fields="name, code")
        self.assertEqual(strategy.get_external_context(), {"lang": "id_ID"})
        self.assertEqual(strategy.prepare_sync_one_dict(), {
            "fields": ["name", "code", "write_date", "company_id"],
            "context": {"lang": "id_ID"},
            "domain": [("active", "=", True)],
        })
        defaulted = self.strategy(external_context="", external_domain="", external_fields=False)
        self.assertEqual(defaulted.get_external_context(), {})
        self.assertEqual(defaulted.prepare_sync_one_dict(), {
            "fields": None, "context": {}, "domain": []})

    def test_external_context_rejects_non_literal_expressions(self):
        strategy = self.strategy(external_context="__import__('os').getcwd()")
        with self.assertRaises(ValueError):
            strategy.get_external_context()

    def test_same_as_external_id_offset_requires_enabled_flag(self):
        strategy = self.strategy(internal_id_offset=100, internal_id_same_as_external=True)
        self.assertEqual(strategy.get_internal_id_same_as_external({"id": 5}), 105)
        self.assertEqual(strategy.get_internal_id_same_as_external([7, "Seven"]), 107)
        strategy.internal_id_same_as_external = False
        self.assertIsNone(strategy.get_internal_id_same_as_external({"id": 5}))

    def test_lookup_by_external_id_uses_offset_only_when_enabled(self):
        strategy = self.strategy(id=4, internal_id_offset=3,
                                 internal_id_same_as_external=True)
        class SearchModel(object):
            def __init__(self):
                self.domains = []
            def search(self, domain, limit=None):
                self.domains.append(domain)
                return types.SimpleNamespace(internal_odoo_id=False)
        sync_model = SearchModel()
        strategy.env = {"external.data.sync": sync_model}
        self.assertEqual(strategy.get_internal_id_from_external_id(9), 12)
        self.assertEqual(sync_model.domains[0], [
            ("sync_strategy_id", "=", 4), ("external_odoo_id", "=", 9)])
        strategy.internal_id_same_as_external = False
        self.assertIsNone(strategy.get_internal_id_from_external_id(9))
        self.assertIsNone(strategy.get_internal_id_from_external_id(False))

    def test_external_id_lookup_prefers_existing_strategy_mapping(self):
        strategy = self.strategy(id=4, external_app_name="app", external_model="remote",
                                 internal_model="res.partner", internal_id_same_as_external=False)
        mapped = types.SimpleNamespace(internal_odoo_id=28)
        class SearchModel(object):
            def __init__(self):
                self.domains = []
            def search(self, domain, limit=None):
                self.domains.append(domain)
                return mapped if len(self.domains) == 1 else None
        sync_model = SearchModel()
        strategy.env = {"external.data.sync": sync_model}
        self.assertEqual(strategy.get_internal_id_from_external_id(9), 28)
        self.assertEqual(len(sync_model.domains), 1)

    def test_eval_script_updates_prepare_dictionary_and_wraps_failures(self):
        strategy = self.strategy(eval_script="prepare['mapped'] = external_data['value'] * 2",
                                 internal_model="res.partner", env={"res.partner": object()})
        self.assertEqual(strategy.execute_prepare_eval({"value": 6}, {"existing": True}),
                         {"existing": True, "mapped": 12})
        strategy.eval_script = "raise RuntimeError('bad script')"
        with self.assertRaisesRegex(ValueError, "Error evaluating script"):
            strategy.execute_prepare_eval({}, {})
        strategy.eval_script = "  "
        original = {"keep": 1}
        self.assertIs(strategy.execute_prepare_eval({}, original), original)

    def test_action_test_execute_requires_selected_sync_data(self):
        strategy = self.strategy(test_external_data_sync_id=False)
        with self.assertRaisesRegex(self.UserError, "Please select one data"):
            strategy.action_test_execute_eval({}, {})


if __name__ == "__main__":
    unittest.main()
