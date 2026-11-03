"""Register only Odoo-native integration tests."""
from . import integration
# Odoo 13 scans tests package attributes named test_* (not subpackages).
from .integration import test_service_client_hook
