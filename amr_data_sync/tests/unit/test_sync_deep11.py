"""Focused behavioral coverage for ExternalDataSync sync and dedupe paths.

Production methods execute directly; fakes isolate only ORM/recordset boundaries.
"""
import importlib.util
import pathlib
import types
import unittest
from unittest.mock import Mock


_HELPER = pathlib.Path(__file__).with_name("test_sync_core.py")
_SPEC = importlib.util.spec_from_file_location("sync_deep11_core_helpers", _HELPER)
_HELPERS = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_HELPERS)
ExternalDataSync, _utils = _HELPERS.load_sync_model()


class RelatedCollection(object):
    def __init__(self, records=(), created=None):
        self.records = list(records)
        self.created = created
        self.create_args = None

    def filtered(self, predicate):
        return _HELPERS.FakeRecords([record for record in self.records if predicate(record)])

    def create_or_get_related(self, *args, **kwargs):
        self.create_args = (args, kwargs)
        return self.created


class EmptySearchResult(object):
    def __init__(self):
        self.write = Mock()

    def __bool__(self):
        return False

    __nonzero__ = __bool__


class RecordCollection(object):
    def __init__(self, records=()):
        self.records = list(records)

    def __iter__(self):
        return iter(self.records)

    def __bool__(self):
        return bool(self.records)

    __nonzero__ = __bool__

    def __ior__(self, record):
        self.records.append(record)
        return self


