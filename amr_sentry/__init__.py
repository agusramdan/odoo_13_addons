
from . import services

try:
    from . import models
    try:
        from . import tests
    except ModuleNotFoundError as exc:
        if exc.name != 'odoo.tests':
            raise
except ModuleNotFoundError as exc:
    if exc.name != 'odoo':
        raise
