"""Configuration, request-token helpers, and OIDC discovery source contract."""
import base64
import unittest
from types import SimpleNamespace
from unittest import mock

if __package__:
    from .support import load_helper_module
else:
    from support import load_helper_module


class _ConfigParameters:
    def __init__(self, values=None):
        self.values = values or {}

    def sudo(self):
        return self

    def get_param(self, key, default=None):
        return self.values.get(key, default)


class TestHelperConfigurationAndDiscovery(unittest.TestCase):
    def setUp(self):
        self.module = load_helper_module()
        self.parameters = _ConfigParameters({
            "amr_token.signature_type": "public_key",
            "amr_token.public_key_algorithm": "ES256",
            "amr_token.expires_in": "90",
            "amr_token.retention_in": "45",
            "amr_token.secret": "SYNTHETIC-NOT-A-REAL-SECRET",
        })
        self.resource = mock.Mock()
        self.resource.get_issuer.return_value = "https://issuer.example.invalid"
        self.resource.get_audience.return_value = "synthetic-client"
        self.resource.get_header_token.return_value = "synthetic-header-token"
        self.resource.get_bearer_token.return_value = "synthetic-bearer-token"
        self.keys = mock.Mock()
        self.keys.sudo.return_value = self.keys
        self.keys.get_jwks.return_value = [{"kid": "synthetic-kid"}]
        self.helper = object.__new__(self.module.TokenHelper)
        self.helper.env = {
            "ir.config_parameter": self.parameters,
            "amr.resource.helper": self.resource,
            "amr.public.key": self.keys,
        }

    def _require(self, method):
        self.assertTrue(callable(getattr(self.module.TokenHelper, method, None)), f"candidate {method} method is missing")

    def test_resource_header_and_bearer_token_delegation(self):
        self._require("get_header_token")
        self._require("get_bearer_token")
        self.assertEqual(self.module.TokenHelper.get_header_token(self.helper), "synthetic-header-token")
        self.assertEqual(self.module.TokenHelper.get_bearer_token(self.helper), "synthetic-bearer-token")
        self.resource.get_header_token.assert_called_once_with()
        self.resource.get_bearer_token.assert_called_once_with()

    def test_basic_auth_parses_only_basic_scheme_and_preserves_password_colons(self):
        self._require("get_basic_auth")
        encoded = base64.b64encode(b"synthetic-user:pass:with:colon").decode("ascii")
        self.module.request.httprequest.headers = {"Authorization": f"Basic {encoded}"}
        self.assertEqual(self.module.TokenHelper.get_basic_auth(self.helper), ["synthetic-user", "pass:with:colon"])

        self.module.request.httprequest.headers = {"Authorization": "Bearer synthetic-token"}
        self.assertEqual(self.module.TokenHelper.get_basic_auth(self.helper), (None, None))

    def test_signature_settings_and_defaults(self):
        self._require("get_signature_type")
        self._require("get_signature_algorithm")
        self.assertEqual(self.module.TokenHelper.get_signature_type(self.helper), "public_key")
        self.assertEqual(self.module.TokenHelper.get_signature_algorithm(self.helper), "ES256")

        self.parameters.values = {"amr_token.signature_type": "secret"}
        self.assertEqual(self.module.TokenHelper.get_signature_algorithm(self.helper), "HS256")
        self.assertEqual(self.module.TokenHelper.get_signature_type(self.helper), "secret")

    def test_expiry_retention_secret_issuer_and_audience_helpers(self):
        for method in ("get_expires_in", "get_retention_in", "get_secret", "get_issuer", "get_audience"):
            self._require(method)
        self.assertEqual(self.module.TokenHelper.get_expires_in(self.helper), 90)
        self.assertEqual(self.module.TokenHelper.get_retention_in(self.helper), 45)
        self.assertEqual(self.module.TokenHelper.get_secret(self.helper), "SYNTHETIC-NOT-A-REAL-SECRET")
        self.assertEqual(self.module.TokenHelper.get_issuer(self.helper), "https://issuer.example.invalid")
        self.assertEqual(self.module.TokenHelper.get_audience(self.helper), "synthetic-client")

        self.parameters.values = {}
        self.assertEqual(self.module.TokenHelper.get_expires_in(self.helper), 86400)
        self.assertEqual(self.module.TokenHelper.get_retention_in(self.helper), 14400)

    def test_incomplete_oidc_discovery_helper_is_not_available(self):
        self._require("get_token_endpoint")
        self.assertFalse(callable(getattr(self.module.TokenHelper, "openid_configuration", None)))
        self.assertEqual(
            self.module.TokenHelper.get_token_endpoint(self.helper),
            "https://issuer.example.invalid/oidc/token",
        )
        self.assertEqual(
            self.module.TokenHelper._service_account_endpoint_defaults(self.helper),
            {
                "issuer": "https://issuer.example.invalid",
                "authorization_endpoint": "https://issuer.example.invalid/oidc/authorize",
                "token_endpoint": "https://issuer.example.invalid/oidc/token",
            },
        )

    def test_jwks_wrapper_uses_sudo_public_key_model(self):
        self._require("oidc_jwks")
        self.assertEqual(self.module.TokenHelper.oidc_jwks(self.helper), {"keys": [{"kid": "synthetic-kid"}]})
        self.keys.sudo.assert_called_once_with()
        self.keys.get_jwks.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
