"""Offline boundary checks for the real optional res.users glue method."""
import ast
import importlib.util
import jwt
import pathlib
import sys
import time
import types
import unittest
from functools import wraps
from unittest import mock


ADDON = pathlib.Path(__file__).resolve().parents[2]


def load_glue_module():
    def simulated_ormcache(*_keys):
        def decorate(function):
            entries = {}
            stats = {"lookups": 0, "hits": 0, "misses": 0}

            @wraps(function)
            def cached(self, *args, **kwargs):
                stats["lookups"] += 1
                key = (args, tuple(sorted(kwargs.items())))
                if key in entries:
                    stats["hits"] += 1
                    return entries[key]
                stats["misses"] += 1
                entries[key] = function(self, *args, **kwargs)
                return entries[key]

            cached.cache_stats = stats
            return cached
        return decorate

    odoo = types.ModuleType("odoo")
    odoo.api = types.SimpleNamespace(model=lambda method: method)
    odoo.models = types.SimpleNamespace(Model=object)
    tools = types.ModuleType("odoo.tools")
    tools.ormcache = simulated_ormcache
    exceptions = types.ModuleType("odoo.exceptions")
    exceptions.AccessError = type("AccessError", (Exception,), {})
    exceptions.UserError = type("UserError", (Exception,), {})
    odoo.exceptions = exceptions
    with mock.patch.dict(sys.modules, {"odoo": odoo, "odoo.tools": tools,
                                       "odoo.exceptions": exceptions}):
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


class VersionedConfig:
    def __init__(self):
        self.values = {
            "amr_token.expires_in": "60",
            "amr_token.signature_type": "secret",
            "amr_token.secret_algorithm": "HS256",
            "amr_token.public_key_algorithm": "RS256",
            "amr_token.secret": "synthetic-secret-a",
            "web.base.url": "https://legacy-cache.invalid",
            "database.uuid": "legacy-default-audience",
        }
        self.versions = {key: 1 for key in self.values}

    def sudo(self):
        return self

    def get_param(self, key, default=None):
        return self.values.get(key, default)

    def set_param(self, key, value):
        self.values[key] = value
        self.versions[key] = self.versions.get(key, 0) + 1

    def search_read(self, domain, fields):
        requested = set(domain[0][2])
        return [
            {"id": index, "key": key, "value": self.values[key],
             "write_date": "version-%s" % self.versions[key]}
            for index, key in enumerate(sorted(requested), 1)
            if key in self.versions
        ]


class FakeSigningKeySet:
    def __init__(self, record=None):
        self.record = record

    def __len__(self):
        return int(self.record is not None)

    def __getattr__(self, name):
        if self.record is None:
            raise AttributeError(name)
        return getattr(self.record, name)


class LegacyCacheEnv(dict):
    def __init__(self, params, uid=7):
        super().__init__()
        self.uid = uid
        self.cr = types.SimpleNamespace(dbname="legacy-cache-test-db")
        self.registry = object()
        self.user = types.SimpleNamespace(has_group=lambda group: True)
        self["ir.config_parameter"] = params
        self["amr.public.key"] = types.SimpleNamespace(
            sudo=lambda: self["amr.public.key"], search=lambda *args, **kwargs: [])


