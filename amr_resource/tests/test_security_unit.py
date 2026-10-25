"""Actual candidate auth methods; Odoo persistence/request and HTTPS boundaries only.
No registry, DB, HTTP deployment, UAT or sibling-module acceptance is implied.
"""
import importlib.util
import json
from pathlib import Path
import socket
import sys
import time
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import Mock, call, patch

import jwt
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from werkzeug.exceptions import Unauthorized

from test_registry_unit import registry, BoundaryModel

ROOT = Path(__file__).resolve().parents[1]


def load_candidates():
    odoo = ModuleType('odoo')
    odoo.api = SimpleNamespace(model=lambda method: method)
    odoo.models = SimpleNamespace(Model=BoundaryModel, AbstractModel=BoundaryModel)
    odoo.SUPERUSER_ID = 1
    http = ModuleType('odoo.http')
    http.request = SimpleNamespace()
    service = ModuleType('odoo.service')
    service.security = SimpleNamespace(compute_session_token=Mock(return_value='synthetic-session'))
    errors = ModuleType('odoo.exceptions')
    errors.UserError = type('UserError', (Exception,), {})
    pkg = ModuleType('resource_candidate')
    pkg.__path__ = [str(ROOT)]
    models = ModuleType('resource_candidate.models')
    models.__path__ = [str(ROOT / 'models')]
    modules = {'odoo': odoo, 'odoo.http': http, 'odoo.service': service,
               'odoo.exceptions': errors, 'resource_candidate': pkg,
               'resource_candidate.models': models}
    loaded = []
    with patch.dict(sys.modules, modules):
        for name in ('helper', 'ir_http', 'res_users'):
            spec = importlib.util.spec_from_file_location('resource_candidate.models.' + name,
                                                          ROOT / 'models' / (name + '.py'))
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            loaded.append(module)
    return loaded


helper_module, http_module, users_module = load_candidates()


class Rows(list):
    def mapped(self, key):
        return [getattr(row, key) for row in self]

    def filtered(self, predicate):
        return Rows(row for row in self if predicate(row))

    def __getattr__(self, name):
        if len(self) != 1:
            raise ValueError('Ambiguous synthetic recordset')
        return getattr(self[0], name)


class User:
    _name = 'res.users'

    def __init__(self, company, **values):
        self.id, self.login = 27, 'synthetic-user'
        self.active, self.share = True, False
        self.company_ids, self.groups = [company], set()
        self.__dict__.update(values)

    def __len__(self):
        return 1

    def exists(self):
        return self

    def has_group(self, name):
        return name in self.groups


class RegistryBoundary:
    def __init__(self, env):
        self.env, self.rows = env, Rows()
        self.searches = []

    def sudo(self):
        return self

    def with_context(self, **kw):
        return self

    def search(self, domain):
        self.searches.append(domain)
        return Rows(row for row in self.rows if all(
            (getattr(row, name).id if name == 'company_id' else getattr(row, name)) == value
            for name, operator, value in domain))

    def _lookup(self, issuer=None, token_profile=None):
        return registry.AmrResourceIssuer._lookup(self, issuer, token_profile)


class Env:
    def __init__(self):
        self.company = SimpleNamespace(id=7)
        self.uid, self.context = 3, {}
        self.registry = RegistryBoundary(self)
        self.users = {}
        self.user_reads = []
        self.parameters = Mock()
        self.parameters.sudo.return_value = self.parameters

    def __getitem__(self, name):
        if name == 'oidc.issuer.register':
            return self.registry
        if name == 'res.users':
            def browse(uid):
                self.user_reads.append(uid)
                return self.users.get(uid, Rows())
            return SimpleNamespace(browse=browse)
        if name == 'ir.config_parameter':
            return self.parameters
        if name == 'amr.resource.helper':
            return self.helper
        if name == 'ir.http':
            return http_module.IrHttp
        raise AssertionError('Unexpected ORM boundary')


class SecurityUnitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.key = rsa.generate_private_key(public_exponent=65537, key_size=2048, backend=default_backend())
        cls.other_key = rsa.generate_private_key(public_exponent=65537, key_size=2048, backend=default_backend())
        cls.pem = cls.key.public_key().public_bytes(serialization.Encoding.PEM,
                                                   serialization.PublicFormat.SubjectPublicKeyInfo).decode('ascii')
        cls.jwk = json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(cls.key.public_key()))
        cls.jwk.update(kid='synthetic-key', alg='RS256', use='sig')

    def setUp(self):
        self.env = Env()
        self.helper = helper_module.ResourceHelper()
        self.helper.env = self.env
        self.env.helper = self.helper
        self.user = User(self.env.company)
        self.env.users[self.user.id] = self.user
        self.profile = SimpleNamespace(issuer='https://issuer.example', active=True,
            company_id=self.env.company, token_profile='jwt', jwks_uri='https://keys.example/jwks',
            local_public_key=False, local_key_ref=False, token_endpoint='https://issuer.example/token',
            mvp_enabled=True, metadata_mode='manual', verification_source='jwks',
            introspection_source='none', introspection_endpoint=False, credential_ref=False,
            client_id='synthetic-client', azp='synthetic-client', allow_missing_azp=False,
            audience_ids=Rows([SimpleNamespace(value='first'), SimpleNamespace(value='second')]),
            binding_ids=Rows([SimpleNamespace(sub='subject', user_id=self.user)]),
            resolver_mode='get_user_match', resolver_key='get_user_match', fixed_user_id=self.user,
            _verification_algorithms=lambda key_metadata: frozenset(['RS256']),
            python_code="raise AssertionError('stored code must never execute')")
        self.env.registry.rows.append(self.profile)
        self.claims = dict(iss=self.profile.issuer, sub='subject', aud='second', client_id='synthetic-client',
                           exp=int(time.time()) + 300, iat=int(time.time()) - 1, jti='synthetic-jti',
                           azp='synthetic-client')
        self.request = SimpleNamespace(env=self.env, uid=None, session=SimpleNamespace(uid=None),
            httprequest=SimpleNamespace(args={}, form={}, headers={}, environ={}))
        for module in (helper_module, http_module):
            guard = patch.object(module, 'request', self.request)
            guard.start()
            self.addCleanup(guard.stop)
        for target in ('socket.create_connection', 'socket.socket.connect', 'socket.getaddrinfo',
                       'logging.Logger._log'):
            guard = patch(target, side_effect=AssertionError('Forbidden external boundary'))
            guard.start()
            self.addCleanup(guard.stop)
        guard = patch.object(helper_module, 'fetch_json', return_value={'keys': [self.jwk]})
        self.fetch = guard.start()
        self.addCleanup(guard.stop)
        guard = patch.object(helper_module, 'preflight_endpoint', return_value=(
            'https://issuer.example/introspect', 'issuer.example', '/introspect',
            (socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, '', ('93.184.216.34', 443)),
            object()))
        self.preflight = guard.start()
        self.addCleanup(guard.stop)

    def token(self, claims=None, headers=None, key=None):
        return jwt.encode(self.claims if claims is None else claims, key or self.key,
                          algorithm='RS256', headers=dict({'typ': 'at+jwt', 'kid': 'synthetic-key'}, **(headers or {})))

    def reject(self, call, *args, **kwargs):
        with self.assertRaises(Unauthorized) as result:
            call(*args, **kwargs)
        self.assertEqual(result.exception.code, 401)
        self.assertIsNone(result.exception.__context__)

    def test_jwks_rejects_malformed_unselected_rsa_member(self):
        malformed_unselected = dict(self.jwk, kid='other-key', n='not-base64url')
        self.fetch.return_value = {'keys': [self.jwk, malformed_unselected]}
        self.reject(self.helper.validate, self.token())

    def test_jwks_rejects_invalid_global_key_ids_and_members(self):
        malformed_sets = (
            [],
            [self.jwk, None],
            [self.jwk, {'kty': 'RSA'}],
            [self.jwk, {'kid': ''}],
            [self.jwk, {'kid': 'a' * 257}],
            [self.jwk, {'kid': 'bad\u00a0kid'}],
            [self.jwk, {'kid': 'bad\u0001kid'}],
            [self.jwk, {'kid': 'synthetic-key'}],
        )
        for keys in malformed_sets:
            with self.subTest(keys=keys):
                self.fetch.return_value = {'keys': keys}
                self.reject(self.helper.validate, self.token())

    def test_opaque_token_dispatch_is_rejected_before_introspection(self):
        self.profile.token_profile = 'opaque'
        self.profile.mvp_enabled = False
        self.reject(self.helper.validate, 'synthetic-opaque-token')
        self.fetch.assert_not_called()
        self.env.parameters.get_param.assert_not_called()

    def test_non_mvp_disabled_ps256_policy_rejected_before_fetch(self):
        self.profile.mvp_enabled = False
        self.profile.algorithm_policy_ids = [SimpleNamespace(
            algorithm_id=SimpleNamespace(name='PS256'), enabled=False)]
        self.reject(self.helper.validate, self.token())
        self.fetch.assert_not_called()
        self.env.parameters.get_param.assert_not_called()

    def test_non_mvp_source_mismatch_does_not_fallback_to_jwks(self):
        self.profile.mvp_enabled = False
        self.profile.verification_source = 'local_public'
        self.profile.local_key_ref = False
        self.profile.local_public_key = False
        self.reject(self.helper.validate, self.token())
        self.fetch.assert_not_called()
        self.env.parameters.get_param.assert_not_called()

    def test_non_mvp_jwks_source_does_not_use_local_key_reference(self):
        self.profile.mvp_enabled = False
        self.profile.verification_source = 'jwks'
        self.profile.local_key_ref = 'fixture.local-public-key'
        self.helper._local_public_key = Mock(return_value=self.pem)
        self.reject(self.helper.validate, self.token())
        self.helper._local_public_key.assert_not_called()
        self.fetch.assert_not_called()

    def test_get_jwks_data_rejects_local_profile_before_fetch(self):
        self.profile.verification_source = 'local_public'
        self.profile.local_key_ref = False
        self.profile.local_public_key = False
        self.profile.jwks_uri = False
        self.reject(self.helper.get_jwks_data, self.profile.issuer)
        self.fetch.assert_not_called()
        self.env.parameters.get_param.assert_not_called()

    def test_validate_rejects_discovery_local_key_before_key_read(self):
        self.profile.metadata_mode = 'oidc_discovery'
        self.profile.verification_source = 'local_public'
        self.profile.jwks_uri = False
        self.profile.local_key_ref = 'fixture.local-public-key'
        self.helper._local_public_key = Mock(return_value=self.pem)
        self.reject(self.helper.validate, self.token())
        self.helper._local_public_key.assert_not_called()
        self.fetch.assert_not_called()
        self.env.parameters.get_param.assert_not_called()

    def test_non_mvp_discovery_profile_fails_before_fetch(self):
        self.profile.mvp_enabled = False
        self.profile.metadata_mode = 'oidc_discovery'
        self.profile.verification_source = 'jwks'
        self.profile.introspection_source = 'none'
        self.reject(self.helper.get_oidc_config, self.profile.issuer)
        self.fetch.assert_not_called()

    def test_non_mvp_ps256_rejected_before_dispatch(self):
        self.profile.mvp_enabled = False
        token = jwt.encode(self.claims, self.key, algorithm='PS256',
                           headers={'typ': 'at+jwt', 'kid': 'synthetic-key'})
        self.reject(self.helper.validate, token)
        self.fetch.assert_not_called()
        self.env.parameters.get_param.assert_not_called()

    def test_uat06_actual_rs256_signature_and_helpers(self):
        token = self.token()
        payload = self.helper.validate(token)
        self.assertTrue(self.helper._verified(payload))
        self.assertIsInstance(payload, dict)
        self.assertEqual(self.helper.get_uid(payload), self.user.id)
        self.assertTrue(self.helper.is_user_match(self.user, payload))
        self.assertEqual(self.helper.get_user_token_login(token), self.user)
        self.assertEqual(self.helper.decode(token)['sub'], 'subject')
        self.assertEqual(self.helper.get_validate_user(token)['alg'], 'RS256')
        self.reject(self.helper.validate, self.token(key=self.other_key))

    def test_uat01_16_unknown_inactive_duplicate_company_zero_egress(self):
        for issuer in ('https://unknown.example', 'https://issuer.example/', 'HTTPS://issuer.example', None, 123):
            claims = dict(self.claims, iss=issuer)
            self.reject(self.helper.validate, self.token(claims))
        self.profile.active = False
        self.reject(self.helper.validate, self.token())
        self.profile.active = True
        self.env.company = SimpleNamespace(id=8)
        payload = self.helper.validate(self.token())
        self.reject(self.helper.get_uid, payload)
        self.env.company = SimpleNamespace(id=7)
        self.env.registry.rows.append(self.profile)
        self.reject(self.helper.validate, self.token())
        self.fetch.assert_called_once()
        self.env.parameters.get_param.assert_not_called()
        self.assertEqual(self.env.user_reads, [self.user.id])

    def test_uat04_27_unsupported_token_classes_zero_egress(self):
        for headers in ({'typ': 'JWT'}, {'typ': None}, {'jku': 'https://caller.example'},
                        {'x5u': 'https://caller.example'}, {'crit': ['unknown']}):
            self.reject(self.helper.validate, self.token(headers=headers))
        hs = jwt.encode(self.claims, 'synthetic-not-a-credential', algorithm='HS256', headers={'typ': 'at+jwt'})
        for token in (hs, '', None, 'a.b', 'a.b.c.d', 'a.b.c'):
            self.reject(self.helper.validate, token)
        self.reject(self.helper.validate_hs, hs)
        self.fetch.assert_not_called()

    def test_uat06_required_claims_and_zero_leeway(self):
        for name in ('iss', 'aud', 'exp', 'iat', 'jti', 'sub', 'client_id'):
            claims = dict(self.claims)
            del claims[name]
            self.reject(self.helper.validate, self.token(claims))
        for changes in ({'exp': int(time.time()) - 1}, {'iat': int(time.time()) + 30},
                        {'nbf': int(time.time()) + 30}, {'exp': True}, {'iat': '123'},
                        {'jti': ''}, {'sub': []}, {'client_id': 'wrong'}):
            self.reject(self.helper.validate, self.token(dict(self.claims, **changes)))
        self.fetch.assert_not_called()

    def test_uat17_audience_any_exact(self):
        for audience in ('first', 'second', ['no', 'second'], ['first', 'second']):
            self.assertTrue(self.helper._verified(self.helper.validate(self.token(dict(self.claims, aud=audience)))))
        self.fetch.reset_mock()
        for audience in ('', 'First', [], ['no'], [['second']], ['second', 1], None, 1):
            self.reject(self.helper.validate, self.token(dict(self.claims, aud=audience)))
        self.fetch.assert_not_called()

    def test_uat18_azp_optional_only_by_profile(self):
        claims = dict(self.claims)
        del claims['azp']
        self.reject(self.helper.validate, self.token(claims))
        self.profile.allow_missing_azp = True
        self.assertTrue(self.helper._verified(self.helper.validate(self.token(claims))))
        for value in ('', 'wrong', [], ['synthetic-client'], None):
            self.reject(self.helper.validate, self.token(dict(claims, azp=value)))

    def test_uat06_jwks_rsa_selection_and_no_cache(self):
        self.helper.validate(self.token())
        self.helper.validate(self.token())
        self.assertEqual(self.fetch.call_count, 2)
        for keys in ([], [self.jwk, self.jwk], [dict(self.jwk, kty='EC')],
                     [dict(self.jwk, alg='HS256')], [dict(self.jwk, use='enc')],
                     [dict(self.jwk, key_ops=['sign'])]):
            self.fetch.return_value = {'keys': keys}
            self.reject(self.helper.validate, self.token())
        for private_name in ('d', 'p', 'q', 'dp', 'dq', 'qi', 'oth', 'k'):
            self.fetch.return_value = {'keys': [dict(self.jwk, **{private_name: 'private'})]}
            self.reject(self.helper.validate, self.token())

    def test_x5c_does_not_replace_selected_trusted_rsa_key(self):
        self.fetch.return_value = {'keys': [dict(self.jwk, x5c=['synthetic-cert'])]}
        self.assertTrue(self.helper._verified(self.helper.validate(
            self.token(headers={'x5c': ['attacker-cert']}))))
        self.reject(self.helper.validate, self.token(key=self.other_key,
                                                     headers={'x5c': ['attacker-cert']}))
        self.assertEqual(self.fetch.call_count, 2)
        self.env.parameters.get_param.assert_not_called()

    def test_metadata_url_and_oidc_metadata_are_strict(self):
        self.assertEqual(helper_module._oidc_discovery_url('https://id.invalid/tenant/'),
                         'https://id.invalid/tenant/.well-known/openid-configuration')
        self.assertEqual(helper_module._rfc8414_metadata_url('https://id.invalid/tenant/'),
                         'https://id.invalid/.well-known/oauth-authorization-server/tenant/')
        metadata = {'issuer': self.profile.issuer,
                    'authorization_endpoint': 'https://id.invalid/authorize',
                    'jwks_uri': 'https://id.invalid/jwks',
                    'response_types_supported': ['code'],
                    'subject_types_supported': ['public'],
                    'id_token_signing_alg_values_supported': ['RS256'],
                    'token_endpoint': 'https://id.invalid/token'}
        self.assertEqual(helper_module._parse_oidc_metadata(metadata, self.profile.issuer)['jwks_uri'],
                         'https://id.invalid/jwks')
        for invalid in (dict(metadata, issuer=self.profile.issuer + '/'),
                        dict(metadata, jwks_uri=None),
                        dict(metadata, response_types_supported=[]),
                        {key: value for key, value in metadata.items() if key != 'jwks_uri'}):
            with self.subTest(metadata=invalid), self.assertRaises(Unauthorized):
                helper_module._parse_oidc_metadata(invalid, self.profile.issuer)

    def test_rfc8414_authorization_endpoint_requirement_uses_grants(self):
        metadata = {'issuer': self.profile.issuer, 'response_types_supported': ['custom'],
                    'grant_types_supported': ['authorization_code'],
                    'token_endpoint': 'https://id.invalid/token',
                    'introspection_endpoint': 'https://id.invalid/introspect'}
        with self.assertRaises(Unauthorized):
            helper_module._parse_rfc8414_metadata(metadata, self.profile.issuer)

    def test_rfc8414_refresh_token_does_not_require_authorization_endpoint(self):
        metadata = {'issuer': self.profile.issuer, 'response_types_supported': ['custom'],
                    'grant_types_supported': ['refresh_token'],
                    'token_endpoint': 'https://id.invalid/token',
                    'introspection_endpoint': 'https://id.invalid/introspect'}
        self.assertEqual(helper_module._parse_rfc8414_metadata(metadata, self.profile.issuer),
                         metadata)

    def test_rfc8414_grant_defaults_and_endpoint_exceptions(self):
        metadata = {'issuer': self.profile.issuer, 'response_types_supported': ['custom'],
                    'introspection_endpoint': 'https://id.invalid/introspect'}
        default_grants = dict(metadata, authorization_endpoint='https://id.invalid/authorize')
        with self.assertRaises(Unauthorized):
            helper_module._parse_rfc8414_metadata(
                dict(metadata, token_endpoint='https://id.invalid/token'), self.profile.issuer)
        with self.assertRaises(Unauthorized):
            helper_module._parse_rfc8414_metadata(default_grants, self.profile.issuer)
        default_grants['token_endpoint'] = 'https://id.invalid/token'
        self.assertEqual(helper_module._parse_rfc8414_metadata(default_grants, self.profile.issuer),
                         default_grants)

        implicit = dict(metadata, grant_types_supported=['implicit'],
                        authorization_endpoint='https://id.invalid/authorize')
        self.assertEqual(helper_module._parse_rfc8414_metadata(implicit, self.profile.issuer), implicit)
        implicit.pop('authorization_endpoint')
        with self.assertRaises(Unauthorized):
            helper_module._parse_rfc8414_metadata(implicit, self.profile.issuer)

        client_credentials = dict(metadata, grant_types_supported=['client_credentials'],
                                  token_endpoint='https://id.invalid/token')
        self.assertEqual(helper_module._parse_rfc8414_metadata(
            client_credentials, self.profile.issuer), client_credentials)

        extension = dict(metadata, grant_types_supported=['urn:example:grant:custom'])
        with self.assertRaises(Unauthorized):
            helper_module._parse_rfc8414_metadata(extension, self.profile.issuer)

        for grants in (None, [], [''], [1]):
            invalid = dict(metadata, grant_types_supported=grants,
                           authorization_endpoint='https://id.invalid/authorize',
                           token_endpoint='https://id.invalid/token')
            with self.subTest(grants=grants), self.assertRaises(Unauthorized):
                helper_module._parse_rfc8414_metadata(invalid, self.profile.issuer)

    def test_rfc8414_present_jwks_uri_is_always_terminal(self):
        metadata = {'issuer': self.profile.issuer, 'response_types_supported': ['code'],
                    'authorization_endpoint': 'https://id.invalid/authorize',
                    'token_endpoint': 'https://id.invalid/token',
                    'introspection_endpoint': 'https://id.invalid/introspect'}
        self.assertEqual(helper_module._parse_rfc8414_metadata(metadata, self.profile.issuer)['introspection_endpoint'],
                         'https://id.invalid/introspect')
        for jwks_value in ('https://id.invalid/jwks', None, '', 7):
            with self.subTest(jwks_uri=jwks_value), self.assertRaises(Unauthorized):
                helper_module._parse_rfc8414_metadata(dict(metadata, jwks_uri=jwks_value),
                                                      self.profile.issuer)
        incomplete = dict(metadata)
        del incomplete['token_endpoint']
        with self.assertRaises(Unauthorized):
            helper_module._parse_rfc8414_metadata(incomplete, self.profile.issuer)

    def test_manual_jwks_config_does_not_require_discovery_unavailable_declaration(self):
        self.profile.mvp_enabled = True
        self.profile.metadata_mode = 'manual'
        self.profile.token_profile = 'jwt'
        self.profile.verification_source = 'jwks'
        self.profile.introspection_source = 'none'
        self.profile.discovery_unavailable_declared = False
        self.profile.discovery_unavailable_evidence_ref = False
        result = self.helper.get_oidc_config(self.profile.issuer)
        self.assertEqual(result['jwks_uri'], self.profile.jwks_uri)
        self.fetch.assert_not_called()

    def test_runtime_rejects_truthy_discovery_fields_before_key_or_network_access(self):
        self.profile.discovery_unavailable_declared = True
        self.helper._local_public_key = Mock(return_value=self.pem)
        self.profile.verification_source = 'local_public'
        self.profile.jwks_uri = False
        self.profile.local_key_ref = 'fixture.local-public-key'
        self.reject(self.helper.validate, self.token())
        self.helper._local_public_key.assert_not_called()
        self.fetch.assert_not_called()
        self.profile.discovery_unavailable_declared = False
        self.profile.discovery_unavailable_evidence_ref = 'evidence.discovery'
        self.reject(self.helper.validate, self.token())
        self.helper._local_public_key.assert_not_called()
        self.fetch.assert_not_called()

    def test_manual_jwks_config_rejects_stale_introspection_and_never_returns_endpoint(self):
        self.profile.introspection_endpoint = False
        config, metadata = self.helper._get_oidc_config(self.profile.issuer)
        self.assertIsNone(config['introspection_endpoint'])
        self.assertIsNone(metadata)
        self.profile.introspection_endpoint = 'https://issuer.example/introspect'
        with self.assertRaises(Unauthorized):
            self.helper._get_oidc_config(self.profile.issuer)

    def test_get_oidc_config_rejects_discovery_and_introspection_modes_before_fetch(self):
        self.profile.mvp_enabled = True
        self.profile.metadata_mode = 'oidc_discovery'
        self.profile.token_profile = 'jwt'
        self.fetch.reset_mock()
        with self.assertRaises(Unauthorized):
            self.helper.get_oidc_config(self.profile.issuer)
        self.fetch.assert_not_called()
        self.profile.metadata_mode = 'manual'
        self.profile.discovery_unavailable_declared = True
        self.profile.discovery_unavailable_evidence_ref = 'evidence.discovery.1'
        self.profile.verification_source = 'none'
        self.profile.jwks_uri = False
        self.profile.introspection_source = 'rfc8414'
        with self.assertRaises(Unauthorized):
            self.helper.get_oidc_config(self.profile.issuer)
        self.fetch.assert_not_called()
        self.env.parameters.get_param.assert_not_called()


    def test_uat06_local_key_no_loopback_or_local_bypass(self):
        self.profile.verification_source = 'local_public'
        self.profile.local_key_ref = "amr_resource.keys.synthetic"
        self.profile.local_public_key, self.profile.jwks_uri = self.pem, False
        self.env.parameters.get_param.return_value = self.profile.local_public_key
        self.assertTrue(self.helper.is_local_token(self.token()))
        self.assertTrue(self.helper._verified(self.helper.validate(self.token())))
        self.reject(self.helper.validate, self.token(key=self.other_key))
        self.fetch.assert_not_called()
        self.env.parameters.get_param.return_value = 'invalid rotated public key'
        self.reject(self.helper.validate, self.token())
        self.fetch.assert_not_called()

    def opaque(self):
        self.profile.token_profile = 'opaque'
        self.profile.jwks_uri = False
        result = dict(active=True, sub='subject', aud='first', client_id=self.profile.client_id, azp=self.profile.azp)
        self.fetch.return_value = result
        return result

    def test_uat05_opaque_post_profile_bound_issuer(self):
        self.opaque()
        self.reject(self.helper.validate, 'synthetic-opaque')
        self.fetch.assert_not_called()

    def test_uat05_opaque_strict_active_claims(self):
        good = self.opaque()
        for changes in ({'active': 1}, {'active': 'true'}, {'active': False}, {'sub': ''},
                        {'aud': 'wrong'}, {'client_id': 'wrong'}, {'iss': 'https://wrong.example'}):
            self.fetch.return_value = dict(good, **changes)
            self.reject(self.helper.validate, 'synthetic-opaque')
        for name in ('sub', 'aud', 'client_id'):
            bad = dict(good)
            del bad[name]
            self.fetch.return_value = bad
            self.reject(self.helper.validate, 'synthetic-opaque')

    def test_opaque_optional_claim_contract(self):
        self.opaque()
        self.reject(self.helper.validate, 'synthetic-opaque')
        self.fetch.assert_not_called()

    def test_uat05_opaque_caller_url_and_credentials_rejected(self):
        self.opaque()
        for kwargs in ({'url': 'https://caller.example'}, {'client_secret': 'synthetic'},
                       {'client_id': 'wrong'}, {'method': 'GET'}, {'iss': 'https://unknown.example'}):
            self.reject(self.helper.introspect_token, 'synthetic-opaque', **kwargs)
        self.reject(self.helper.introspect_token, self.token())
        self.fetch.assert_not_called()

    def test_uat19_binding_exact_no_email_login_or_autobind(self):
        payload = self.helper.validate(self.token(dict(self.claims, email='collision@example.invalid')))
        self.profile.binding_ids = Rows()
        self.reject(self.helper.get_user_match, payload)
        self.assertEqual(self.env.user_reads, [])
        self.profile.binding_ids = Rows([SimpleNamespace(sub='wrong', user_id=self.user)])
        self.reject(self.helper.get_user_match, payload)
        self.profile.binding_ids = Rows([SimpleNamespace(sub='subject', user_id=self.user)] * 2)
        self.reject(self.helper.get_user_match, payload)
        self.assertEqual(self.env.user_reads, [])

    def test_introspection_client_id_requires_exact_builtin_string(self):
        class StringSubclass(str):
            pass

        for value in ('a', 'a' * 1024, 'auth client+:/%'):
            with self.subTest(value_length=len(value)):
                self.assertTrue(helper_module._introspection_client_id(value))
        for value in (StringSubclass('auth-client'), '', ' ' * 3, 'a' * 1025,
                      'a\x00b', 'a\x7fb', 'a\x80b'):
            with self.subTest(value=repr(value)):
                self.assertFalse(helper_module._introspection_client_id(value))

    def test_oauth_basic_encodes_client_and_secret_components_before_base64(self):
        value = helper_module._introspection_basic_header('A +:/%', 's +:/%é')
        self.assertEqual(value, 'Basic QSslMkIlM0ElMkYlMjU6cyslMkIlM0ElMkYlMjUlQzMlQTk=')
        for client_id, secret in (('', 'secret'), ('client', '')):
            with self.subTest(client_id=client_id, secret=secret), self.assertRaises(Unauthorized):
                helper_module._introspection_basic_header(client_id, secret)

    def test_mvp_verification_uses_intersected_issuer_algorithm_policy(self):
        self.profile.mvp_enabled = True
        self.profile.metadata_mode = 'manual'
        self.profile.verification_source = 'jwks'
        self.profile.introspection_source = 'none'
        self.profile._verification_algorithms = Mock(return_value=frozenset(['RS256']))
        self.helper.validate(self.token())
        self.assertEqual(self.profile._verification_algorithms.call_count, 2)
        self.assertEqual(self.profile._verification_algorithms.call_args_list[0][0], ({},))
        self.assertEqual(self.profile._verification_algorithms.call_args_list[1][0], (self.jwk,))

        self.fetch.reset_mock()
        self.profile._verification_algorithms = Mock(return_value=frozenset())
        self.reject(self.helper.validate, self.token())
        self.profile._verification_algorithms.assert_called_once_with({})
        self.fetch.assert_not_called()

    def test_mapping_cardinality_postcheck_company_and_no_fallback(self):
        self.profile.resolver_mode = 'mapping'
        self.profile.mvp_enabled = True
        self.profile.metadata_mode = 'manual'
        self.profile.verification_source = 'jwks'
        self.profile.introspection_source = 'none'
        self.profile.user_mapping_ids = Rows([
            SimpleNamespace(active=True, sequence=10, field_user='login', jwt_key='primary'),
            SimpleNamespace(active=True, sequence=20, field_user='login', jwt_key='secondary'),
        ])
        claims = dict(self.claims, primary='none', secondary='synthetic-user')
        validation = self.helper.validate(self.token(claims))
        self.helper._find_mapping_users = Mock(side_effect=[Rows(), Rows([self.user])])
        self.assertEqual(self.helper.get_uid(validation), self.user.id)
        self.assertEqual(self.helper._find_mapping_users.call_args_list,
                         [call('login', 'none'), call('login', 'synthetic-user')])

        self.helper._find_mapping_users.reset_mock()
        other = User(SimpleNamespace(id=8), id=28)
        self.helper._find_mapping_users.side_effect = [Rows([self.user, other]), Rows([self.user])]
        self.reject(self.helper.get_uid, validation)
        self.helper._find_mapping_users.assert_called_once_with('login', 'none')

        self.helper._find_mapping_users.reset_mock()
        self.env.users[28] = other
        self.profile.binding_ids = Rows([SimpleNamespace(sub='subject', user_id=other)])
        self.helper._find_mapping_users.side_effect = [Rows([other])]
        self.reject(self.helper.get_uid, validation)
        self.helper._find_mapping_users.assert_called_once_with('login', 'none')

        self.profile.binding_ids = Rows([SimpleNamespace(sub='subject', user_id=self.user)])
        self.profile.resolver_mode = 'fixed_user'
        self.profile.fixed_user_id = self.user
        self.helper._find_mapping_users.reset_mock()
        self.profile.resolver_mode = 'mapping'
        self.helper._find_mapping_users.side_effect = [Rows(), Rows()]
        self.reject(self.helper.get_uid, validation)
        self.assertEqual(self.helper._find_mapping_users.call_count, 2)

    def test_mapping_resolver_requires_unique_candidate_and_matching_existing_binding(self):
        self.profile.resolver_mode = 'mapping'
        self.profile.mvp_enabled = True
        self.profile.metadata_mode = 'manual'
        self.profile.verification_source = 'jwks'
        self.profile.introspection_source = 'none'
        self.profile.user_mapping_ids = Rows([
            SimpleNamespace(active=True, sequence=20, field_user='login', jwt_key='preferred_username'),
            SimpleNamespace(active=True, sequence=10, field_user='login', jwt_key='preferred_username'),
        ])
        payload = self.helper.validate(self.token(dict(self.claims, preferred_username='synthetic-user')))
        self.helper._find_mapping_users = Mock(return_value=Rows([self.user]))
        self.assertEqual(self.helper.get_uid(payload), self.user.id)
        self.helper._find_mapping_users.assert_called_once_with('login', 'synthetic-user')

        self.profile.binding_ids = Rows([SimpleNamespace(sub='subject', user_id=SimpleNamespace(id=999))])
        self.reject(self.helper.get_uid, payload)
        self.profile.binding_ids = Rows([SimpleNamespace(sub='subject', user_id=self.user)])
        self.profile.user_mapping_ids = Rows([
            SimpleNamespace(active=True, sequence=10, field_user='login', jwt_key='preferred_username')
        ] + [SimpleNamespace(active=False, sequence=sequence, field_user='login',
                             jwt_key='historical_%d' % sequence)
             for sequence in range(20, 41)])
        self.helper._find_mapping_users = Mock(return_value=Rows([self.user]))
        self.assertEqual(self.helper.get_uid(payload), self.user.id)

    def test_uat20_fixed_user_and_ineligible_results(self):
        self.profile.resolver_mode = 'fixed_user'
        payload = self.helper.validate(self.token(dict(self.claims, uid=1)))
        self.assertEqual(self.helper.get_uid(payload), self.user.id)
        for values in ({'active': False}, {'id': 1}, {'share': True}, {'company_ids': []},
                       {'groups': {'base.group_portal'}}, {'groups': {'base.group_public'}}):
            bad = User(self.env.company, **values)
            self.env.users[self.profile.fixed_user_id.id] = bad
            self.reject(self.helper.get_user_match, payload)
        for bad in (Rows(), Rows([self.user, self.user]), 27, {}, None):
            self.env.users[self.profile.fixed_user_id.id] = bad
            self.reject(self.helper.get_user_match, payload)

    def test_uat21_22_23_allowlist_python_and_no_fallback(self):
        payload = self.helper.validate(self.token())
        self.profile.resolver_mode = 'resolver'
        self.assertEqual(self.helper.get_uid(payload), self.user.id)
        self.profile.resolver_key = 'arbitrary.model.method'
        self.reject(self.helper.get_user_match, payload)
        for mode in ('python_code', '', False, 'unknown'):
            self.profile.resolver_mode = mode
            self.reject(self.helper.get_user_match, payload)
        self.profile.resolver_mode = 'get_user_match'
        self.user.active = False
        self.reject(self.helper.get_user_match, payload)

    def test_uat27_payload_provenance_not_a_dict_marker(self):
        payload = self.helper.validate(self.token())
        self.reject(self.helper.get_uid, dict(payload))
        self.reject(self.helper.get_user_match, {'__verified': True, **dict(payload)})
        payload['sub'] = 'changed'
        self.reject(self.helper.get_uid, payload)
        payload = self.helper.validate(self.token())
        self.env.uid += 1
        self.reject(self.helper.get_uid, payload)
        self.env.uid -= 1
        self.env.company = SimpleNamespace(id=99)
        self.reject(self.helper.get_uid, payload)

    def test_uat28_standalone_helpers_unknown_zero_egress(self):
        for method in (self.helper.get_jwks_data, self.helper.get_oidc_config, self.helper.is_local_issuer):
            self.reject(method, 'https://unknown.example')
        self.fetch.assert_not_called()
        config = self.helper.get_oidc_config(self.profile.issuer)
        self.assertEqual(config['jwks_uri'], self.profile.jwks_uri)
        self.fetch.assert_not_called()
        self.assertEqual(self.helper.get_audiences(), ['first', 'second'])
        self.assertEqual(self.helper.get_issuer(), self.profile.issuer)

    def test_uat04_generate_static_endpoint_no_caller_secret(self):
        self.fetch.return_value = {'access_token': 'synthetic-opaque'}
        self.profile.credential_ref = 'amr_resource.credential.synthetic'
        self.env.parameters.get_param.return_value = 'synthetic-secret'
        self.assertEqual(self.helper.encode(iss=self.profile.issuer, grant_type='client_credentials'), 'synthetic-opaque')
        self.fetch.assert_called_once_with(self.profile.token_endpoint,
            data={'grant_type': 'client_credentials'}, headers={'Authorization': 'Basic c3ludGhldGljLWNsaWVudDpzeW50aGV0aWMtc2VjcmV0'})
        self.fetch.reset_mock()
        self.reject(self.helper.generate_token, iss='https://unknown.example')
        self.reject(self.helper.generate_token, iss=self.profile.issuer, client_secret='synthetic')
        self.fetch.assert_not_called()

    def test_generate_token_strict_selector_and_parameters(self):
        self.fetch.return_value = {'access_token': 'synthetic-opaque'}
        self.profile.credential_ref = 'amr_resource.credential.synthetic'
        self.env.parameters.get_param.return_value = 'synthetic-secret'
        issuer = self.profile.issuer
        for kwargs in ({}, {'iss': issuer, 'issuer': 'https://other.example'},
                       {'iss': issuer, 'client_secret': ''}, {'iss': issuer, 'client_secret': None},
                       {'iss': issuer, 'client_id': ''}, {'iss': issuer, 'client_id': None},
                       {'iss': issuer, 'grant_type': 'password'}, {'iss': issuer, 'scope': []},
                       {'iss': issuer, 'unexpected': 'value'}):
            self.reject(self.helper.generate_token, **kwargs)
        self.fetch.assert_not_called()
        result = self.helper.generate_token(iss=issuer, issuer=issuer, issuer_url=issuer,
                                            grant_type='client_credentials', scope='')
        self.assertEqual(result['access_token'], 'synthetic-opaque')
        self.fetch.assert_called_once_with(self.profile.token_endpoint,
            data={'grant_type': 'client_credentials', 'scope': ''},
            headers={'Authorization': 'Basic c3ludGhldGljLWNsaWVudDpzeW50aGV0aWMtc2VjcmV0'})
        self.fetch.reset_mock()
        self.profile.credential_ref = False
        self.reject(self.helper.generate_token, iss=issuer, grant_type='client_credentials')
        self.fetch.assert_not_called()

    def test_uat09_session_bearer_params_and_no_weaker_fallback(self):
        candidate = http_module.IrHttp
        session = type('Auth', (candidate,), {'_auth_method_user': classmethod(lambda cls: None)})
        self.request.httprequest.headers['Authorization'] = 'malformed'
        session._auth_method_user_or_param()
        self.fetch.assert_not_called()
        denied = type('Auth', (candidate,), {'_auth_method_user': classmethod(lambda cls: (_ for _ in ()).throw(Unauthorized()))})
        self.request.httprequest.args['access_token'] = self.token()
        self.reject(denied._auth_method_user_or_param)
        self.fetch.assert_not_called()
        self.request.httprequest.headers['Authorization'] = 'Bearer a.b.c'
        self.reject(denied._auth_method_user_or_param)
        self.fetch.assert_not_called()
        self.request.httprequest.headers.clear()
        denied._auth_method_user_or_param()
        self.assertEqual(self.request.uid, self.user.id)

    def test_uat09_same_uid_metadata_preserved(self):
        self.request.uid = self.user.id
        self.request.httprequest.headers['Authorization'] = 'Bearer ' + self.token()
        http_module.IrHttp._auth_method_machine()
        self.assertFalse(hasattr(self.request, 'jwt_payload'))
        self.assertEqual(http_module.IrHttp.get_jwt_payload(), {})

    def test_uat27_request_payload_cannot_be_forged(self):
        self.request.jwt_payload = dict(self.claims)
        self.assertEqual(http_module.IrHttp.get_jwt_payload(), {})
        self.request.jwt_payload = self.helper.validate(self.token())
        self.assertTrue(self.helper._verified(http_module.IrHttp.get_jwt_payload()))

    def test_uat09_invalid_token_never_resolves_or_changes_uid(self):
        self.request.httprequest.headers['Authorization'] = 'Bearer a.b.c'
        self.reject(http_module.IrHttp._auth_method_machine)
        self.assertIsNone(self.request.uid)
        self.assertEqual(self.env.user_reads, [])
        self.fetch.assert_not_called()

    def test_uat27_user_context_requires_actual_provenance(self):
        class Consumer(users_module.ResUsers):
            def __init__(self, env):
                self.env, self.id = env, 27
            def with_context(self, **context):
                return context
        consumer = Consumer(self.env)
        self.env.context = {'__access_token_context': dict(self.claims)}
        self.reject(consumer.with_access_token_context, validate=False)
        self.request.jwt_payload = self.helper.validate(self.token())
        result = consumer.with_access_token_context(validate=False)
        self.assertTrue(self.helper._verified(result['__access_token_context']))

    def test_jwt_shaped_introspection_does_not_require_response_jti(self):
        settings = dict(mvp_enabled=True, metadata_mode='manual',
            discovery_unavailable_declared=True, discovery_unavailable_evidence_ref='evidence.discovery',
            verification_source='none', jwks_uri=False, local_key_ref=False, local_public_key=False,
            no_jwks_declaration=True, no_jwks_evidence_ref='evidence.keys',
            introspection_source='manual', introspection_endpoint='https://issuer.example/introspect',
            introspection_credential_ref='fixture.introspection.secret',
            introspection_auth_client_id='auth-client', introspection_auth_method='client_secret_basic',
            introspection_basic_contract_ref='accepted.contract.ref',
            introspection_credential_endpoint='https://issuer.example/introspect',
            allow_jwt_introspection=True)
        for name, value in settings.items():
            setattr(self.profile, name, value)
        self.profile.token_profile = 'jwt'
        self.env.parameters.get_param.return_value = 'synthetic-secret'
        response = dict(self.claims, active=True)
        response.pop('jti')
        self.fetch.return_value = response
        self.reject(self.helper.validate, self.token())
        self.fetch.assert_not_called()
        self.env.parameters.get_param.assert_not_called()

    def test_explicit_jwt_no_jwks_uses_authoritative_introspection_after_prefilter(self):
        for name, value in dict(mvp_enabled=True, metadata_mode='manual',
            discovery_unavailable_declared=True, discovery_unavailable_evidence_ref='evidence.discovery',
            verification_source='none', jwks_uri=False, local_key_ref=False, local_public_key=False,
            no_jwks_declaration=True, no_jwks_evidence_ref='evidence.keys',
            introspection_source='manual', introspection_endpoint='https://issuer.example/introspect',
            introspection_credential_ref='fixture.introspection.secret',
            introspection_auth_client_id='auth-client', introspection_auth_method='client_secret_basic',
            introspection_basic_contract_ref='accepted.contract.ref',
            introspection_credential_endpoint='https://issuer.example/introspect',
            allow_jwt_introspection=True).items():
            setattr(self.profile, name, value)
        self.profile.token_profile = 'jwt'
        self.env.parameters.get_param.return_value = 'synthetic-secret'
        response = dict(self.claims, active=True)
        self.fetch.return_value = response
        token = self.token()
        self.reject(self.helper.validate, token)
        self.fetch.assert_not_called()
        self.env.parameters.get_param.assert_not_called()

    def test_policy_revision_check_refreshes_cached_orm_state(self):
        profile = SimpleNamespace(active=True, policy_revision=1, ids=[3])
        profile.invalidate_cache = Mock(side_effect=lambda fnames, ids: setattr(profile, 'policy_revision', 2))
        with self.assertRaises(Unauthorized):
            helper_module._require_policy_revision(profile, 1)
        profile.invalidate_cache.assert_called_once_with(fnames=['active', 'policy_revision'], ids=[3])

    def test_stale_policy_before_local_key_read_rejects_without_reading_key(self):
        self.profile.policy_revision = 1
        self.profile.verification_source = 'local_public'
        self.profile.jwks_uri = False
        self.profile.local_key_ref = 'fixture.local-public-key'
        self.profile.invalidate_cache = Mock(
            side_effect=lambda fnames, ids: setattr(self.profile, 'policy_revision', 2))
        self.helper._local_public_key = Mock(return_value=self.pem)
        self.reject(self.helper.validate, self.token())
        self.helper._local_public_key.assert_not_called()

    def test_policy_revision_change_during_user_eligibility_rejects_dispatch(self):
        self.profile.policy_revision = 1
        validation = self.helper.validate(self.token())

        def stale_after_eligibility(user):
            self.profile.policy_revision = 2
            return user

        with patch.object(self.helper, '_eligible_user', side_effect=stale_after_eligibility):
            self.reject(self.helper.get_user_match, validation)

    def test_policy_revision_rechecked_after_resolution_before_token_dispatch(self):
        self.profile.policy_revision = 1

        def stale_user(validation):
            self.profile.policy_revision = 2
            return self.user

        with patch.object(self.helper, 'get_user_match', side_effect=stale_user):
            self.reject(self.helper.get_user_token_login, self.token())

    def test_verified_claims_reject_policy_revision_changes(self):
        self.profile.policy_revision = 1
        validation = self.helper.validate(self.token())
        self.assertTrue(self.helper._verified(validation))
        self.profile.policy_revision = 2
        self.assertFalse(self.helper._verified(validation))
        self.profile.policy_revision = 3
        def changed_during_jwks(*args, **kwargs):
            self.profile.policy_revision = 4
            return {'keys': [self.jwk]}
        self.fetch.side_effect = changed_during_jwks
        self.reject(self.helper.validate, self.token())

    def test_introspection_rejects_revision_change_during_claim_validation(self):
        settings = dict(mvp_enabled=True, metadata_mode='manual',
            discovery_unavailable_declared=True, discovery_unavailable_evidence_ref='evidence.discovery',
            verification_source='none', jwks_uri=False, local_key_ref=False, local_public_key=False,
            no_jwks_declaration=True, no_jwks_evidence_ref='evidence.keys',
            introspection_source='manual', introspection_endpoint='https://issuer.example/introspect',
            introspection_credential_ref='fixture.introspection.secret',
            introspection_auth_client_id='auth-client', introspection_auth_method='client_secret_basic',
            introspection_basic_contract_ref='accepted.contract.ref',
            introspection_credential_endpoint='https://issuer.example/introspect')
        for name, value in settings.items():
            setattr(self.profile, name, value)
        self.profile.token_profile = 'opaque'
        self.profile.policy_revision = 5
        self.env.parameters.get_param.return_value = 'synthetic-secret'
        self.fetch.return_value = dict(self.claims, active=True)
        original_claims = self.helper._claims

        def change_revision_after_claims(claims, profile, **kwargs):
            verified = original_claims(claims, profile, **kwargs)
            profile.policy_revision += 1
            return verified

        with patch.object(self.helper, '_claims', side_effect=change_revision_after_claims):
            self.reject(self.helper.introspect_token, 'opaque-token', iss=self.profile.issuer)

    def test_prohibited_jwt_introspection_paths_do_not_read_secret_or_post(self):
        settings = dict(mvp_enabled=True, metadata_mode='manual',
            discovery_unavailable_declared=True, discovery_unavailable_evidence_ref='evidence.discovery',
            verification_source='none', jwks_uri=False, local_key_ref=False, local_public_key=False,
            no_jwks_declaration=True, no_jwks_evidence_ref='evidence.keys',
            introspection_source='manual', introspection_endpoint='https://issuer.example/introspect',
            introspection_credential_ref='fixture.introspection.secret',
            introspection_auth_client_id='auth-client', introspection_auth_method='client_secret_basic',
            introspection_basic_contract_ref='accepted.contract.ref',
            introspection_credential_endpoint='https://issuer.example/introspect',
            allow_jwt_introspection=True)
        for name, value in settings.items():
            setattr(self.profile, name, value)
        self.profile.token_profile = 'jwt'
        cases = ('unknown', 'inactive', 'source', 'key', 'not-allowed', 'bad-signature',
                 'bad-header', 'bad-auth', 'bad-endpoint', 'missing-secret-ref',
                 'bad-prefilter', 'unsupported-alg')
        for case in cases:
            with self.subTest(case=case):
                for name, value in settings.items():
                    setattr(self.profile, name, value)
                self.profile.active = True
                self.profile.local_key_ref = False
                self.profile.verification_source = 'none'
                self.profile.allow_jwt_introspection = True
                token = self.token()
                if case == 'unknown':
                    token = self.token(dict(self.claims, iss='https://unknown.example'))
                elif case == 'inactive':
                    self.profile.active = False
                elif case == 'source':
                    self.profile.verification_source = 'jwks'
                elif case == 'key':
                    self.profile.local_key_ref = 'protected.local.key'
                elif case == 'not-allowed':
                    self.profile.allow_jwt_introspection = False
                elif case == 'bad-signature':
                    token = self.token(key=self.other_key)
                    self.profile.verification_source = 'jwks'
                    self.profile.jwks_uri = 'https://issuer.example/jwks'
                    self.fetch.return_value = {'keys': [self.jwk]}
                elif case == 'bad-header':
                    token = self.token(headers={'typ': 'JWT'})
                elif case == 'bad-auth':
                    self.profile.introspection_auth_method = 'client_secret_post'
                elif case == 'bad-endpoint':
                    self.profile.introspection_credential_endpoint = 'https://wrong.example/introspect'
                elif case == 'missing-secret-ref':
                    self.profile.introspection_credential_ref = False
                elif case == 'bad-prefilter':
                    invalid_claims = dict(self.claims)
                    del invalid_claims['aud']
                    token = self.token(invalid_claims)
                elif case == 'unsupported-alg':
                    token = jwt.encode(self.claims, 'synthetic-secret', algorithm='HS256',
                                       headers={'typ': 'at+jwt'})
                self.fetch.reset_mock()
                self.env.parameters.get_param.reset_mock()
                self.reject(self.helper.validate, token)
                self.env.parameters.get_param.assert_not_called()
                posts = [item for item in self.fetch.call_args_list if item[1].get('data') == {'token': token}]
                self.assertEqual(posts, [])

    def test_rfc8414_introspection_capability_is_rejected_before_fetch_or_secret(self):
        for name, value in dict(mvp_enabled=True, metadata_mode='rfc8414',
            discovery_unavailable_declared=True, discovery_unavailable_evidence_ref='evidence.discovery',
            verification_source='none', jwks_uri=False, local_key_ref=False, local_public_key=False,
            no_jwks_declaration=True, no_jwks_evidence_ref='evidence.keys',
            introspection_source='rfc8414', introspection_endpoint=False,
            introspection_credential_ref='fixture.introspection.secret',
            introspection_auth_client_id='auth-client', introspection_auth_method='client_secret_basic',
            introspection_basic_contract_ref='accepted.contract.ref',
            introspection_credential_endpoint='https://issuer.example/introspect').items():
            setattr(self.profile, name, value)
        self.profile.token_profile = 'opaque'
        self.fetch.return_value = {'issuer': self.profile.issuer,
            'introspection_endpoint': 'https://issuer.example/introspect'}
        self.reject(self.helper.get_oidc_config, self.profile.issuer)
        self.reject(self.helper.introspect_token, 'opaque-token', iss=self.profile.issuer)
        self.fetch.assert_not_called()
        self.env.parameters.get_param.assert_not_called()

    def test_generation_and_introspection_keep_distinct_credential_references(self):
        self.profile.mvp_enabled = False
        self.profile.metadata_mode = 'manual'
        self.profile.credential_ref = 'fixture.generation.secret'
        self.profile.introspection_credential_ref = 'fixture.introspection.secret'
        self.env.parameters.get_param.return_value = 'generation-secret'
        self.fetch.return_value = dict(access_token='generated-access')
        self.assertEqual(self.helper.encode(iss=self.profile.issuer,
            grant_type='client_credentials'), 'generated-access')
        self.fetch.assert_called_once_with(self.profile.token_endpoint,
            data={'grant_type': 'client_credentials'},
            headers={'Authorization': helper_module._introspection_basic_header(
                self.profile.client_id, 'generation-secret')})
        self.env.parameters.get_param.assert_called_once_with('fixture.generation.secret')

    def test_mvp_opaque_requires_explicit_absent_issuer_policy(self):
        for name, value in dict(mvp_enabled=True, metadata_mode='manual',
            discovery_unavailable_declared=True, discovery_unavailable_evidence_ref='evidence.discovery',
            verification_source='none', jwks_uri=False, local_key_ref=False, local_public_key=False,
            no_jwks_declaration=True, no_jwks_evidence_ref='evidence.keys',
            introspection_source='manual', introspection_endpoint='https://issuer.example/introspect',
            introspection_credential_ref='fixture.introspection.secret',
            introspection_auth_client_id='auth-client', introspection_auth_method='client_secret_basic',
            introspection_basic_contract_ref='accepted.contract.ref',
            introspection_credential_endpoint='https://issuer.example/introspect').items():
            setattr(self.profile, name, value)
        self.profile.token_profile = 'opaque'
        self.env.parameters.get_param.return_value = 'synthetic-secret'
        self.fetch.return_value = {'active': True, 'sub': 'subject'}
        self.reject(self.helper.introspect_token, 'opaque-token', iss=self.profile.issuer)
        self.fetch.assert_not_called()
        self.env.parameters.get_param.assert_not_called()

    def test_unsafe_introspection_endpoint_rejected_before_secret_lookup(self):
        for name, value in dict(mvp_enabled=True, metadata_mode='manual',
            discovery_unavailable_declared=True, discovery_unavailable_evidence_ref='evidence.discovery',
            verification_source='none', jwks_uri=False, local_key_ref=False, local_public_key=False,
            no_jwks_declaration=True, no_jwks_evidence_ref='evidence.keys',
            introspection_source='manual', introspection_endpoint='https://127.0.0.1/introspect',
            introspection_credential_ref='fixture.introspection.secret',
            introspection_auth_client_id='auth-client', introspection_auth_method='client_secret_basic',
            introspection_basic_contract_ref='evidence.basic',
            introspection_credential_endpoint='https://127.0.0.1/introspect').items():
            setattr(self.profile, name, value)
        self.profile.token_profile = 'opaque'
        with patch.object(helper_module.ResourceHelper, '_get_oidc_config', return_value=(
                {'introspection_endpoint': self.profile.introspection_endpoint}, None)):
            with patch.object(helper_module, 'preflight_endpoint', create=True,
                              side_effect=ValueError('unsafe synthetic endpoint')):
                with self.assertRaises(Unauthorized):
                    self.helper._mvp_introspect('opaque-token', self.profile)
        self.env.parameters.get_param.assert_not_called()
        self.fetch.assert_not_called()

    def test_mvp_introspection_uses_separate_credential_and_authoritative_claims(self):
        for name, value in dict(mvp_enabled=True, metadata_mode='manual',
            discovery_unavailable_declared=True, discovery_unavailable_evidence_ref='evidence.discovery',
            verification_source='none', jwks_uri=False, local_key_ref=False, local_public_key=False,
            no_jwks_declaration=True, no_jwks_evidence_ref='evidence.keys',
            introspection_source='manual', introspection_endpoint='https://issuer.example/introspect',
            introspection_credential_ref='fixture.introspection.secret',
            introspection_auth_client_id='auth-client', introspection_auth_method='client_secret_basic',
            introspection_basic_contract_ref='evidence.basic',
            introspection_credential_endpoint='https://issuer.example/introspect').items():
            setattr(self.profile, name, value)
        self.profile.token_profile = 'opaque'
        self.env.parameters.get_param.return_value = 'secret:/+ %'
        self.fetch.return_value = dict(iss=self.profile.issuer, active=True, sub='subject')
        self.reject(self.helper.introspect_token, 'opaque-token', iss=self.profile.issuer)
        self.fetch.assert_not_called()
        self.env.parameters.get_param.assert_not_called()


if __name__ == '__main__':
    unittest.main()
