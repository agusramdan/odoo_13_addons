"""Small in-memory doubles; not an Odoo ORM implementation."""
import contextlib
import sys
import types
from unittest.mock import patch

class MockRecordset:
    def __init__(self, records=()): self._records = list(records)
    def __iter__(self): return iter(self._records)
    def __len__(self): return len(self._records)
    def __bool__(self): return bool(self._records)
    def __getitem__(self, index):
        result = self._records[index]
        return MockRecordset(result) if isinstance(index, slice) else result
    @property
    def ids(self): return [r.id for r in self]
    def ensure_one(self):
        if len(self) != 1: raise ValueError('Expected singleton')
        return self._records[0]
    def write(self, values):
        for record in self: record.write(values)
        return True
    def mapped(self, name): return [getattr(r, name) for r in self]
    def filtered(self, fn): return MockRecordset(r for r in self if fn(r))
    def sudo(self): return self
    def with_context(self, **kwargs): return self

class Record:
    def __init__(self, **values): self.__dict__.update(values)
    def write(self, values): self.__dict__.update(values); return True

class MockModel:
    def __init__(self, records=()):
        self.records = list(records)
        self._next_id = max([getattr(r, 'id', 0) for r in self.records] or [0]) + 1
    def create(self, values):
        values = dict(values)
        values.setdefault('id', self._next_id)
        self._next_id = max(self._next_id, values['id'] + 1)
        rec = Record(**values); self.records.append(rec); return rec
    def browse(self, ids):
        ids = [ids] if isinstance(ids, int) else list(ids)
        return MockRecordset(r for r in self.records if r.id in ids)
    def search(self, domain, limit=None):
        def matches(r):
            for term in domain:
                if not isinstance(term, (tuple, list)) or len(term) != 3: raise NotImplementedError('Only AND triplets supported')
                field, op, value = term
                actual = getattr(r, field)
                if op == '=': ok = actual == value
                elif op == '!=': ok = actual != value
                elif op == 'in': ok = actual in value
                elif op == 'not in': ok = actual not in value
                else: raise NotImplementedError('Unsupported operator: ' + op)
                if not ok: return False
            return True
        found = [r for r in self.records if matches(r)]
        return MockRecordset(found if limit is None else found[:limit])
    def sudo(self): return self
    def with_context(self, **kwargs): return self

class MockOdooEnv:
    def __init__(self, models=None, context=None, user=None):
        self.models = dict(models or {}); self.context = dict(context or {}); self.user = user
    def __getitem__(self, name): return self.models[name]
    @property
    def cr(self): raise RuntimeError('Database cursor forbidden in unit tests')
    def ref(self, xmlid): raise NotImplementedError('Stub env.ref explicitly')

class MockFactory:
    @staticmethod
    def record(**values): return Record(**values)
    @staticmethod
    def recordset(*records): return MockRecordset(records)
    @staticmethod
    def model(*records): return MockModel(records)
    @staticmethod
    def env(**models): return MockOdooEnv(models)

def _decorator(*args, **kwargs):
    if len(args) == 1 and callable(args[0]) and not kwargs: return args[0]
    return lambda fn: fn

@contextlib.contextmanager
def odoo_modules():
    """Temporarily install a small import shim; import target modules within scope."""
    odoo = types.ModuleType('odoo'); odoo.__path__ = []
    api = types.ModuleType('odoo.api')
    for name in ('model', 'multi', 'depends', 'constrains', 'onchange', 'returns', 'model_create_multi'):
        setattr(api, name, _decorator)
    fields = types.ModuleType('odoo.fields')
    def field(*args, **kwargs): return None
    for name in ('Char', 'Text', 'Boolean', 'Integer', 'Float', 'Monetary', 'Selection', 'Many2one', 'One2many', 'Many2many', 'Date', 'Datetime', 'Binary', 'Html'):
        setattr(fields, name, field)
    models = types.ModuleType('odoo.models')
    models.Model = type('Model', (), {}); models.TransientModel = type('TransientModel', (), {}); models.AbstractModel = type('AbstractModel', (), {})
    exceptions = types.ModuleType('odoo.exceptions')
    exceptions.UserError = type('UserError', (Exception,), {}); exceptions.ValidationError = type('ValidationError', (Exception,), {})
    http = types.ModuleType('odoo.http'); http.Controller = type('Controller', (), {}); http.route = _decorator; http.request = None
    odoo.api, odoo.fields, odoo.models, odoo.exceptions, odoo.http = api, fields, models, exceptions, http
    with patch.dict(sys.modules, {'odoo': odoo, 'odoo.api': api, 'odoo.fields': fields, 'odoo.models': models, 'odoo.exceptions': exceptions, 'odoo.http': http}):
        yield