def make_cached_user(module):
    params = VersionedConfig()
    env = LegacyCacheEnv(params)
    helper = types.SimpleNamespace()

    def get_signature_type():
        value = params.get_param("amr_token.signature_type")
        if value not in ("secret", "public_key"):
            raise ValueError("A supported signature type is required")
        return value

    def get_signature_algorithm():
        signature_type = get_signature_type()
        key = ("amr_token.public_key_algorithm" if signature_type == "public_key"
               else "amr_token.secret_algorithm")
        value = params.get_param(key)
        if not value:
            raise ValueError("A configured signing algorithm is required")
        return value

    def get_issuer():
        issuer = params.get_param("web.base.url")
        if not issuer or not issuer.startswith("https://"):
            raise ValueError("A valid HTTPS issuer is required")
        return issuer.rstrip("/")

    def validate_audience(audience):
        if isinstance(audience, str) and audience.strip():
            return audience
        if isinstance(audience, (list, tuple)) and audience and all(
                isinstance(value, str) and value.strip() for value in audience):
            return list(audience)
        raise ValueError("A valid audience is required")

    def get_encoder():
        signature_type = get_signature_type()
        algorithm = get_signature_algorithm()
        issuer = get_issuer()
        if signature_type == "secret":
            secret = params.get_param("amr_token.secret")
            if not secret:
                raise ValueError("JWT Secret not set")
            return types.SimpleNamespace(algorithm=algorithm, issuer=issuer, secret=secret)
        return types.SimpleNamespace(algorithm=algorithm, issuer=issuer)

    def check_access(user):
        if user.id != env.uid and not env.user.has_group("base.group_system"):
            raise module.AccessError("You may only issue an access token for yourself.")

    def generate(user, audience=module._AUDIENCE_UNSET):
        check_access(user)
        if audience is module._AUDIENCE_UNSET:
            audience = params.get_param("database.uuid")
        lifetime = int(params.get_param("amr_token.expires_in", 86400))
        encoder = get_encoder()
        signing_id = getattr(encoder, "secret", "asymmetric")
        token = "token-%s-%s-%s" % (signing_id, audience, generate.calls)
        generate.calls += 1
        return token, {}, lifetime
    generate.calls = 0

    helper._validate_audience = validate_audience
    helper._generate_user_token = mock.Mock(side_effect=generate)
    helper._check_token_issuance_access = check_access
    helper.get_expires_in = lambda: int(params.get_param("amr_token.expires_in", 86400))
    helper.get_signature_type = get_signature_type
    helper.get_signature_algorithm = get_signature_algorithm
    helper.get_issuer = get_issuer
    helper.get_audience = lambda: params.get_param("database.uuid")
    helper._get_secret = lambda: params.get_param("amr_token.secret")
    helper._get_encoder = get_encoder
    env["amr.oidc.helper"] = helper

    user = module.ResUsers()
    user.id = 7
    user.env = env
    user.ensure_one = lambda: None
    user.is_user_allow_create_token = lambda: True
    user.browse = lambda uid: types.SimpleNamespace(id=uid)
    return user, params, helper


