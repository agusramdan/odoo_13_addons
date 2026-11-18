import importlib.util
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

SKILL_SCRIPTS = Path(__file__).parents[3] / '.agents' / 'skills' / 'odoo-unit-test' / 'scripts'
sys.path.insert(0, str(SKILL_SCRIPTS))
from mock_odoo import odoo_modules


def load_model(name):
    path = Path(__file__).parents[2] / 'models' / (name + '.py')
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    with odoo_modules():
        spec.loader.exec_module(module)
    return module


class TestUsers(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_model('res_users')

    def user(self):
        user = self.module.ResUsers()
        user.id = 7
        user.ensure_one = Mock()
        return user

    def test_machine_sudo_and_group_classification(self):
        base = self.module.Base()
        base.with_user = Mock(return_value='changed')
        self.assertIs(base.user_machine_sudo(None), base)
        base.with_user.assert_not_called()
        self.assertEqual(base.user_machine_sudo(7), 'changed')
        base.with_user.assert_called_once_with(7)
        user = self.user()
        user.has_group = Mock(side_effect=lambda group: group.endswith('group_machine'))
        self.assertTrue(user.is_user_machine())
        self.assertFalse(user.is_user_technical())
        user.share = False
        self.assertTrue(user.is_user_business())
        user.share = True
        self.assertFalse(user.is_user_business())
        user.share = False
        user.has_group = Mock(return_value=True)
        self.assertFalse(user.is_user_business())

    def test_decode_only_returns_matching_user_payload(self):
        user = self.user()
        helper = Mock()
        helper.decode.return_value = {'sub': 'test-user'}
        user.env = {'amr.resource.helper': helper}
        helper.get_uid.return_value = 7
        self.assertEqual(user.decode('test-token', audience='app'), {'sub': 'test-user'})
        helper.decode.assert_called_once_with('test-token', audience='app')
        helper.get_uid.return_value = 8
        self.assertIsNone(user.decode('test-token'))

    def test_token_creation_denied_or_unsupported(self):
        user = self.user()
        self.assertTrue(user.is_user_allow_create_token())
        for method in (user.get_access_token, user.create_access_token):
            user.is_user_allow_create_token = lambda: False
            with self.assertRaisesRegex(self.module.UserError, 'not allowed'):
                method()
            user.is_user_allow_create_token = lambda: True
            with self.assertRaisesRegex(self.module.UserError, 'not supported'):
                method()

    def test_url_methods_forward_only_auto_login(self):
        user = self.user()
        user.get_auto_login_url = Mock(return_value='auto')
        self.assertEqual(user._resource_access_url('/path'), '/path')
        self.assertEqual(user.add_url_access_token('/path'), '/path')
        user.get_auto_login_url.assert_not_called()
        self.assertEqual(user.add_url_access_token('/path', url_type='auto', flag=True), 'auto')
        user.get_auto_login_url.assert_called_once_with(url='/path', flag=True)
        self.assertEqual(self.module.ResUsers.get_auto_login_url(user, '/path'), '/path')

    def test_access_context_validates_provenance_and_user(self):
        from werkzeug.exceptions import Unauthorized
        user = self.user()
        helper = Mock()
        http = Mock()
        user.env = {'amr.resource.helper': helper, 'ir.http': http}
        class Env(dict):
            context = {}
        user.env = Env(user.env)
        user.with_context = Mock(return_value='contextual')
        helper._verified.side_effect = lambda payload: payload in ('marker', 'valid', 'other')
        helper.get_uid.side_effect = lambda payload: 8 if payload == 'other' else 7
        user.env.context = {'__access_token_context': 'marker'}
        self.assertIs(user.with_access_token_context(), user)
        helper.validate.assert_not_called()
        user.env.context = {}
        helper.get_bearer_token.return_value = 'test-bearer'
        helper.validate.return_value = 'valid'
        self.assertEqual(user.with_access_token_context(), 'contextual')
        helper.validate.assert_called_once_with('test-bearer')
        user.with_context.assert_called_once_with(__access_token_context='valid')
        http.get_jwt_payload.return_value = 'other'
        self.assertIs(user.with_access_token_context(validate=False), user)
        http.get_jwt_payload.return_value = 'unverified'
        with self.assertRaises(Unauthorized):
            user.with_access_token_context(validate=False)


class TestSettings(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_model('res_config_settings')

    def test_edit_base_url_action_searches_with_sudo(self):
        settings = self.module.ResConfigSettings()
        params = Mock()
        params.sudo.return_value.search.return_value = SimpleNamespace(id=42)
        settings.env = {'ir.config_parameter': params}
        self.assertEqual(settings.action_edit_web_base_url(), {
            'type': 'ir.actions.act_window', 'res_model': 'ir.config_parameter',
            'res_id': 42, 'view_mode': 'form'})
        params.sudo.return_value.search.assert_called_once_with(
            [('key', '=', 'web.base.url')], limit=1)

    def test_open_issuers_checks_read_and_admin_before_loading_action(self):
        settings = self.module.ResConfigSettings()
        registry = Mock()
        action = {'type': 'ir.actions.act_window'}
        class Env(dict):
            ref = Mock(return_value=SimpleNamespace(read=lambda: [action]))
        settings.env = Env({'oidc.issuer.register': registry})
        registry._registry_role.return_value = True
        self.assertEqual(settings.action_open_resource_issuers(), action)
        registry.check_access_rights.assert_called_with('read')
        registry._registry_role.assert_called_with('amr_resource.group_oidc_trust_admin')
        settings.env.ref.assert_called_once_with('amr_resource.action_resource_issuers')
        settings.env.ref.reset_mock()
        registry._registry_role.return_value = False
        with odoo_modules():
            from odoo.exceptions import AccessError
            with self.assertRaises(AccessError):
                settings.action_open_resource_issuers()
        settings.env.ref.assert_not_called()
        registry.check_access_rights.side_effect = ValueError('denied')
        registry._registry_role.reset_mock()
        with self.assertRaisesRegex(ValueError, 'denied'):
            settings.action_open_resource_issuers()
        registry._registry_role.assert_not_called()
        settings.env.ref.assert_not_called()
