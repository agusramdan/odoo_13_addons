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

    def test_client_validate_token_uses_oidc_helper(self):
        client = self.env['oidc.client'].create({'name': 'test', 'client_id': 'audience'})
        helper_class = type(self.env['amr.oidc.helper'])
        original = helper_class.validate
        claims = {'sub': 'verified-subject'}
        calls = []

        def validate(recordset, token, audience=None):
            calls.append((token, audience))
            return claims

        helper_class.validate = validate
        try:
            result = client.validate_token('sentinel-token')
        finally:
            helper_class.validate = original
        self.assertIs(result, claims)
        self.assertEqual(calls, [('sentinel-token', 'audience')])

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
