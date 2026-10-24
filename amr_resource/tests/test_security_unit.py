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
from unittest.mock import Mock, patch

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
            introspection_endpoint='https://issuer.example/introspect', credential_ref=False,
            client_id='synthetic-client', azp='synthetic-client', allow_missing_azp=False,
            audience_ids=Rows([SimpleNamespace(value='first'), SimpleNamespace(value='second')]),
            binding_ids=Rows([SimpleNamespace(sub='subject', user_id=self.user)]),
            resolver_mode='get_user_match', resolver_key='get_user_match', fixed_user_id=self.user,
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

    def token(self, claims=None, headers=None, key=None):
        return jwt.encode(self.claims if claims is None else claims, key or self.key,
                          algorithm='RS256', headers=dict({'typ': 'at+jwt', 'kid': 'synthetic-key'}, **(headers or {})))

    def reject(self, call, *args, **kwargs):
        with self.assertRaises(Unauthorized) as result:
            call(*args, **kwargs)
        self.assertEqual(result.exception.code, 401)
        self.assertIsNone(result.exception.__context__)

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

    def test_get_oidc_config_resolves_discovery_or_declared_no_jwks(self):
        self.profile.mvp_enabled = True
        self.profile.metadata_mode = 'oidc_discovery'
        self.profile.token_profile = 'jwt'
        metadata = {'issuer': self.profile.issuer,
                    'authorization_endpoint': 'https://id.invalid/authorize',
                    'jwks_uri': 'https://id.invalid/jwks',
                    'response_types_supported': ['code'],
                    'subject_types_supported': ['public'],
                    'id_token_signing_alg_values_supported': ['RS256'],
                    'token_endpoint': 'https://id.invalid/token'}
        self.fetch.return_value = metadata
        result = self.helper.get_oidc_config(self.profile.issuer)
        self.assertEqual(result['jwks_uri'], metadata['jwks_uri'])
        self.fetch.assert_called_once_with(helper_module._oidc_discovery_url(self.profile.issuer))
        self.fetch.reset_mock()
        self.fetch.side_effect = [metadata, {'keys': [self.jwk]}]
        self.assertEqual(self.helper.get_jwks_data(self.profile.issuer), {'keys': [self.jwk]})
        self.assertEqual(self.fetch.call_args_list[0][0],
                         (helper_module._oidc_discovery_url(self.profile.issuer),))
        self.assertEqual(self.fetch.call_args_list[1][0], ('https://id.invalid/jwks',))
        self.fetch.side_effect = None
        self.fetch.reset_mock()
        self.profile.metadata_mode = 'manual'
        self.profile.discovery_unavailable_declared = False
        with self.assertRaises(Unauthorized):
            self.helper.get_oidc_config(self.profile.issuer)
        self.fetch.assert_not_called()

        self.profile.discovery_unavailable_declared = True
        self.profile.discovery_unavailable_evidence_ref = 'evidence.discovery.1'
        self.profile.verification_source = 'none'
        self.profile.jwks_uri = False
        self.profile.no_jwks_declaration = True
        self.profile.no_jwks_evidence_ref = 'evidence.jwks.absent'
        self.profile.introspection_source = 'rfc8414'
        self.profile.introspection_endpoint = False
        rfc = {'issuer': self.profile.issuer, 'response_types_supported': ['code'],
               'authorization_endpoint': 'https://id.invalid/authorize',
               'token_endpoint': 'https://id.invalid/token',
               'introspection_endpoint': 'https://id.invalid/introspect'}
        self.fetch.return_value = rfc
        result = self.helper.get_oidc_config(self.profile.issuer)
        self.assertIsNone(result['jwks_uri'])
        self.assertEqual(result['introspection_endpoint'], rfc['introspection_endpoint'])
        self.fetch.assert_called_once_with(helper_module._rfc8414_metadata_url(self.profile.issuer))
        self.env.parameters.get_param.assert_not_called()

    def test_uat06_local_key_no_loopback_or_local_bypass(self):
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
        payload = self.helper.validate('synthetic-opaque')
        self.assertEqual(payload['iss'], self.profile.issuer)
        self.assertEqual(self.helper.get_uid(payload), self.user.id)
        self.fetch.assert_called_once_with(self.profile.introspection_endpoint,
                                          data={'token': 'synthetic-opaque'}, headers={})
        self.helper.validate('synthetic-opaque')
        self.assertEqual(self.fetch.call_count, 2)

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
        good = self.opaque()
        good.update(exp=int(time.time()) + 30, iat=int(time.time()), nbf=int(time.time()),
                    extra_uid=1, company_id=999, roles=['admin'])
        good.pop('azp')
        self.profile.allow_missing_azp = True
        self.fetch.return_value = good
        payload = self.helper.validate('synthetic-opaque')
        self.assertEqual(payload['iss'], self.profile.issuer)
        self.assertNotIn('typ', payload)
        self.assertNotIn('jti', payload)
        for name, value in (('exp', int(time.time())), ('iat', int(time.time()) + 1),
                            ('nbf', int(time.time()) + 1), ('iat', True), ('exp', '123')):
            self.fetch.return_value = dict(good, **{name: value})
            self.reject(self.helper.validate, 'synthetic-opaque')

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

    def test_mapping_resolver_requires_unique_candidate_and_matching_existing_binding(self):
        self.profile.resolver_mode = 'mapping'
        self.profile.mvp_enabled = True
        self.profile.metadata_mode = 'manual'
        self.profile.discovery_unavailable_declared = True
        self.profile.discovery_unavailable_evidence_ref = 'synthetic.discovery.evidence'
        self.profile.verification_source = 'jwks'
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
        self.helper._find_mapping_users.assert_called_with('login', 'synthetic-user')
        self.assertEqual(self.helper._find_mapping_users.call_count, 2)

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


if __name__ == '__main__':
    unittest.main()
