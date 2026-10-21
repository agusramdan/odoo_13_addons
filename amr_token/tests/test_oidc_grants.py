"""P-05/OIDC grant routing and claim construction contract."""
import unittest
from types import SimpleNamespace
from unittest import mock

if __package__:
    from .support import load_helper_module
else:
    from support import load_helper_module


class _Environment(dict):
    def __init__(self, *args, dbname="synthetic-db", **kwargs):
        super().__init__(*args, **kwargs)
        self.cr = SimpleNamespace(dbname=dbname)


class TestOidcGrantFlows(unittest.TestCase):
    def setUp(self):
        self.module = load_helper_module()
        self.helper = object.__new__(self.module.TokenHelper)
        self.helper.env = _Environment()

    def _require(self, method):
        self.assertTrue(callable(getattr(self.module.TokenHelper, method, None)), f"candidate {method} method is missing")

    def test_grant_type_dispatch_and_unsupported_response(self):
        self._require("oidc_token")
        self.helper.do_password_grant = mock.Mock(return_value={"grant": "password"})
        self.helper.do_challenge_grant = mock.Mock(return_value={"grant": "challenge"})
        self.helper.do_digital_signature_grant = mock.Mock(return_value={"grant": "digital_signature"})

        self.assertEqual(self.module.TokenHelper.oidc_token(self.helper, "password", value=1), {"grant": "password"})
        self.assertEqual(self.module.TokenHelper.oidc_token(self.helper, "challenge_approval", value=2), {"grant": "challenge"})
        self.assertEqual(self.module.TokenHelper.oidc_token(self.helper, "digital_signature", value=3), {"grant": "digital_signature"})
        unsupported = self.module.TokenHelper.oidc_token(self.helper, "other")
        self.assertEqual(unsupported["status"], 401)
        self.assertEqual(unsupported["error"], "unsupported_grant_type")

    def test_password_grant_authenticates_and_returns_bearer_token(self):
        self._require("do_password_grant")
        user = mock.Mock()
        user.with_user.return_value = user
        users = mock.Mock()
        users.sudo.return_value = users
        users.get_user_by_username.return_value = user
        self.helper.env["res.users"] = users
        self.helper.generate_user_token = mock.Mock(return_value=("synthetic-token", {"sub": "u"}, 60))
        data = {
            "username": "synthetic-user",
            "password": "synthetic-password",
            "client_id": "synthetic-client",
            "client_secret": "synthetic-client-secret",
            "scope": "profile",
        }

        result = self.module.TokenHelper.do_password_grant(self.helper, data)

        user.with_user.assert_called_once_with(user)
        user._check_credentials.assert_called_once_with("synthetic-password")
        self.helper.generate_user_token.assert_called_once_with(user, scope="profile")
        self.assertEqual(result, {
            "access_token": "synthetic-token",
            "token_type": "Bearer",
            "expires_in": 60,
        })
        self.assertNotIn("client_secret", data)

    def test_password_grant_reports_missing_credentials(self):
        self._require("do_password_grant")
        result = self.module.TokenHelper.do_password_grant(self.helper, {"username": "synthetic-user"})
        self.assertEqual(result["status"], 401)
        self.assertEqual(result["error"], "invalid_grant")

    def test_challenge_grant_uses_request_audience_or_default(self):
        self._require("do_challenge_grant")
        self.helper.get_issuer = mock.Mock(return_value="https://issuer.example.invalid")
        self.helper.get_audience = mock.Mock(return_value="default-audience")
        self.helper.generate_token_asymmetric = mock.Mock(return_value=("synthetic-challenge", {}))
        data = {"client_id": "synthetic-client", "client_secret": "synthetic-secret", "aud": "resource-a", "scope": "custom", "nonce": "n"}

        result = self.module.TokenHelper.do_challenge_grant(self.helper, data)

        self.assertEqual(result, {"challenge": "synthetic-challenge"})
        payload = self.helper.generate_token_asymmetric.call_args[0][0]
        self.assertEqual(payload["iss"], "https://issuer.example.invalid")
        self.assertEqual(payload["aud"], "resource-a")
        self.assertEqual(payload["scope"], "custom")
        self.assertEqual(payload["nonce"], "n")

    def test_digital_signature_grant_uses_default_audience(self):
        self._require("do_digital_signature_grant")
        self.helper.get_issuer = mock.Mock(return_value="https://issuer.example.invalid")
        self.helper.get_audience = mock.Mock(return_value="default-audience")
        self.helper.generate_token_asymmetric = mock.Mock(return_value=("synthetic-signature", {}))
        data = {"grant_type": "digital_signature", "client_id": "synthetic-client", "client_secret": "synthetic-secret", "nonce": "n"}

        result = self.module.TokenHelper.do_digital_signature_grant(self.helper, data)

        self.assertEqual(result, {"digital_signature": "synthetic-signature"})
        payload = self.helper.generate_token_asymmetric.call_args[0][0]
        self.assertEqual(payload["iss"], "https://issuer.example.invalid")
        self.assertEqual(payload["aud"], "default-audience")
        self.assertEqual(payload["nonce"], "n")

    def test_user_token_maps_identity_resource_and_expiry(self):
        self._require("generate_user_token")
        user = SimpleNamespace(
            id=23,
            login="synthetic-login",
            email="synthetic@example.invalid",
            is_user_machine=mock.Mock(return_value=True),
            is_user_business=mock.Mock(return_value=False),
            is_user_technical=mock.Mock(return_value=False),
        )
        self.helper.generate_token = mock.Mock(return_value=("synthetic-token", {"exp": 1}))

        result = self.module.TokenHelper.generate_user_token(
            self.helper, user, audience="requested-audience", expires_in=30,
            scope="profile", resource="service-a", role="reader",
        )

        args, kwargs = self.helper.generate_token.call_args
        payload = args[0]
        self.assertEqual(payload["uid"], 23)
        self.assertEqual(payload["user_id"], "synthetic-login")
        self.assertEqual(payload["sub"], "synthetic-login")
        self.assertEqual(payload["email"], "synthetic@example.invalid")
        self.assertEqual(payload["db"], "synthetic-db")
        self.assertEqual(payload["type"], "machine")
        self.assertEqual(payload["aud"], "service-a")
        self.assertEqual(payload["role"], "reader")
        self.assertEqual(kwargs, {"audience": "requested-audience", "expires_in": 30, "scope": "profile"})
        self.assertEqual(result, ("synthetic-token", {"exp": 1}, 30))


if __name__ == "__main__":
    unittest.main()
