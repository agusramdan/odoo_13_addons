
from . import services

try:
    from . import models
except ModuleNotFoundError as exc:
    if exc.name != 'odoo':
        raise
