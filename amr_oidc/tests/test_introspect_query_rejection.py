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
        helper_model = type(self.env['amr.token.helper'])
        sentinel = {'active': True, 'sentinel': 'legacy-handler-was-called'}
        with patch.object(helper_model, 'oidc_introspect', return_value=sentinel) as helper:
            response = self.url_open('/oidc/introspect?token=query-secret')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json().get('error'), 'invalid_request')
        self.assertNotIn('query-secret', response.text)
        helper.assert_not_called()

    def test_post_query_token_is_rejected_before_helper(self):
        helper_model = type(self.env['amr.token.helper'])
        sentinel = {'active': True, 'sentinel': 'legacy-handler-was-called'}
        with patch.object(helper_model, 'oidc_introspect', return_value=sentinel) as helper:
            response = self.url_open('/oidc/introspect?access_token=query-secret', data={'token': 'body-token'}, headers={'Content-Type': 'application/x-www-form-urlencoded'})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json().get('error'), 'invalid_request')
        self.assertNotIn('query-secret', response.text)
        helper.assert_not_called()

    def test_post_body_token_keeps_legacy_dispatch(self):
        helper_model = type(self.env['amr.token.helper'])
        sentinel = {'active': True, 'sentinel': 'legacy-handler-was-called'}
        with patch.object(helper_model, 'oidc_introspect', return_value=sentinel) as helper:
            response = self.url_open('/oidc/introspect', data={'token': 'body-token'}, headers={'Content-Type': 'application/x-www-form-urlencoded'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), sentinel)
        helper.assert_called_once_with(token='body-token')
