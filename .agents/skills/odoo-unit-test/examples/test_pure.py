import unittest
from unittest.mock import Mock
import pytest

def approve(state, amount):
    if state != 'draft' or amount <= 0: raise ValueError('Invalid approval')
    return 'approved'

def send_invoice(client, payload):
    response = client.post('/invoices', json=payload, timeout=3)
    response.raise_for_status()
    return response.json()['id']

class TestPure(unittest.TestCase):
    def test_approval(self):
        self.assertEqual(approve('draft', 10), 'approved')
        with self.assertRaises(ValueError): approve('approved', 10)
    def test_external_api_success_and_failure(self):
        client = Mock(); client.post.return_value.json.return_value = {'id': 'inv-1'}
        self.assertEqual(send_invoice(client, {'amount': 10}), 'inv-1')
        client.post.assert_called_once_with('/invoices', json={'amount': 10}, timeout=3)
        client.post.return_value.raise_for_status.side_effect = RuntimeError('API error')
        with self.assertRaises(RuntimeError): send_invoice(client, {})

def test_invalid_amount():
    with pytest.raises(ValueError): approve('draft', 0)
