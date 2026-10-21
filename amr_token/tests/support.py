"""Minimal Odoo doubles for isolated amr_token source-contract tests.

This module never imports the addon package root or boots an Odoo registry.
"""
import contextlib
import datetime
import importlib.util
import pathlib
import sys
import types
from urllib.parse import urlencode

ROOT = pathlib.Path(__file__).resolve().parents[2]
ADDON = ROOT / "amr_token"


class FieldSpec:
    def __init__(self, kind, args, kwargs):
        self.kind = kind
        self.args = args
        self.kwargs = kwargs


class FieldType:
    def __init__(self, name):
        self.name = name

    def __call__(self, *args, **kwargs):
        return FieldSpec(self.name, args, kwargs)

    @staticmethod
    def now():
        return datetime.datetime(2000, 1, 1)


class API:
    @staticmethod
    def model(function):
        return function

    @staticmethod
    def constrains(*_names):
        return lambda function: function

    @staticmethod
    def depends(*_names):
        return lambda function: function


class ValidationError(Exception):
    pass


class UserError(Exception):
    pass


class StubHTTPException(Exception):
    pass


class StubResponse:
    def __init__(self, response="", status=200, headers=None, content_type=None):
        self.response = response
        self.status_code = status
        self.status = status
        self.headers = dict(headers or [])
        if content_type:
            self.headers["Content-Type"] = content_type

    def get_data(self, as_text=False):
        body = self.response
        if isinstance(body, bytes):
            return body.decode("utf-8") if as_text else body
        return body if as_text else str(body).encode("utf-8")


@contextlib.contextmanager
def odoo_stubs():
    api = API()
    fields = types.SimpleNamespace(**{
        name: FieldType(name)
        for name in ("Boolean", "Char", "Datetime", "Integer", "Selection", "Text")
    })

    class AbstractModel:
        def introspect_token(self, token, **kwargs):
            return {"via": "base.introspect_token", "token": token, "kwargs": kwargs}

        def validate(self, token):
            return {"via": "base.validate", "token": token}

        def decode(self, token, **kwargs):
            return {"via": "base.decode", "token": token, "kwargs": kwargs}

    models = types.SimpleNamespace(
        Model=type("Model", (), {}),
        AbstractModel=AbstractModel,
        TransientModel=type("TransientModel", (), {}),
    )
    odoo = types.ModuleType("odoo")
    setattr(odoo, "api", api)
    setattr(odoo, "fields", fields)
    setattr(odoo, "models", models)
    setattr(odoo, "_", lambda value: value)

    exceptions = types.ModuleType("odoo.exceptions")
    setattr(exceptions, "ValidationError", ValidationError)
    setattr(exceptions, "UserError", UserError)

    tools = types.ModuleType("odoo.tools")
    setattr(tools, "config", types.SimpleNamespace(get=lambda _key, default=None: default))
    setattr(tools, "ormcache", lambda *_keys: (lambda function: function))
    setattr(odoo, "tools", tools)

    request = types.SimpleNamespace(
        httprequest=types.SimpleNamespace(headers={}),
        env={},
    )
    http = types.ModuleType("odoo.http")
    setattr(http, "request", request)
    setattr(http, "Controller", type("Controller", (), {}))
    setattr(http, "Response", StubResponse)

    def route(paths, **options):
        def decorate(function):
            function._route_paths = paths
            function._route_options = options
            return function
        return decorate

    setattr(http, "route", route)
    setattr(odoo, "http", http)

    werkzeug = types.ModuleType("werkzeug")
    setattr(werkzeug, "url_encode", urlencode)
    werkzeug_exceptions = types.ModuleType("werkzeug.exceptions")
    setattr(werkzeug_exceptions, "HTTPException", StubHTTPException)
    werkzeug_wrappers = types.ModuleType("werkzeug.wrappers")
    setattr(werkzeug_wrappers, "Response", StubResponse)
    setattr(werkzeug, "exceptions", werkzeug_exceptions)
    setattr(werkzeug, "wrappers", werkzeug_wrappers)

    replacements = {
        "odoo": odoo,
        "odoo.exceptions": exceptions,
        "odoo.tools": tools,
        "odoo.http": http,
        "werkzeug": werkzeug,
        "werkzeug.exceptions": werkzeug_exceptions,
        "werkzeug.wrappers": werkzeug_wrappers,
    }
    previous = {name: sys.modules.get(name) for name in replacements}
    sys.modules.update(replacements)
    try:
        yield
    finally:
        for name, old in previous.items():
            if old is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = old


def _load_candidate(relative_path, module_name):
    path = ADDON / relative_path
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot create candidate module spec for {relative_path}")
    module = importlib.util.module_from_spec(spec)
    with odoo_stubs():
        spec.loader.exec_module(module)
    return module


def load_helper_module():
    return _load_candidate("models/helper.py", "_amr_token_candidate_helper")


def load_public_key_model():
    return _load_candidate("models/public_key.py", "_amr_token_candidate_public_key")


def load_settings_model():
    return _load_candidate("models/res_config_settings.py", "_amr_token_candidate_settings")


def load_res_users_model():
    return _load_candidate("models/res_users.py", "_amr_token_candidate_res_users")


def load_controller_module():
    return _load_candidate("controllers/main.py", "_amr_token_candidate_controller")
