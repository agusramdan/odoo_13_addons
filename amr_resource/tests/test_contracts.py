"""UT-02, UT-07..UT-10; ORM cases require real disposable Odoo 13.

Direct controller calls do not prove routing, ACLs, rendering or role access.
"""
import ast
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch
from xml.etree import ElementTree

from odoo.exceptions import AccessError, UserError, ValidationError
from psycopg2 import IntegrityError
from werkzeug.exceptions import Unauthorized

from .. import exceptions
from ..controllers import main
from ..models import ir_http
from .test_helper import ResourceCase


ROOT = Path(__file__).resolve().parents[1]


class TestResourceContracts(ResourceCase):
    def test_ut02_settings_action_and_declarations(self):
        settings = self.env['res.config.settings'].with_user(self.admin).create({})
        action = settings.action_open_resource_issuers()
        self.assertEqual(action['res_model'], 'oidc.issuer.register')
        self.assertEqual(action['type'], 'ir.actions.act_window')
        self.assertEqual(action['view_mode'], 'tree,form')
        params = self.env['ir.config_parameter'].sudo()
        params.set_param('web.base.url', 'http://127.0.0.1:19000')
        parameter = params.search([('key', '=', 'web.base.url')], limit=1)
        self.assertEqual(settings.action_edit_web_base_url(), {
            'type': 'ir.actions.act_window', 'res_model': 'ir.config_parameter',
            'res_id': parameter.id, 'view_mode': 'form',
        })
        self.assertEqual(parameter.value, 'http://127.0.0.1:19000')
        parameter.unlink()
        self.assertFalse(settings.action_edit_web_base_url()['res_id'])
        self.assertFalse(params.search([('key', '=', 'web.base.url')]))
        self.assertNotIn('amr_select_issuer', settings._fields)
        self.assertNotIn('amr_select_audience', settings._fields)
        self.assertNotIn('amr_select_issuer', settings.default_get(['amr_select_issuer']))
        self.assertNotIn('amr_select_audience', settings.default_get(['amr_select_audience']))
        self.assertEqual(settings._fields['amr_web_base_url_freeze'].config_parameter,
                         'web.base.url.freeze')
        root = ElementTree.parse(str(ROOT / 'views/res_config_settings_views.xml')).getroot()
        block = root.find(".//div[@id='amr_resource_addons']")
        self.assertEqual(block.get('string'), 'Server Resource')
        self.assertEqual(block.get('data-string'), 'amr_resource_addons')
        self.assertEqual(block.get('groups'), 'base.group_erp_manager')
        self.assertIsNone(root.find(".//field[@name='amr_select_issuer']"))
        self.assertIsNone(root.find(".//field[@name='amr_select_audience']"))
        edit = root.find(".//button[@name='action_open_resource_issuers']")
        self.assertIsNotNone(edit)
        self.assertEqual(edit.get('groups'), 'amr_resource.group_oidc_trust_admin')
        self.assertEqual(edit.get('type'), 'object')
        freeze = root.find(".//field[@name='amr_web_base_url_freeze']")
        self.assertIsNotNone(freeze)
        self.assertIsNone(freeze.get('attrs'))
        settings_ast = ast.parse((ROOT / 'models/res_config_settings.py').read_text())
        freeze_decl = next(n.value for n in ast.walk(settings_ast)
                           if isinstance(n, ast.Assign) and any(
                               isinstance(t, ast.Name) and t.id == 'amr_web_base_url_freeze'
                               for t in n.targets))
        self.assertNotIn('default', [k.arg for k in freeze_decl.keywords])

    def test_ut07_auth_machine_params_and_metadata(self):
        payload = {'synthetic': True}
        helper = Mock()
        helper._verified.return_value = False
        helper.get_validate_user.return_value = payload
        helper.get_user_match.return_value = self.admin
        helper.get_bearer_token.return_value = self.token
        helper.get_param_token.return_value = self.token
        request = SimpleNamespace(env={'amr.resource.helper': helper}, uid=False)
        with patch.object(ir_http, 'request', request):
            self.assertEqual(ir_http.IrHttp.get_jwt_payload(), {})
            self.assertIsNone(ir_http.IrHttp.check_scope('ungranted'))
            for method, extraction in (
                    (ir_http.IrHttp._auth_method_machine, helper.get_bearer_token),
                    (ir_http.IrHttp._auth_method_params, helper.get_param_token)):
                request.uid = False
                helper.reset_mock()
                self.assertIsNone(method())
                extraction.assert_called_once_with()
                helper.get_validate_user.assert_called_once_with(self.token)
                helper.get_user_match.assert_called_once_with(payload)
                self.assertEqual(request.uid, self.admin.id)
                self.assertIs(request.jwt_token, self.token)
                self.assertIs(request.jwt_payload, payload)
                request.jwt_payload = 'existing-metadata'
                method()
                self.assertEqual(request.jwt_payload, 'existing-metadata')
                helper.get_validate_user.side_effect = Unauthorized()
                helper.get_user_match.reset_mock()
                with self.assertRaises(Unauthorized):
                    method()
                helper.get_user_match.assert_not_called()
                self.assertEqual(request.uid, self.admin.id)
                self.assertEqual(request.jwt_payload, 'existing-metadata')
                helper.get_validate_user.side_effect = None
                helper.get_user_match.return_value = None
                with self.assertRaises(Unauthorized):
                    method()
                self.assertEqual(request.uid, self.admin.id)
                self.assertEqual(request.jwt_payload, 'existing-metadata')
                helper.get_user_match.return_value = self.admin
            helper.get_header_token.assert_not_called()

    def test_ut07_session_params_bearer_order(self):
        calls = []
        class AuthProbe:
            _auth_method_user_or_param = classmethod(ir_http.IrHttp._auth_method_user_or_param.__func__)
            _authenticate_token = classmethod(ir_http.IrHttp._authenticate_token.__func__)
            @classmethod
            def _auth_method_user(cls):
                calls.append('session')
                if session_valid[0]:
                    return 'session-result'
                raise Unauthorized()
            @classmethod
            def _auth_method_params(cls):
                calls.append('params')
                if params_valid[0]:
                    return 'params-result'
                raise Unauthorized()
        helper = Mock()
        helper.get_bearer_token.side_effect = lambda: calls.append('bearer') or bearer[0]
        helper.get_validate_user.return_value = {'synthetic': True}
        helper.get_user_match.return_value = self.admin
        session_valid, params_valid, bearer = [True], [True], [self.token]
        request = SimpleNamespace(env={'amr.resource.helper': helper}, uid=False)
        with patch.object(ir_http, 'request', request):
            self.assertEqual(AuthProbe._auth_method_user_or_param(), 'session-result')
            self.assertEqual(calls, ['session'])
            helper.get_bearer_token.assert_not_called()
            session_valid[0] = False
            calls[:] = []
            self.assertIsNone(AuthProbe._auth_method_user_or_param())
            self.assertEqual(calls, ['session', 'bearer'])
            self.assertEqual(request.uid, self.admin.id)
            for failure in ('validation', 'resolver'):
                calls[:] = []
                helper.get_validate_user.side_effect = Unauthorized() if failure == 'validation' else None
                helper.get_user_match.return_value = None if failure == 'resolver' else self.admin
                with self.assertRaises(Unauthorized):
                    AuthProbe._auth_method_user_or_param()
                self.assertEqual(calls, ['session', 'bearer'])
                self.assertEqual(request.uid, self.admin.id)
            calls[:] = []
            bearer[0] = None
            self.assertEqual(AuthProbe._auth_method_user_or_param(), 'params-result')
            self.assertEqual(calls, ['session', 'bearer', 'params'])
            calls[:] = []
            params_valid[0] = False
            with self.assertRaises(Unauthorized):
                AuthProbe._auth_method_user_or_param()
            self.assertEqual(calls, ['session', 'bearer', 'params'])

    def synthetic_user(self, suffix, groups=()):
        return self.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Synthetic Resource ' + suffix, 'login': 'resource-' + suffix,
            'groups_id': [(6, 0, [g.id for g in groups])]})

    def test_ut08_user_predicates_environment_and_stubs(self):
        machine = self.synthetic_user('machine', [self.env.ref('base.group_user'),
                                                  self.env.ref('amr_resource.group_machine')])
        ordinary = self.synthetic_user('ordinary', [self.env.ref('base.group_user')])
        technical = self.synthetic_user('technical', [self.env.ref('base.group_user'),
                                                      self.env.ref('amr_resource.group_machine'),
                                                      self.env.ref('amr_resource.group_technical')])
        self.assertTrue(machine.is_user_machine())
        self.assertTrue(machine.is_user_business())
        self.assertFalse(ordinary.is_user_machine())
        self.assertFalse(ordinary.is_user_business())
        self.assertTrue(technical.is_user_technical())
        self.assertFalse(technical.is_user_business())
        self.assertIs(self.helper.user_machine_sudo(self.env['res.users']), self.helper)
        elevated = self.helper.user_machine_sudo(machine)
        self.assertEqual(elevated.env.uid, machine.id)
        self.assertFalse(elevated.env.su)
        self.assertEqual(self.helper.user_machine_sudo(ordinary).env.uid, ordinary.id)
        self.assertTrue(machine.is_user_allow_create_token())
        for method in (machine.get_access_token, machine.create_access_token):
            with self.assertRaises(UserError):  # source raises NotImplemented singleton
                method()
        url = 'http://127.0.0.1:19000/fixture'
        self.assertEqual(machine.add_url_access_token(url), url)
        self.assertEqual(machine.add_url_access_token(url, url_type='auto_login'), url)
        self.assertEqual(machine.get_auto_login_url(url), url)
        payload = {'sub': 'synthetic'}
        self.patch_model(self.helper, 'decode', return_value=payload)
        uid = self.patch_model(self.helper, 'get_uid', return_value=machine.id)
        self.assertEqual(machine.decode(self.token), payload)
        uid.return_value = ordinary.id
        self.assertIsNone(machine.decode(self.token))

    def test_ut08_context(self):
        from odoo.addons.amr_resource.models.helper import _VerifiedClaims
        from ..models import res_users as users_module
        self.profile.binding_ids = [(0, 0, {'sub': 'subject-a', 'user_id': self.admin.id})]
        payload = _VerifiedClaims(dict(iss=self.profile.issuer, sub='subject-a'),
                                  self.env.company.id, self.admin.id)
        user = self.admin.with_user(self.admin)
        with patch.object(type(self.helper), 'get_bearer_token', return_value=self.token) as bearer, \
                patch.object(type(self.helper), 'validate', return_value=payload) as validate:
            result = user.with_access_token_context()
            self.assertIs(result.env.context['__access_token_context'], payload)
            bearer.reset_mock()
            validate.reset_mock()
            self.assertIs(result.with_access_token_context(), result)
            bearer.assert_not_called()
            validate.assert_not_called()
            other = self.synthetic_user('context-other', [self.env.ref('base.group_user')])
            other = other.with_user(self.admin)
            self.assertIs(other.with_access_token_context(), other)
        forged = user.with_context(__access_token_context={'sub': 'subject-a'})
        with patch.object(type(self.helper), 'get_bearer_token', return_value=self.token) as bearer, \
                patch.object(type(self.helper), 'validate', side_effect=Unauthorized()) as validate:
            with self.assertRaises(Unauthorized):
                forged.with_access_token_context()
            bearer.assert_called_once_with()
            validate.assert_called_once_with(self.token)
        with patch.object(type(self.helper), 'get_bearer_token', return_value=None), \
                patch.object(type(self.helper), 'validate', side_effect=Unauthorized()):
            with self.assertRaises(Unauthorized):
                user.with_access_token_context()
        with patch.object(users_module, 'request', SimpleNamespace(env=self.helper.env)), \
                patch.object(type(self.env['ir.http']), 'get_jwt_payload', return_value=payload), \
                patch.object(type(self.helper), 'validate') as validate:
            self.assertIs(user.with_access_token_context(validate=False).env.context[
                '__access_token_context'], payload)
            validate.assert_not_called()
        with patch.object(type(self.env['ir.http']), 'get_jwt_payload', return_value=dict(payload)), \
                patch.object(type(self.helper), 'validate') as validate:
            with self.assertRaises(Unauthorized):
                user.with_access_token_context(validate=False)
            validate.assert_not_called()

    def test_ut08_session_helper(self):
        user = SimpleNamespace(id=2468, login='synthetic')
        session = SimpleNamespace(get_context=Mock())
        request = SimpleNamespace(session=session, env=self.env)
        with patch.object(ir_http, 'request', request), \
                patch.object(ir_http.security, 'compute_session_token', return_value='synthetic-session-marker') as compute:
            ir_http.IrHttp.set_session(user)
            self.assertTrue(session.rotate)
            self.assertEqual(request.uid, user.id)
            self.assertFalse(request.disable_db)
            session.get_context.assert_called_once_with()
            compute.return_value = None
            ir_http.IrHttp.set_session(user)
            self.assertIsNone(request.uid)
            self.assertIsNone(session.uid)
            self.assertIsNone(session.login)
            compute.reset_mock()
            empty_user = self.env['res.users'].browse()
            ir_http.IrHttp.set_session(empty_user, session_token='synthetic-session-marker')
            compute.assert_not_called()
            self.assertFalse(request.uid)
            self.assertEqual(session.session_token, 'synthetic-session-marker')
            ir_http.IrHttp.set_session(empty_user)
            self.assertIsNone(request.uid)
            self.assertIsNone(session.uid)

    def test_ut09_direct_controller_contract(self):
        controller = main.RedirectController()
        url = 'http://127.0.0.1:19000/fixture'
        user = self.synthetic_user('controller', [self.env.ref('base.group_user')])

        class Env(dict):
            pass

        env = Env()
        env.user = user
        request = SimpleNamespace(env=env)
        with patch.object(main, 'request', request):
            for kind in ('access_token', 'auto_login'):
                response = controller.access_url(url=url, type=kind)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(json.loads(response.get_data(as_text=True)),
                                 {'url': url, 'url_access_token': url})
            self.assertEqual(controller.access_url(url=url, type='unsupported').status_code, 400)
            model = Mock(spec=['browse', 'get_url_access_token'])
            model.browse.return_value = model
            model.get_url_access_token.return_value = {'synthetic': True}
            env['synthetic.model'] = model
            response = controller.access_url(res_model='synthetic.model', res_id=1)
            self.assertEqual(json.loads(response.get_data(as_text=True)), {'synthetic': True})
            for kind in ('internal', 'public'):
                model = Mock(spec=['browse', 'get_internal_url', 'get_public_url'])
                model.browse.return_value = model
                model.get_internal_url.return_value = url
                model.get_public_url.return_value = url
                env['synthetic.model'] = model
                response = controller.access_url(res_model='synthetic.model', res_id=1, type_url=kind)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(json.loads(response.get_data(as_text=True))['url'], url)
            public_only = Mock(spec=['browse', 'get_public_url'])
            public_only.browse.return_value = public_only
            env['synthetic.model'] = public_only
            response = controller.access_url(res_model='synthetic.model', res_id=1, type_url='public')
            self.assertEqual(response.status_code, 400)  # existing mismatched guard
            public_only.get_public_url.assert_not_called()
            internal_only = Mock(spec=['browse', 'get_internal_url'])
            internal_only.browse.return_value = internal_only
            env['synthetic.model'] = internal_only
            with self.assertRaises(AttributeError):
                controller.access_url(res_model='synthetic.model', res_id=1, type_url='public')
            with patch.object(main, 'redirect', return_value='redirect-result') as redirect:
                self.assertEqual(controller.redirect_url(url), 'redirect-result')
                redirect.assert_called_once_with(url)
            self.assertEqual(controller.connection_test().status_code, 200)
            env['synthetic.model'] = object()
            with patch.object(main, 'call_kw', return_value=['synthetic']) as call:
                rpc = main.JsonRpcApi()
                self.assertEqual(rpc.call_kw('synthetic.model', 'read', [1], {}), ['synthetic'])
                call.assert_called_once_with(env['synthetic.model'], 'read', [1], {})
                call.reset_mock()
                with self.assertRaises(AccessError):
                    rpc.call_kw('synthetic.model', '_private', [], {})
                call.assert_not_called()
        with self.assertRaises(Unauthorized):
            controller.handle_exception(Unauthorized())
        self.assertEqual(controller.handle_exception(ValueError('synthetic')).status_code, 500)
        custom = exceptions.handle_exception(exceptions.APIException('synthetic', 'fixture', 409))
        self.assertEqual(custom.status_code, 409)
        self.assertEqual(json.loads(custom.get_data(as_text=True))['error'], 'synthetic')
        self.assertEqual(exceptions.handle_exception(ValueError('synthetic')).status_code, 500)

    def test_ut10_wizard_and_seed(self):
        template = self.synthetic_user('template', [self.env.ref('base.group_user'),
                                                    self.env.ref('amr_resource.group_machine')])
        template.active = False
        wizard = self.env['create.user.wizard'].create({
            'name': 'Synthetic Created', 'login': 'resource-created',
            'email': 'resource-created@example.invalid', 'template_id': template.id})
        action = wizard.action_create()
        self.assertEqual(action['res_model'], 'res.users')
        self.assertEqual(action['view_mode'], 'form')
        self.assertEqual(action['target'], 'current')
        created = self.env['res.users'].browse(action['res_id'])
        self.assertEqual(created.name, wizard.name)
        self.assertEqual(created.login, wizard.login)
        self.assertEqual(created.email, wizard.email)
        self.assertEqual(created.share, template.share)
        self.assertTrue(template.groups_id <= created.groups_id)
        self.assertTrue(created.active)
        with self.assertRaises(ValidationError):
            wizard.action_create()
        for field in ('name', 'login', 'template_id'):
            self.assertTrue(wizard._fields[field].required)
            values = {'name': 'Synthetic Required', 'login': 'resource-required',
                      'template_id': template.id}
            values[field] = False
            # Roll back the failing DB statement before asserting its error class;
            # suppress SQL logger output rather than recording raw error details.
            with patch('odoo.sql_db._logger'):
                with self.assertRaises((ValidationError, IntegrityError)), self.cr.savepoint():
                    self.env['create.user.wizard'].create(values)
        tree = ElementTree.parse(str(ROOT / 'security/res_groups.xml'))
        data = tree.find('data')
        self.assertEqual(data.get('noupdate'), '1')
        records = {r.get('id'): r for r in data.findall('record')}
        for xml_id in ('group_machine', 'group_technical'):
            self.assertIn(xml_id, records)
            self.assertTrue(self.env.ref('amr_resource.' + xml_id))
        templates = [r for r in records.values() if r.get('model') == 'res.users'
                     and r.find("field[@name='active']") is not None]
        self.assertEqual(len(templates), 1)
        seed = templates[0]
        self.assertEqual(seed.find("field[@name='active']").get('eval'), 'False')
        self.assertEqual(seed.find("field[@name='share']").get('eval'), 'False')
        self.assertIn('group_machine', seed.find("field[@name='groups_id']").get('eval'))
        manifest = ast.literal_eval((ROOT / '__manifest__.py').read_text())
        self.assertEqual(manifest['version'], '13.0.1.0.0')
        self.assertEqual(manifest['depends'], ['base', 'web', 'base_setup'])
        for path in ('security/res_groups.xml', 'views/res_config_settings_views.xml',
                     'wizard/create_user_wizard.xml'):
            self.assertIn(path, manifest['data'])
        for path, imports in (('__init__.py', ['controllers', 'models', 'wizard', 'exceptions']),
                              ('models/__init__.py', ['helper', 'ir_http', 'res_users', 'res_config_settings']),
                              ('wizard/__init__.py', ['create_user_wizard'])):
            parsed = ast.parse((ROOT / path).read_text())
            imported = [alias.name for node in parsed.body if isinstance(node, ast.ImportFrom)
                        for alias in node.names]
            for name in imports:
                self.assertIn(name, imported)
