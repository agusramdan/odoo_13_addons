"""Offline behavioral tests for production internal-data/res model methods.

These tests load the real source modules and fake only Odoo's recordset/API
boundary. They do not exercise a live registry, ORM, ACLs, or persistence.
"""
import importlib.util
import pathlib
import sys
import types
import unittest


ADDON = pathlib.Path(__file__).resolve().parents[2]


class FakeModelBase(object):
    pass


class FakeAbstractModel(FakeModelBase):
    pass


class FakeRecord(object):
    def __init__(self, **values):
        self.__dict__.update(values)

    def get_internal_object(self):
        return getattr(self, "internal_object", self)

    def __bool__(self):
        return bool(getattr(self, "ids", [True]))

    __nonzero__ = __bool__


class FakeRecordset(object):
    def __init__(self, record=None):
        self.record = record

    def get_internal_object(self):
        return self.record.get_internal_object() if self.record else False

    def __bool__(self):
        return self.record is not None

    __nonzero__ = __bool__


class FakeSearchModel(object):
    def __init__(self, result=None):
        self.result = result or FakeRecordset()
        self.calls = []

    def search(self, domain, limit=None):
        self.calls.append((domain, limit))
        return self.result


class FakeStrategy(object):
    def __init__(self, **values):
        self.__dict__.update(values)


class FakeEnv(dict):
    pass


