import importlib.util
import json
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from werkzeug.exceptions import BadRequest, Unauthorized

SCRIPTS = Path(__file__).parents[3] / '.agents' / 'skills' / 'odoo-unit-test' / 'scripts'
sys.path.insert(0, str(SCRIPTS))
from mock_odoo import odoo_modules


def load_modules():
    root = Path(__file__).parents[2]
    service = types.ModuleType('odoo.service')
    service.security = types.SimpleNamespace(compute_session_token=Mock())
    with odoo_modules():
        import odoo.api
        import odoo.models
        odoo.api.call_kw = Mock()
        odoo.models.check_method_name = Mock()
        with patch.dict(sys.modules, {'odoo.service': service}):
            modules = []
            for name, path in [('controller', root / 'controllers' / 'main.py'),
                               ('ir_http', root / 'models' / 'ir_http.py')]:
                spec = importlib.util.spec_from_file_location(name, str(path))
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                modules.append(module)
    return modules


def body(response):
    return json.loads(response.get_data(as_text=True))


class TestController(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m, _ = load_modules()

    def setUp(self):
        self.controller = self.m.RedirectController()
        self.user = types.SimpleNamespace(_resource_access_url=Mock(return_value='https://example.test/token'))
        self.request = types.SimpleNamespace(env={'demo': types.SimpleNamespace(browse=Mock())})
        self.request.env = type('Env', (dict,), {})(self.request.env)
        self.request.env.user = self.user
        self.request_patch = patch.object(self.m, 'request', self.request)
        self.request_patch.start()
        self.addCleanup(self.request_patch.stop)

    def test_response_and_exception_contract(self):
        response = self.controller.make_response()
        self.assertEqual(body(response)['error'], 'unknown_error')
        response = self.controller.handle_exception(ValueError('bad'), status=400)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(body(response), {'success': False, 'error': 'general_error', 'error_description': 'bad'})
        with self.assertRaises(BadRequest):
            self.controller.handle_exception(BadRequest())
        self.assertEqual(body(self.controller.connection_test()), {'data': 'test connection machine ok'})

    def test_redirect_and_explicit_access_url(self):
        self.assertEqual(self.controller.redirect_url('https://example.test').location, 'https://example.test/token')
        response = self.controller.access_url(url='https://example.test', type='access_token')
        self.assertEqual(body(response), {'url': 'https://example.test', 'url_access_token': 'https://example.test/token'})
        self.user._resource_access_url.assert_called_with('https://example.test', url_type='access_token')
        response = self.controller.access_url(url='x', type='invalid')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(body(response)['error'], 'invalid type')

    def test_record_url_selection_and_missing_methods(self):
        browse = self.request.env['demo'].browse
        browse.return_value = types.SimpleNamespace(get_url_access_token=lambda: {'url': 'direct'})
        self.assertEqual(body(self.controller.access_url(res_model='demo', res_id=4)), {'url': 'direct'})
        browse.assert_called_with(4)
        browse.return_value = types.SimpleNamespace(get_internal_url=lambda: 'internal', get_public_url=lambda: 'public')
        self.assertEqual(body(self.controller.access_url(res_model='demo'))['url'], 'internal')
        self.assertEqual(body(self.controller.access_url(res_model='demo', type_url='public'))['url'], 'public')
        browse.return_value = object()
        for kind in ('internal', 'public'):
            response = self.controller.access_url(res_model='demo', type_url=kind)
            self.assertEqual(response.status_code, 400)
            self.assertEqual(body(response)['error_description'], 'get_%s_url not found' % kind)

    def test_rpc_denies_protected_models_and_checks_method_before_dispatch(self):
        rpc = self.m.JsonRpcApi()
        self.m.check_method_name.reset_mock()
        self.m.call_kw.reset_mock(return_value=True)
        for model in self.m.EXCLUDE_MODEL:
            with self.assertRaises(self.m.AccessError):
                rpc.call_kw(model, 'search', [], {})
        self.m.check_method_name.assert_not_called()
        self.m.call_kw.assert_not_called()
        self.m.call_kw.return_value = 'result'
        self.assertEqual(rpc.call_kw('demo', 'search', [1], {'limit': 2}), 'result')
        self.m.check_method_name.assert_called_once_with('search')
        self.m.call_kw.assert_called_once_with(self.request.env['demo'], 'search', [1], {'limit': 2})
        self.m.check_method_name.side_effect = ValueError('private')
        self.m.call_kw.reset_mock()
        try:
            with self.assertRaises(ValueError):
                rpc.call_kw('demo', '_private', [], {})
            self.m.call_kw.assert_not_called()
        finally:
            self.m.check_method_name.side_effect = None


class TestAuthentication(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _, cls.m = load_modules()

    def setUp(self):
        self.helper = types.SimpleNamespace(decode=Mock(return_value={'sub': 'alice'}),
                                            get_user_match=Mock(return_value=types.SimpleNamespace(id=7)),
                                            _verified=Mock(return_value=True))
        httprequest = types.SimpleNamespace(environ={'HTTP_AUTHORIZATION': 'Bearer bearer'},
                                            headers={}, args={'access_token': 'param'}, form={})
        self.request = types.SimpleNamespace(env={'oidc.issuer.register': self.helper}, uid=None,
                                             httprequest=httprequest)
        request_patch = patch.object(self.m, 'request', self.request)
        request_patch.start()
        self.addCleanup(request_patch.stop)
        self.http = self.m.IrHttp

    def test_token_authenticates_and_preserves_existing_user_context(self):
        self.assertIsNone(self.http._authenticate_token('token'))
        self.assertEqual((self.request.uid, self.request.jwt_token, self.request.jwt_payload),
                         (7, 'token', {'sub': 'alice'}))
        self.helper.decode.assert_called_once_with('token')
        self.request.jwt_token = 'old'
        self.http._authenticate_token('new')
        self.assertEqual(self.request.jwt_token, 'old')

    def test_invalid_token_and_unmatched_user_are_unauthorized(self):
        self.helper.decode.side_effect = ValueError('secret')
        with self.assertRaises(Unauthorized) as exc:
            self.http._authenticate_token('bad')
        self.assertIsNone(exc.exception.__cause__)
        self.helper.decode.side_effect = None
        self.helper.get_user_match.return_value = None
        with self.assertRaises(Unauthorized):
            self.http._authenticate_token('bad')
        self.assertIsNone(self.request.uid)

    def test_token_sources_and_user_fallback_order(self):
        with patch.object(self.http, '_authenticate_token', return_value='ok') as authenticate:
            self.assertEqual(self.http._auth_method_machine(), 'ok')
            authenticate.assert_called_with('bearer')
            self.assertEqual(self.http._auth_method_params(), 'ok')
            authenticate.assert_called_with('param')
            with patch.object(self.http, '_auth_method_user', create=True, return_value='session'):
                self.assertEqual(self.http._auth_method_user_or_param(), 'session')
            with patch.object(self.http, '_auth_method_user', create=True, side_effect=Unauthorized()):
                self.assertEqual(self.http._auth_method_user_or_param(), 'ok')
                authenticate.assert_called_with('bearer')
                self.request.httprequest.environ.clear()
                self.assertEqual(self.http._auth_method_user_or_param(), 'ok')
                authenticate.assert_called_with('param')

    def test_verified_payload_and_session_state(self):
        self.request.jwt_payload = {'sub': 'alice'}
        self.assertEqual(self.http.get_jwt_payload(), {'sub': 'alice'})
        self.helper._verified.return_value = False
        self.assertEqual(self.http.get_jwt_payload(), {})
        session = types.SimpleNamespace(get_context=Mock())
        self.request.session = session
        user = types.SimpleNamespace(id=7, login='alice')
        self.m.security.compute_session_token.return_value = 'session-token'
        self.http.set_session(user)
        self.assertEqual((session.uid, session.login, session.session_token, self.request.uid),
                         (7, 'alice', 'session-token', 7))
        self.assertTrue(session.rotate)
        self.assertFalse(self.request.disable_db)
        session.get_context.assert_called_once_with()
        self.m.security.compute_session_token.return_value = None
        self.http.set_session(user)
        self.assertEqual((session.uid, session.login, self.request.uid), (None, None, None))


if __name__ == '__main__':
    unittest.main()
