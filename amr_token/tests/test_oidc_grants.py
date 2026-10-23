"""Fail-closed token-endpoint contract for incomplete/unsupported grants."""
import unittest
from types import SimpleNamespace
from unittest import mock

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
        self.helper.generate_user_token = mock.Mock(
            return_value=("synthetic-token", {"sub": "synthetic-user"}, 60)
        )

    def test_incomplete_and_unsupported_grants_fail_closed_without_token(self):
        cases = (
            ("password", "do_password_grant"),
            ("challenge_approval", "do_challenge_grant"),
            ("digital_signature", "do_digital_signature_grant"),
            ("client_credentials", "do_client_credentials"),
            ("urn:ietf:params:oauth:grant-type:jwt-bearer", "do_client_assertion"),
            ("refresh_token", "do_refresh_grant"),
            ("authorization_code", "do_authorization_code_grant"),
            ("custom_extension", "do_custom_grant"),
            (None, "do_unknown_grant"),
        )
        spies = {}
        for grant_type, handler_name in cases:
            spy = mock.Mock(return_value={"access_token": "must-not-be-issued"})
            setattr(self.helper, handler_name, spy)
            spies[handler_name] = spy

            response = self.module.TokenHelper.oidc_token(
                self.helper, grant_type=grant_type, marker="synthetic"
            )

            self.assertEqual(response.get("status"), 400, grant_type)
            self.assertEqual(response.get("error"), "unsupported_grant_type", grant_type)
            self.assertNotIn("access_token", response)

        for spy in spies.values():
            spy.assert_not_called()
        self.helper.generate_user_token.assert_not_called()

    def test_legacy_grant_handlers_are_not_public_methods(self):
        for method in (
            "do_password_grant",
            "do_challenge_grant",
            "do_digital_signature_grant",
        ):
            with self.subTest(method=method):
                self.assertFalse(callable(getattr(self.module.TokenHelper, method, None)))

    def test_generic_user_token_helper_remains_available(self):
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
        self.assertEqual(kwargs, {
            "audience": "requested-audience",
            "expires_in": 30,
            "scope": "profile",
        })
        self.assertEqual(result, ("synthetic-token", {"exp": 1}, 30))


if __name__ == "__main__":
    unittest.main()
