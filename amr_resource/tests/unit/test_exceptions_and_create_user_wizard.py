import importlib.util
import json
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import Mock

SCRIPTS = Path(__file__).parents[3] / '.agents' / 'skills' / 'odoo-unit-test' / 'scripts'
sys.path.insert(0, str(SCRIPTS))
from mock_odoo import odoo_modules


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestExceptions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with odoo_modules():
            import odoo.http
            odoo.http.Response = Mock(side_effect=lambda body, **kwargs: (body, kwargs))
            cls.module = load_module('resource_exceptions', Path(__file__).parents[2] / 'exceptions.py')

    def test_api_exception_default_and_custom_status(self):
        for status in (400, 403):
            error = self.module.APIException('invalid_request', 'bad input', status)
            self.assertEqual(str(error), 'bad input')
            body, options = self.module.handle_exception(error)
            self.assertEqual(json.loads(body), {'error': 'invalid_request', 'error_description': 'bad input'})
            self.assertEqual(options, {'status': status, 'content_type': 'application/json'})
        self.assertEqual(self.module.APIException('bad').http_status, 400)

    def test_unexpected_exception_returns_server_error(self):
        body, options = self.module.handle_exception(ValueError('unexpected'))
        self.assertEqual(json.loads(body), {'error': 'unknown_error', 'error_description': 'unexpected'})
        self.assertEqual(options, {'status': 500, 'content_type': 'application/json'})


class TestCreateUserWizard(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with odoo_modules():
            cls.module = load_module('create_user_wizard', Path(__file__).parents[2] / 'wizard' / 'create_user_wizard.py')

    def setUp(self):
        self.users = Mock()
        self.users.search.return_value = []
        self.users.create.return_value = types.SimpleNamespace(id=42)
        self.wizard = self.module.CreateUserWizard()
        self.wizard.ensure_one = Mock()
        self.wizard.env = {'res.users': self.users}
        self.wizard.name = 'Test User'
        self.wizard.login = 'test-user'
        self.wizard.email = 'test@example.invalid'
        self.wizard.template_id = types.SimpleNamespace(
            share=True, groups_id=[types.SimpleNamespace(id=3), types.SimpleNamespace(id=7)])

    def test_creates_user_with_template_groups_and_returns_action(self):
        action = self.wizard.action_create()
        self.wizard.ensure_one.assert_called_once_with()
        self.users.search.assert_called_once_with([('login', '=', 'test-user')])
        self.users.create.assert_called_once_with({
            'name': 'Test User', 'login': 'test-user', 'email': 'test@example.invalid',
            'share': True, 'groups_id': [(4, 3), (4, 7)],
        })
        self.assertEqual(action, {'type': 'ir.actions.act_window', 'res_model': 'res.users',
                                  'res_id': 42, 'view_mode': 'form', 'target': 'current'})

    def test_duplicate_login_prevents_creation(self):
        self.users.search.return_value = [object()]
        with self.assertRaisesRegex(self.module.ValidationError, 'Login already exists'):
            self.wizard.action_create()
        self.users.create.assert_not_called()

    def test_singleton_validation_precedes_search(self):
        self.wizard.ensure_one.side_effect = ValueError('Expected singleton')
        with self.assertRaises(ValueError):
            self.wizard.action_create()
        self.users.search.assert_not_called()
        self.users.create.assert_not_called()
