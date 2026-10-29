"""Narrow import doubles: declarations and parent delegation, never Odoo boot."""
import importlib.util
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
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
        self.headers = kwargs.get('headers', {})


class StubNotFound(Exception):
    code = 404
    description = "Not Found"


class StubHTTPException(Exception):
    def __init__(self, message, response=None):
        super().__init__(message)
        self.response = response


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
    with patch.dict(sys.modules, {'odoo': odoo, 'odoo.http': http,
                                 'jwt': jwt, 'psycopg2': psycopg2}):
        spec.loader.exec_module(module)
    return module


def load_amr_token_parent_helper():
    """Load the base helper through its offline test doubles, not Odoo boot."""
    support_path = ADDON.parent / 'amr_token' / 'tests' / 'support.py'
    spec = importlib.util.spec_from_file_location(
        '_amr_token_offline_support', str(support_path)
    )
    if spec is None or spec.loader is None:
        raise ImportError('cannot create amr_token test support spec')
    support = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(support)
    jwt = ModuleType('jwt')
    setattr(jwt, 'InvalidTokenError', type('InvalidTokenError', (Exception,), {}))
    with patch.dict(sys.modules, {'jwt': jwt}):
        return support.load_helper_module().TokenHelper


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

    addons = ModuleType('odoo.addons')
    setattr(addons, '__path__', [])
    amr_token = ModuleType('odoo.addons.amr_token')
    setattr(amr_token, '__path__', [])
    controllers = ModuleType('odoo.addons.amr_token.controllers')
    setattr(controllers, '__path__', [])
    parent_spec = importlib.util.spec_from_file_location(
        'odoo.addons.amr_token.controllers.main',
        str(ADDON.parent / 'amr_token/controllers/main.py'),
    )
    if parent_spec is None or parent_spec.loader is None:
        raise ImportError('cannot create parent controller module spec')
    parent_controller = importlib.util.module_from_spec(parent_spec)

    werkzeug = ModuleType('werkzeug')
    utils = ModuleType('werkzeug.utils')
    setattr(utils, 'redirect', lambda url, code=302: StubResponse(status=code))
    exceptions = ModuleType('werkzeug.exceptions')
    setattr(exceptions, 'HTTPException', StubHTTPException)
    setattr(exceptions, 'NotFound', StubNotFound)
    wrappers = ModuleType('werkzeug.wrappers')
    setattr(wrappers, 'Response', StubResponse)
    setattr(werkzeug, 'utils', utils)
    setattr(werkzeug, 'exceptions', exceptions)
    setattr(werkzeug, 'wrappers', wrappers)

    replacements = {
        'odoo': odoo,
        'odoo.http': http,
        'odoo.addons': addons,
        'odoo.addons.amr_token': amr_token,
        'odoo.addons.amr_token.controllers': controllers,
        'odoo.addons.amr_token.controllers.main': parent_controller,
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
        parent_spec.loader.exec_module(parent_controller)
        spec.loader.exec_module(module)
    return module