class TestResourceGlueLifetimeContract(unittest.TestCase):
    def setUp(self):
        self.module = load_glue_module()
        if not hasattr(self.module, "time"):
            self.module.time = time

    def _assert_rotation_fixture_source_contract(self):
        fixture = ADDON / "tests" / "integration" / "test_user_token_glue.py"
        tree = ast.parse(fixture.read_text())
        test = next(node for node in ast.walk(tree)
                    if isinstance(node, ast.FunctionDef)
                    and node.name == "test_signing_configuration_change_uses_new_key_and_ttl")

        def calls_method(call, model, method):
            return (
                isinstance(call, ast.Call)
                and isinstance(call.func, ast.Attribute)
                and call.func.attr == method
                and isinstance(call.func.value, ast.Name)
                and call.func.value.id == model
            )

        calls = [node for node in ast.walk(test) if isinstance(node, ast.Call)]
        reads_new_token = any(
            calls_method(call, "helper", "decode") and call.args
            and isinstance(call.args[0], ast.Name)
            and call.args[0].id == "new_token"
            for call in calls
        )
        self.assertFalse(reads_new_token)

        expected_options = {"verify_exp": False, "verify_aud": False}
        has_options = False
        for call in calls:
            if not calls_method(call, "jwt", "decode"):
                continue
            for keyword in call.keywords:
                if keyword.arg != "options":
                    continue
                try:
                    has_options = ast.literal_eval(keyword.value) == expected_options
                except (TypeError, ValueError):
                    has_options = False
                if has_options:
                    break
            if has_options:
                break
        self.assertTrue(has_options)

        def is_audience_subscript(node):
            if not isinstance(node, ast.Subscript):
                return False
            if not isinstance(node.value, ast.Name):
                return False
            if node.value.id != "claims":
                return False
            index = node.slice
            if isinstance(index, ast.Index):
                index = getattr(index, "value", index)
            try:
                return ast.literal_eval(index) == "aud"
            except (TypeError, ValueError):
                return False

        self.assertTrue(any(is_audience_subscript(node) for node in ast.walk(test)))

    def user(self, ttl):
        user = Users(ttl)
        user.get_access_token = self.module.ResUsers.get_access_token.__get__(user)
        user._legacy_cache_fingerprint = self.module.ResUsers._legacy_cache_fingerprint.__get__(user)
        user._legacy_cache_context = self.module.ResUsers._legacy_cache_context.__get__(user)
        user._get_access_token_cached = self.module.ResUsers._get_access_token_cached.__get__(user)
        user._get_access_token_fresh = self.module.ResUsers._get_access_token_fresh.__get__(user)
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

    def test_legacy_issuance_reuses_only_within_full_scoped_cache_key(self):
        user, params, helper = make_cached_user(self.module)
        cached = getattr(self.module.ResUsers, "_get_access_token_cached", None)
        cache_stats = getattr(cached, "cache_stats", None)
        if cache_stats is not None:
            cache_stats.update(lookups=0, hits=0, misses=0)

        with mock.patch.object(self.module.time, "time", return_value=1800000000):
            first = user.get_access_token(audience=["cache-audience", "cache-secondary"])
            repeated = user.get_access_token(audience=["cache-audience", "cache-secondary"])
            self.assertEqual(repeated, first)
            self.assertEqual(helper._generate_user_token.call_count, 1)

            default_first = user.get_access_token()
            default_repeated = user.get_access_token()
            self.assertEqual(default_repeated, default_first)
            self.assertEqual(helper._generate_user_token.call_count, 2)

            user.get_access_token(audience="different-audience")
            self.assertEqual(helper._generate_user_token.call_count, 3)

        with mock.patch.object(self.module.time, "time", return_value=1800000060):
            user.get_access_token(audience=["cache-audience", "cache-secondary"])
        self.assertEqual(helper._generate_user_token.call_count, 4)

        user.env.uid = 8
        user.get_access_token(audience=["cache-audience", "cache-secondary"])
        self.assertEqual(helper._generate_user_token.call_count, 5)

        params.set_param("amr_token.secret", "synthetic-secret-b")
        user.get_access_token(audience=["cache-audience", "cache-secondary"])
        self.assertEqual(helper._generate_user_token.call_count, 6)
        user.env.cr.dbname = "other-legacy-cache-test-db"
        user.get_access_token(audience=["cache-audience", "cache-secondary"])
        self.assertEqual(helper._generate_user_token.call_count, 7)
        user.env.cr.dbname = "legacy-cache-test-db"
        user.env.registry = object()
        user.get_access_token(audience=["cache-audience", "cache-secondary"])
        self.assertEqual(helper._generate_user_token.call_count, 8)
        user.id = 8
        user.get_access_token(audience=["cache-audience", "cache-secondary"])
        self.assertEqual(helper._generate_user_token.call_count, 9)
        if cache_stats is None:
            self.fail("test ORM cache simulator was not installed")
        self.assertGreaterEqual(cache_stats["hits"], 2)

    def test_database_signing_key_material_change_cannot_cross_hit(self):
        user, params, helper = make_cached_user(self.module)
        params.set_param("amr_token.signature_type", "public_key")
        key = types.SimpleNamespace(
            id=41, kid="synthetic-signing-kid", algorithm="RS256",
            write_date="same-second", active=True, is_signing=True,
            private_key="synthetic-private-key-a",
        )
        key_model = types.SimpleNamespace()
        key_model.sudo = lambda: key_model

        def search(domain, limit=1):
            algorithm = next(item[2] for item in domain if item[0] == "algorithm")
            active = key.active and key.is_signing and key.algorithm == algorithm
            return FakeSigningKeySet(key if active else None)

        key_model.search = search
        user.env["amr.public.key"] = key_model
        first = user.get_access_token(audience="public-key-cache-audience")
        repeated = user.get_access_token(audience="public-key-cache-audience")
        self.assertEqual(first, repeated)
        self.assertEqual(helper._generate_user_token.call_count, 1)

        # Keep the row timestamp fixed to prove key material itself is revision-bound.
        key.private_key = "synthetic-private-key-b"
        rotated = user.get_access_token(audience="public-key-cache-audience")
        self.assertNotEqual(rotated, first)
        self.assertEqual(helper._generate_user_token.call_count, 2)

    def test_actor_and_invalid_ttl_are_checked_before_a_warm_cache_lookup(self):
        user, params, helper = make_cached_user(self.module)
        user.get_access_token(audience="warm-audience")
        cached = getattr(self.module.ResUsers, "_get_access_token_cached", None)
        lookup_stats = getattr(cached, "cache_stats", None)
        before = lookup_stats["lookups"] if lookup_stats is not None else 0

        user.is_user_allow_create_token = lambda: False
        with self.assertRaisesRegex(self.module.UserError, "not allowed"):
            user.get_access_token(audience="warm-audience")
        self.assertEqual(helper._generate_user_token.call_count, 1)
        if lookup_stats is not None:
            self.assertEqual(lookup_stats["lookups"], before)

        user.is_user_allow_create_token = lambda: True
        user.env.uid = 8
        user.env.user.has_group = lambda group: False
        with self.assertRaises(self.module.AccessError):
            user.get_access_token(audience="warm-audience")
        if lookup_stats is not None:
            self.assertEqual(lookup_stats["lookups"], before)

        user.env.uid = 7
        user.env.user.has_group = lambda group: True
        params.set_param("amr_token.expires_in", "")
        cached_method = getattr(user, "_get_access_token_cached", None)
        if cached_method is None:
            with mock.patch.object(user, "_get_access_token", return_value="warm-token"):
                with self.assertRaises(ValueError):
                    user.get_access_token(audience="warm-audience")
        else:
            with mock.patch.object(user, "_get_access_token_cached", wraps=cached_method) as lookup:
                with self.assertRaises(ValueError):
                    user.get_access_token(audience="warm-audience")
                lookup.assert_not_called()
        self.assertEqual(helper._generate_user_token.call_count, 1)

    def test_signing_configuration_change_during_cache_fill_fails_closed(self):
        user, params, helper = make_cached_user(self.module)
        generate = helper._generate_user_token.side_effect

        def rotate_after_signing(target, audience=None):
            result = generate(target, audience=audience)
            params.set_param("amr_token.secret", "synthetic-secret-rotated-mid-call")
            return result

        helper._generate_user_token.side_effect = rotate_after_signing
        with self.assertRaisesRegex(ValueError, "Signing configuration changed during token issuance"):
            user.get_access_token(audience="mid-call-rotation-audience")
        self.assertEqual(helper._generate_user_token.call_count, 1)

    def test_nonpositive_legacy_ttl_never_uses_cache(self):
        user, params, helper = make_cached_user(self.module)
        cached = self.module.ResUsers._get_access_token_cached
        stats = cached.cache_stats
        for value in ("0", "-1"):
            params.set_param("amr_token.expires_in", value)
            first = user.get_access_token(audience="nonpositive-ttl-audience")
            repeated = user.get_access_token(audience="nonpositive-ttl-audience")
            self.assertNotEqual(first, repeated)
        self.assertEqual(helper._generate_user_token.call_count, 4)
        self.assertEqual(stats["lookups"], 0)

    def test_rotation_fixture_checks_audience_without_wall_clock_decode(self):
        self._assert_rotation_fixture_source_contract()

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

    def test_rotation_fixture_source_contract_does_not_require_ast_source_segment(self):
        with mock.patch.object(ast, "get_source_segment", None, create=True):
            self._assert_rotation_fixture_source_contract()


