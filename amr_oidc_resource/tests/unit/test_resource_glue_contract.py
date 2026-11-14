"""Offline boundary checks for the real optional res.users glue method."""
import ast
import importlib.util
import jwt
import pathlib
import sys
import types
import unittest
from unittest import mock


ADDON = pathlib.Path(__file__).resolve().parents[2]


def load_glue_module():
    odoo = types.ModuleType("odoo")
    odoo.api = types.SimpleNamespace(model=lambda method: method)
    odoo.models = types.SimpleNamespace(Model=object)
    exceptions = types.ModuleType("odoo.exceptions")
    exceptions.AccessError = type("AccessError", (Exception,), {})
    exceptions.UserError = type("UserError", (Exception,), {})
    odoo.exceptions = exceptions
    with mock.patch.dict(sys.modules, {"odoo": odoo, "odoo.exceptions": exceptions}):
        spec = importlib.util.spec_from_file_location(
            "candidate_resource_user_glue", ADDON / "models" / "res_users.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    return module


class Config:
    def __init__(self, value):
        self.value = value

    def sudo(self):
        return self

    def get_param(self, key):
        if key != "amr_token.expires_in":
            raise AssertionError("unexpected configuration lookup")
        return self.value


class Env(dict):
    uid = 7
    user = types.SimpleNamespace(has_group=lambda group: False)


class Users:
    id = 7

    def __init__(self, ttl):
        self._sign = mock.Mock(return_value=("token", {}, ttl))
        helper = types.SimpleNamespace(_validate_audience=lambda value: value,
                                       _generate_user_token=self._sign)
        self.env = Env({"ir.config_parameter": Config(ttl),
                        "amr.oidc.helper": helper})

    def ensure_one(self):
        return None

    def is_user_allow_create_token(self):
        return True

    def browse(self, uid):
        return types.SimpleNamespace(id=uid)


class TestResourceGlueLifetimeContract(unittest.TestCase):
    def setUp(self):
        self.module = load_glue_module()

    def user(self, ttl):
        user = Users(ttl)
        user.get_access_token = self.module.ResUsers.get_access_token.__get__(user)
        user._get_access_token = self.module.ResUsers._get_access_token.__get__(user)
        return user

    def test_legacy_configured_ttl_is_read_by_existing_helper(self):
        user = self.user("900")

        self.assertEqual(user.get_access_token(), "token")

        user._sign.assert_called_once_with(user.browse(user.id))

    def test_legacy_missing_ttl_is_delegated_to_the_existing_helper(self):
        user = self.user(None)
        del user.env["ir.config_parameter"]

        self.assertEqual(user.get_access_token(), "token")

        user._sign.assert_called_once_with(user.browse(user.id))

    def test_legacy_override_is_not_reinterpreted_by_the_glue(self):
        user = self.user("900")

        self.assertEqual(user.get_access_token(expires_in=30), "token")

        user._sign.assert_called_once_with(user.browse(user.id))

    def test_rotation_fixture_checks_audience_without_wall_clock_decode(self):
        fixture = ADDON / "tests" / "integration" / "test_user_token_glue.py"
        tree = ast.parse(fixture.read_text())
        test = next(node for node in ast.walk(tree)
                    if isinstance(node, ast.FunctionDef)
                    and node.name == "test_signing_configuration_change_uses_new_key_and_ttl")
        body = ast.get_source_segment(fixture.read_text(), test) or ""
        self.assertNotIn("helper.decode(new_token", body)
        self.assertIn('options={"verify_exp": False, "verify_aud": False}', body)
        self.assertIn('claims["aud"]', body)

        secret = "synthetic-rotated-signing-secret-012345"
        audience = "key-rotation-audience"
        token = jwt.encode({"exp": 1800000120, "aud": audience}, secret,
                           algorithm="HS256")
        claims = jwt.decode(token, secret, algorithms=["HS256"],
                            options={"verify_exp": False, "verify_aud": False})
        self.assertEqual(claims["aud"], audience)
        with self.assertRaises(jwt.InvalidSignatureError):
            jwt.decode(token, "different-secret-with-enough-bytes-012345", algorithms=["HS256"],
                       options={"verify_exp": False, "verify_aud": False})


if __name__ == "__main__":
    unittest.main()
