"""UT-01..UT-07: existing behavior, not security acceptance.

Run only in a disposable Odoo 13 database. All token-like inputs are synthetic;
network and the production helper logger are blocked before each test.
"""
import base64
import time
from types import SimpleNamespace
from unittest.mock import Mock, patch

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from requests import HTTPError
from werkzeug.exceptions import Unauthorized
from odoo.exceptions import ValidationError
from odoo.tests.common import SavepointCase

from ...models import helper as helper_module


class ResourceCase(SavepointCase):
    def setUp(self):
        super().setUp()
        log_guard = patch("logging.Logger._log")
        self.logger = log_guard.start()
        self.addCleanup(log_guard.stop)
        self.token = 'synthetic-invalid-access-token'
        self.admin = self.env['res.users'].create({
            'name': 'Synthetic trust administrator', 'login': 'trust-admin-unit',
            'company_id': self.env.company.id,
            'company_ids': [(6, 0, self.env.company.ids)],
            'groups_id': [(6, 0, [self.env.ref(x).id for x in (
                'base.group_user', 'base.group_system',
                'amr_resource.group_oidc_trust_admin', 'amr_resource.group_oidc_code_admin')])],
        })
        self.helper = self.env['amr.resource.helper'].with_user(self.admin)
        self.registry = self.env['oidc.issuer.register'].with_user(self.admin)
        self.profile = self.registry.create({
            'issuer': 'https://issuer.invalid', 'client_id': 'client-a',
            'token_profile': 'jwt', 'jwks_uri': 'https://keys.invalid/jwks',
            'metadata_mode': 'manual', 'verification_source': 'jwks',
            'introspection_source': 'none', 'token_endpoint': 'https://issuer.invalid/token', 'allow_missing_azp': True,
            'resolver_mode': 'get_user_match',
            'audience_ids': [(0, 0, {'value': 'resource-a'})],
        })
        for target in ('socket.getaddrinfo', 'socket.socket', 'requests.sessions.Session.request'):
            guard = patch(target, side_effect=AssertionError('Unexpected external I/O'))
            guard.start()
            self.addCleanup(guard.stop)

    def patch_model(self, record, name, **kwargs):
        patcher = patch.object(type(record), name, **kwargs)
        result = patcher.start()
        self.addCleanup(patcher.stop)
        return result


