"""UT-01..UT-07: existing behavior, not security acceptance.

Run only in a disposable Odoo 13 database. All token-like inputs are synthetic;
network and the production helper logger are blocked before each test.
"""
from types import SimpleNamespace
from unittest.mock import Mock, patch

import jwt
from requests import HTTPError
from werkzeug.exceptions import Unauthorized
from odoo.tests.common import SavepointCase

from ..models import helper as helper_module


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
            'token_endpoint': 'https://issuer.invalid/token', 'allow_missing_azp': True,
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
    def test_ut01_resolution_and_compute(self):
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
                if value:
                    with self.assertRaises(Unauthorized):
                        self.helper.get_bearer_token()
                else:
                    self.assertIsNone(self.helper.get_bearer_token())

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

    def test_ut04_issuance_and_wrappers(self):
        with patch.object(helper_module, 'fetch_json', return_value={
                'access_token': 'synthetic-result'}) as fetch:
            for aliases in (
                    {'iss': self.profile.issuer, 'issuer': 'unknown', 'issuer_url': 'unknown'},
                    {'issuer': self.profile.issuer, 'issuer_url': 'unknown'},
                    {'issuer_url': self.profile.issuer}, {}):
                for credentials in ({}, {'client_id': self.profile.client_id}):
                    fetch.reset_mock()
                    self.assertEqual(self.helper.generate_token(
                        grant_type='synthetic', **dict(aliases, **credentials)),
                        {'access_token': 'synthetic-result'})
                    fetch.assert_called_once_with(
                        self.profile.token_endpoint, data={'grant_type': 'synthetic'}, headers={})
            self.assertEqual(self.helper.encode(iss=self.profile.issuer), 'synthetic-result')
            for credentials in ({'client_secret': 'synthetic-rejected'},
                                {'client_id': self.profile.client_id,
                                 'client_secret': 'synthetic-rejected'},
                                {'client_id': 'wrong-client'}, {'iss': 'unknown'}):
                fetch.reset_mock()
                with self.assertRaises(Unauthorized):
                    self.helper.generate_token(**credentials)
                fetch.assert_not_called()
            for error in (HTTPError(), ValueError()):
                fetch.side_effect = error
                with self.assertRaises(Unauthorized):
                    self.helper.generate_token(iss=self.profile.issuer)
            fetch.side_effect = None
            for invalid in (None, [], {}, {'access_token': ''}):
                fetch.return_value = invalid
                with self.assertRaises(Unauthorized):
                    self.helper.generate_token(iss=self.profile.issuer)
        with patch.object(type(self.helper), 'validate', return_value={'synthetic': True}) as validate:
            self.assertEqual(self.helper.decode(self.token, unused=True), {'synthetic': True})
            validate.assert_called_once_with(self.token)
        with patch.object(type(self.helper), '_profile', return_value=SimpleNamespace(
                token_endpoint=False)), patch.object(helper_module, 'fetch_json') as fetch:
            with self.assertRaises(Unauthorized):
                self.helper.generate_token()
            fetch.assert_not_called()

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
        self.profile.write({'token_profile': 'opaque', 'jwks_uri': False,
                            'introspection_endpoint': 'https://issuer.invalid/introspect'})
        import time
        claims = dict(active=True, sub='subject-a', client_id='client-a',
                      aud='resource-a', exp=time.time() + 300)
        with patch.object(helper_module, 'fetch_json', return_value=claims) as fetch, \
                patch.object(jwt, 'decode') as decode:
            for credentials in ({}, {'client_id': self.profile.client_id}):
                fetch.reset_mock()
                result = self.helper.introspect_token(
                    self.token, iss=self.profile.issuer, **credentials)
                self.assertTrue(self.helper._verified(result))
                self.assertEqual(result, dict(claims, iss=self.profile.issuer))
                fetch.assert_called_once_with(self.profile.introspection_endpoint,
                                              data={'token': self.token}, headers={})
                decode.assert_not_called()
            self.assertEqual(self.helper.validate(self.token), dict(claims, iss=self.profile.issuer))
            for credentials in ({'client_id': 'wrong-client'},
                                {'client_secret': 'synthetic-rejected'},
                                {'client_id': self.profile.client_id,
                                 'client_secret': 'synthetic-rejected'},
                                {'url': 'https://override.invalid'}, {'iss': 'unknown'}):
                fetch.reset_mock()
                with self.assertRaises(Unauthorized):
                    self.helper.introspect_token(self.token, **credentials)
                fetch.assert_not_called()
            for error in (HTTPError(), ValueError()):
                fetch.side_effect = error
                with self.assertRaises(Unauthorized):
                    self.helper.introspect_token(self.token, iss=self.profile.issuer)
            fetch.side_effect = None
            for active in (False, 'true', 1, None):
                claims['active'] = active
                with self.assertRaises(Unauthorized):
                    self.helper.introspect_token(self.token, iss=self.profile.issuer)
            claims.pop('active')
            with self.assertRaises(Unauthorized):
                self.helper.introspect_token(self.token, iss=self.profile.issuer)
            decode.assert_not_called()
        with patch.object(type(self.helper), '_profile', return_value=SimpleNamespace(
                introspection_endpoint=False)), patch.object(helper_module, 'fetch_json') as fetch:
            with self.assertRaises(Unauthorized):
                self.helper.introspect_token(self.token)
            fetch.assert_not_called()
        claims['active'] = True
        for audience in (None, '', [], ['wrong-resource']):
            claims['aud'] = audience
            with patch.object(helper_module, 'fetch_json', return_value=claims):
                with self.assertRaises(Unauthorized):
                    self.helper.introspect_token(self.token, iss=self.profile.issuer)

    def test_ut06_verified_jwt_and_failures(self):
        import time
        import json
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048, backend=default_backend())
        public = key.public_key().public_bytes(serialization.Encoding.PEM,
                                              serialization.PublicFormat.SubjectPublicKeyInfo).decode('ascii')
        self.env['ir.config_parameter'].sudo().set_param('amr_resource.keys.synthetic', public)
        self.profile.write({'jwks_uri': False, 'local_key_ref': 'amr_resource.keys.synthetic'})
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
        self.profile.write({'local_key_ref': False, 'jwks_uri': 'https://keys.invalid/jwks'})
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
                                   self.env.company.id, self.admin.id)
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
