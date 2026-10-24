"""Offline source loader and minimal Odoo doubles for ADDONS13-29 characterization."""
import importlib.util, pathlib, sys, types, unittest
ROOT = pathlib.Path(__file__).resolve().parents[2]
ADDON = ROOT / 'amr_service_client'

def _deny_external(*args, **kwargs):
    raise AssertionError('unexpected offline boundary')

class _RequestException(Exception):
    def __init__(self, *args, response=None, **kwargs):
        self.response = response
        super().__init__(*args)

class _RequestTimeout(_RequestException): pass
class _RequestConnectionError(_RequestException): pass
class _RequestHTTPError(_RequestException): pass

_requests = types.ModuleType('requests')
_request_exceptions = types.ModuleType('requests.exceptions')
_request_exceptions.RequestException = _RequestException
_request_exceptions.Timeout = _RequestTimeout
_request_exceptions.ConnectionError = _RequestConnectionError
_request_exceptions.HTTPError = _RequestHTTPError
class _Session:
    request = _deny_external
    send = _deny_external
_requests.RequestException = _RequestException
_requests.Timeout = _RequestTimeout
_requests.ConnectionError = _RequestConnectionError
_requests.HTTPError = _RequestHTTPError
_requests.exceptions = _request_exceptions
_requests.Session = _Session
_requests.request = _deny_external
_requests.post = _deny_external

class _JWTDecodeError(Exception): pass
_jwt = types.ModuleType('jwt')
_jwt.DecodeError = _JWTDecodeError
_jwt.encode = _deny_external
_jwt.decode = _deny_external

def install_external_stubs():
    sys.modules.update({'requests': _requests, 'requests.exceptions': _request_exceptions, 'jwt': _jwt})

install_external_stubs()

class _API:
    def model(self, fn): return fn
    def constrains(self, *a): return lambda fn: fn
    def depends(self, *a): return lambda fn: fn
    def onchange(self, *a): return lambda fn: fn
api = _API()
class _Model: pass
class _Field:
    def __call__(self, *a, **kw): return None
fields = types.SimpleNamespace(**{n:_Field() for n in ('Boolean','Char','Many2one','One2many','Text','Selection','Integer','Float','Date','Datetime','Binary','Json')})
fields.Datetime = types.SimpleNamespace(to_string=lambda x:x.isoformat())
fields.Date = types.SimpleNamespace(to_string=lambda x:x.isoformat())

def _ormcache(*a): return lambda fn: fn
tools = types.SimpleNamespace(ormcache=_ormcache, timedelta=__import__('datetime').timedelta)
config = types.SimpleNamespace(get=lambda k: None)
class UserError(Exception): pass
class ValidationError(Exception): pass
class AccessError(Exception): pass

def install_odoo_stubs():
    install_external_stubs()
    odoo = types.ModuleType('odoo'); odoo.api=api; odoo.models=types.SimpleNamespace(Model=_Model, AbstractModel=_Model, TransientModel=_Model); odoo.fields=fields; odoo.tools=tools
    exc=types.ModuleType('odoo.exceptions'); exc.UserError=UserError; exc.ValidationError=ValidationError; exc.AccessError=AccessError
    ot=types.ModuleType('odoo.tools'); ot.config=config; ot.ormcache=_ormcache; ot.timedelta=tools.timedelta
    se=types.ModuleType('odoo.tools.safe_eval'); se.safe_eval=lambda *a,**k: None; se.test_python_expr=lambda *a,**k: None
    of=types.ModuleType('odoo.fields'); of.Datetime=fields.Datetime; of.Date=fields.Date
    odoo.exceptions=exc; odoo.fields=fields; odoo.tools=ot
    sys.modules.update({'odoo':odoo,'odoo.exceptions':exc,'odoo.tools':ot,'odoo.tools.safe_eval':se,'odoo.fields':of})
    # Package shells only; never execute addon __init__.
    for name, path in [('amr_service_client',ADDON),('amr_service_client.services',ADDON/'services'),('amr_service_client.models',ADDON/'models')]:
        pkg=types.ModuleType(name); pkg.__path__=[str(path)]; sys.modules[name]=pkg

def load(rel, name=None):
    install_odoo_stubs()
    path=ADDON/rel; modname=name or ('amr_service_client.'+rel.replace('/','.').removesuffix('.py'))
    spec=importlib.util.spec_from_file_location(modname,path); module=importlib.util.module_from_spec(spec); sys.modules[modname]=module; spec.loader.exec_module(module); return module

class OfflineCase(unittest.TestCase):
    def setUp(self):
        # Fail closed on network, file-open, and process-environment boundaries.
        import socket, builtins, os, urllib.request, http.client
        import requests
        def denied(*a, **k):
            raise AssertionError('unexpected offline boundary')
        targets = [
            (socket, 'socket'), (socket, 'create_connection'),
            (socket, 'getaddrinfo'), (socket, 'gethostbyname'),
            (socket, 'gethostbyname_ex'), (socket, 'gethostbyaddr'),
            (urllib.request, 'urlopen'),
            (http.client.HTTPConnection, 'connect'),
            (http.client.HTTPSConnection, 'connect'),
            (requests, 'request'), (requests, 'post'),
            (requests.Session, 'request'), (requests.Session, 'send'),
            (builtins, 'open'), (os, 'getenv'),
        ]
        if hasattr(socket, 'create_server'):
            targets.append((socket, 'create_server'))
        self._originals = [(obj, name, getattr(obj, name)) for obj, name in targets]
        for obj, name, _ in self._originals:
            setattr(obj, name, denied)

    def tearDown(self):
        for obj, name, value in reversed(self._originals):
            setattr(obj, name, value)
