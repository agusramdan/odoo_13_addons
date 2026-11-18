import importlib.util
from pathlib import Path
import unittest
from unittest.mock import Mock
import pytest
from mock_odoo import MockFactory, MockModel, MockOdooEnv, odoo_modules

with odoo_modules():
    spec = importlib.util.spec_from_file_location('example_addon_logic', Path(__file__).with_name('addon_logic.py'))
    addon = importlib.util.module_from_spec(spec); spec.loader.exec_module(addon)
    UserError = __import__('odoo.exceptions', fromlist=['UserError']).UserError

class TestOdooMocked(unittest.TestCase):
    def setUp(self):
        self.order = MockFactory.record(id=1, state='draft', amount=10)
        self.model = MockModel([self.order])
        self.env = MockOdooEnv({'sale.order': self.model})
    def test_model_and_approval_workflow(self):
        obj = addon.Order(); obj.amount = 10; obj.state = 'draft'; obj.action_approve()
        self.assertEqual(obj.state, 'approved')
        obj.amount = 0
        with self.assertRaises(UserError): obj.action_approve()
    def test_wizard(self):
        wizard = addon.ApprovalWizard(); wizard.env = self.env; wizard.order_id = 1; wizard.action_confirm()
        self.assertEqual(self.order.state, 'approved')
    def test_cron(self):
        other = self.model.create({'state':'approved', 'amount':5})
        cron = addon.Order(); cron.env = self.env; cron.cron_expire()
        self.assertEqual((self.order.state, other.state), ('expired', 'approved'))
    def test_controller(self):
        self.assertEqual(addon.OrderController().status(self.order), {'state':'draft'})
    def test_model_domain_and_singleton(self):
        self.assertEqual(self.model.search([('state', '=', 'draft')]).ids, [1])
        with self.assertRaises(NotImplementedError): self.model.search([('id', '>', 0)])
        with self.assertRaises(ValueError): self.model.browse([]).ensure_one()
    def test_cursor_is_forbidden(self):
        with self.assertRaises(RuntimeError): _ = self.env.cr

def test_factory_and_mock():
    record = MockFactory.record(id=4, state='draft')
    callback = Mock(); callback(MockFactory.recordset(record).ensure_one())
    callback.assert_called_once_with(record)
    with pytest.raises(KeyError): MockOdooEnv()['missing']
