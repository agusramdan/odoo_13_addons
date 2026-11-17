"""Behavioral coverage for remaining utility and mapping branches."""
import pathlib
import sys
import types
import unittest
from unittest.mock import Mock

from test_mapping_logic import load_mapping_class
from test_utils_remaining import load_utils


class MoreUtilityCoverageTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.utils = load_utils()

    def test_safe_call_rejects_missing_method_parameter(self):
        with self.assertRaisesRegex(AttributeError, "No Method parameter"):
            self.utils.safe_call_method(object(), None)

    def test_safe_call_drops_extra_positional_arguments(self):
        class Receiver(object):
            def run(self, first):
                return first

        self.assertEqual(self.utils.safe_call_method(
            Receiver(), "run", args=["kept", "ignored"]), "kept")

    def test_get_callable_method_handles_missing_and_non_string_names(self):
        receiver = types.SimpleNamespace(run=lambda: "ok")
        self.assertTrue(self.utils.get_callable_method(receiver, "run"))
        self.assertFalse(self.utils.is_callable_method(receiver, "missing"))
        self.assertFalse(self.utils.get_callable_method(receiver, None))

    def test_convert_external_data_preserves_dict_and_maps_list_forms(self):
        original = {"id": 9, "display_name": "Provided"}
        self.assertIs(self.utils.convert_from_external_data(original), original)
        self.assertEqual(self.utils.convert_from_external_data(8), {"id": 8})
        self.assertEqual(self.utils.convert_from_external_data([4, "Label"]),
                         {"id": 4, "display_name": "Label"})
        self.assertEqual(self.utils.convert_from_external_data([]), {})
        self.assertEqual(self.utils.convert_from_external_data("unsupported"), {})

    def test_call_with_savepoint_returns_result_and_rethrows_only_on_request(self):
        class Savepoint(object):
            def __enter__(self):
                return self

            def __exit__(self, *exc_info):
                return False

        receiver = types.SimpleNamespace(env=types.SimpleNamespace(
            cr=types.SimpleNamespace(savepoint=Savepoint)))
        receiver.run = lambda value: value + 1
        self.assertEqual(self.utils.call_with_savepoint(receiver, "run", args=[2]), 3)

        def fail():
            raise RuntimeError("expected failure")

        receiver.fail = fail
        with self.assertRaisesRegex(RuntimeError, "expected failure"):
            self.utils.call_with_savepoint(receiver, "fail", rethrow=True)
        self.assertIsNone(self.utils.call_with_savepoint(receiver, "fail"))


class MoreMappingCoverageTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mapping_class = load_mapping_class()

    def mapping(self, **values):
        result = self.mapping_class()
        result.__dict__.update(values)
        return result

    def test_function_mapping_prefers_related_model_method(self):
        target = types.SimpleNamespace(convert=lambda: "related")
        model = types.SimpleNamespace(convert=lambda: "fallback")
        mapping = self.mapping(mapping_strategy="function", function_name="convert",
                               env={"res.partner": target}, sync_strategy_id=None)
        field = types.SimpleNamespace(relational=True, comodel_name="res.partner")
        self.assertEqual(mapping.mapping_data({}, model=model, field=field), "related")

    def test_function_mapping_falls_back_to_model_for_unavailable_relation_method(self):
        model = types.SimpleNamespace(convert=lambda: "fallback")
        mapping = self.mapping(mapping_strategy="function", function_name="convert",
                               env={}, sync_strategy_id=None)
        field = types.SimpleNamespace(relational=True, comodel_name="res.partner")
        self.assertEqual(mapping.mapping_data({}, model=model, field=field), "fallback")

    def test_mapping_data_parent_creates_related_record_and_marks_empty_value_done(self):
        related = Mock()
        related.get_data_relation.return_value = {"id": 6}
        relation_model = Mock()
        relation_model.get_relation_data.return_value = None
        relation_model.create_parent.return_value = related
        mapping = self.mapping(mapping_strategy="parent", internal_field="parent_id",
                               key_name=None, env={"external.data.sync.related": relation_model})
        self.assertEqual(mapping.mapping_data({"parent_id": None}, parent_data_sync="parent"),
                         {"id": 6})
        relation_model.create_parent.assert_called_once_with("parent_id", "parent", None)
        related.write.assert_called_once_with({"state": "done"})

    def test_mapping_data_many2one_updates_changed_json_without_marking_nonempty_done(self):
        related = Mock(data_json='"old"')
        related.get_data_relation.return_value = 12
        relation_model = Mock()
        relation_model.get_relation_data.return_value = related
        mapping = self.mapping(mapping_strategy="many2one", internal_field="partner_id",
                               key_name=None, env={"external.data.sync.related": relation_model})
        self.assertEqual(mapping.mapping_data({"partner_id": "new"}, parent_data_sync=3), 12)
        related.write.assert_called_once_with({"data_json": '"new"'})
        relation_model.create_many2one.assert_not_called()

    def test_mapping_data_many2many_creates_relation_for_new_value(self):
        related = Mock()
        related.get_data_relation.return_value = [2, 3]
        relation_model = Mock()
        relation_model.get_relation_data.return_value = None
        relation_model.create_many2many.return_value = related
        strategy = object()
        mapping = self.mapping(mapping_strategy="many2many", internal_field="tag_ids",
                               key_name=None, env={"external.data.sync.related": relation_model},
                               relation_strategy_id=strategy)
        self.assertEqual(mapping.mapping_data({"tag_ids": [2, 3]}, parent_data_sync=5), [2, 3])
        relation_model.create_many2many.assert_called_once_with("tag_ids", 5, [2, 3], strategy)
        related.write.assert_not_called()


if __name__ == "__main__":
    unittest.main()
