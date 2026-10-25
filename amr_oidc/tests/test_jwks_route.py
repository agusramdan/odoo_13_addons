# -*- coding: utf-8 -*-
import unittest
import json
from unittest.mock import Mock, patch

try:
    import odoo
except ModuleNotFoundError as error:
    if error.name != "odoo":
        raise
    raise unittest.SkipTest("requires Odoo runtime")

from odoo.tests.common import HttpCase, TransactionCase

import odoo.addons.amr_oidc.controllers.main as oidc_controller
import odoo.addons.amr_token.controllers.main as token_controller


class TestJwksRouteOwnership(TransactionCase):
    def test_jwks_route_uses_oidc_helper_and_preserves_public_route(self):
        keys = [{"kid": "oidc-key", "kty": "RSA", "use": "sig"}]
        oidc_helper = Mock()
        oidc_helper.oidc_jwks.return_value = {"keys": keys}
        legacy_helper = Mock()
        legacy_helper.oidc_jwks.return_value = {"keys": []}
        request_stub = Mock()
        request_stub.env = {
            "amr.oidc.helper": oidc_helper,
            "amr.token.helper": legacy_helper,
        }
        controller = oidc_controller.ControllerOIDC()

        with patch.object(oidc_controller, "request", request_stub), \
                patch.object(token_controller, "request", request_stub):
            response = controller.well_known_jwks.__wrapped__(controller)

        oidc_helper.oidc_jwks.assert_called_once_with()
        legacy_helper.oidc_jwks.assert_not_called()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, "application/json; charset=utf-8")
        self.assertEqual(json.loads(response.data), {"keys": keys})
        method = oidc_controller.ControllerOIDC.well_known_jwks
        self.assertEqual(method.routing['routes'], ['/.well-known/jwks.json'])
        self.assertEqual(method.routing['type'], 'http')
        self.assertEqual(method.routing['auth'], 'public')
        self.assertEqual(method.routing['methods'], ['GET'])
        self.assertFalse(method.routing['csrf'])


class TestJwksHttpRoute(HttpCase):
    def test_live_jwks_route_dispatches_to_oidc_helper(self):
        oidc_model = type(self.env['amr.oidc.helper'])
        legacy_model = type(self.env['amr.token.helper'])

        oidc_payload = {'keys': [{'kid': 'oidc-route-test', 'kty': 'RSA', 'use': 'sig'}]}
        with patch.object(oidc_model, 'oidc_jwks', return_value=oidc_payload), \
                patch.object(legacy_model, 'oidc_jwks', return_value={'keys': []}):
            response = self.url_open('/.well-known/jwks.json')

        self.assertEqual(response.status_code, 200)
        self.assertIn('application/json', response.headers.get('Content-Type', ''))
        self.assertEqual(response.json(), oidc_payload)
