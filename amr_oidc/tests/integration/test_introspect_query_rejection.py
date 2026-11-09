# -*- coding: utf-8 -*-
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
