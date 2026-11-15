"""Offline controller-boundary tests; not a native HTTP or ORM test."""
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest import mock


SUPPORT = Path(__file__).resolve().parents[1] / 'support.py'


class IntrospectionControllerTests(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location('introspection_support', str(SUPPORT))
        if spec is None or spec.loader is None:
            raise ImportError('cannot load unit test support')
        support = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(support)
        self.module = support.load_controller()
        self.controller = self.module.ControllerOIDC()
        self.token = 'synthetic-token'
        self.client_id = 'synthetic-client'
        self.secret = 'synthetic-credential'
        self.helper = mock.Mock()
        self.helper.get_basic_auth.return_value = (self.client_id, self.secret)
        self.helper.decode.return_value = {
            'sub': 'subject', 'aud': self.client_id, 'scope': 'read',
            'internal': 'not-for-response',
        }
        self.client = mock.Mock()
        self.client.client_id = self.client_id
        self.client.allow_introspection = True
        def check_credentials(value):
            if value != self.secret:
                raise ValueError('invalid credential')
        self.client.check_credentials.side_effect = check_credentials
        self.clients = mock.Mock()
        self.clients.sudo.return_value.search.return_value = self.client
        self.module.request.env = {'amr.oidc.helper': self.helper, 'oidc.client': self.clients}
        self.request = SimpleNamespace(method='POST', is_secure=True, args={},
                                       form={'token': self.token})
        self.module.request.httprequest = self.request

    def invoke(self, **kwargs):
        return self.controller.api_oidc_introspect(**kwargs)

    def test_secure_form_authenticates_and_projects_allowlist(self):
        response = self.invoke(token=self.token)
        self.assertEqual(response.status_code, 200)
        payload = json.loads(response.data.decode('utf-8'))
        self.assertEqual(payload, {'active': True, 'sub': 'subject',
                                   'aud': self.client_id, 'scope': 'read'})
        self.assertFalse(self.secret in response.data.decode('utf-8'))
        self.helper.get_basic_auth.assert_called_once_with()
        self.assertEqual(self.client.check_credentials.call_count, 1)
        self.assertTrue(self.client.check_credentials.call_args[0][0] == self.secret)
        self.clients.sudo.return_value.search.assert_called_once_with(
            [('client_id', '=', self.client_id), ('active', '=', True)], limit=1)
        self.helper.decode.assert_called_once_with(self.token, audience=self.client_id)

    def test_insecure_query_and_invalid_forms_rejected_before_auth(self):
        cases = [
            ('insecure', {'is_secure': False}, {'token': self.token}),
            ('query', {'args': {'extra': 'value'}}, {'token': self.token}),
            ('missing', {'form': {}}, {}),
            ('empty', {'form': {'token': ''}}, {'token': ''}),
            ('extra_form', {'form': {'token': self.token, 'extra': 'value'}},
             {'token': self.token, 'extra': 'value'}),
            ('mismatched_kwargs', {}, {'token': 'other'}),
            ('wrong_method', {'method': 'GET'}, {'token': self.token}),
        ]
        for name, overrides, kwargs in cases:
            with self.subTest(case=name):
                self.helper.reset_mock()
                self.clients.reset_mock()
                self.client.reset_mock()
                self.request.method = 'POST'
                self.request.is_secure = True
                self.request.args = {}
                self.request.form = {'token': self.token}
                for key, value in overrides.items():
                    setattr(self.request, key, value)
                response = self.invoke(**kwargs)
                self.assertEqual(response.status_code, 400)
                self.assertEqual(json.loads(response.data.decode('utf-8'))['error'],
                                 'invalid_request')
                self.helper.get_basic_auth.assert_not_called()
                self.clients.sudo.assert_not_called()
                self.client.check_credentials.assert_not_called()
                self.helper.decode.assert_not_called()

    def test_auth_failure_stops_decode(self):
        self.client.check_credentials.side_effect = ValueError('invalid credential')
        response = self.invoke(token=self.token)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(json.loads(response.data.decode('utf-8'))['error'], 'invalid_client')
        self.assertEqual(self.client.check_credentials.call_count, 1)
        self.assertTrue(self.client.check_credentials.call_args[0][0] == self.secret)
        self.helper.decode.assert_not_called()

    def test_decode_failure_returns_inactive(self):
        self.helper.decode.side_effect = ValueError('invalid token')
        response = self.invoke(token=self.token)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data.decode('utf-8')), {'active': False})
        self.assertEqual(self.client.check_credentials.call_count, 1)
        self.assertTrue(self.client.check_credentials.call_args[0][0] == self.secret)
        self.helper.decode.assert_called_once_with(self.token, audience=self.client_id)
