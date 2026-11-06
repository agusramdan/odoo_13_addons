# -*- coding: utf-8 -*-
import unittest

try:
    from odoo.tests.common import TransactionCase
except ModuleNotFoundError:
    TransactionCase = unittest.TestCase
    _ODOO_TESTS_AVAILABLE = False
else:
    _ODOO_TESTS_AVAILABLE = True


@unittest.skipUnless(_ODOO_TESTS_AVAILABLE, 'requires Odoo runtime')


class TestOidcHelperDecode(TransactionCase):
    def test_provider_acquisition_methods_are_owned_by_oidc_helper(self):
        resource = self.env['amr.resource.helper']
        oidc = self.env['amr.oidc.helper']
        self.assertFalse(hasattr(resource, 'encode'))
        self.assertFalse(hasattr(resource, 'generate_token'))
        self.assertTrue(hasattr(oidc, 'encode'))
        self.assertTrue(hasattr(oidc, 'generate_token'))

    def test_decode_delegates_once_and_returns_verified_claims(self):
        helper = self.env['amr.oidc.helper']
        claims = {'sub': 'verified-subject'}
        authoritative = self.env['amr.resource.helper']
        calls = []
        original = type(authoritative).decode

        def counted(recordset, token, *args, **kwargs):
            calls.append(token)
            return claims

        type(authoritative).decode = counted
        try:
            result = helper.decode('sentinel-token')
        finally:
            type(authoritative).decode = original
        self.assertIs(result, claims)
        self.assertEqual(calls, ['sentinel-token'])

    def test_client_validate_token_accepts_profile_allowed_audience(self):
        """Empty-self validation accepts a locally trusted profile audience."""
        import time
        import jwt
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import rsa

        admin = self._trust_admin('oidc-audience-trust-admin')
        key, public = self._rsa_key()
        profile = self._profile(admin, 'empty', public, 'profile-resource-audience')
        self.env['oidc.client'].create({'name': 'Decoy relying party', 'client_id': 'different-decoy-id'})
        token = self._signed(profile.issuer, profile.client_id, 'profile-resource-audience', key)
        model = self.env['oidc.client']
        model_class = type(model)
        original_search = model_class.search
        searches = []

        def observed_search(recordset, domain, *args, **kwargs):
            result = original_search(recordset, domain, *args, **kwargs)
            searches.append((domain, result.ids))
            return result

        from unittest.mock import patch
        with patch.object(model_class, 'search', observed_search):
            verified = model.validate_token(token)
        self.assertEqual(searches, [([('client_id', '=', 'profile-resource-audience')], [])])
        self.assertEqual(verified['aud'], 'profile-resource-audience')

    def test_nonempty_client_accepts_profile_audience_not_client_id(self):
        admin = self._trust_admin('oidc-nonempty-trust-admin')
        key, public = self._rsa_key()
        profile = self._profile(admin, 'nonempty', public, 'profile-allowed-audience')
        client = self.env['oidc.client'].create({'name': 'Different relying party', 'client_id': 'other-client-id'})
        self.env['amr.public.key'].create({'name': 'Legacy test verifier', 'kid': 'test-key', 'public_key': public})
        token = self._signed(profile.issuer, profile.client_id, 'profile-allowed-audience', key)
        self.assertNotEqual(client.client_id, 'profile-allowed-audience')
        verified = client.validate_token(token)
        self.assertEqual(verified['aud'], 'profile-allowed-audience')

    def test_local_profile_loads_only_selected_key_on_valid_and_wrong_key_tokens(self):
        from unittest.mock import patch
        from werkzeug.exceptions import Unauthorized
        import odoo.addons.amr_resource.models.helper as helper_module

        admin = self._trust_admin('oidc-key-spy-admin')
        key_a, public_a = self._rsa_key()
        key_b, public_b = self._rsa_key()
        profile_a = self._profile(admin, 'keya', public_a, 'aud-a')
        profile_b = self._profile(admin, 'keyb', public_b, 'aud-b')
        self.env['amr.public.key'].create({'name': 'Global decoy verifier', 'kid': 'test-key', 'public_key': public_b})
        original_local = helper_module.ResourceHelper._local_public_key
        key_reads, selections, global_searches, fetches = [], [], [], []

        def local_spy(recordset, profile):
            key_reads.append(profile.issuer)
            return original_local(recordset, profile)

        registry_class = type(self.env['oidc.issuer.register'])
        original_profile_search = registry_class.search
        original_lookup = registry_class._lookup
        lookups = []

        def profile_search(recordset, domain, *args, **kwargs):
            result = original_profile_search(recordset, domain, *args, **kwargs)
            selections.append((domain, result.mapped('issuer')))
            return result

        def lookup(recordset, issuer, *args, **kwargs):
            result = original_lookup(recordset, issuer, *args, **kwargs)
            lookups.append((issuer, args[0] if args else kwargs.get('token_profile'), result.mapped('issuer')))
            return result

        key_class = type(self.env['amr.public.key'])
        original_global_search = key_class.search

        def global_search(recordset, domain, *args, **kwargs):
            global_searches.append(domain)
            return original_global_search(recordset, domain, *args, **kwargs)

        token_a = self._signed(profile_a.issuer, profile_a.client_id, 'aud-a', key_a)
        token_wrong_key = self._signed(profile_a.issuer, profile_a.client_id, 'aud-a', key_b)
        with patch.object(helper_module.ResourceHelper, '_local_public_key', local_spy), patch.object(registry_class, 'search', profile_search), patch.object(registry_class, '_lookup', lookup), patch.object(key_class, 'search', global_search), patch.object(helper_module, 'fetch_json', side_effect=lambda *a, **kw: fetches.append((a, kw))):
            verified = self.env['oidc.client'].validate_token(token_a)
            self.assertEqual(verified['iss'], profile_a.issuer)
            self.assertEqual(key_reads, [profile_a.issuer])
            self.assertEqual(selections, [([('issuer', '=', profile_a.issuer), ('active', '=', True)], [profile_a.issuer])])
            self.assertEqual(lookups, [(profile_a.issuer, 'jwt', [profile_a.issuer])])
            key_reads[:], selections[:], lookups[:], global_searches[:], fetches[:] = [], [], [], [], []
            with self.assertRaises(Unauthorized):
                self.env['oidc.client'].validate_token(token_wrong_key)
            self.assertEqual(key_reads, [profile_a.issuer])
            self.assertEqual(selections, [([('issuer', '=', profile_a.issuer), ('active', '=', True)], [profile_a.issuer])])
            self.assertEqual(lookups, [(profile_a.issuer, 'jwt', [profile_a.issuer])])
            self.assertEqual(global_searches, [])
            self.assertEqual(fetches, [])

    def test_selected_profile_rejects_audience_allowed_only_by_other_profile(self):
        from unittest.mock import patch
        from werkzeug.exceptions import Unauthorized
        import odoo.addons.amr_resource.models.helper as helper_module
        admin = self._trust_admin('oidc-audience-isolation-admin')
        key_a, public_a = self._rsa_key()
        key_b, public_b = self._rsa_key()
        profile_a = self._profile(admin, 'isola', public_a, 'aud-a')
        self._profile(admin, 'isolb', public_b, 'aud-b')
        token = self._signed(profile_a.issuer, profile_a.client_id, 'aud-b', key_a)
        registry_class = type(self.env['oidc.issuer.register'])
        original_lookup = registry_class._lookup
        lookups, key_reads, global_searches, fetches = [], [], [], []
        original_local = helper_module.ResourceHelper._local_public_key
        key_class = type(self.env['amr.public.key'])
        original_global_search = key_class.search

        def lookup(recordset, issuer, *args, **kwargs):
            result = original_lookup(recordset, issuer, *args, **kwargs)
            lookups.append((issuer, args[0] if args else kwargs.get('token_profile'), result.mapped('issuer')))
            return result

        def local_spy(recordset, profile):
            key_reads.append(profile.issuer)
            return original_local(recordset, profile)

        def global_search(recordset, domain, *args, **kwargs):
            global_searches.append(domain)
            return original_global_search(recordset, domain, *args, **kwargs)

        with patch.object(registry_class, '_lookup', lookup), patch.object(helper_module.ResourceHelper, '_local_public_key', local_spy), patch.object(key_class, 'search', global_search), patch.object(helper_module, 'fetch_json', side_effect=lambda *a, **kw: fetches.append((a, kw))):
            with self.assertRaises(Unauthorized):
                self.env['oidc.client'].validate_token(token)
        self.assertEqual(lookups, [(profile_a.issuer, 'jwt', [profile_a.issuer])])
        self.assertEqual(key_reads, [])
        self.assertEqual(global_searches, [])
        self.assertEqual(fetches, [])

    def test_inactive_profile_is_rejected(self):
        from werkzeug.exceptions import Unauthorized
        admin = self._trust_admin('oidc-inactive-admin')
        key, public = self._rsa_key()
        profile = self._profile(admin, 'inactive', public, 'aud-inactive')
        profile.with_user(admin).write({'active': False})
        token = self._signed(profile.issuer, profile.client_id, 'aud-inactive', key)
        with self.assertRaises(Unauthorized):
            self.env['oidc.client'].validate_token(token)

    def test_signed_unknown_missing_and_malformed_issuer_rejected(self):
        from werkzeug.exceptions import Unauthorized
        admin = self._trust_admin('oidc-issuer-cases-admin')
        key, public = self._rsa_key()
        profile = self._profile(admin, 'issuer', public, 'aud-issuer')
        for issuer in ('https://unknown.invalid', None, 42, [], ''):
            with self.subTest(issuer=issuer):
                token = self._signed(issuer, profile.client_id, 'aud-issuer', key)
                with self.assertRaises(Unauthorized):
                    self.env['oidc.client'].validate_token(token)

    def test_registry_rejects_opaque_profile_and_consumer_fails_closed(self):
        from unittest.mock import patch
        from odoo.exceptions import ValidationError
        from werkzeug.exceptions import Unauthorized
        import odoo.addons.amr_resource.models.helper as helper_module

        admin = self._trust_admin('oidc-opaque-admin')
        key, public = self._rsa_key()
        issuer = 'https://issuer-opaque.invalid'
        with self.assertRaises(ValidationError) as raised:
            self.env['oidc.issuer.register'].with_user(admin).create({
                'issuer': issuer, 'client_id': 'profile-client-opaque',
                'token_profile': 'opaque', 'metadata_mode': 'manual',
                'verification_source': 'local_public', 'introspection_source': 'none',
                'local_key_ref': 'amr_resource.keys.test_oidc_opaque', 'jwks_uri': False,
                'allow_missing_azp': True, 'token_endpoint': issuer + '/token',
                'resolver_mode': 'get_user_match',
                'audience_ids': [(0, 0, {'value': 'opaque-client'})],
            })
        self.assertEqual(raised.exception.args[0],
                         'Only manual JWT/JWKS or local-public profiles without introspection are supported.')
        token = self._signed(issuer, 'profile-client-opaque', 'opaque-client', key)
        with patch.object(helper_module, 'fetch_json', side_effect=AssertionError('network call')) as fetch:
            with self.assertRaises(Unauthorized):
                self.env['oidc.client'].validate_token(token)
            fetch.assert_not_called()

    def test_duplicate_issuer_is_rejected_by_registry_uniqueness(self):
        from psycopg2 import IntegrityError
        admin = self._trust_admin('oidc-duplicate-admin')
        key, public = self._rsa_key()
        first = self._profile(admin, 'dup1', public, 'aud-dup')
        with self.assertRaises(IntegrityError):
            with self.env.cr.savepoint():
                self.env['oidc.issuer.register'].with_user(admin).create({
                    'issuer': first.issuer, 'client_id': 'profile-client-dup2',
                    'token_profile': 'jwt', 'metadata_mode': 'manual', 'verification_source': 'local_public',
                    'introspection_source': 'none', 'local_key_ref': 'amr_resource.keys.test_oidc_dup2',
                    'jwks_uri': False, 'allow_missing_azp': True,
                    'token_endpoint': first.token_endpoint, 'resolver_mode': 'get_user_match',
                    'audience_ids': [(0, 0, {'value': 'aud-dup'})],
                })

    def _trust_admin(self, login):
        return self.env['res.users'].create({
            'name': 'Synthetic trust administrator', 'login': login,
            'company_id': self.env.company.id,
            'company_ids': [(6, 0, self.env.company.ids)],
            'groups_id': [(6, 0, [self.env.ref(x).id for x in (
                'base.group_user', 'base.group_system',
                'amr_resource.group_oidc_trust_admin', 'amr_resource.group_oidc_code_admin')])],
        })

    def _rsa_key(self):
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048, backend=default_backend())
        public = key.public_key().public_bytes(
            serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo).decode('ascii')
        return key, public

    def _profile(self, admin, suffix, public, audience):
        params = self.env['ir.config_parameter'].sudo()
        key_ref = 'amr_resource.keys.test_oidc_' + suffix
        params.set_param(key_ref, public)
        return self.env['oidc.issuer.register'].with_user(admin).create({
            'issuer': 'https://issuer-' + suffix + '.invalid', 'client_id': 'profile-client-' + suffix,
            'token_profile': 'jwt', 'metadata_mode': 'manual', 'verification_source': 'local_public',
            'introspection_source': 'none', 'local_key_ref': key_ref, 'jwks_uri': False,
            'allow_missing_azp': True, 'token_endpoint': 'https://issuer-' + suffix + '.invalid/token',
            'resolver_mode': 'get_user_match', 'audience_ids': [(0, 0, {'value': audience})],
        })

    def _signed(self, issuer, client_id, audience, key):
        import time
        import jwt
        claims = {'sub': 'subject', 'client_id': client_id, 'aud': audience,
                  'exp': int(time.time()) + 300, 'iat': int(time.time()) - 1, 'jti': 'test-' + str(audience)}
        if issuer is not None:
            claims['iss'] = issuer
        return jwt.encode(claims, key, algorithm='RS256', headers={'typ': 'at+jwt', 'kid': 'test-key'})

    def test_client_validate_token_uses_oidc_helper(self):
        helper_class = type(self.env['amr.oidc.helper'])
        original_decode = helper_class.decode
        original_validate = helper_class.validate
        claims = {'sub': 'verified-subject'}
        decode_calls = []
        jwt_calls = []
        validate_calls = []

        def decode(recordset, token, *args, **kwargs):
            decode_calls.append((token, args, kwargs))
            return claims

        def validate(recordset, token, *args, **kwargs):
            validate_calls.append((token, args, kwargs))
            return claims

        import odoo.addons.amr_oidc.models.oidc_client as oidc_client_module
        jwt_decode = oidc_client_module.jwt.decode

        def legacy_decode(token, **kwargs):
            jwt_calls.append((token, kwargs))
            return {'aud': 'unregistered-legacy-audience'}

        helper_class.decode = decode
        helper_class.validate = validate
        oidc_client_module.jwt.decode = legacy_decode
        try:
            result = self.env['oidc.client'].validate_token('sentinel-token')
        finally:
            helper_class.decode = original_decode
            helper_class.validate = original_validate
            oidc_client_module.jwt.decode = jwt_decode
        self.assertIs(result, claims)
        self.assertEqual(jwt_calls, [('sentinel-token', {
            'options': {
                'verify_signature': False, 'verify_exp': True,
                'verify_aud': False, 'verify_iss': False,
            },
        })])
        self.assertEqual(decode_calls, [('sentinel-token', (), {})])
        self.assertEqual(validate_calls, [])

    def test_service_account_export_uses_oidc_helper(self):
        client = self.env['oidc.client'].create({'name': 'test', 'client_id': 'audience'})
        helper_class = type(self.env['amr.oidc.helper'])
        original_key = helper_class.generate_key
        original_defaults = helper_class._service_account_endpoint_defaults
        calls = []

        def generate_key(recordset, algorithm):
            calls.append(('key', algorithm))
            return {'kid': 'kid', 'private_key': 'private', 'public_key': 'public', 'algorithm': algorithm}

        def defaults(recordset):
            calls.append(('defaults',))
            return {'issuer': 'issuer', 'authorization_endpoint': 'authorize', 'token_endpoint': 'token'}

        helper_class.generate_key = generate_key
        helper_class._service_account_endpoint_defaults = defaults
        try:
            exported = client.export_service_account('RS256')
        finally:
            helper_class.generate_key = original_key
            helper_class._service_account_endpoint_defaults = original_defaults
        self.assertEqual(exported['private_key_id'], 'kid')
        self.assertEqual(calls, [('key', 'RS256'), ('defaults',)])
