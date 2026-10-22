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
        return (grant_type, kwargs)


def load(relative):
    """Load only one leaf module with inert fields and no external libraries."""
    odoo = ModuleType('odoo')
    odoo.api = SimpleNamespace(model=lambda method: method)
    odoo.fields = SimpleNamespace(**{name: Field for name in (
        'Boolean', 'Char', 'Text', 'Many2one', 'One2many', 'Datetime',
        'Selection', 'Binary')})
    odoo.models = SimpleNamespace(Model=object, AbstractModel=ParentHelper,
                                  TransientModel=object)
    http = ModuleType('odoo.http')
    http.request = SimpleNamespace()
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


def load_controller():
    """Load the controller with inert route/base-class doubles, not Odoo."""
    odoo = ModuleType('odoo')
    odoo.__path__ = []
    setattr(odoo, 'api', SimpleNamespace(model=lambda method: method))

    http = ModuleType('odoo.http')
    setattr(http, 'request', SimpleNamespace())

    def route(*args, **kwargs):
        def decorate(method):
            method.route_args = args
            method.route_kwargs = kwargs
            return method
        return decorate

    setattr(http, 'route', route)

    addons = ModuleType('odoo.addons')
    addons.__path__ = []
    token_addon = ModuleType('odoo.addons.amr_token')
    token_addon.__path__ = []
    token_controllers = ModuleType('odoo.addons.amr_token.controllers')
    token_controllers.__path__ = []
    token_main = ModuleType('odoo.addons.amr_token.controllers.main')

    class ControllerToken:
        def invalid_response(self, status, error):
            return {"status": status, "error": error}

        def make_response(self, **payload):
            return payload

    setattr(token_main, 'ControllerToken', ControllerToken)

    werkzeug = ModuleType('werkzeug')
    werkzeug.__path__ = []
    setattr(werkzeug, 'utils', SimpleNamespace(redirect=lambda target: {"redirect": target}))
    modules = {
        'odoo': odoo,
        'odoo.http': http,
        'odoo.addons': addons,
        'odoo.addons.amr_token': token_addon,
        'odoo.addons.amr_token.controllers': token_controllers,
        'odoo.addons.amr_token.controllers.main': token_main,
        'werkzeug': werkzeug,
    }
    spec = importlib.util.spec_from_file_location(
        '_isolated_oidc_controller', str(ADDON / "controllers/main.py")
    )
    if spec is None or spec.loader is None:
        raise ImportError("Unable to load isolated OIDC controller")
    module = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, modules):
        spec.loader.exec_module(module)
    return module
