"""Issuance boundaries for provider-owned OIDC signing helpers."""
import ast
import importlib.util
from datetime import datetime
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest import mock

ADDON = Path(__file__).resolve().parents[2]


def _load_support():
    path = ADDON / "tests" / "support.py"
    spec = importlib.util.spec_from_file_location("oidc_security_test_support", str(path))
    if spec is None or spec.loader is None:
        raise ImportError("cannot create isolated support module spec")
    support = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(support)
    return support


def _load_module(support, relative):
    if relative == "models/token_helper.py":
        packages = {name: ModuleType(name) for name in (
            "cryptography", "cryptography.hazmat", "cryptography.hazmat.primitives",
            "cryptography.hazmat.primitives.asymmetric")}
        setattr(packages["cryptography.hazmat.primitives.asymmetric"], "ec", mock.Mock())
        setattr(packages["cryptography.hazmat.primitives.asymmetric"], "rsa", mock.Mock())
        with mock.patch.dict(sys.modules, packages):
            return support.load(relative)
    return support.load(relative)


def _method_names(relative, class_name):
    tree = ast.parse((ADDON / relative).read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return {member.name for member in node.body
                    if isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef))}
    raise AssertionError("class not found: " + class_name)


class TestEncodePrivacyNames(unittest.TestCase):
    def test_oidc_model_encode_methods_are_private(self):
        self.assertNotIn("encode", _method_names("models/oidc_client.py", "OidcClient"))
        self.assertIn("_encode", _method_names("models/oidc_client.py", "OidcClient"))

    def test_token_helper_encode_methods_are_private(self):
        self.assertNotIn("encode", _method_names("models/token_helper.py", "TokenHelper"))
        self.assertIn("_encode", _method_names("models/token_helper.py", "TokenHelper"))


class FakeEnv(dict):
    def __init__(self, uid, system=False):
        super(FakeEnv, self).__init__()
        self.uid = uid
        self.user = SimpleNamespace(
            has_group=lambda group: system and group == "base.group_system")
        self.cr = SimpleNamespace(dbname="unit-db")


class FakeUser(object):
    def __init__(self, user_id):
        self.id = user_id
        self.login = "target-user"
        self.email = ""

    def ensure_one(self):
        return None