class TestResourceHelper(ResourceCase):
    def test_issuer_policy_child_models_have_queryable_tables(self):
        mappings = self.env['oidc.issuer.user.mapping']
        policies = self.env['oidc.issuer.algorithm.policy']
        self.assertEqual(mappings.search([], limit=1).ids, [])
        self.assertEqual(policies.search([], limit=1).ids, [])

    def test_ut01_resolution_and_compute(self):
        # sudo: seed protected global config keys used by the issuer/audience test.
        params = self.env['ir.config_parameter'].sudo()
        params.set_param('web.base.url', 'http://127.0.0.1:19000')
        params.set_param('database.uuid', 'synthetic-resource-db')
        for selector in ('web.base.url', 'database.uuid'):
            params.set_param('amr_resource.issuer', selector)
            params.set_param('amr_resource.audience', selector)
            self.assertEqual(self.helper.get_issuer(), self.profile.issuer)
            self.assertEqual(self.helper.get_audience(), 'resource-a')
            self.assertEqual(self.helper.get_audiences(), ['resource-a'])
            self.assertFalse(self.helper.is_local_issuer(self.profile.issuer))
            for legacy in ('http://127.0.0.1:19000', 'synthetic-resource-db'):
                with self.assertRaises(Unauthorized):
                    self.helper.is_local_issuer(legacy)
            with self.assertRaises(Unauthorized):
                self.helper.get_audiences('ignored')
        for key in ('database.uuid', 'web.base.url'):
            params.search([('key', '=', key)]).unlink()
            self.assertEqual(self.helper.get_issuer(), self.profile.issuer)
            self.assertEqual(self.helper.get_audiences(), ['resource-a'])
        settings = self.env['res.config.settings']
        for field in ('amr_select_issuer', 'amr_select_audience',
                      'amr_resource_issuer', 'amr_resource_audience'):
            self.assertNotIn(field, settings._fields)
        self.profile.active = False
        for method in (self.helper.get_issuer, self.helper.get_audience,
                       self.helper.get_audiences):
            with self.assertRaises(Unauthorized):
                method()

    def test_ut03_extraction_precedence(self):
        http = SimpleNamespace(args={}, form={}, headers={}, environ={})
        with patch.object(helper_module, 'request', SimpleNamespace(httprequest=http)):
            order = [(http.args, 'access_token'), (http.form, 'access_token'),
                     (http.args, 'token'), (http.form, 'token'),
                     (http.args, 'token_access'), (http.form, 'token_access')]
            for index, (mapping, key) in enumerate(order):
                mapping[key] = 'fixture-%s' % index
            for index, (mapping, key) in enumerate(order):
                self.assertEqual(self.helper.get_param_token(), 'fixture-%s' % index)
                del mapping[key]
            self.assertIsNone(self.helper.get_param_token())
            http.headers.update(access_token='first', token='second')
            self.assertEqual(self.helper.get_header_token(), 'first')
            del http.headers['access_token']
            self.assertEqual(self.helper.get_header_token(), 'second')
            http.headers['Authorization'] = 'Bearer header-fixture'
            http.environ['HTTP_AUTHORIZATION'] = 'Bearer environ-fixture'
            self.assertEqual(self.helper.get_bearer_token(), 'environ-fixture')
            del http.environ['HTTP_AUTHORIZATION']
            self.assertEqual(self.helper.get_bearer_token(), 'header-fixture')
            for value in ('', 'bearer fixture', 'Bearer  fixture', 'Bearer', 'Basic fixture'):
                http.headers['Authorization'] = value
                with self.assertRaises(Unauthorized):
                    self.helper.get_bearer_token()
            del http.headers['Authorization']
            self.assertIsNone(self.helper.get_bearer_token())

    def test_addons13_83_uat03_manual_config_and_jwks_boundary(self):
        # AC03: the RS owns manual trust and may fetch only its selected JWKS.
        self.assertIn('oidc.issuer.register', self.env.registry.models)
        self.assertIn('amr.resource.helper', self.env.registry.models)
        # sudo: inspect the global installed-addon registry regardless of test-user ACLs.
        module_states = self.env['ir.module.module'].sudo().search([
            ('name', 'in', ['amr_oidc', 'amr_token'])
        ])
        self.assertFalse(module_states, 'provider/token addon state must be absent')

        credential_ref = 'amr_resource.synthetic_credential_ref_uat03'
        self.profile.credential_ref = credential_ref

        def b64url_uint(value):
            width = (value.bit_length() + 7) // 8
            encoded = base64.urlsafe_b64encode(value.to_bytes(width, 'big'))
            return encoded.rstrip(b'=').decode('ascii')

        public_numbers = rsa.generate_private_key(
            public_exponent=65537, key_size=2048
        ).public_key().public_numbers()
        jwks = {'keys': [{'kty': 'RSA', 'kid': 'synthetic-rs-key',
                          'use': 'sig', 'alg': 'RS256',
                          'n': b64url_uint(public_numbers.n),
                          'e': b64url_uint(public_numbers.e)}]}
        self.assertEqual(int.from_bytes(base64.urlsafe_b64decode(
            jwks['keys'][0]['n'] + '=' * (-len(jwks['keys'][0]['n']) % 4)), 'big'),
            public_numbers.n)
        self.assertEqual(int.from_bytes(base64.urlsafe_b64decode(
            jwks['keys'][0]['e'] + '=' * (-len(jwks['keys'][0]['e']) % 4)), 'big'),
            public_numbers.e)

        expected_config = {
            'issuer': self.profile.issuer,
            'jwks_uri': self.profile.jwks_uri,
            'token_endpoint': self.profile.token_endpoint,
            'introspection_endpoint': None,
        }
        param_model = self.env['ir.config_parameter']
        original_get_param = type(param_model).get_param
        looked_up_names = []

        def observe_get_param(recordset, key, *args, **kwargs):
            looked_up_names.append(key)
            return original_get_param(recordset, key, *args, **kwargs)

        with patch.object(helper_module, 'fetch_json') as fetch_json, \
                patch.object(type(param_model), 'get_param', observe_get_param):
            self.assertEqual(self.helper.get_oidc_config(self.profile.issuer), expected_config)
            fetch_json.assert_not_called()
            fetch_json.return_value = jwks
            self.assertEqual(self.helper.get_jwks_data(self.profile.issuer), jwks)
            fetch_json.assert_called_once_with(self.profile.jwks_uri)

        self.assertNotIn(credential_ref, looked_up_names)
        # Report only boundary key names, never parameter values.
        self.assertTrue(all(isinstance(name, str) for name in looked_up_names))

    def test_addons13_83_uat04_missing_selected_local_key_no_fallback(self):
        local_key_ref = 'amr_resource.keys.synthetic_uat04'
        credential_ref = 'amr_resource.credentials.synthetic_uat04'
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        public_pem = private_key.public_key().public_bytes(
            serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('ascii')
        # sudo: seed a protected config key with a synthetic PEM for the local-key test.
        params = self.env['ir.config_parameter'].sudo()
        params.set_param(local_key_ref, public_pem)
        self.profile.write({
            'jwks_uri': False, 'local_key_ref': local_key_ref,
            'verification_source': 'local_public', 'metadata_mode': 'manual',
            'introspection_source': 'none', 'credential_ref': credential_ref,
        })

        claims = {
            'iss': self.profile.issuer, 'sub': 'subject-uat04', 'client_id': 'client-a',
            'aud': 'resource-a', 'exp': int(time.time()) + 300,
            'iat': int(time.time()) - 1, 'jti': 'synthetic-jti-uat04',
        }
        token = jwt.encode(claims, private_key, algorithm='RS256', headers={'typ': 'at+jwt'})
        original_get_param = type(params).get_param
        looked_up_names = []

        def observe_get_param(recordset, key, *args, **kwargs):
            looked_up_names.append(key)
            return original_get_param(recordset, key, *args, **kwargs)

        with patch.object(helper_module, 'fetch_json') as fetch_json, \
                patch.object(type(params), 'get_param', observe_get_param):
            self.assertEqual(self.helper.validate(token)['iss'], self.profile.issuer)
            fetch_json.assert_not_called()

            params.set_param(local_key_ref, False)
            params.invalidate_cache()
            self.profile.invalidate_cache()
            looked_up_names.clear()

            with self.assertRaises(Unauthorized) as error:
                self.helper.validate(token)
            self.assertEqual(error.exception.code, 401)
            fetch_json.assert_not_called()
            self.assertEqual(looked_up_names, [local_key_ref])

    def _uat04_jwks_fixture(self, suffix):
        trusted_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        alternate_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        trusted_kid = 'synthetic-trusted-kid-' + suffix
        credential_ref = 'amr_resource.credentials.synthetic_uat04_' + suffix
        self.profile.write({
            'token_profile': 'jwt', 'jwks_uri': 'https://keys.invalid/jwks',
            'metadata_mode': 'manual', 'verification_source': 'jwks',
            'introspection_source': 'none', 'credential_ref': credential_ref,
        })

        def b64url_uint(value):
            width = (value.bit_length() + 7) // 8
            encoded = base64.urlsafe_b64encode(value.to_bytes(width, 'big'))
            return encoded.rstrip(b'=').decode('ascii')

        public_numbers = trusted_key.public_key().public_numbers()
        jwks = {'keys': [{
            'kty': 'RSA', 'kid': trusted_kid, 'use': 'sig', 'alg': 'RS256',
            'n': b64url_uint(public_numbers.n), 'e': b64url_uint(public_numbers.e),
        }]}
        fetch_patcher = patch.object(helper_module, 'fetch_json', return_value=jwks)
        fetch_json = fetch_patcher.start()
        self.addCleanup(fetch_patcher.stop)

        params = self.env['ir.config_parameter']
        original_get_param = type(params).get_param
        looked_up_names = []

        def observe_get_param(recordset, key, *args, **kwargs):
            looked_up_names.append(key)
            return original_get_param(recordset, key, *args, **kwargs)

        param_patcher = patch.object(type(params), 'get_param', observe_get_param)
        param_patcher.start()
        self.addCleanup(param_patcher.stop)
        return trusted_key, alternate_key, trusted_kid, fetch_json, looked_up_names, credential_ref

    def _uat04_jwks_token(self, signing_key, suffix, issuer=None, audience=None, kid=None):
        now = int(time.time())
        claims = {
            'iss': issuer or self.profile.issuer,
            'aud': audience or 'resource-a',
            'exp': now + 300, 'iat': now - 1,
            'jti': 'synthetic-jti-' + suffix,
            'sub': 'synthetic-subject-' + suffix,
            'client_id': 'client-a',
        }
        return jwt.encode(
            claims, signing_key, algorithm='RS256',
            headers={'typ': 'at+jwt', 'kid': kid or 'synthetic-trusted-kid-' + suffix},
        )

    def _assert_uat04_jwks_positive_control(
            self, signing_key, suffix, kid, fetch_json, looked_up_names, credential_ref):
        token = self._uat04_jwks_token(signing_key, suffix, kid=kid)
        claims = self.helper.validate(token)
        self.assertEqual(claims['iss'], self.profile.issuer)
        self.assertEqual(claims['aud'], 'resource-a')
        self.assertEqual(claims['kid'], kid)
        self.assertEqual(claims['alg'], 'RS256')
        fetch_json.assert_called_once_with(self.profile.jwks_uri)
        self.assertEqual(looked_up_names, [])
        self.assertNotIn(credential_ref, looked_up_names)
        fetch_json.reset_mock()
        looked_up_names.clear()

    def test_addons13_83_uat04_untrusted_issuer_rejected_before_transport(self):
        trusted_key, _, trusted_kid, fetch_json, looked_up, credential_ref = \
            self._uat04_jwks_fixture('issuer')
        self._assert_uat04_jwks_positive_control(
            trusted_key, 'issuer-positive', trusted_kid, fetch_json, looked_up, credential_ref)
        token = self._uat04_jwks_token(
            trusted_key, 'issuer-negative', issuer='https://untrusted-issuer.invalid', kid=trusted_kid)
        with self.assertRaises(Unauthorized) as error:
            self.helper.validate(token)
        self.assertEqual(error.exception.code, 401)
        fetch_json.assert_not_called()
        self.assertEqual(looked_up, [])
        self.assertNotIn(credential_ref, looked_up)

    def test_addons13_83_uat04_untrusted_audience_rejected_before_jwks(self):
        trusted_key, _, trusted_kid, fetch_json, looked_up, credential_ref = \
            self._uat04_jwks_fixture('audience')
        self._assert_uat04_jwks_positive_control(
            trusted_key, 'audience-positive', trusted_kid, fetch_json, looked_up, credential_ref)
        token = self._uat04_jwks_token(
            trusted_key, 'audience-negative', audience='resource-untrusted', kid=trusted_kid)
        with self.assertRaises(Unauthorized) as error:
            self.helper.validate(token)
        self.assertEqual(error.exception.code, 401)
        fetch_json.assert_not_called()
        self.assertEqual(looked_up, [])
        self.assertNotIn(credential_ref, looked_up)

    def test_addons13_83_uat04_untrusted_kid_rejected_without_fallback(self):
        trusted_key, _, trusted_kid, fetch_json, looked_up, credential_ref = \
            self._uat04_jwks_fixture('kid')
        self._assert_uat04_jwks_positive_control(
            trusted_key, 'kid-positive', trusted_kid, fetch_json, looked_up, credential_ref)
        token = self._uat04_jwks_token(
            trusted_key, 'kid-negative', kid='synthetic-untrusted-kid')
        with self.assertRaises(Unauthorized) as error:
            self.helper.validate(token)
        self.assertEqual(error.exception.code, 401)
        fetch_json.assert_called_once_with(self.profile.jwks_uri)
        self.assertEqual(looked_up, [])
        self.assertNotIn(credential_ref, looked_up)

    def test_addons13_83_uat04_invalid_signature_rejected_without_fallback(self):
        trusted_key, alternate_key, trusted_kid, fetch_json, looked_up, credential_ref = \
            self._uat04_jwks_fixture('signature')
        self._assert_uat04_jwks_positive_control(
            trusted_key, 'signature-positive', trusted_kid, fetch_json, looked_up, credential_ref)
        token = self._uat04_jwks_token(alternate_key, 'signature-negative', kid=trusted_kid)
        with self.assertRaises(Unauthorized) as error:
            self.helper.validate(token)
        self.assertEqual(error.exception.code, 401)
        fetch_json.assert_called_once_with(self.profile.jwks_uri)
        self.assertEqual(looked_up, [])
        self.assertNotIn(credential_ref, looked_up)

    def test_ut04_discovery_and_errors(self):
        with patch.object(helper_module, 'fetch_json') as fetch:
            self.assertEqual(self.helper.get_oidc_config(self.profile.issuer), {
                'issuer': self.profile.issuer,
                'jwks_uri': self.profile.jwks_uri,
                'token_endpoint': self.profile.token_endpoint,
                'introspection_endpoint': None,
            })
            fetch.assert_not_called()
            for issuer in ('https://unknown.invalid', self.profile.issuer + '///'):
                for method in (self.helper.get_oidc_config, self.helper.get_jwks_data):
                    with self.assertRaises(Unauthorized):
                        method(issuer)
                    fetch.assert_not_called()
            fetch.return_value = {'keys': []}
            self.assertEqual(self.helper.get_jwks_data(self.profile.issuer), {'keys': []})
            fetch.assert_called_once_with(self.profile.jwks_uri)
            for error in (HTTPError(), ValueError()):
                fetch.side_effect = error
                with self.assertRaises(Unauthorized):
                    self.helper.get_jwks_data(self.profile.issuer)
            fetch.side_effect = None
            for invalid in (None, [], {}, {'keys': 'invalid'}):
                fetch.return_value = invalid
                with self.assertRaises(Unauthorized):
                    self.helper.get_jwks_data(self.profile.issuer)

    def test_resource_helper_does_not_acquire_provider_tokens(self):
        helper_type = type(self.helper)
        self.assertTrue(callable(self.helper.decode))
        self.assertTrue(callable(self.helper.encode))
        self.assertTrue(callable(self.helper.generate_token))
        with patch.object(helper_type, 'validate', return_value={'synthetic': True}) as validate, \
                patch.object(helper_type, 'generate_token') as generate_token:
            self.assertEqual(self.helper.decode(self.token, unused=True), {'synthetic': True})
            validate.assert_called_once_with(self.token)
            generate_token.assert_not_called()

    def test_manual_jwks_config_does_not_require_discovery_unavailable_declaration(self):
        self.profile.write({'token_profile': 'jwt', 'metadata_mode': 'manual',
                            'verification_source': 'jwks', 'introspection_source': 'none',
                            'local_key_ref': False, 'jwks_uri': 'https://keys.invalid/jwks'})
        self.assertEqual(self.helper.get_oidc_config(self.profile.issuer), {
            'issuer': self.profile.issuer, 'jwks_uri': self.profile.jwks_uri,
            'token_endpoint': self.profile.token_endpoint or None,
            'introspection_endpoint': None})

    def test_manual_jwks_config_does_not_require_discovery_unavailable_declaration(self):
        self.profile.write({'token_profile': 'jwt', 'metadata_mode': 'manual',
                            'verification_source': 'jwks', 'introspection_source': 'none',
                            'local_key_ref': False, 'jwks_uri': 'https://keys.invalid/jwks'})
        self.assertEqual(self.helper.get_oidc_config(self.profile.issuer), {
            'issuer': self.profile.issuer, 'jwks_uri': self.profile.jwks_uri,
            'token_endpoint': self.profile.token_endpoint or None,
            'introspection_endpoint': None})

    def test_ut05_introspection_and_hs(self):
        with patch.object(helper_module, 'fetch_json') as fetch, patch.object(jwt, 'decode') as decode:
            for operation in (
                    lambda: self.helper.validate_hs(self.token),
                    lambda: self.helper.introspect_token(self.token, url='https://override.invalid'),
                    lambda: self.helper.introspect_token(self.token, iss=self.profile.issuer)):
                with self.assertRaises(Unauthorized):
                    operation()
                fetch.assert_not_called()
                decode.assert_not_called()
        with self.assertRaises(ValidationError):
            self.profile.write({'token_profile': 'opaque', 'jwks_uri': False,
                                'introspection_endpoint': 'https://issuer.invalid/introspect'})
        with patch.object(helper_module, 'fetch_json') as fetch, \
                patch.object(jwt, 'decode') as decode:
            with self.assertRaises(Unauthorized):
                self.helper.introspect_token(self.token, iss=self.profile.issuer)
            with self.assertRaises(Unauthorized):
                self.helper.validate(self.token)
            fetch.assert_not_called()
            decode.assert_not_called()

    def test_ut06_verified_jwt_and_failures(self):
        import time
        import json
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048, backend=default_backend())
        public = key.public_key().public_bytes(serialization.Encoding.PEM,
                                              serialization.PublicFormat.SubjectPublicKeyInfo).decode('ascii')
        # sudo: seed the protected config key used by the local-public-key validation test.
        self.env['ir.config_parameter'].sudo().set_param('amr_resource.keys.synthetic', public)
        self.profile.write({'jwks_uri': False, 'local_key_ref': 'amr_resource.keys.synthetic',
                            'verification_source': 'local_public', 'metadata_mode': 'manual',
                            'introspection_source': 'none'})
        claims = dict(iss=self.profile.issuer, sub='subject-a', client_id='client-a', aud='resource-a',
                      exp=int(time.time())+300, iat=int(time.time())-1, jti='synthetic-id')
        token = jwt.encode(claims, key, algorithm='RS256', headers={'typ': 'at+jwt'})
        with patch.object(helper_module, 'fetch_json') as fetch:
            result = self.helper.validate(token)
            self.assertTrue(self.helper._verified(result))
            self.assertTrue(self.helper.is_local_token(token))
            for field in ('exp', 'iat', 'jti', 'sub', 'client_id', 'aud', 'iss'):
                invalid = dict(claims)
                invalid.pop(field)
                with self.assertRaises(Unauthorized):
                    self.helper.validate(jwt.encode(invalid, key, algorithm='RS256', headers={'typ': 'at+jwt'}))
            with self.assertRaises(Unauthorized):
                self.helper.validate(jwt.encode(claims, key, algorithm='RS256', headers={'typ': 'JWT'}))
            fetch.assert_not_called()
        self.assertEqual(result, dict(claims, kid=None, alg='RS256'))
        with patch.object(type(self.helper), 'get_jwks_data') as jwks:
            self.assertEqual(self.helper.validate(token), result)
            jwks.assert_not_called()
        for malformed in ('malformed.jwt.input', 'one.two', '', None):
            with self.assertRaises(Unauthorized):
                self.helper.validate(malformed)
        for error in (AttributeError(), jwt.DecodeError(), jwt.InvalidTokenError(),
                      jwt.ExpiredSignatureError(), jwt.InvalidAudienceError(),
                      jwt.InvalidIssuerError(), jwt.InvalidSignatureError()):
            with patch.object(jwt, 'get_unverified_header', side_effect=error):
                with self.assertRaises(Unauthorized):
                    self.helper.validate(token)
        jwk = json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(key.public_key()))
        jwk.update(kid='synthetic-key', alg='RS256', use='sig')
        self.profile.write({'local_key_ref': False, 'jwks_uri': 'https://keys.invalid/jwks',
                            'verification_source': 'jwks', 'metadata_mode': 'manual',
                            'introspection_source': 'none'})
        remote_token = jwt.encode(claims, key, algorithm='RS256',
                                  headers={'typ': 'at+jwt', 'kid': 'synthetic-key'})
        with patch.object(helper_module, 'fetch_json', return_value={'keys': [jwk]}) as fetch, \
                patch.object(jwt, 'decode', wraps=jwt.decode) as decode:
            remote_result = self.helper.validate(remote_token)
            self.assertEqual(remote_result, dict(claims, kid='synthetic-key', alg='RS256'))
            self.assertTrue(self.helper._verified(remote_result))
            fetch.assert_called_once_with(self.profile.jwks_uri)
            self.assertEqual(decode.call_args[0][0], remote_token)
            self.assertEqual(decode.call_args[1], {
                'algorithms': ['RS256'], 'issuer': self.profile.issuer,
                'audience': ['resource-a'], 'leeway': 0,
                'options': {'require': ['iss', 'aud', 'exp', 'iat', 'jti', 'sub', 'client_id']},
            })
        for error in (HTTPError(), ValueError()):
            with patch.object(helper_module, 'fetch_json', side_effect=error):
                with self.assertRaises(Unauthorized):
                    self.helper.validate(remote_token)
        for error in (jwt.InvalidSignatureError, jwt.InvalidAudienceError, jwt.InvalidIssuerError):
            with patch.object(helper_module, 'fetch_json', return_value={'keys': [jwk]}), \
                    patch.object(jwt, 'decode', side_effect=[claims, error()]) as decode:
                with self.assertRaises(Unauthorized):
                    self.helper.validate(remote_token)
                self.assertEqual(decode.call_count, 2)
        retained = dict(claims, kid='existing-claim', alg='existing-claim')
        retained_token = jwt.encode(retained, key, algorithm='RS256',
                                    headers={'typ': 'at+jwt', 'kid': 'synthetic-key'})
        with patch.object(helper_module, 'fetch_json', return_value={'keys': [jwk]}):
            self.assertEqual(self.helper.validate(retained_token), retained)
        self.assertFalse(self.logger.called)

    def test_ut07_matching(self):
        from odoo.addons.amr_resource.models.helper import _VerifiedClaims
        self.profile.binding_ids = [(0, 0, {'sub': 'subject-a', 'user_id': self.admin.id})]
        def verified(**values):
            return _VerifiedClaims(dict(iss=self.profile.issuer, **values),
                                   self.env.company.id, self.admin.id, self.profile.policy_revision)
        self.admin.email = 'bound-user@example.invalid'
        email_user = self.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Synthetic email collision', 'login': 'email-collision',
            'email': 'email-collision@example.invalid',
            'groups_id': [(6, 0, [self.env.ref('base.group_user').id])],
        })
        claims = verified(sub='subject-a', email=email_user.email)
        self.assertEqual(self.helper.get_user_match(claims), self.admin)
        self.assertEqual(self.helper.get_uid(claims), self.admin.id)
        self.assertTrue(self.helper.is_user_match(self.admin, claims))
        self.assertFalse(self.helper.is_user_match(self.env['res.users'].browse(), {}))
        for untrusted in ({}, {'sub': self.admin.login}, dict(claims)):
            for method in (self.helper.get_user_match, self.helper.get_uid):
                with self.assertRaises(Unauthorized):
                    method(untrusted)
        for claims in (verified(sub=self.admin.login),
                       verified(sub='unbound', email=self.admin.email),
                       verified(sub='unbound', email=self.admin.login), verified()):
            with self.assertRaises(Unauthorized):
                self.helper.get_user_match(claims)
        claims = verified(sub='subject-a')
        with patch.object(type(self.helper), 'validate', return_value=claims) as validate:
            self.assertIs(self.helper.get_validate_user(self.token), claims)
            self.assertEqual(self.helper.get_user_token_login(self.token), self.admin)
            validate.assert_called_with(self.token)
        with patch.object(type(self.helper), 'validate', return_value={}):
            self.assertIsNone(self.helper.get_validate_user(self.token))
        self.admin.active = False
        for claims in (verified(sub='subject-a'), verified(sub='subject-a', type='machine')):
            with self.assertRaises(Unauthorized):
                self.helper.get_user_match(claims)
