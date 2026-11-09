# -*- coding: utf-8 -*-
import base64
import unittest
from unittest.mock import patch

import jwt
import time

try:
    import odoo
except ModuleNotFoundError as error:
    if error.name != "odoo":
        raise
    raise unittest.SkipTest("requires Odoo runtime")

from odoo.tests.common import HttpCase

import odoo.addons.amr_oidc.controllers.main as oidc_controller


class TestIntrospectHttpSecurity(HttpCase):
    def test_route_contract_preserves_get_and_post(self):
        routing = oidc_controller.ControllerOIDC.api_oidc_introspect.routing
        self.assertEqual(routing['routes'], ['/oidc/introspect'])
        self.assertEqual(routing['type'], 'http')
        self.assertEqual(routing['auth'], 'none')
        self.assertEqual(routing['methods'], ['GET', 'POST'])
        self.assertFalse(routing['csrf'])

    def test_cleartext_post_is_rejected_before_client_authentication(self):
        # This HttpCase request is cleartext: only the TLS guard is asserted.
        # Secure handler logic has offline unit coverage; HTTPS transport remains unverified.
        helper_model = type(self.env['amr.oidc.helper'])
        with patch.object(helper_model, 'get_basic_auth') as auth, \
                patch.object(helper_model, 'validate') as helper:
            response = self.url_open(
                '/oidc/introspect', data={'token': '[REDACTED]'},
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
            )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json().get('error'), 'invalid_request')
        auth.assert_not_called()
        helper.assert_not_called()

    def test_post_introspection_returns_allowlisted_signed_token_claims(self):
        issuer = 'https://oidc-introspection.invalid'
        signing_secret = 'synthetic-introspection-signing-secret'
        client_id = 'synthetic-introspection-client'
        client_secret = 'synthetic-introspection-credential'
        internal_claim = 'synthetic-internal-claim-marker'
        now = int(time.time())
        self.env['ir.config_parameter'].sudo().set_param(
            'amr_token.signature_type', 'secret')
        self.env['ir.config_parameter'].sudo().set_param(
            'amr_token.secret_algorithm', 'HS256')
        self.env['ir.config_parameter'].sudo().set_param(
            'amr_token.secret', signing_secret)
        self.env['ir.config_parameter'].sudo().set_param(
            'web.base.url', issuer)
        self.env['oidc.client'].sudo().create({
            'name': 'Synthetic introspection client',
            'client_id': client_id,
            'active': True,
            'allow_introspection': True,
            'client_secret_hash': self.env['res.users']._crypt_context().hash(
                client_secret),
        })
        token = jwt.encode({
            'iss': issuer,
            'exp': now + 300,
            'aud': client_id,
            'sub': 'synthetic-introspection-subject',
            'iat': now,
            'synthetic_internal_claim': internal_claim,
        }, signing_secret, algorithm='HS256')
        if not isinstance(token, str):
            token = token.decode('ascii')
        basic = 'Basic ' + base64.b64encode(
            (client_id + ':' + client_secret).encode('utf-8')
        ).decode('ascii')

        response = self.url_open(
            '/oidc/introspect',
            data={'token': token},
            headers={
                'Authorization': basic,
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-Forwarded-Proto': 'https',
                'X-Forwarded-Host': 'oidc-introspection.invalid',
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(
            payload.get('active'),
            'active=%r response_keys=%r' % (payload.get('active'), sorted(payload)),
        )
        self.assertEqual(set(payload), {'active', 'sub', 'aud', 'iss', 'exp', 'iat'})
        self.assertEqual(payload['sub'], 'synthetic-introspection-subject')
        self.assertEqual(payload['aud'], client_id)
        self.assertEqual(payload['iss'], issuer)
        self.assertEqual(payload['exp'], now + 300)
        self.assertEqual(payload['iat'], now)
        self.assertNotIn('synthetic_internal_claim', payload)
        self.assertNotIn(internal_claim, response.text)
        self.assertNotIn(client_secret, response.text)

    def test_profile_returns_sub_for_real_signed_bearer_token(self):
        issuer = 'https://oidc-profile.invalid'
        audience = 'synthetic-profile-audience'
        secret = 'synthetic-profile-signing-secret'
        self.env['ir.config_parameter'].sudo().set_param(
            'amr_token.signature_type', 'secret')
        self.env['ir.config_parameter'].sudo().set_param(
            'amr_token.secret_algorithm', 'HS256')
        self.env['ir.config_parameter'].sudo().set_param(
            'amr_token.secret', secret)
        self.env['ir.config_parameter'].sudo().set_param(
            'web.base.url', issuer)
        self.env['ir.config_parameter'].sudo().set_param(
            'database.uuid', audience)
        token = jwt.encode({
            'sub': 'synthetic-profile-subject',
            'iss': issuer,
            'aud': audience,
            'iat': int(time.time()),
            'exp': int(time.time()) + 300,
        }, secret, algorithm='HS256')

        response = self.url_open(
            '/oidc/profile',
            headers={'Authorization': 'Bearer ' + token},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'sub': 'synthetic-profile-subject'})
