"""Behavior tests for remaining utility and mapping edge paths."""
import types
import unittest
from unittest.mock import Mock, call

from test_mapping_logic import load_mapping_class
from test_utils_remaining import load_utils


class HelperMore9Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.utils = load_utils()
        cls.mapping_class = load_mapping_class()

    def mapping(self, **values):
        instance = self.mapping_class()
        instance.__dict__.update(values)
        return instance

    def test_safe_call_uses_defaults_and_routes_varargs_and_keyword_only_values(self):
        class Receiver(object):
            def invoke(self, first, second='default', *rest, required, **options):
                return first, second, rest, required, options

        result = self.utils.safe_call_method(
            Receiver(), 'invoke', args=['one', 'two', 'extra'],
            kwargs={'required': 'yes', 'mode': 'fast'})
        self.assertEqual(result, ('one', 'two', ('extra',), 'yes', {'mode': 'fast'}))

    def test_safe_call_rejects_missing_required_positional_argument(self):
        class Receiver(object):
            def invoke(self, required):
                return required

        with self.assertRaisesRegex(TypeError, 'Missing required argument: required'):
            self.utils.safe_call_method(Receiver(), 'invoke')

    def test_safe_call_non_model_falsey_receiver_is_ignored(self):
        self.assertIsNone(self.utils.safe_call_method(None, 'invoke'))

    def test_parent_mapping_updates_changed_data_and_returns_related_payload(self):
        related = Mock(data_json='"old"')
        related.get_data_relation.return_value = {'parent': 9}
        relation_model = Mock()
        relation_model.get_relation_data.return_value = related
        mapping = self.mapping(mapping_strategy='parent', internal_field='parent_id',
                               key_name='remote_parent',
                               env={'external.data.sync.related': relation_model})
        result = mapping.mapping_data({'remote_parent': {'id': 9}}, parent_data_sync=4)
        self.assertEqual(result, {'parent': 9})
        related.write.assert_called_once_with({'data_json': '{"id": 9}'})
        relation_model.create_parent.assert_not_called()

    def test_many2many_mapping_marks_empty_existing_relation_done(self):
        related = Mock(data_json='[]')
        related.get_data_relation.return_value = []
        relation_model = Mock()
        relation_model.get_relation_data.return_value = related
        mapping = self.mapping(mapping_strategy='many2many', internal_field='tag_ids',
                               key_name=None,
                               env={'external.data.sync.related': relation_model})
        self.assertEqual(mapping.mapping_data({'tag_ids': []}, parent_data_sync=7), [])
        related.write.assert_called_once_with({'state': 'done'})
        relation_model.create_many2many.assert_not_called()

    def test_mapping_rejects_invalid_numeric_constant(self):
        mapping = self.mapping(mapping_strategy='constant', constant_value_type='integer',
                               constant_value='not-an-integer')
        with self.assertRaises(ValueError):
            mapping.mapping_data({})


if __name__ == '__main__':
    unittest.main()
