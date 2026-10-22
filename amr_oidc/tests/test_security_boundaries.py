"""Offline Rev4 contracts only; not Odoo ORM/RPC/HTTP or UAT evidence."""
import ast
import csv
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from support import ADDON, load


class SecurityBoundaries(unittest.TestCase):
    def test_refresh_acl_system_only(self):
        with (ADDON / 'security/ir.model.access.csv').open() as stream:
            rows = [r for r in csv.DictReader(stream)
                    if r['model_id:id'] == 'model_oidc_refresh_token']
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['group_id:id'], 'base.group_system')
        self.assertEqual([rows[0]['perm_' + op] for op in
                          ('read', 'write', 'create', 'unlink')], ['1', '1', '1', '0'])

    def test_refresh_expiry_boundary(self):
        module = load('models/oidc_refresh_token.py')
        model = module.OidcRefreshToken()
        accessor = '_get_secret' if hasattr(model, '_get_secret') else 'get_secret'
        setattr(model, accessor, Mock(return_value=object()))
        model.get_issuer = Mock(return_value='synthetic-issuer')
        model.get_algorithm = Mock(return_value='HS256')
        payload = {'token': object()}
        module.jwt.decode = Mock(return_value=payload)
        module.fields.Datetime = SimpleNamespace(now=lambda: 100)
        row = {'token': payload['token'], 'revoked': False, 'expires_at': 101}
        def search(domain, limit):
            operators = {'=': lambda a, b: a == b,
                         '>': lambda a, b: a > b, '<': lambda a, b: a < b}
            return all(operators[op](row[key], value) for key, op, value in domain)
        model.sudo = Mock(return_value=SimpleNamespace(search=search))
        for expiry, revoked, eligible in [(101, False, True), (100, False, False),
                                          (99, False, False), (101, True, False)]:
            row.update(expires_at=expiry, revoked=revoked)
            with self.subTest(expiry=expiry, revoked=revoked):
                self.assertEqual(model.validate_token(object(), 'synthetic-audience'),
                                 payload if eligible else None)

    def test_client_and_code_admin_boundary(self):
        with (ADDON / 'security/ir.model.access.csv').open() as stream:
            rows = list(csv.DictReader(stream))
        for model in ('model_oidc_client', 'model_oidc_authorization_code'):
            grants = [r for r in rows if r['model_id:id'] == model]
            self.assertEqual(len(grants), 1)
            self.assertEqual(grants[0]['group_id:id'], 'base.group_erp_manager')
            self.assertEqual([grants[0]['perm_' + op] for op in
                              ('read', 'write', 'create', 'unlink')], ['1'] * 4)
        tree = ast.parse((ADDON / 'models/oidc_client.py').read_text())
        field = next(n.value for n in ast.walk(tree) if isinstance(n, ast.Assign)
                     and any(isinstance(t, ast.Name) and t.id == 'client_secret'
                             for t in n.targets))
        self.assertEqual({k.arg: ast.literal_eval(k.value) for k in field.keywords}
                         .get('groups'), 'base.group_erp_manager')

    def test_redirect_exact_and_fixed_callback(self):
        module = load('models/oidc_client.py')
        client = module.OidcClient()
        target = 'https://example.invalid/callback?mode=one#done'
        client.redirect_path = False
        client.redirect_uri = target + '\nhttps://second.invalid/callback'
        for value, allowed in [(target, True), ('https://second.invalid/callback', True),
                               (None, False), ('', False),
                               (target.replace('https:', 'http:'), False),
                               (target.replace('example.invalid', 'attacker.invalid'), False),
                               (target.replace('/callback', '/other'), False),
                               (target.replace('one', 'two'), False),
                               (target.replace('#done', '#other'), False),
                               (target + '&extra=1', False)]:
            self.assertEqual(client.validate_redirect_uri(value), allowed)
        for config in (False, '', '\n'):
            client.redirect_uri = config
            self.assertFalse(client.validate_redirect_uri(target))
        client.redirect_path = 'auth_oauth_oidc'
        client.web_base_url = 'https://odoo.invalid'
        callback = client.web_base_url + module.REDIRECT_MODE[client.redirect_path]
        for value, allowed in [(None, True), (callback, True), (target, False),
                               (callback + '?extra=1', False),
                               (callback + '#other', False)]:
            self.assertEqual(client.validate_redirect_uri(value), allowed)
        client.redirect_path = 'unknown'
        self.assertFalse(client.validate_redirect_uri(None))

    def test_redirect_rejected_before_issuance(self):
        module = load('controllers/main.py')
        client_module = load('models/oidc_client.py')
        client = client_module.OidcClient()
        client.redirect_path = False
        client.redirect_uri = 'https://example.invalid/callback'
        client.create_authorization_code = Mock()
        client.create_access_token = Mock()
        store = Mock()
        store.sudo.return_value = store
        store.search.return_value = client
        module.request.env = {'oidc.client': store}
        controller = module.ControllerOIDC()
        rejected = object()
        controller.invalid_response = Mock(return_value=rejected)
        for response_type in ('code', 'token'):
            for target in (None, '', 'https://attacker.invalid/callback',
                           client.redirect_uri + '?extra=1'):
                self.assertIs(controller.oidc_authorize(client_id='synthetic-client',
                              response_type=response_type, redirect_uri=target), rejected)
                client.create_authorization_code.assert_not_called()
                client.create_access_token.assert_not_called()

    def test_state_changing_routes_protected_post(self):
        tree = ast.parse((ADDON / 'controllers/main.py').read_text())
        for name in ('login_submit', 'authorize_continue'):
            method = next(n for n in ast.walk(tree)
                          if isinstance(n, ast.FunctionDef) and n.name == name)
            route = method.decorator_list[0]
            options = {k.arg: ast.literal_eval(k.value) for k in route.keywords}
            self.assertEqual(options.get('methods'), ['POST'])
            self.assertIs(options.get('csrf'), True)
        import xml.etree.ElementTree as ET
        root = ET.fromstring((ADDON / 'views/login_template.xml').read_text())
        for action in ('/oidc/login/submit', '/oidc/authorize_continue'):
            forms = [n for n in root.iter('form') if n.get('action') == action]
            self.assertEqual(len(forms), 1)
            self.assertEqual(forms[0].get('method').lower(), 'post')
            inputs = {n.get('name'): n for n in forms[0].iter('input')}
            self.assertEqual(inputs['csrf_token'].get('t-att-value'),
                             'request.csrf_token()')
            self.assertIn('params', inputs)
        self.assertFalse(any('/oidc/authorize_continue' in str(n.attrib)
                             for n in root.iter('a')))

    def test_secret_getter_not_public_and_internal_use_preserved(self):
        module = load('models/oidc_refresh_token.py')
        self.assertFalse(hasattr(module.OidcRefreshToken, 'get_secret'))
        secret = object()
        config = Mock()
        config.sudo.return_value = config
        config.get_param.return_value = secret
        for role in ('PUBLIC_A', 'PORTAL_A', 'USER_A'):
            model = module.OidcRefreshToken()
            model.env = {'ir.config_parameter': config}
            with self.subTest(role=role):
                with self.assertRaises(AttributeError):
                    model.get_secret()
                config.get_param.assert_not_called()
        self.assertIs(model._get_secret(), secret)
        config.get_param.assert_called_once_with('amr_token.secret')
        tree = ast.parse((ADDON / 'models/oidc_refresh_token.py').read_text())
        for name in ('create_refresh_token', 'validate_token'):
            fn = next(n for n in ast.walk(tree)
                      if isinstance(n, ast.FunctionDef) and n.name == name)
            calls = [n.func.attr for n in ast.walk(fn) if isinstance(n, ast.Call)
                     and isinstance(n.func, ast.Attribute)]
            self.assertIn('_get_secret', calls)
            self.assertNotIn('get_secret', calls)