class SyncDeepElevenTest(unittest.TestCase):
    def model(self, **values):
        record = ExternalDataSync()
        for name, value in values.items():
            setattr(record, name, value)
        return record

    def test_get_related_data_updates_matching_relation_json_and_returns_value(self):
        relation = types.SimpleNamespace(name="partner_id", write=Mock(),
                                         get_data_relation=Mock(return_value=17))
        relations = RelatedCollection([relation])
        record = self.model(related_ids=relations, sync_strategy_id=None)
        field = types.SimpleNamespace(name="partner_id", comodel_name="res.partner",
                                      type="many2one", required=True)

        result = record.get_related_data(field, {"id": 17})

        self.assertEqual(result, 17)
        relation.write.assert_called_once_with({"data_json": '{"id": 17}'})
        relation.get_data_relation.assert_called_once_with()

    def test_get_related_data_creates_nested_relation_with_inverse_for_one2many(self):
        created = types.SimpleNamespace(get_data_relation=Mock(return_value=[5, 6]))
        relations = RelatedCollection(created=created)
        strategy = types.SimpleNamespace(external_app_name="remote")
        strategy.lookup_strategy = Mock(return_value="child-strategy")
        record = self.model(related_ids=relations, sync_strategy_id=strategy)
        field = types.SimpleNamespace(name="line_ids", comodel_name="sale.line",
                                      type="one2many", required=True, inverse_name="order_id")

        self.assertEqual(record.get_related_data(field, [{"id": 5}]), [5, 6])
        strategy.lookup_strategy.assert_called_once_with(
            "sale.line", parent_sync_strategy=strategy, external_app_name="remote")
        args, kwargs = relations.create_args
        self.assertEqual(args, (record, "line_ids", "one2many"))
        self.assertEqual(kwargs, {"field_required": True, "related_sync_strategy_id": "child-strategy",
                                  "internal_model": "sale.line", "inverse_field": "order_id",
                                  "value": [{"id": 5}]})
        created.get_data_relation.assert_called_once_with()

    def test_data_from_external_id_reuses_existing_strategy_match_without_fetch(self):
        existing = object()
        record = self.model(search=Mock(return_value=existing))
        strategy = types.SimpleNamespace(id=9, get_external_one_data=Mock())

        self.assertIs(record.data_from_external_id(22, strategy), existing)
        record.search.assert_called_once_with([
            ("external_odoo_id", "=", 22), ("sync_strategy_id", "=", 9)], limit=1)
        strategy.get_external_one_data.assert_not_called()

    def test_data_from_external_id_claims_unassigned_record_for_strategy(self):
        existing = types.SimpleNamespace(write=Mock())
        record = self.model(search=Mock(side_effect=[False, existing]))
        strategy = types.SimpleNamespace(id=9, external_app_name="remote", external_model="Contact",
                                         internal_model="res.partner")

        self.assertIs(record.data_from_external_id(22, strategy), existing)
        self.assertEqual(record.search.call_args_list[1][0][0], [
            ("external_app_name", "=", "remote"), ("external_model", "=", "Contact"),
            ("internal_model", "=", "res.partner"), ("external_odoo_id", "=", 22),
            ("sync_strategy_id", "=", False)])
        existing.write.assert_called_once_with({"sync_strategy_id": 9})

    def test_data_from_external_id_fetches_creates_and_maps_external_record(self):
        item = {"id": 22, "name": "Remote", "write_date": "2024-01-02 03:04:05"}
        created = _HELPERS.FakeRecords([types.SimpleNamespace(id=81)])
        strategy = types.SimpleNamespace(
            id=9, external_app_name="remote", external_model="Contact", internal_model="res.partner",
            get_external_one_data=Mock(return_value=item), internal_lookup=Mock(return_value=False),
            get_internal_id_from_external_id=Mock(return_value=44))
        record = self.model(search=Mock(side_effect=[False, EmptySearchResult()]), create=Mock(return_value=created))

        result = record.data_from_external_id(22, strategy)

        self.assertIs(result, created[0])
        strategy.get_external_one_data.assert_called_once_with(22)
        strategy.internal_lookup.assert_called_once_with(item)
        self.assertEqual(record.create.call_args[0][0], [{
            "display_name": "Remote", "external_last_update": "parsed:2024-01-02 03:04:05",
            "sync_strategy_id": 9, "data_json": '{"id": 22, "name": "Remote", "write_date": "2024-01-02 03:04:05"}',
            "internal_odoo_id": 44}])

    def test_remove_duplicate_data_archives_duplicates_repoints_updates_and_processes_unique(self):
        first = types.SimpleNamespace(id=1, sync_strategy_id=types.SimpleNamespace(id=7),
                                      external_odoo_id=30, internal_model="res.partner",
                                      external_model="Contact", process_with_handel_error=Mock())
        duplicate = types.SimpleNamespace(id=2, sync_strategy_id=types.SimpleNamespace(id=7),
                                          external_odoo_id=30, internal_model="res.partner",
                                          external_model="Contact", action_archive=Mock())
        distinct = types.SimpleNamespace(id=3, sync_strategy_id=types.SimpleNamespace(id=7),
                                         external_odoo_id=31, internal_model="res.partner",
                                         external_model="Contact", process_with_handel_error=Mock())
        change1, change2, change3 = (types.SimpleNamespace(write=Mock()) for _ in range(3))
        updates = types.SimpleNamespace(search=Mock(side_effect=[change1, change2, change3]))
        result_set = RecordCollection()
        recordset = self.model(env={"external.data.update": updates},
                               browse=Mock(return_value=result_set))
        recordset.__class__.__iter__ = lambda self: iter([first, duplicate, distinct])
        recordset.__class__.__ior__ = lambda self, rec: (result_set.records.append(rec) or result_set)

        result = recordset.remove_duplicate_data()

        self.assertIs(result, result_set)
        self.assertEqual(result_set.records, [first, distinct])
        duplicate.action_archive.assert_called_once_with()
        self.assertEqual([call[0][0] for call in updates.search.call_args_list], [
            [("data_id", "=", 1)], [("data_id", "=", 2)], [("data_id", "=", 3)]])
        change1.write.assert_called_once_with({"data_id": 1})
        change2.write.assert_called_once_with({"data_id": 1})
        change3.write.assert_called_once_with({"data_id": 3})
        first.process_with_handel_error.assert_called_once_with()
        distinct.process_with_handel_error.assert_called_once_with()

    def test_save_data_updates_existing_record_when_external_updates_are_allowed(self):
        existing = types.SimpleNamespace(write=Mock())
        strategy = types.SimpleNamespace(internal_id_same_as_external=False)
        record = self.model(sync_strategy_id=strategy, is_update_able_from_external=Mock(return_value=True),
                            is_create_able_from_external=Mock(return_value=True), internal_model="res.partner",
                            internal_odoo_id=55)
        values = {"name": "updated"}

        result = record.save_data(existing, {"id": 55}, values)

        self.assertIs(result, existing)
        existing.write.assert_called_once_with({"name": "updated"})
        strategy.internal_lookup = Mock()
        strategy.internal_lookup.assert_not_called()

    def test_save_data_creates_a_record_when_absent_and_creation_is_allowed(self):
        created = types.SimpleNamespace(id=44)
        model_object = types.SimpleNamespace(create=Mock(return_value=[created]))
        strategy = types.SimpleNamespace(internal_id_same_as_external=False,
                                         internal_model_object=Mock(return_value=model_object))
        record = self.model(sync_strategy_id=strategy, is_update_able_from_external=Mock(return_value=True),
                            is_create_able_from_external=Mock(return_value=True), internal_model="res.partner")
        values = {"name": "new"}

        result = record.save_data(False, {"id": 44}, values)

        self.assertIs(result, created)
        strategy.internal_model_object.assert_called_once_with()
        model_object.create.assert_called_once_with([{"name": "new"}])


if __name__ == "__main__":
    unittest.main()
