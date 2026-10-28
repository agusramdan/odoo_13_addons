import importlib.util
import base64
import json
import sys
import unittest
from urllib.parse import quote_plus, urlencode
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import patch

ADDON = Path(__file__).resolve().parents[1]


class _Field:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs


class _Response:
    def __init__(self, response='', status=200, content_type=None, headers=None, **kwargs):
        self.response = response
        self.status_code = status
        self.headers = headers or {}


class _Unauthorized(Exception):
    def __init__(self, response=None, **kwargs):
        self.response = response


class _BadRequest(Exception):
    def __init__(self, response=None, **kwargs):
        self.response = response


def _load_auth_module():
    odoo = ModuleType('odoo')
    odoo.api = SimpleNamespace(model=lambda method: method)
    odoo.fields = SimpleNamespace(Selection=_Field)
    odoo.models = SimpleNamespace(AbstractModel=object, Model=object)
    http_module = ModuleType('odoo.http')
    http_module.request = SimpleNamespace(httprequest=None)
    werkzeug = ModuleType('werkzeug')
    exceptions = ModuleType('werkzeug.exceptions')
    exceptions.BadRequest = _BadRequest
    exceptions.Unauthorized = _Unauthorized
    wrappers = ModuleType('werkzeug.wrappers')
    wrappers.Response = _Response
    module_name = '_offline_token_client_auth'
    spec = importlib.util.spec_from_file_location(
        module_name, str(ADDON / 'models' / 'token_client_auth.py'))
    module = importlib.util.module_from_spec(spec)
    replacements = {
        'odoo': odoo,
        'odoo.http': http_module,
        'werkzeug': werkzeug,
        'werkzeug.exceptions': exceptions,
        'werkzeug.wrappers': wrappers,
    }
    with patch.dict(sys.modules, replacements):
        spec.loader.exec_module(module)
    return module, http_module.request


class _MultiDict:
    def __init__(self, pairs=()):
        self.pairs = list(pairs)

    def __contains__(self, key):
        return any(name == key for name, _value in self.pairs)

    def keys(self):
        return list(dict.fromkeys(name for name, _value in self.pairs))

    def getlist(self, key):
        return [value for name, value in self.pairs if name == key]

    def get(self, key, default=None):
        values = self.getlist(key)
        return values[0] if values else default


class _Headers(dict):
    def __init__(self, values=None, lists=None):
        super().__init__(values or {})
        self._lists = lists or {}

    def getlist(self, key):
        return list(self._lists.get(key.lower(), []))


class _Client:
    def __init__(self, client_id='post-client', secret='post-secret',
                 method='client_secret_post', confidential=True, active=True):
        self.client_id = client_id
        self.expected_secret = secret
        self.authentication_method = method
        self.is_confidential = confidential
        self.active = active

    def check_credentials(self, secret):
        if secret != self.expected_secret:
            raise ValueError('synthetic mismatch')
        return True


class _ClientModel:
    def __init__(self, client):
        self.client = client

    def sudo(self):
        return self

    def search(self, domain, limit=1):
        requested = next(value for name, operator, value in domain if name == 'client_id')
        if requested == self.client.client_id and self.client.active:
            return self.client
        return None


class _Environment(dict):
    pass