class TokenIssuerSecurityTests(unittest.TestCase):
    def test_create_authorization_code_is_private(self):
        methods = _method_names("models/oidc_client.py", "OidcClient")
        self.assertNotIn("create_authorization_code", methods)
        self.assertIn("_create_authorization_code", methods)

    def _client_credentials_fixture(self):
        support = _load_support()
        module = support.load("models/oidc_client.py")
        record = module.OidcClient()
        record.env = FakeEnv(uid=7)
        record.sudo = lambda: record
        record.search = mock.Mock(return_value=record)
        client = mock.Mock()
        client.check_credentials.side_effect = lambda secret: (
            True if secret else (_ for _ in ()).throw(ValueError("Invalid secret")))
        record.check_credentials = client.check_credentials
        helper = mock.Mock()
        helper.generate_user_token.return_value = ("opaque-token", {}, 60)
        record.env["amr.oidc.helper"] = helper
        return record, client.check_credentials, helper

    def test_client_credentials_is_private_and_missing_secret_fails_before_signing(self):
        methods = _method_names("models/oidc_client.py", "OidcClient")
        self.assertNotIn("client_credentials", methods)
        self.assertIn("_client_credentials", methods)
        record, check, helper = self._client_credentials_fixture()
        with self.assertRaises(ValueError):
            record._client_credentials(client_id="client-a", audience="aud-a")
        check.assert_called_once_with(None)
        helper.generate_user_token.assert_not_called()

    def test_client_credentials_rejects_empty_and_invalid_secrets_before_signing(self):
        for secret, error in (("", ValueError("bad")), ("wrong", ValueError("bad"))):
            with self.subTest(secret=secret):
                record, check, helper = self._client_credentials_fixture()
                check.side_effect = error
                with self.assertRaises(ValueError):
                    record._client_credentials(client_secret=secret, scope="read")
                check.assert_called_once_with(secret)
                helper.generate_user_token.assert_not_called()

    def test_client_credentials_valid_secret_is_not_forwarded_and_shape_is_preserved(self):
        record, check, helper = self._client_credentials_fixture()
        result = record._client_credentials(client_secret="correct", client_id="client-a",
                                            audience="aud-a", scope="read")
        check.assert_called_once_with("correct")
        helper.generate_user_token.assert_called_once_with(
            mock.ANY, client_id="client-a", audience="aud-a", scope="read")
        self.assertEqual(result, {"access_token": "opaque-token", "token_type": "Bearer",
                                 "expires_in": 60})

    def test_token_helper_secret_and_signing_methods_are_private(self):
        methods = _method_names("models/token_helper.py", "TokenHelper")
        for public_name, internal_name in (
                ("get_secret", "_get_secret"),
                ("generate_token", "_generate_token"),
                ("generate_token_secret", "_generate_token_secret"),
                ("generate_token_asymmetric", "_generate_token_asymmetric")):
            with self.subTest(method=public_name):
                self.assertNotIn(public_name, methods)
                self.assertIn(internal_name, methods)

    def test_public_key_signing_method_is_private(self):
        methods = _method_names("models/public_key.py", "PublicKey")
        self.assertNotIn("get_private_key", methods)
        self.assertIn("_get_private_key", methods)
        self.assertNotIn("generate_token", methods)
        self.assertIn("_generate_token", methods)

    def test_refresh_secret_and_issuer_methods_are_private(self):
        methods = _method_names("models/oidc_refresh_token.py", "OidcRefreshToken")
        self.assertNotIn("get_secret", methods)
        self.assertNotIn("create_refresh_token", methods)
        self.assertIn("_get_secret", methods)
        self.assertIn("_create_refresh_token", methods)

    def test_res_users_rejects_other_user_without_system_group_before_cache(self):
        support = _load_support()
        module = support.load("models/res_users.py")
        record = module.ResUsers()
        record.id = 29
        record.ensure_one = lambda: None
        record.env = FakeEnv(uid=7, system=False)
        cached = mock.Mock(return_value="opaque-token")
        record._get_access_token = cached

        with self.assertRaises(support.AccessError):
            record.get_access_token(audience="client-audience")

        cached.assert_not_called()

    def test_res_users_allows_self_and_system_user_before_cache(self):
        support = _load_support()
        module = support.load("models/res_users.py")
        for actor_uid, target_uid, is_system in ((29, 29, False), (7, 29, True)):
            with self.subTest(actor_uid=actor_uid, is_system=is_system):
                record = module.ResUsers()
                record.id = target_uid
                record.ensure_one = lambda: None
                record.env = FakeEnv(uid=actor_uid, system=is_system)
                cached = mock.Mock(return_value="opaque-token")
                record._get_access_token = cached
                with mock.patch("time.time", return_value=900):
                    self.assertEqual(record.get_access_token(audience="client-audience"),
                                     "opaque-token")
                cached.assert_called_once_with(target_uid, "client-audience", 3)

    def test_helper_rejects_other_user_before_signing(self):
        support = _load_support()
        module = _load_module(support, "models/token_helper.py")
        helper = module.TokenHelper()
        helper.env = FakeEnv(uid=7, system=False)
        helper.get_expires_in = lambda: 60
        signer = mock.Mock(return_value=("opaque-token", {}))
        helper.generate_token = signer
        helper._generate_token = signer
        method = getattr(helper, "_generate_user_token", None)
        if method is None:
            method = helper.generate_user_token

        with self.assertRaises(support.AccessError):
            method(FakeUser(29), audience="client-audience", expires_in=60)

        signer.assert_not_called()

    def test_helper_allows_self_and_system_user_to_sign(self):
        support = _load_support()
        module = _load_module(support, "models/token_helper.py")
        for actor_uid, target_uid, is_system in ((29, 29, False), (7, 29, True)):
            with self.subTest(actor_uid=actor_uid, is_system=is_system):
                helper = module.TokenHelper()
                helper.env = FakeEnv(uid=actor_uid, system=is_system)
                helper.get_expires_in = lambda: 60
                signer = mock.Mock(return_value=("opaque-token", {}))
                helper.generate_token = signer
                helper._generate_token = signer
                method = getattr(helper, "_generate_user_token", None)
                if method is None:
                    method = helper.generate_user_token
                result = method(FakeUser(target_uid), audience="client-audience", expires_in=60)
                self.assertEqual(result[0], "opaque-token")
                signer.assert_called_once()

    def _refresh_fixture(self, support, actor_uid, is_system):
        module = support.load("models/oidc_refresh_token.py")
        module.fields.Datetime.now = staticmethod(lambda: datetime(2026, 1, 1))
        module.jwt.encode = mock.Mock(return_value="opaque-token")
        record = module.OidcRefreshToken()
        record.env = FakeEnv(uid=actor_uid, system=is_system)
        record.create = mock.Mock()
        record._get_secret = lambda: object()
        record.get_secret = lambda: object()
        record._get_issuer = lambda: "https://issuer.invalid"
        method = getattr(record, "_create_refresh_token", None)
        if method is None:
            method = record.create_refresh_token
        return module, record, method

    def test_refresh_creator_rejects_other_user_before_storage_or_signing(self):
        support = _load_support()
        module, record, method = self._refresh_fixture(support, 7, False)

        with self.assertRaises(support.AccessError):
            method(FakeUser(29))

        record.create.assert_not_called()
        module.jwt.encode.assert_not_called()

    def test_refresh_creator_allows_self_and_system_user(self):
        support = _load_support()
        for actor_uid, target_uid, is_system in ((29, 29, False), (7, 29, True)):
            with self.subTest(actor_uid=actor_uid, is_system=is_system):
                module, record, method = self._refresh_fixture(support, actor_uid, is_system)
                self.assertEqual(method(FakeUser(target_uid)), "opaque-token")
                record.create.assert_called_once()
                module.jwt.encode.assert_called_once()


if __name__ == "__main__":
    unittest.main()
