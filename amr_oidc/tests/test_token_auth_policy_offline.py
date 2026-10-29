import importlib.util
import base64
import json
import logging
from io import BytesIO, StringIO
import sys
import unittest
from urllib.parse import quote_plus, urlencode
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import Mock, patch

from support import load, load_controller, StubHTTPException, StubResponse

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


def _load_auth_module(parent_helper=object):
    odoo = ModuleType('odoo')
    odoo.api = SimpleNamespace(model=lambda method: method)
    odoo.fields = SimpleNamespace(Selection=_Field)
    odoo.models = SimpleNamespace(AbstractModel=parent_helper, Model=object)
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
                        method='POST', raw_body=None, parent_helper=object):
        module, request = _load_auth_module(parent_helper)
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


    def test_fake_header_lists_and_combined_values_are_invalid_request(self):
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


    def _assert_error(self, helper, error, basic=False):
        response = self._captured_response(helper)
        self.assertIsNotNone(response, 'unstructured authentication error')
        self.assertEqual(response.status_code, 401 if basic else 400)
        self.assertEqual(response.headers.get('WWW-Authenticate'), 'Basic' if basic else None)
        payload = json.loads(response.response)
        self.assertEqual(payload['error'], error)
        for field in ('access_token', 'refresh_token', 'id_token'):
            self.assertNotIn(field, payload)
        return response

    def test_legacy_and_explicit_basic_authenticate(self):
        for method in ('client_secret', 'client_secret_basic'):
            client = _Client(method=method)
            helper = self._request_helper(client, authorization_values=(
                'Basic ' + base64.b64encode(b'post-client:post-secret').decode('ascii'),))
            with self.subTest(method=method):
                self.assertIs(helper._authenticate_token_client(), client)

    def test_partial_empty_and_failed_post_credentials_are_invalid_client(self):
        cases = (
            (('client_id', 'post-client'),),
            (('client_secret', 'post-secret'),),
            (('client_id', 'post-client'), ('client_secret', '')),
            (('client_id', ''), ('client_secret', 'post-secret')),
            (('client_id', 'unknown'), ('client_secret', 'post-secret')),
        )
        for index, pairs in enumerate(cases):
            with self.subTest(case=index):
                self._assert_error(self._request_helper(_Client(), body_pairs=pairs), 'invalid_client')

    def test_wrong_inactive_unsupported_and_empty_verifier_basic_fail(self):
        basic = 'Basic ' + base64.b64encode(b'post-client:post-secret').decode('ascii')
        clients = (_Client(method='client_secret', secret='different'),
                   _Client(method='client_secret', active=False),
                   _Client(method='private_key_jwt'), _Client(method='client_secret_post'))
        for index, client in enumerate(clients):
            with self.subTest(case=index):
                self._assert_error(self._request_helper(client, authorization_values=(basic,)),
                                   'invalid_client', basic=True)
        client = _Client(method='client_secret')
        with patch.object(client, 'check_credentials', side_effect=ValueError('synthetic verifier error')):
            response = self._assert_error(self._request_helper(client, authorization_values=(basic,)),
                                          'invalid_client', basic=True)
        self.assertNotIn('synthetic verifier error', response.response)

    def test_post_wrong_method_inactive_and_verifier_failure(self):
        pairs = (('client_id', 'post-client'), ('client_secret', 'post-secret'))
        for client in (_Client(method='client_secret'), _Client(method='client_secret_basic'),
                       _Client(method='private_key_jwt'), _Client(active=False)):
            self._assert_error(self._request_helper(client, body_pairs=pairs), 'invalid_client')
        client = _Client()
        with patch.object(client, 'check_credentials', side_effect=ValueError('synthetic verifier error')):
            response = self._assert_error(self._request_helper(client, body_pairs=pairs), 'invalid_client')
        self.assertNotIn('synthetic verifier error', response.response)

    def test_malformed_basic_is_invalid_client_with_challenge(self):
        headers = ('Basic', 'Basic !!!', 'Basic YQ==', 'Basic YTo= extra',
                   'Basic ' + base64.b64encode(b'a%ZZ:secret').decode('ascii'),
                   'Basic ' + base64.b64encode(b'a:%FF').decode('ascii'))
        for index, header in enumerate(headers):
            with self.subTest(case=index):
                self._assert_error(self._request_helper(_Client(), authorization_values=(header,)),
                                   'invalid_client', basic=True)

    def test_encoding_components_are_distinct_for_basic_and_post(self):
        cases = (('colon:client', 'literal:colon', 'colon%3Aclient:literal:colon'),
                 ('colon:client', 'encoded:colon', 'colon%3Aclient:encoded%3Acolon'),
                 ('plus+client', 'plus+secret', 'plus%2Bclient:plus%2Bsecret'),
                 ('space client', 'space secret', 'space+client:space+secret'),
                 ('utfé', '秘密', 'utf%C3%A9:%E7%A7%98%E5%AF%86'))
        for index, (client_id, secret, encoded_pair) in enumerate(cases):
            with self.subTest(case=index):
                client = _Client(client_id=client_id, secret=secret, method='client_secret_basic')
                basic = 'Basic ' + base64.b64encode(encoded_pair.encode('ascii')).decode('ascii')
                helper = self._request_helper(client, authorization_values=(basic,))
                self.assertIs(helper._authenticate_token_client(), client)
                client.authentication_method = 'client_secret_post'
                helper = self._request_helper(client, body_pairs=(('client_id', client_id),
                                                                 ('client_secret', secret)))
                self.assertIs(helper._authenticate_token_client(), client)

    def test_empty_duplicates_and_query_names_are_invalid_request(self):
        pairs = [('client_id', 'post-client'), ('client_secret', 'post-secret'),
                 ('grant_type', 'client_credentials')]
        for name in ('client_id', 'client_secret', 'grant_type'):
            with self.subTest(duplicate=name):
                self._assert_error(self._request_helper(_Client(), body_pairs=pairs + [(name, '')]),
                                   'invalid_request')
        for name in ('client_id', 'client_secret'):
            with self.subTest(query=name):
                self._assert_error(self._request_helper(_Client(), body_pairs=pairs,
                                                        query_pairs=((name, ''),)), 'invalid_request')

    def test_malformed_forms_and_unsupported_media_are_invalid_request(self):
        for body in (b'client_id=%', b'client_id=%FF', b'client_id=one&bare', b'client_id=\xff'):
            self._assert_error(self._request_helper(_Client(), raw_body=body), 'invalid_request')
        for media in ('application/json', 'multipart/form-data', 'text/plain'):
            self._assert_error(self._request_helper(_Client(), content_type=media), 'invalid_request')
        self._assert_error(self._request_helper(_Client(), method='GET'), 'invalid_request')

    def test_unknown_parameters_are_ignored_for_basic_and_post(self):
        for method in ('client_secret_basic', 'client_secret_post'):
            client = _Client(method=method)
            pairs = [('unrecognized', 'one'), ('unrecognized', 'two')]
            headers = ()
            if method == 'client_secret_post':
                pairs += [('client_id', client.client_id), ('client_secret', 'post-secret')]
            else:
                headers = ('Basic ' + base64.b64encode(b'post-client:post-secret').decode('ascii'),)
            self.assertIs(self._request_helper(client, body_pairs=pairs,
                                                authorization_values=headers)._authenticate_token_client(), client)

    def test_mixed_channels_and_public_clients_never_verify_or_dispatch(self):
        parent = load('models/token_helper.py').TokenHelper
        basic = 'Basic ' + base64.b64encode(b'post-client:post-secret').decode('ascii')
        for client, pairs, headers, error, challenge in (
                (_Client(), (('client_id', 'post-client'),), (basic,), 'invalid_request', False),
                (_Client(), (('client_id', 'different'), ('client_secret', 'different')),
                 (basic,), 'invalid_request', False),
                (_Client(confidential=False), (('client_id', 'post-client'),
                                               ('client_secret', 'post-secret')), (), 'invalid_client', False),
                (_Client(method='client_secret', confidential=False), (), (basic,), 'invalid_client', True)):
            helper = self._request_helper(client, body_pairs=pairs, authorization_values=headers,
                                           parent_helper=parent)
            with patch.object(client, 'check_credentials') as verify, patch.object(parent, 'oidc_token') as dispatch:
                try:
                    helper.oidc_token(grant_type='client_credentials')
                except (_BadRequest, _Unauthorized) as exc:
                    self.assertEqual(json.loads(exc.response.response)['error'], error)
                    self.assertEqual(exc.response.status_code, 401 if challenge else 400)
                else:
                    self.fail('invalid request reached dispatch')
                verify.assert_not_called()
                dispatch.assert_not_called()

    def test_authenticated_basic_and_post_call_real_fail_closed_dispatch_once(self):
        parent = load('models/token_helper.py').TokenHelper
        grants = (None, 'client_credentials', 'password', 'refresh_token', 'authorization_code',
                  'urn:ietf:params:oauth:grant-type:jwt-bearer', 'challenge_approval',
                  'digital_signature', 'synthetic-grant-canary')
        for method in ('client_secret', 'client_secret_basic', 'client_secret_post'):
            for grant in grants:
                with self.subTest(method=method, grant=grant):
                    client = _Client(method=method)
                    events = []
                    verify_original = client.check_credentials
                    dispatch_original = parent.oidc_token
                    def verify(secret):
                        events.append('verify')
                        return verify_original(secret)
                    def dispatch(record, **kwargs):
                        events.append('dispatch')
                        return dispatch_original(record, **kwargs)
                    headers = ()
                    pairs = [('grant_type', grant)] if grant is not None else []
                    if method == 'client_secret_post':
                        pairs += [('client_id', client.client_id), ('client_secret', 'post-secret')]
                    else:
                        headers = ('Basic ' + base64.b64encode(b'post-client:post-secret').decode('ascii'),)
                    helper = self._request_helper(client, body_pairs=pairs, authorization_values=headers,
                                                   parent_helper=parent)
                    with patch.object(client, 'check_credentials', verify), patch.object(parent, 'oidc_token', dispatch):
                        result = helper.oidc_token(grant_type=grant)
                    self.assertEqual(events, ['verify', 'dispatch'])
                    self.assertEqual(result['status'], 400)
                    self.assertEqual(result['error'], 'unsupported_grant_type')
                    for field in ('access_token', 'refresh_token', 'id_token'):
                        self.assertNotIn(field, result)

    def test_real_dispatch_description_is_constant_and_does_not_reflect_grant(self):
        parent = load('models/token_helper.py').TokenHelper
        descriptions = set()
        for grant in (None, 'client_credentials', 'synthetic-grant-canary'):
            helper = self._request_helper(_Client(), body_pairs=(('client_id', 'post-client'),
                ('client_secret', 'post-secret')), parent_helper=parent)
            result = helper.oidc_token(grant_type=grant)
            descriptions.add(result['error_description'])
        self.assertEqual(len(descriptions), 1, 'grant dispatcher reflects untrusted grant_type')