def load_source(relative_path, module_name, odoo_module, injected=None):
    package_names = ("amr_data_sync", "amr_data_sync.models", "amr_data_sync.tools")
    names = ("odoo", "odoo.api", "amr_data_sync.tools.utils") + package_names
    previous = {key: sys.modules.get(key) for key in names}
    for package_name, package_path in (("amr_data_sync", ADDON),
                                       ("amr_data_sync.models", ADDON / "models"),
                                       ("amr_data_sync.tools", ADDON / "tools")):
        package = types.ModuleType(package_name)
        package.__path__ = [str(package_path)]
        sys.modules[package_name] = package
    utils = types.ModuleType("amr_data_sync.tools.utils")
    utils.convert_from_external_data = lambda item: (
        {"id": item} if isinstance(item, int) else
        ({"id": item[0], "display_name": item[1]} if isinstance(item, list) and len(item) > 1 else
         ({"id": item[0]} if isinstance(item, list) and item else (item if isinstance(item, dict) else {}))))
    if injected:
        for key, value in injected.items():
            setattr(utils, key, value)
    api = types.ModuleType("odoo.api")
    api.model = lambda method: method
    odoo_module.api = api
    odoo_module.models = types.SimpleNamespace(Model=FakeModelBase, AbstractModel=FakeAbstractModel,
                                               TransientModel=FakeModelBase)
    sys.modules["odoo"] = odoo_module
    sys.modules["odoo.api"] = api
    sys.modules["amr_data_sync.tools.utils"] = utils
    try:
        spec = importlib.util.spec_from_file_location(module_name, ADDON / relative_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        for key, value in previous.items():
            if value is None:
                sys.modules.pop(key, None)
            else:
                sys.modules[key] = value


def load_internal_data():
    return load_source("models/internal_data.py", "amr_data_sync.models.internal_data_test", types.ModuleType("odoo"))


def load_res_model(filename, module_name):
    return load_source("models/" + filename, module_name, types.ModuleType("odoo"))


class InternalDataMixinTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.models = load_internal_data()

    def test_name_mixin_looks_up_name_or_display_name_and_returns_empty_on_miss(self):
        found = FakeRecordset(FakeRecord(ids=[8]))
        for item, name in (({"name": "Acme"}, "Acme"), ([8, "Display"], "Display")):
            search = FakeSearchModel(found)
            model = self.models.InternalDataNameMixin()
            model.search = search.search
            self.assertIs(model.lookup_internal_from_external_data(item), found)
            self.assertEqual(search.calls, [([("name", "=", name)], 1)])

        model = self.models.InternalDataNameMixin()
        empty = FakeRecordset()
        model.browse = lambda: empty
        self.assertIs(model.lookup_internal_from_external_data({"id": 9}), empty)

    def test_name_mixin_delegates_when_external_item_has_no_name(self):
        delegated = FakeRecordset(FakeRecord(ids=[5]))

        class Parent(FakeModelBase):
            def lookup_internal_from_external_data(self, item, **kwargs):
                return delegated

        class Combined(self.models.InternalDataNameMixin, Parent):
            pass

        self.assertIs(Combined().lookup_internal_from_external_data({"id": 5}), delegated)

    def test_default_mixin_prefers_existing_mapping_and_returns_internal_object(self):
        target = FakeRecord(ids=[42])
        mapping = FakeRecord(internal_object=target)
        lookup = FakeSearchModel(FakeRecordset(mapping))
        external_sync = types.SimpleNamespace(search=lookup.search)
        model = self.models.InternalDataDefaultMixin()
        model.env = FakeEnv({"external.data.sync": external_sync})
        model.browse = lambda: FakeRecordset()
        strategy = FakeStrategy(id=3, internal_id_same_as_external=False)

        self.assertIs(model.lookup_internal_from_external_data({"id": "ext-1"},
                                                                sync_strategy=strategy), target)
        self.assertEqual(lookup.calls[0][0], [("external_id", "=", "ext-1"),
                                              ("sync_strategy_id", "=", 3)])

    def test_default_mixin_uses_same_id_strategy_then_parent_fallback(self):
        expected = FakeRecordset(FakeRecord(ids=[17]))
        lookup = FakeSearchModel()
        external_sync = types.SimpleNamespace(search=lookup.search)
        strategy = FakeStrategy(id=4, internal_id_same_as_external=True,
                                internal_model="res.partner",
                                get_internal_id_same_as_external=lambda item: 17)
        model = self.models.InternalDataDefaultMixin()
        model._name = "res.partner"
        model.env = FakeEnv({"external.data.sync": external_sync})
        model.browse = lambda: FakeRecordset()
        model.search = lambda domain, limit=None: expected
        self.assertIs(model.lookup_internal_from_external_data([17, "x"], sync_strategy=strategy), expected)

        class Parent(FakeModelBase):
            def lookup_internal_from_external_data(self, item, **kwargs):
                return expected

        class Combined(self.models.InternalDataDefaultMixin, Parent):
            def browse(self):
                return FakeRecordset()

        self.assertIs(Combined().lookup_internal_from_external_data({"id": 1}), expected)

    def test_internal_data_only_sudos_allowed_record_id_one(self):
        model = self.models.InternalData()
        empty = FakeRecordset()
        elevated = types.SimpleNamespace(browse=lambda record_id: ("sudo-record", record_id))
        model.sudo = lambda: elevated
        model.browse = lambda: empty

        self.assertEqual(model.lookup_internal_from_external_data(1), ("sudo-record", 1))
        self.assertIs(model.lookup_internal_from_external_data(2), empty)


class ResLookupModelsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bank = load_res_model("res_bank.py", "test_res_bank").Bank
        cls.partner = load_res_model("res_partner.py", "test_res_partner").ResPartnerUsers
        cls.users = load_res_model("res_users.py", "test_res_users").ResUsers

    def test_bank_lookup_accepts_name_dict_or_external_tuple_and_sudos_search(self):
        for item in ({"name": "Bank"}, [7, "Bank"]):
            result = FakeRecordset(FakeRecord(ids=[1]))
            search = FakeSearchModel(result)
            model = self.bank()
            model.sudo = lambda: types.SimpleNamespace(search=search.search)
            model.browse = lambda: FakeRecordset()
            self.assertIs(model.lookup_internal_from_external_data(item), result)
            self.assertEqual(search.calls, [([("name", "=", "Bank")], 1)])

    def test_bank_without_name_returns_empty_browse_without_search(self):
        empty = FakeRecordset()
        model = self.bank()
        model.sudo = lambda: self.fail("sudo search should not run without a name")
        model.browse = lambda: empty
        self.assertIs(model.lookup_internal_from_external_data([10]), empty)

    def test_partner_lookup_searches_by_email_and_empty_input_returns_empty(self):
        result = FakeRecordset(FakeRecord(ids=[2]))
        search = FakeSearchModel(result)
        model = self.partner()
        model.sudo = lambda: types.SimpleNamespace(search=search.search)
        empty = FakeRecordset()
        model.browse = lambda: empty
        self.assertIs(model.lookup_internal_from_external_data({"email": "a@example.test"}), result)
        self.assertEqual(search.calls, [([("email", "=", "a@example.test")], 1)])
        self.assertIs(model.lookup_internal_from_external_data(None), empty)

    def test_user_lookup_prioritizes_builtin_id_then_email_then_login(self):
        model = self.users()
        browsed = []
        result = FakeRecordset(FakeRecord(ids=[1]))
        search = FakeSearchModel(result)
        model.sudo = lambda: types.SimpleNamespace(browse=lambda record_id: browsed.append(record_id) or result,
                                                  search=search.search)
        model.browse = lambda: FakeRecordset()
        self.assertIs(model.lookup_internal_from_external_data([2, "Builtin"]), result)
        self.assertEqual(browsed, [2])
        self.assertIs(model.lookup_internal_from_external_data({"email": "u@example.test", "login": "u"}), result)
        self.assertEqual(search.calls[-1], ([('email', '=', 'u@example.test')], 1))
        self.assertIs(model.lookup_internal_from_external_data({"login": "user"}), result)
        self.assertEqual(search.calls[-1], ([('login', '=', 'user')], 1))


class ResNameModelTest(unittest.TestCase):
    def test_small_named_res_models_declare_name_mixin_inheritance(self):
        for filename, module_name, class_name, model_name in (
                ("res_country.py", "test_res_country", "ResCountry", "res.country"),
                ("res_currency.py", "test_res_currency", "ResCurrency", "res.currency"),
                ("res_lang.py", "test_res_lang", "ResLang", "res.lang"),
                ("res_company.py", "test_res_company", "ResCompany", "res.company")):
            cls = getattr(load_res_model(filename, module_name), class_name)
            with self.subTest(model=model_name):
                self.assertEqual(cls._name, model_name)
                self.assertEqual(cls._inherit, [model_name, "internal.data.name.mixin"])


if __name__ == "__main__":
    unittest.main()