def root_integration_import_bindings(source):
    tests_init = ast.parse(source)
    return [
        alias.asname or alias.name
        for node in tests_init.body
        if isinstance(node, ast.ImportFrom)
        and node.level == 1
        and node.module == "integration"
        for alias in node.names
    ]


class TestOdoo13TestDiscoveryContract(unittest.TestCase):
    def test_integration_modules_are_registered_in_root_tests_package(self):
        tests_dir = ADDON / "tests"
        integration_modules = sorted(
            path.stem for path in (tests_dir / "integration").glob("test_*.py")
        )
        tests_init_source = (tests_dir / "__init__.py").read_text()
        registered_modules = root_integration_import_bindings(tests_init_source)

        self.assertEqual(
            len(integration_modules),
            len(registered_modules),
            "each integration test module must be registered exactly once",
        )
        self.assertCountEqual(
            integration_modules,
            registered_modules,
            "tests/__init__.py must bind every integration test module by its test_* name",
        )

    def test_non_test_alias_is_not_counted_as_root_test_module(self):
        aliased_import = "from .integration import test_probe as helper"

        registered_modules = root_integration_import_bindings(aliased_import)

        self.assertEqual(["helper"], registered_modules)
        self.assertNotEqual(["test_probe"], registered_modules)


if __name__ == "__main__":
    unittest.main()
