"""P-05 user introspection/profile response construction contract."""
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


class TestOidcUserResponses(unittest.TestCase):
    def setUp(self):
        self.module = load_helper_module()
        self.helper = object.__new__(self.module.TokenHelper)
        self.user = mock.Mock()
        self.user.exists.return_value = True
        self.user.id = 17
        self.user.login = "synthetic-login"
        self.user.name = "Synthetic User"
        self.user.email = "synthetic@example.invalid"
        self.users = mock.Mock()
        self.users.sudo.return_value = self.users
        self.users.browse.return_value = self.user
        self.helper.env = _Environment({"res.users": self.users})
        self.helper.validate = mock.Mock(return_value={"uid": 17, "sub": "synthetic-login", "scope": "profile"})

    def _require(self, method):
        self.assertTrue(callable(self.module.TokenHelper.__dict__.get(method)), f"candidate {method} method is missing")

    def test_introspection_adds_identity_and_database_claim(self):
        self._require("oidc_introspect")
        result = self.module.TokenHelper.oidc_introspect(self.helper, access_token="synthetic-token")

        self.assertEqual(result, {
            "uid": 17,
            "sub": "synthetic-login",
            "scope": "profile",
            "active": True,
            "user_id": 17,
            "name": "Synthetic User",
            "login": "synthetic-login",
            "db": "synthetic-db",
        })
        self.helper.validate.assert_called_once_with("synthetic-token")
        self.users.browse.assert_called_once_with(17)

    def test_profile_adds_identity_and_database_without_active_flag(self):
        self._require("oidc_profile")
        result = self.module.TokenHelper.oidc_profile(self.helper, token="synthetic-token")

        self.assertEqual(result, {
            "uid": 17,
            "sub": "synthetic-login",
            "scope": "profile",
            "user_id": 17,
            "name": "Synthetic User",
            "login": "synthetic-login",
            "db": "synthetic-db",
        })
        self.assertNotIn("active", result)

    def test_invalid_or_unmapped_token_is_inactive(self):
        self._require("oidc_introspect")
        self.helper.validate.return_value = {}

        result = self.module.TokenHelper.oidc_introspect(self.helper, access_token="invalid-token")

        self.assertEqual(result, {"active": False, "error": "invalid_token"})
        self.users.browse.assert_not_called()

    def test_payload_enhancers_add_database_name_in_place(self):
        self._require("oidc_introspect_payload_response_enhance")
        self._require("oidc_profile_payload_response_enhance")
        introspection = {"active": True}
        profile = {"sub": "synthetic-login"}

        self.assertIs(self.module.TokenHelper.oidc_introspect_payload_response_enhance(self.helper, introspection), introspection)
        self.assertIs(self.module.TokenHelper.oidc_profile_payload_response_enhance(self.helper, profile), profile)
        self.assertEqual(introspection["db"], "synthetic-db")
        self.assertEqual(profile["db"], "synthetic-db")


if __name__ == "__main__":
    unittest.main()
