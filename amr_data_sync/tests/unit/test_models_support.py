"""Offline behavior tests for support models (no Odoo registry/database)."""
import datetime
import importlib.util
import pathlib
import sys
import types
import unittest


ADDON = pathlib.Path(__file__).resolve().parents[2]


class ModelBase(object):
    def create(self, values):
        return values

    def write(self, values):
        return True

    def with_context(self, **kwargs):
        self._context = kwargs
        return self

    def __iter__(self):
        return iter([self])


class BaseModel(ModelBase):
    pass


class Field(object):
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs


def identity_decorator(*args, **kwargs):
    if args and callable(args[0]) and len(args) == 1 and not kwargs:
        return args[0]
    return lambda method: method


def load_model(filename, module_name, include_utils=False):
    """Load the actual support-model module with narrow Odoo import doubles."""
    odoo = types.ModuleType("odoo")
    odoo.__path__ = []
    odoo.api = types.SimpleNamespace(
        depends=identity_decorator, model=identity_decorator,
        model_create_multi=identity_decorator,
        returns=lambda *args, **kwargs: identity_decorator,
    )
    odoo.fields = types.SimpleNamespace(
        Boolean=Field, Many2one=Field, Char=Field, Integer=Field,
        Selection=Field, Datetime=Field,
    )
    odoo.models = types.SimpleNamespace(Model=ModelBase, BaseModel=BaseModel)
    previous = {name: sys.modules.get(name) for name in (
        "odoo", "odoo.addons", "odoo.addons.amr_data_sync",
        "odoo.addons.amr_data_sync.tools",
        "odoo.addons.amr_data_sync.tools.utils")}
    sys.modules["odoo"] = odoo
    if include_utils:
        addons = types.ModuleType("odoo.addons")
        addons.__path__ = []
        addon_package = types.ModuleType("odoo.addons.amr_data_sync")
        addon_package.__path__ = [str(ADDON)]
        tools = types.ModuleType("odoo.addons.amr_data_sync.tools")
        tools.__path__ = [str(ADDON / "tools")]
        utils = types.ModuleType("odoo.addons.amr_data_sync.tools.utils")
        utils.convert_from_external_data = lambda value: value
        sys.modules.update({"odoo.addons": addons,
                            "odoo.addons.amr_data_sync": addon_package,
                            "odoo.addons.amr_data_sync.tools": tools,
                            "odoo.addons.amr_data_sync.tools.utils": utils})
    try:
        path = ADDON / "models" / filename
        spec = importlib.util.spec_from_file_location(module_name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        for name, value in previous.items():
            if value is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = value


class Record(object):
    def __init__(self, **values):
        self.__dict__.update(values)

    def __bool__(self):
        return bool(getattr(self, "ids", [True]))

    __nonzero__ = __bool__


class Records(list):
    def __bool__(self):
        return bool(len(self))

    __nonzero__ = __bool__

    def __getattr__(self, name):
        if name == "company_id" and len(self) == 1:
            return self[0].company_id
        raise AttributeError(name)


class SearchModel(object):
    def __init__(self, results=()):
        self.results = list(results)
        self.domains = []

    def search(self, domain, limit=None, **kwargs):
        self.domains.append((domain, limit))
        return self.results.pop(0) if self.results else Records()


class DataCompanyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model_class = load_model("data_company.py", "test_data_company_support", True).ExternalDataLookup

    def test_lookup_company_returns_matching_company_and_queries_app_key(self):
        company = Record(id=19)
        result = Records([Record(company_id=company)])
        search = SearchModel([result])
        model = self.model_class()
        model.search = search.search

        self.assertIs(model.lookup_company({"id": 8}, external_app_name="billing"), company)
        self.assertEqual(search.domains, [([("external_id", "=", 8),
                                           ("external_app_name", "=", "billing")], 1)])

    def test_lookup_company_resolves_app_from_server_after_initial_miss(self):
        company = Record(id=4)
        search = SearchModel([Records(), Records([Record(company_id=company)])])
        model = self.model_class()
        model.search = search.search
        server = Record(get_application_name=lambda: "resolved-app")

        self.assertIs(model.lookup_company({"id": 11}, server_sync=server,
                                           external_app_name="old-app"), company)
        self.assertEqual(search.domains[0][0][1], ("external_app_name", "=", "old-app"))
        self.assertEqual(search.domains[1][0][1], ("external_app_name", "=", "resolved-app"))

    def test_reverse_mapping_partitions_found_and_unmapped_company_ids(self):
        rows = Records([Record(company_id=Record(id=2), external_id=22),
                        Record(company_id=Record(id=2), external_id=23)])
        model = self.model_class()
        model.search = lambda domain: rows
        internal = BaseModel()
        internal.ids = [1, 2, 3]

        mapping, unmapped = model.reverse_mapping(internal, external_app_name="app")

        self.assertEqual(mapping, {2: [22, 23]})
        self.assertEqual(unmapped, {1, 3})

    def test_reverse_mapping_rejects_non_recordset_when_requested(self):
        model = self.model_class()
        with self.assertRaisesRegex(ValueError, "Internal Object must"):
            model.reverse_mapping([1], external_app_name="app")


class ExclusionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model_class = load_model("data_sync_exclude.py", "test_data_sync_exclude_support").ExternalDataSyncExclude

    def test_field_exclusions_combine_active_global_and_model_specific_entries(self):
        env = {"abstract.base": Record(_fields={"id": 1, "name": 1}),
               "res.partner": Record(_fields={"email": 1})}
        model = self.model_class()
        model.env = env
        results = [Records([Record(model="abstract.base")]),
                   Records([Record(model="res.partner", fields="email,phone")])]
        seen = []

        def search(domain):
            seen.append(domain)
            return results.pop(0)

        model.search = search
        excluded = model.get_exclude_fields("res.partner")
        self.assertEqual(set(excluded), {"id", "name", "email", "phone"})
        self.assertEqual(seen[0], [("exclude", "=", "all_fields"), ("active", "=", True)])
        self.assertEqual(seen[1], [("exclude", "=", "fields"),
                                   ("model", "=", "res.partner"), ("active", "=", True)])

    def test_all_fields_helper_only_includes_abstract_models(self):
        model = self.model_class()
        model.env = {"abstract.base": Record(_abstract=True, _fields={"x": 1}),
                     "concrete": Record(_abstract=False, _fields={"y": 1})}
        model.search = lambda domain: Records([Record(model="abstract.base"),
                                                Record(model="concrete")])
        self.assertEqual(model.get_exclude_all_fields(), ["x"])

    def test_is_exclude_model_uses_active_model_filter_and_limit(self):
        model = self.model_class()
        calls = []
        model.search = lambda domain, limit=None: calls.append((domain, limit)) or Records([Record()])
        self.assertTrue(model.is_exclude_model("res.partner"))
        self.assertEqual(calls, [([("exclude", "=", "model"),
                                   ("model", "=", "res.partner"), ("active", "=", True)], 1)])


class ServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model_class = load_model("data_sync_server.py", "test_data_sync_server_support").ExternalServerSync

    def test_endpoint_and_application_name_delegate_to_configured_values(self):
        server = self.model_class()
        server.app_name = "warehouse"
        server.base_url = "https://sync.example.invalid"
        self.assertEqual(server.get_application_name(), "warehouse")
        self.assertEqual(server.get_endpoint_url(), "https://sync.example.invalid")

    def test_create_remote_model_passes_server_model_and_options_to_client(self):
        server = self.model_class()
        server.env = {"service.client": Record(get_remote_object=lambda *args, **kwargs:
                                                 (args, kwargs))}
        result = server.create_remote_model("res.partner", timeout=12)
        self.assertEqual(result, ((server, "res.partner"), {"timeout": 12}))


class CronTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model_class = load_model("data_sync_cron.py", "test_data_sync_cron_support").ExternalDataSyncCron

    def test_create_enables_internal_cron_context_for_parent_create(self):
        cron = self.model_class()
        cron.with_context = lambda **kwargs: (setattr(cron, "_context", kwargs) or cron)
        cron.create = self.model_class.create.__get__(cron, self.model_class)
        values = [{"active": True}]
        self.assertIs(cron.create(values), values)
        self.assertEqual(cron._context, {"__from_sync_cron": True})

    def test_write_propagates_active_change_to_strategy_and_skips_cron_context(self):
        cron = self.model_class()
        strategy = Record(sync_cron=False, writes=[])
        strategy.write = lambda values: (strategy.writes.append(dict(values)),
                                          setattr(strategy, "sync_cron", values["sync_cron"]))[0]
        cron._context = {}
        cron.sync_strategy_id = strategy
        cron.active = True
        cron.write = self.model_class.write.__get__(cron, self.model_class)
        parent_calls = []

        class Parent(object):
            def write(self, values):
                parent_calls.append(dict(values))
                return True

        # The production method explicitly calls super(); supply that parent in its MRO
        # through a temporary subclass with an observable base implementation.
        class ParentModel(object):
            def write(self, values):
                parent_calls.append(dict(values))
                return True

        class CronWithParent(self.model_class, ParentModel):
            pass

        cron = CronWithParent()
        cron._context = {}
        cron.sync_strategy_id = strategy
        cron.active = True
        self.assertTrue(cron.write({"active": True}))
        self.assertEqual(strategy.writes, [{"sync_cron": True}])
        cron._context = {"__from_sync_cron": True}
        cron.write({"active": False})
        self.assertEqual(strategy.writes, [{"sync_cron": True}])

    def test_action_sync_now_delegates_to_related_strategy(self):
        cron = self.model_class()
        calls = []
        cron.sync_strategy_id = Record(action_sync_now=lambda: calls.append("sync"))
        cron.action_sync_now()
        self.assertEqual(calls, ["sync"])

    def test_cron_sync_updates_schedule_even_when_remote_sync_fails(self):
        class DateTimeField(object):
            @staticmethod
            def now():
                return datetime.datetime(2024, 1, 2, 3, 4, 5)

        module = load_model("data_sync_cron.py", "test_data_sync_cron_clock")
        module.fields.Datetime = DateTimeField
        model_class = module.ExternalDataSyncCron
        cron = model_class()
        cron.sync_strategy_id = Record(sync_from_application_server=lambda: (_ for _ in ()).throw(ValueError("offline")),
                                       is_delete_able_from_external=lambda: False)
        cron.external_app_name = "app"
        cron.external_model = "res.partner"
        writes = []
        cron.write = lambda values: writes.append(values)
        cron.env = {}

        cron.cron_sync_from_server()

        self.assertEqual(writes, [{"last_sync_datetime": datetime.datetime(2024, 1, 2, 3, 4, 5),
                                   "next_sync_datetime": datetime.datetime(2024, 1, 2, 4, 4, 5)}])


if __name__ == "__main__":
    unittest.main()
