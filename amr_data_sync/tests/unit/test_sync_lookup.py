"""Offline unit tests for the real ExternalDataLookup model methods.

The fakes isolate the Odoo registry/recordset boundary; they do not assert ORM,
ACL, database, or installed-registry behavior.
"""
import importlib.util
import pathlib
import sys
import types
import unittest


ADDON = pathlib.Path(__file__).resolve().parents[2]


class FakeOdooModel(object):
    """Minimal inherited hooks used only to observe create/write delegation."""
    def create(self, values):
        return values

    def write(self, values):
        return values


class FakeEnv(dict):
    def __init__(self, models=None, context=None):
        dict.__init__(self, models or {})
        self.context = context or {}


def load_lookup_model():
    """Load data_lookup.py directly with minimal Odoo API stand-ins."""
    odoo = types.ModuleType("odoo")
    odoo._ = lambda value: value
    odoo.api = types.SimpleNamespace(
        depends=lambda *args: lambda method: method,
        model=lambda method: method,
        model_create_multi=lambda method: method,
    )
    odoo.fields = types.SimpleNamespace(
        Boolean=lambda **kwargs: None,
        Char=lambda **kwargs: None,
        Integer=lambda **kwargs: None,
        Many2one=lambda *args, **kwargs: None,
        Reference=lambda **kwargs: None,
    )
    odoo.models = types.SimpleNamespace(Model=FakeOdooModel)
    exceptions = types.ModuleType("odoo.exceptions")

    class UserError(Exception):
        pass

    exceptions.UserError = UserError
    old_odoo = sys.modules.get("odoo")
    old_exceptions = sys.modules.get("odoo.exceptions")
    sys.modules["odoo"] = odoo
    sys.modules["odoo.exceptions"] = exceptions
    try:
        module_name = "amr_data_sync_test_data_lookup"
        spec = importlib.util.spec_from_file_location(
            module_name, ADDON / "models" / "data_lookup.py")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module.ExternalDataLookup, UserError
    finally:
        sys.modules.pop("amr_data_sync_test_data_lookup", None)
        if old_odoo is None:
            sys.modules.pop("odoo", None)
        else:
            sys.modules["odoo"] = old_odoo
        if old_exceptions is None:
            sys.modules.pop("odoo.exceptions", None)
        else:
            sys.modules["odoo.exceptions"] = old_exceptions


class FakeRecord(object):
    def __init__(self, **values):
        self.__dict__.update(values)

    def get_internal_object(self):
        getter = getattr(self, "_internal_object", None)
        return getter() if getter else self

    def __bool__(self):
        return bool(getattr(self, "ids", [True]))

    __nonzero__ = __bool__


class FakeRecords(object):
    def __init__(self, records=()):
        self.records = list(records)

    def __bool__(self):
        return bool(self.records)

    __nonzero__ = __bool__

    def __iter__(self):
        return iter(self.records)

    def ensure_one(self):
        if len(self.records) != 1:
            raise AssertionError("expected exactly one fake record")
        return self.records[0]

    def get_internal_object(self):
        return self.records[0].get_internal_object() if self.records else False


class FakeModel(object):
    def __init__(self, rows=(), results=None):
        self.rows = list(rows)
        self.results = list(results or [])
        self.domains = []

    def search(self, domain, limit=None):
        self.domains.append((list(domain), limit))
        if self.results:
            return self.results.pop(0)
        for row in self.rows:
            if all(self._matches(row, term) for term in domain):
                return FakeRecords([row])
        return FakeRecords()

    @staticmethod
    def _matches(row, term):
        field, operator, value = term
        actual = getattr(row, field, None)
        if operator == "=":
            return actual == value
        if operator == "in":
            return actual in value
        if operator == "not ilike":
            return value.lower() not in (actual or "").lower()
        raise AssertionError("unsupported fake search operator: %s" % operator)


class LookupModelTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model_class, cls.UserError = load_lookup_model()

    def model(self, **values):
        instance = self.model_class()
        for key, value in values.items():
            setattr(instance, key, value)
        return instance

    def test_compute_external_app_name_uses_server_app_and_preserves_manual_value(self):
        with_server = FakeRecord(server_sync_id=FakeRecord(app_name="inventory"),
                                 external_app_name="old")
        manual = FakeRecord(server_sync_id=False, external_app_name="manual")

        self.model_class._compute_external_app_name(FakeRecords([with_server, manual]))

        self.assertEqual(with_server.external_app_name, "inventory")
        self.assertEqual(manual.external_app_name, "manual")

    def test_selection_internal_model_sudos_searches_and_applies_context_whitelist(self):
        metadata = FakeModel(results=[FakeRecords([
            FakeRecord(model="res.partner", name="Contact")])])
        elevated = FakeRecord(search=metadata.search)
        ir_model = FakeRecord(sudo=lambda: elevated)
        instance = self.model(env=FakeEnv({"ir.model": ir_model},
                                          {"allowed_internal_models": ["res.partner"]}))

        choices = instance._selection_internal_model()

        self.assertEqual(choices, [("res.partner", "Contact")])
        self.assertEqual(metadata.domains[0][0][-1], ("model", "in", ["res.partner"]))
        self.assertEqual(metadata.domains[0][0][0], ("transient", "=", False))

    def test_selection_internal_model_omits_whitelist_when_context_value_is_falsey(self):
        metadata = FakeModel(results=[FakeRecords([])])
        instance = self.model(env=FakeEnv({"ir.model": FakeRecord(
            sudo=lambda: FakeRecord(search=metadata.search))}))

        self.assertEqual(instance._selection_internal_model(), [])
        self.assertFalse(any(term[0] == "model" and term[1] == "in"
                             for term in metadata.domains[0][0]))

    def test_create_derives_internal_model_and_id_from_reference(self):
        values = {"internal_ref": "res.partner,42"}
        instance = self.model()

        result = instance.create([values])

        self.assertEqual(result, [values])
        self.assertEqual(values["internal_model"], "res.partner")
        self.assertEqual(values["internal_id"], 42)

    def test_write_derives_reference_and_leaves_values_without_reference_unchanged(self):
        values = {"internal_ref": "res.company,9"}
        instance = self.model()

        self.assertIs(instance.write(values), values)

        self.assertEqual(values["internal_model"], "res.company")
        self.assertEqual(values["internal_id"], 9)
        untouched = {"name": "new label"}
        self.assertIs(instance.write(untouched), untouched)
        self.assertEqual(untouched, {"name": "new label"})

    def test_action_open_internal_returns_form_action_for_ready_record(self):
        instance = self.model(internal_model="res.partner", internal_id=42)
        instance.ensure_one = lambda: None

        result = instance.action_open_internal()

        self.assertEqual(result, {"name": "Lookup Data", "type": "ir.actions.act_window",
                                  "res_model": "res.partner", "res_id": 42,
                                  "view_mode": "form"})

    def test_action_open_internal_rejects_unready_record(self):
        instance = self.model(internal_model=False, internal_id=False)
        instance.ensure_one = lambda: None

        with self.assertRaisesRegex(self.UserError, "Data Not Ready"):
            instance.action_open_internal()

    def test_get_internal_object_browses_reference_target(self):
        target = FakeRecord(ids=[42])
        target_model = FakeRecord(browse=lambda record_id: ("record", record_id))
        instance = self.model(internal_model="res.partner", internal_id=42,
                              env={"res.partner": target_model})

        self.assertEqual(instance.get_internal_object(), ("record", 42))
        self.assertTrue(target)

    def test_lookup_rejects_missing_required_parameters(self):
        instance = self.model()
        for params in ((None, "res.partner", "res.partner"),
                       ("app", None, "res.partner"),
                       ("app", "res.partner", None)):
            with self.subTest(params=params):
                with self.assertRaisesRegex(self.UserError, "Invalid parameter"):
                    instance.lookup_internal(*params)

    def test_lookup_prefers_exact_app_and_matches_external_id_and_display_name(self):
        target = FakeRecord(ids=[7], internal_model="res.partner", internal_id=7)
        row = FakeRecord(external_app_name="app-A", external_model="contact",
                         internal_model="res.partner", internal_id=7,
                         external_id=33, name="Alpha",
                         _internal_object=lambda: target)
        model = FakeModel(rows=[row])
        instance = self.model(env={"res.partner": FakeRecord(browse=lambda record_id: record_id)},
                              search=model.search)

        result = instance.lookup_internal("app-A", "contact", "res.partner", 33, "Alpha")

        self.assertIs(result, target)
        self.assertEqual(model.domains[0][0][:3], [
            ("external_app_name", "=", "app-A"), ("external_model", "=", "contact"),
            ("internal_model", "=", "res.partner")])
        self.assertEqual(model.domains[0][0][-2:], [("external_id", "=", 33),
                                                    ("name", "=", "Alpha")])

    def test_lookup_falls_back_to_external_id_then_name_within_exact_app(self):
        by_id = FakeRecord(ids=[1], internal_model="res.partner", internal_id=1)
        by_name = FakeRecord(ids=[2], internal_model="res.partner", internal_id=2)
        model = FakeModel(results=[FakeRecords([]), FakeRecords([by_id])])
        instance = self.model(search=model.search)

        self.assertIs(instance.lookup_internal("app", "contact", "res.partner", 5, "Beta"),
                      by_id.get_internal_object())
        self.assertEqual(len(model.domains), 2)
        self.assertEqual(model.domains[1][0][-1], ("external_id", "=", 5))

        model = FakeModel(results=[FakeRecords([]), FakeRecords([]), FakeRecords([by_name])])
        instance = self.model(search=model.search)
        self.assertIs(instance.lookup_internal("app", "contact", "res.partner", 5, "Beta"),
                      by_name.get_internal_object())
        self.assertEqual(model.domains[2][0][-1], ("name", "=", "Beta"))

    def test_lookup_uses_wildcard_app_only_after_exact_app_misses(self):
        wildcard = FakeRecord(ids=[4], internal_model="res.partner", internal_id=4)
        model = FakeModel(results=[FakeRecords([]), FakeRecords([wildcard])])
        instance = self.model(search=model.search)

        result = instance.lookup_internal("app", "contact", "res.partner", 5, None)

        self.assertIs(result, wildcard.get_internal_object())
        self.assertEqual(model.domains[0][0][0], ("external_app_name", "=", "app"))
        self.assertEqual(model.domains[1][0][0], ("external_app_name", "=", "*"))

    def test_lookup_returns_empty_browse_when_no_mapping_exists(self):
        model = FakeModel(results=[FakeRecords([]), FakeRecords([])])
        empty = FakeRecord(ids=[])
        target_model = FakeRecord(browse=lambda: empty)
        instance = self.model(search=model.search, env={"res.partner": target_model})

        self.assertIs(instance.lookup_internal("app", "contact", "res.partner", 5, None), empty)


if __name__ == "__main__":
    unittest.main()
