"""Additional offline tests for production ExternalDataSyncRelated methods.

Odoo's registry/recordsets are replaced only at the boundary; model methods
are loaded from the production module. No ORM or persistence claims are made.
"""
import importlib.util
import pathlib
import sys
import types
import unittest
from unittest.mock import Mock

ADDON = pathlib.Path(__file__).resolve().parents[2]


class FakeModelBase(object):
    def write(self, values):
        self.writes.append(dict(values))
        for key, value in values.items():
            setattr(self, key, value)
        return True


def load_model():
    odoo = types.ModuleType("odoo")
    odoo.SUPERUSER_ID = 1
    odoo.api = types.SimpleNamespace(Environment=Mock())
    datetime_field = lambda *a, **k: None
    datetime_field.now = lambda: "now"
    odoo.fields = types.SimpleNamespace(
        Boolean=lambda *a, **k: None, Char=lambda *a, **k: None,
        Datetime=datetime_field,
        Many2one=lambda *a, **k: None, Selection=lambda *a, **k: None,
        Text=lambda *a, **k: None)
    odoo.models = types.SimpleNamespace(Model=FakeModelBase)
    tools = types.ModuleType("odoo.tools")
    tools.date_utils = types.SimpleNamespace(json_default=lambda value: str(value))
    package = types.ModuleType("amr_data_sync")
    package.__path__ = [str(ADDON)]
    models_package = types.ModuleType("amr_data_sync.models")
    models_package.__path__ = [str(ADDON / "models")]
    tool_package = types.ModuleType("amr_data_sync.tools")
    tool_package.__path__ = [str(ADDON / "tools")]
    utils = types.ModuleType("amr_data_sync.tools.utils")
    utils.is_callable_method = lambda model, name: callable(getattr(model, name, None))
    names = ("odoo", "odoo.tools", "amr_data_sync", "amr_data_sync.models",
             "amr_data_sync.tools", "amr_data_sync.tools.utils",
             "amr_data_sync.models.data_sync_related")
    previous = dict((name, sys.modules.get(name)) for name in names)
    sys.modules.update({"odoo": odoo, "odoo.tools": tools,
                        "amr_data_sync": package, "amr_data_sync.models": models_package,
                        "amr_data_sync.tools": tool_package,
                        "amr_data_sync.tools.utils": utils})
    try:
        name = "amr_data_sync.models.data_sync_related"
        spec = importlib.util.spec_from_file_location(
            name, ADDON / "models" / "data_sync_related.py")
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        return module.ExternalDataSyncRelated
    finally:
        for name, old in previous.items():
            if old is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = old


class Record(object):
    def __init__(self, **values):
        self.__dict__.update(values)

    def __bool__(self):
        return bool(getattr(self, "ids", [True]))

    __nonzero__ = __bool__

    def __int__(self):
        return self.id

    def write(self, values):
        self.writes.append(dict(values))
        for key, value in values.items():
            setattr(self, key, value)
        return True


class SyncRelatedMoreTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model_class = load_model()

    def model(self, **values):
        result = self.model_class()
        for key, value in values.items():
            setattr(result, key, value)
        return result

    def test_create_or_get_related_creates_parent_for_same_internal_model(self):
        created = Record(id=16)
        parent = Record(id=8, internal_model="res.partner")
        related = self.model(search=Mock(return_value=False),
                             create_parent=Mock(return_value=created))

        result = related.create_or_get_related(
            parent, "partner_id", "many2one", related_external_data_sync_id=21,
            internal_model="res.partner", value={"id": 3})

        self.assertIs(result, created)
        related.create_parent.assert_called_once_with(
            "partner_id", parent, {"id": 3})

    def test_create_or_get_related_creates_new_draft_for_unlinked_field(self):
        created = Record(id=19)
        related = self.model(search=Mock(return_value=False),
                             create=Mock(return_value=[created]))
        parent = Record(id=8, internal_model="res.partner")

        result = related.create_or_get_related(parent, "note", "char", value="memo")

        self.assertIs(result, created)
        related.create.assert_called_once_with([{
            "name": "note", "external_data_sync_id": 8, "state": "draft",
            "field_after_create": False, "field_type": "char",
            "internal_model": None, "data_json": '"memo"'}])

    def test_process_data_defers_many2many_with_unresolved_related_record(self):
        strategy = Record(internal_id_same_as_external=False,
                          get_or_create_relation_from_external=Mock(
            return_value=[Record(internal_odoo_id=31, state="done"),
                          Record(internal_odoo_id=False, state="process")]))
        related = self.model(data_json='[{"id": 1}, {"id": 2}]',
                             field_type="many2many", sync_strategy_id=strategy,
                             writes=[])

        related.process_data()

        self.assertEqual(related.writes, [{"state": "process", "internal_data_eval": None}])
        strategy.get_or_create_relation_from_external.assert_called_once_with(
            [{"id": 1}, {"id": 2}], related)

    def test_get_data_relation_reads_linked_many2one_internal_id(self):
        linked = Record(internal_odoo_id=47)
        related = self.model(state="done", field_type="many2one",
                             related_external_data_sync_id=linked,
                             internal_data_eval="99")

        self.assertEqual(related.get_data_relation(), 47)

    def test_internal_lookup_passes_dict_id_and_display_name_to_lookup_model(self):
        lookup = Record(lookup_internal=Mock(return_value=False))
        internal_model = Record(sudo=lambda: Record())
        related = self.model(internal_model="res.partner", external_app_name="crm",
                             env={"external.data.lookup": lookup,
                                  "res.partner": internal_model})

        result = related.internal_lookup({"id": 12, "display_name": "Ada"})

        self.assertFalse(result)
        lookup.lookup_internal.assert_called_once_with(
            "crm", "res.partner", "res.partner", external_id=12,
            display_name="Ada")


if __name__ == "__main__":
    unittest.main()
