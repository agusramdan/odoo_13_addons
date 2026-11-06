"""Narrow import doubles: declarations and parent delegation, never Odoo boot."""
import importlib.util
import json
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
from urllib.parse import urlencode
from unittest.mock import patch


ADDON = Path(__file__).resolve().parents[1]


class Field:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs


class ParentHelper:
    def oidc_token(self, grant_type=None, **kwargs):
        return {"status": 400, "error": "unsupported_grant_type"}


class StubResponse:
    def __init__(self, response="", status=200, status_code=None, **kwargs):
        self.status_code = status if status_code is None else status_code
        if isinstance(response, str):
            response = response.encode("utf-8")
        self.data = response
        self.response = response


class StubNotFound(Exception):
    code = 404
    description = "Not Found"


def _route(paths, **options):
    def decorate(function):
        function._route_paths = paths
        function._route_options = options
        return function
    return decorate


def load(relative, parent_helper=None):
    """Load only one leaf model module with inert fields and no external libraries."""
    odoo = ModuleType('odoo')
    setattr(odoo, '_', lambda value: value)
    setattr(odoo, 'api', SimpleNamespace(
        model=lambda method: method,
        constrains=lambda *field_names: (lambda method: method),
    ))
    setattr(odoo, 'fields', SimpleNamespace(**{name: Field for name in (
        'Boolean', 'Char', 'Text', 'Many2one', 'Many2many', 'One2many', 'Datetime',
        'Selection', 'Binary')}))
    abstract_model = parent_helper or ParentHelper
    setattr(odoo, 'models', SimpleNamespace(Model=object, AbstractModel=abstract_model,
                                             TransientModel=object))
    exceptions = ModuleType('odoo.exceptions')
    setattr(exceptions, 'UserError', type('UserError', (Exception,), {}))
    setattr(exceptions, 'ValidationError', type('ValidationError', (Exception,), {}))
    tools = ModuleType('odoo.tools')
    setattr(tools, 'ormcache', lambda *_keys: (lambda function: function))
    setattr(tools, 'config', {})
    setattr(odoo, 'tools', tools)
    http = ModuleType('odoo.http')
    setattr(http, 'request', SimpleNamespace())
    setattr(http, 'route', _route)
    setattr(http, 'Controller', type('Controller', (), {}))
    jwt = ModuleType('jwt')
    jwt.InvalidTokenError = type('InvalidTokenError', (Exception,), {})
    psycopg2 = ModuleType('psycopg2')
    psycopg2.IntegrityError = type('IntegrityError', (Exception,), {})
    spec = importlib.util.spec_from_file_location('_isolated_oidc_leaf',
                                                  str(ADDON / relative))
    module = importlib.util.module_from_spec(spec)
    werkzeug = ModuleType('werkzeug')
    setattr(werkzeug, 'url_encode', urlencode)
    with patch.dict(sys.modules, {'odoo': odoo, 'odoo.http': http,
                                 'odoo.exceptions': exceptions, 'odoo.tools': tools,
                                 'werkzeug': werkzeug,
                                 'jwt': jwt, 'psycopg2': psycopg2}):
        spec.loader.exec_module(module)
    return module


def load_controller():
    """Load the controller with isolated Odoo/Werkzeug declarations."""
    odoo = ModuleType('odoo')
    setattr(odoo, 'api', SimpleNamespace(
        model=lambda method: method,
        constrains=lambda *field_names: (lambda method: method),
    ))
    setattr(odoo, 'fields', SimpleNamespace())
    http = ModuleType('odoo.http')
    setattr(http, 'request', SimpleNamespace(env={}))
    setattr(http, 'route', _route)
    setattr(http, 'Controller', type('Controller', (), {}))

    werkzeug = ModuleType('werkzeug')
    utils = ModuleType('werkzeug.utils')
    setattr(utils, 'redirect', lambda url, code=302: StubResponse(status=code))
    exceptions = ModuleType('werkzeug.exceptions')
    setattr(exceptions, 'HTTPException', type('HTTPException', (Exception,), {}))
    setattr(exceptions, 'NotFound', StubNotFound)
    wrappers = ModuleType('werkzeug.wrappers')
    setattr(wrappers, 'Response', StubResponse)
    setattr(werkzeug, 'utils', utils)
    setattr(werkzeug, 'exceptions', exceptions)
    setattr(werkzeug, 'wrappers', wrappers)

    replacements = {
        'odoo': odoo,
        'odoo.http': http,
        'werkzeug': werkzeug,
        'werkzeug.utils': utils,
        'werkzeug.exceptions': exceptions,
        'werkzeug.wrappers': wrappers,
    }
    spec = importlib.util.spec_from_file_location(
        '_isolated_oidc_controller', str(ADDON / 'controllers/main.py')
    )
    if spec is None or spec.loader is None:
        raise ImportError('cannot create controller module spec')
    module = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, replacements):
        spec.loader.exec_module(module)
    return module
