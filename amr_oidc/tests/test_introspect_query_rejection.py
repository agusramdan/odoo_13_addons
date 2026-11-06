# -*- coding: utf-8 -*-
import unittest
from unittest.mock import patch

try:
    import odoo
except ModuleNotFoundError as error:
    if error.name != "odoo":
        raise
    raise unittest.SkipTest("requires Odoo runtime")

from odoo.tests.common import HttpCase

import odoo.addons.amr_oidc.controllers.main as oidc_controller


class TestIntrospectQueryRejection(HttpCase):
    def test_route_contract_preserves_get_and_post(self):
        routing = oidc_controller.ControllerOIDC.api_oidc_introspect.routing
        self.assertEqual(routing['routes'], ['/oidc/introspect'])
        self.assertEqual(routing['type'], 'http')
        self.assertEqual(routing['auth'], 'none')
        self.assertEqual(routing['methods'], ['GET', 'POST'])
        self.assertFalse(routing['csrf'])

    def test_get_query_token_is_rejected_before_helper(self):
        helper_model = type(self.env['amr.oidc.helper'])
        claims = {'active': True}
        with patch.object(helper_model, 'validate', return_value=claims) as helper:
            response = self.url_open('/oidc/introspect?token=query-secret')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json().get('error'), 'invalid_request')
        self.assertNotIn('query-secret', response.text)
        helper.assert_not_called()

    def test_post_query_token_is_rejected_before_helper(self):
        helper_model = type(self.env['amr.oidc.helper'])
        claims = {'active': True}
        with patch.object(helper_model, 'validate', return_value=claims) as helper:
            response = self.url_open('/oidc/introspect?access_token=query-secret', data={'token': 'body-token'}, headers={'Content-Type': 'application/x-www-form-urlencoded'})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json().get('error'), 'invalid_request')
        self.assertNotIn('query-secret', response.text)
        helper.assert_not_called()

    def test_post_form_token_validates_and_returns_validated_client_id(self):
        import base64
        client_id = 'introspect-test-client'
        secret = 'synthetic-introspect-secret'
        client = self.env['oidc.client'].create({
            'client_id': client_id, 'allow_introspection': True,
        })
        verifier = self.env['res.users']._crypt_context().hash(secret)
        client.sudo().write({'client_secret_hash': verifier})
        auth = base64.b64encode((client_id + ':' + secret).encode()).decode()
        helper_model = type(self.env['amr.oidc.helper'])
        claims = {'client_id': 'token-owner', 'sub': 'subject', 'aud': client_id}
        with patch.object(helper_model, 'validate', return_value=claims) as helper:
            response = self.url_open(
                '/oidc/introspect', data={'token': 'body-token'},
                headers={
                    'Authorization': 'Basic ' + auth,
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            'active': True, 'client_id': 'token-owner', 'sub': 'subject', 'aud': client_id,
        })
        helper.assert_called_once_with('body-token', audience=client_id)
