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
    http.route = lambda *args, **kwargs: lambda method: method
    controller = ModuleType('odoo.addons.amr_token.controllers.main')
    controller.ControllerToken = object
    werkzeug = ModuleType('werkzeug')
    werkzeug.utils = SimpleNamespace(redirect=lambda target: target)
    jwt = ModuleType('jwt')
    jwt.InvalidTokenError = type('InvalidTokenError', (Exception,), {})
    psycopg2 = ModuleType('psycopg2')
    psycopg2.IntegrityError = type('IntegrityError', (Exception,), {})
    spec = importlib.util.spec_from_file_location('_isolated_oidc_leaf',
                                                  str(ADDON / relative))
    module = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, {'odoo': odoo, 'odoo.http': http,
                                 'jwt': jwt, 'psycopg2': psycopg2, 'odoo.addons.amr_token.controllers.main': controller, 'werkzeug': werkzeug}):
        spec.loader.exec_module(module)
    return module