class TestTokenRouteExceptionPrivacy(unittest.TestCase):
    def test_unexpected_exception_returns_generic_response_without_raw_logs(self):
        sentinel = 'synthetic-token-route-exception-canary'
        module = load_controller()
        helper = SimpleNamespace(sudo=lambda: helper,
                                 oidc_token=Mock(side_effect=ValueError(sentinel)))
        module.request.env = {'amr.oidc.helper': helper}
        output = StringIO()
        handler = logging.StreamHandler(output)
        handler.setFormatter(logging.Formatter('%(name)s:%(levelname)s:%(message)s'))
        logger = logging.getLogger()
        logger.addHandler(handler)
        try:
            response = module.ControllerOIDC().api_oidc_token(grant_type=sentinel)
        finally:
            logger.removeHandler(handler)
            handler.close()
        self.assertEqual(response.status_code, 401)
        self.assertEqual(json.loads(response.data), {
            'success': False,
            'error': 'invalid_request',
            'error_description': 'Request could not be processed.',
        })
        self.assertNotIn(sentinel, response.data.decode('utf-8'))
        self.assertNotIn(sentinel, output.getvalue())
        self.assertNotIn('Traceback', output.getvalue())

    def test_prepared_http_exception_is_reraised_unchanged_without_raw_logs(self):
        sentinel = 'synthetic-token-route-http-canary'
        module = load_controller()
        for status, error in ((400, 'invalid_request'), (401, 'invalid_client')):
            with self.subTest(status=status):
                prepared = StubResponse(json.dumps({'error': error}), status=status,
                    headers={'WWW-Authenticate': 'Basic'} if status == 401 else {})
                exception = StubHTTPException(sentinel, response=prepared)
                helper = SimpleNamespace(sudo=lambda: helper,
                                         oidc_token=Mock(side_effect=exception))
                module.request.env = {'amr.oidc.helper': helper}
                output = StringIO()
                handler = logging.StreamHandler(output)
                logger = logging.getLogger()
                logger.addHandler(handler)
                try:
                    with self.assertRaises(StubHTTPException) as caught:
                        module.ControllerOIDC().api_oidc_token()
                finally:
                    logger.removeHandler(handler)
                    handler.close()
                self.assertIs(caught.exception, exception)
                self.assertIs(caught.exception.response, prepared)
                self.assertEqual(prepared.status_code, status)
                self.assertEqual(json.loads(prepared.data), {'error': error})
                self.assertEqual(prepared.headers.get('WWW-Authenticate'),
                                 'Basic' if status == 401 else None)
                self.assertNotIn(sentinel, output.getvalue())
                self.assertNotIn('Traceback', output.getvalue())