class TestTokenClientAuthOffline(unittest.TestCase):
    def _request_helper(self, client, body_pairs=(), query_pairs=(),
                        authorization_values=(), content_type='application/x-www-form-urlencoded',
                        method='POST', raw_body=None):
        module, request = _load_auth_module()
        helper = module.TokenHelperClientAuth()
        helper.env = _Environment({'oidc.client': _ClientModel(client)})
        headers = _Headers(
            {'Content-Type': content_type},
            {'authorization': list(authorization_values)},
        )
        if authorization_values:
            headers['Authorization'] = authorization_values[0]
        body = raw_body if raw_body is not None else urlencode(list(body_pairs)).encode('ascii')
        request.httprequest = SimpleNamespace(
            method=method,
            mimetype=content_type.split(';', 1)[0].strip().lower(),
            args=_MultiDict(query_pairs),
            form=_MultiDict(body_pairs),
            headers=headers,
            query_string=urlencode(list(query_pairs)).encode('ascii'),
            get_data=lambda cache=True: body,
        )
        return helper

    def _captured_response(self, helper):
        try:
            helper._authenticate_token_client()
        except Exception as error:
            return getattr(error, 'response', None)
        self.fail('request unexpectedly authenticated')

    def test_explicit_post_method_authenticates_form_credentials(self):
        module, request = _load_auth_module()
        client = _Client()
        helper = module.TokenHelperClientAuth()
        helper.env = _Environment({'oidc.client': _ClientModel(client)})
        request.httprequest = SimpleNamespace(
            method='POST',
            mimetype='application/x-www-form-urlencoded',
            args=_MultiDict(),
            form=_MultiDict((('client_id', client.client_id),
                             ('client_secret', 'post-secret'),
                             ('grant_type', 'client_credentials'))),
            headers=_Headers({'Content-Type': 'application/x-www-form-urlencoded'}),
            get_data=lambda cache=True: b'client_id=post-client&client_secret=post-secret&grant_type=client_credentials',
        )
        try:
            authenticated = helper._authenticate_token_client()
        except Exception as error:
            self.fail('valid explicit Post credentials were rejected: %s' % type(error).__name__)
        self.assertIs(authenticated, client)

    def test_failed_explicit_post_returns_400_without_basic_challenge(self):
        module, request = _load_auth_module()
        client = _Client()
        helper = module.TokenHelperClientAuth()
        helper.env = _Environment({'oidc.client': _ClientModel(client)})
        request.httprequest = SimpleNamespace(
            method='POST',
            mimetype='application/x-www-form-urlencoded',
            args=_MultiDict(),
            form=_MultiDict((('client_id', client.client_id),
                             ('client_secret', 'wrong-secret'),
                             ('grant_type', 'client_credentials'))),
            headers=_Headers({'Content-Type': 'application/x-www-form-urlencoded'}),
            get_data=lambda cache=True: b'client_id=post-client&client_secret=wrong-secret&grant_type=client_credentials',
        )
        try:
            helper._authenticate_token_client()
        except Exception as error:
            response = error.response
            self.assertEqual(response.status_code, 400)
            self.assertEqual(json.loads(response.response)['error'], 'invalid_client')
            self.assertNotIn('WWW-Authenticate', response.headers)
        else:
            self.fail('invalid Post credentials unexpectedly authenticated')

    def test_missing_authentication_returns_400_without_basic_challenge(self):
        module, request = _load_auth_module()
        helper = module.TokenHelperClientAuth()
        helper.env = _Environment({'oidc.client': _ClientModel(_Client())})
        response = None
        request.httprequest = SimpleNamespace(
            method='POST',
            mimetype='application/x-www-form-urlencoded',
            args=_MultiDict(),
            form=_MultiDict((('grant_type', 'client_credentials'),)),
            headers=_Headers({'Content-Type': 'application/x-www-form-urlencoded'}),
            get_data=lambda cache=True: b'grant_type=client_credentials',
        )
        try:
            helper._authenticate_token_client()
        except Exception as error:
            response = error.response
        self.assertIsNotNone(response, 'missing authentication was accepted')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response.response)['error'], 'invalid_client')
        self.assertNotIn('WWW-Authenticate', response.headers)

    def test_non_basic_authorization_is_invalid_request(self):
        helper = self._request_helper(
            _Client(), authorization_values=('Bearer synthetic-token',),
            body_pairs=(('grant_type', 'client_credentials'),))
        response = self._captured_response(helper)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response.response)['error'], 'invalid_request')
        self.assertNotIn('WWW-Authenticate', response.headers)

    def test_basic_plus_body_credentials_is_invalid_request_without_fallback(self):
        basic = base64.b64encode(b'post-client:post-secret').decode('ascii')
        helper = self._request_helper(
            _Client(),
            body_pairs=(('client_id', 'post-client'),
                        ('client_secret', 'post-secret'),
                        ('grant_type', 'client_credentials')),
            authorization_values=('Basic ' + basic,))
        response = self._captured_response(helper)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response.response)['error'], 'invalid_request')
        self.assertNotIn('WWW-Authenticate', response.headers)


    def test_query_credentials_are_invalid_request_even_with_basic(self):
        basic = base64.b64encode(b'post-client:post-secret').decode('ascii')
        helper = self._request_helper(
            _Client(),
            body_pairs=(('grant_type', 'client_credentials'),),
            query_pairs=(('client_id', 'post-client'),),
            authorization_values=('Basic ' + basic,))
        response = self._captured_response(helper)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response.response)['error'], 'invalid_request')
        self.assertNotIn('WWW-Authenticate', response.headers)


    def test_duplicate_consumed_form_parameters_are_invalid_request(self):
        cases = (
            (('client_id', 'post-client'), ('client_id', 'post-client'),
             ('client_secret', 'post-secret'), ('grant_type', 'client_credentials')),
            (('client_id', 'post-client'), ('client_secret', 'post-secret'),
             ('client_secret', 'post-secret'), ('grant_type', 'client_credentials')),
            (('client_id', 'post-client'), ('client_secret', 'post-secret'),
             ('grant_type', 'client_credentials'), ('grant_type', 'client_credentials')),
        )
        for body_pairs in cases:
            with self.subTest(duplicate=body_pairs):
                helper = self._request_helper(_Client(), body_pairs=body_pairs)
                response = self._captured_response(helper)
                self.assertEqual(response.status_code, 400)
                self.assertEqual(json.loads(response.response)['error'], 'invalid_request')

    def test_malformed_form_percent_escape_is_invalid_request(self):
        helper = self._request_helper(
            _Client(),
            body_pairs=(('grant_type', 'client_credentials'),),
            raw_body=b'client_id=post%ZZ&client_secret=post-secret&grant_type=client_credentials')
        response = self._captured_response(helper)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response.response)['error'], 'invalid_request')


    def test_unsupported_content_type_is_invalid_request(self):
        basic = base64.b64encode(b'post-client:post-secret').decode('ascii')
        helper = self._request_helper(
            _Client(),
            body_pairs=(('grant_type', 'client_credentials'),),
            authorization_values=('Basic ' + basic,),
            content_type='application/json')
        response = self._captured_response(helper)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response.response)['error'], 'invalid_request')
        self.assertNotIn('WWW-Authenticate', response.headers)


    def test_duplicate_authorization_header_values_are_invalid_request(self):
        client = _Client()
        client.authentication_method = 'client_secret'
        basic = base64.b64encode(b'post-client:post-secret').decode('ascii')
        values = (
            ('Basic ' + basic, 'Basic ' + basic),
            ('Basic ' + basic + ', Basic ' + basic,),
            ('Basic ' + basic + ' Basic ' + basic,),
        )
        for authorization_values in values:
            with self.subTest(header_count=len(authorization_values), value_count=len(authorization_values[0].split())):
                helper = self._request_helper(
                    client, body_pairs=(('grant_type', 'client_credentials'),),
                    authorization_values=authorization_values)
                response = self._captured_response(helper)
                self.assertEqual(response.status_code, 400)
                self.assertEqual(json.loads(response.response)['error'], 'invalid_request')
                self.assertNotIn('WWW-Authenticate', response.headers)


    def test_unknown_basic_client_returns_invalid_client_challenge(self):
        basic = base64.b64encode(b'unknown-client:synthetic-secret').decode('ascii')
        helper = self._request_helper(
            _Client(), body_pairs=(('grant_type', 'client_credentials'),),
            authorization_values=('Basic ' + basic,))
        response = self._captured_response(helper)
        self.assertIsNotNone(response, 'unknown client caused an unstructured exception')
        self.assertEqual(response.status_code, 401)
        self.assertEqual(json.loads(response.response)['error'], 'invalid_client')
        self.assertEqual(response.headers.get('WWW-Authenticate'), 'Basic')


    def test_basic_credentials_decode_form_encoding_and_first_colon(self):
        client_id = 'encoded:client +space'
        secret = 'secret:with+space value'
        client = _Client(client_id=client_id, secret=secret, method='client_secret')
        encoded = quote_plus(client_id, safe='') + ':' + quote_plus(secret, safe='')
        basic = base64.b64encode(encoded.encode('ascii')).decode('ascii')
        helper = self._request_helper(
            client, body_pairs=(('grant_type', 'client_credentials'),),
            authorization_values=('Basic ' + basic,))
        self.assertIs(helper._authenticate_token_client(), client)

    def test_nonconfidential_client_rejects_basic_authentication(self):
        client = _Client(method='client_secret', confidential=False)
        basic = base64.b64encode(b'post-client:post-secret').decode('ascii')
        helper = self._request_helper(
            client, body_pairs=(('grant_type', 'client_credentials'),),
            authorization_values=('Basic ' + basic,))
        response = self._captured_response(helper)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(json.loads(response.response)['error'], 'invalid_client')
        self.assertEqual(response.headers.get('WWW-Authenticate'), 'Basic')

    def test_nonconfidential_client_rejects_post_authentication(self):
        client = _Client(confidential=False)
        helper = self._request_helper(
            client, body_pairs=(('client_id', 'post-client'),
                                ('client_secret', 'post-secret'),
                                ('grant_type', 'client_credentials')))
        response = self._captured_response(helper)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response.response)['error'], 'invalid_client')
        self.assertNotIn('WWW-Authenticate', response.headers)


if __name__ == '__main__':
    unittest.main()
