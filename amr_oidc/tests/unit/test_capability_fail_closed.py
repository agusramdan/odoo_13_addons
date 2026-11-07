"""Fail-closed OIDC metadata and authorization contract using isolated doubles."""
import json
import unittest
from types import SimpleNamespace
from unittest import mock

import importlib.util
from pathlib import Path

ADDON_ROOT = Path(__file__).resolve().parents[2]
_SUPPORT_SPEC = importlib.util.spec_from_file_location(
    "oidc_test_support", str(ADDON_ROOT / "tests" / "support.py")
)
support = importlib.util.module_from_spec(_SUPPORT_SPEC)
_SUPPORT_SPEC.loader.exec_module(support)
load, load_controller = support.load, support.load_controller


class _Environment(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = SimpleNamespace(_is_public=mock.Mock(return_value=True))


class TestFailClosedOidcSurface(unittest.TestCase):
    def test_service_account_export_keeps_its_internal_endpoint_consumer(self):
        module = load("models/oidc_client.py")
        helper = mock.Mock(spec=["_generate_key", "_service_account_endpoint_defaults"])
        helper._generate_key.return_value = {
            "kid": "synthetic-kid",
            "private_key": "synthetic-private-key",
            "public_key": "synthetic-public-key",
            "algorithm": "RS256",
        }
        helper._service_account_endpoint_defaults.return_value = {
            "issuer": "https://issuer.example.invalid",
            "authorization_endpoint": "https://issuer.example.invalid/oidc/authorize",
            "token_endpoint": "https://issuer.example.invalid/oidc/token",
        }
        client = SimpleNamespace(
            ensure_one=mock.Mock(),
            env={"amr.oidc.helper": helper},
            client_id="synthetic-client",
            client_email="synthetic@example.invalid",
        )

        exported = module.OidcClient.export_service_account(client, "RS256")

        self.assertEqual(exported["auth_uri"], "https://issuer.example.invalid/oidc/authorize")
        self.assertEqual(exported["token_uri"], "https://issuer.example.invalid/oidc/token")
        self.assertEqual(exported["issuer"], "https://issuer.example.invalid")
        helper._service_account_endpoint_defaults.assert_called_once_with()

    def test_oidc_discovery_route_is_owned_by_child_and_returns_404(self):
        module = load_controller()
        route = module.ControllerOIDC.__dict__.get("well_known_openid_configuration")
        self.assertIsNotNone(route)
        self.assertEqual(route._route_paths, "/.well-known/openid-configuration")
        self.assertEqual(route._route_options["methods"], ["GET"])
        self.assertEqual(route._route_options["auth"], "public")
        self.assertFalse(route._route_options["csrf"])
        declared_paths = []
        for method in module.ControllerOIDC.__dict__.values():
            paths = getattr(method, "_route_paths", [])
            declared_paths.extend(paths if isinstance(paths, (list, tuple)) else [paths])
        self.assertNotIn("/.well-known/oauth-authorization-server", declared_paths)

        response = module.ControllerOIDC().well_known_openid_configuration()
        self.assertEqual(response.status_code, 404)

    def test_authorization_and_token_response_types_are_rejected_before_side_effects(self):
        module = load_controller()
        controller = module.ControllerOIDC()
        client = mock.Mock()
        client.sudo.return_value = client
        client.search.return_value = client
        client.name = "synthetic-client"
        client.redirect_uri = "https://client.example.invalid/callback"
        client.validate_redirect_uri.return_value = True
        client.create_authorization_code.return_value = SimpleNamespace(
            code="synthetic-code", redirect_uri=client.redirect_uri
        )
        client.create_access_token.return_value = SimpleNamespace(
            token="synthetic-token", redirect_uri=client.redirect_uri,
            get_expires_in=mock.Mock(return_value=60),
        )
        module.request.env = _Environment({"oidc.client": client})

        response = controller.authorize(client_id="synthetic-client", response_type="code")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response.data)["error"], "unsupported_response_type")

        for method_name in ("authorize_continue", "login_submit"):
            with self.subTest(method=method_name):
                response = getattr(controller, method_name)()
                self.assertEqual(response.status_code, 400)
                self.assertEqual(json.loads(response.data)["error"], "unsupported_response_type")

        for response_type in ("code", "token"):
            with self.subTest(response_type=response_type):
                response = controller.oidc_authorize(
                    client_id="synthetic-client",
                    redirect_uri=client.redirect_uri,
                    response_type=response_type,
                )
                self.assertEqual(response.status_code, 400)
                self.assertEqual(json.loads(response.data)["error"], "unsupported_response_type")

        client.create_authorization_code.assert_not_called()
        client.create_access_token.assert_not_called()


if __name__ == "__main__":
    unittest.main()