class TestWerkzeugAuthorizationBoundary(unittest.TestCase):
    """Real parser/environ/request, in-memory only; no Odoo registry or HTTP server."""

    def _wire_request(self, values, body=b'grant_type=client_credentials'):
        from werkzeug.datastructures import ImmutableOrderedMultiDict
        from werkzeug.serving import WSGIRequestHandler
        from werkzeug.wrappers import Request
        raw = (b'POST /oidc/token HTTP/1.1\r\nHost: synthetic.invalid\r\n' +
               b''.join(b'Authorization: ' + value.encode('ascii') + b'\r\n' for value in values) +
               b'Content-Type: application/x-www-form-urlencoded\r\nContent-Length: ' +
               str(len(body)).encode('ascii') + b'\r\n\r\n' + body)
        handler = WSGIRequestHandler.__new__(WSGIRequestHandler)
        handler.rfile = BytesIO(raw)
        handler.wfile = BytesIO()
        handler.client_address = ('127.0.0.1', 12345)
        handler.server = SimpleNamespace(ssl_context=None, multithread=False, multiprocess=False,
                                         server_address=('synthetic.invalid', 80))
        handler.raw_requestline = handler.rfile.readline()
        self.assertTrue(handler.parse_request())
        parsed_count = len(handler.headers.get_all('Authorization') or [])
        request = Request(handler.make_environ())
        # Match Odoo Root.dispatch without booting Odoo or opening a database.
        request.parameter_storage_class = ImmutableOrderedMultiDict
        return parsed_count, request

    def test_parser_receives_two_fields_but_wsgi_keeps_only_last(self):
        last = 'Basic ' + base64.b64encode(b'post-client:post-secret').decode('ascii')
        for first in (last, 'Bearer synthetic-token', ''):
            with self.subTest(first_kind='same' if first == last else 'different-or-empty'):
                count, request = self._wire_request((first, last))
                single_count, single = self._wire_request((last,))
                self.assertEqual(count, 2)
                self.assertEqual(single_count, 1)
                self.assertEqual(request.headers.getlist('Authorization'), [last])
                self.assertEqual(request.headers.getlist('Authorization'), single.headers.getlist('Authorization'))
                self.assertEqual(request.environ['HTTP_AUTHORIZATION'], single.environ['HTTP_AUTHORIZATION'])

    def test_single_basic_control_authenticates_after_real_boundary(self):
        basic = 'Basic ' + base64.b64encode(b'post-client:post-secret').decode('ascii')
        count, http = self._wire_request((basic,))
        module, request = _load_auth_module()
        client = _Client(method='client_secret')
        helper = module.TokenHelperClientAuth()
        helper.env = _Environment({'oidc.client': _ClientModel(client)})
        request.httprequest = http
        self.assertEqual(count, 1)
        self.assertIs(helper._authenticate_token_client(), client)

    def test_real_form_parser_preserves_consumed_duplicates(self):
        _count, http = self._wire_request((), body=(
            b'client_id=post-client&client_secret=post-secret&grant_type=one&grant_type='))
        self.assertEqual(http.form.getlist('grant_type'), ['one', ''])
        self.assertEqual(http.get_data(cache=True), b'')
        module, request = _load_auth_module()
        helper = module.TokenHelperClientAuth()
        helper.env = _Environment({'oidc.client': _ClientModel(_Client())})
        request.httprequest = http
        with self.assertRaises(_BadRequest) as caught:
            helper._authenticate_token_client()
        self.assertEqual(json.loads(caught.exception.response.response)['error'], 'invalid_request')

    def test_valid_post_control_after_framework_consumes_form(self):
        _count, http = self._wire_request((), body=b'client_id=post%25ZZ&client_secret=post-secret')
        self.assertEqual(http.form['client_id'], 'post%ZZ')
        self.assertEqual(http.get_data(cache=True), b'')
        module, request = _load_auth_module()
        client = _Client(client_id='post%ZZ')
        helper = module.TokenHelperClientAuth()
        helper.env = _Environment({'oidc.client': _ClientModel(client)})
        request.httprequest = http
        self.assertIs(helper._authenticate_token_client(), client)

    def test_malformed_form_syntax_unavailable_after_parse_uses_parsed_value(self):
        _count, http = self._wire_request((), body=b'client_id=post%ZZ&client_secret=post-secret')
        self.assertEqual(http.form['client_id'], 'post%ZZ')
        self.assertEqual(http.get_data(cache=True), b'')
        module, request = _load_auth_module()
        client = _Client(client_id='post%ZZ')
        helper = module.TokenHelperClientAuth()
        helper.env = _Environment({'oidc.client': _ClientModel(client)})
        request.httprequest = http
        # The accepted W-63-R8-01 exception is limited to raw syntax already
        # lost at this parser boundary; the helper validates the parsed value.
        self.assertIs(helper._authenticate_token_client(), client)

    def test_repeated_authorization_collapsed_by_wsgi_uses_surviving_value(self):
        basic = 'Basic ' + base64.b64encode(b'post-client:post-secret').decode('ascii')
        count, http = self._wire_request(('Bearer synthetic-token', basic))
        module, request = _load_auth_module()
        client = _Client(method='client_secret')
        helper = module.TokenHelperClientAuth()
        helper.env = _Environment({'oidc.client': _ClientModel(client)})
        request.httprequest = http
        self.assertEqual(count, 2)
        self.assertEqual(http.headers.getlist('Authorization'), [basic])
        # The accepted W-63-R8-02 exception applies only because WSGI has
        # discarded the original field multiplicity before the helper.
        self.assertIs(helper._authenticate_token_client(), client)


if __name__ == '__main__':
    unittest.main()
