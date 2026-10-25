"""Odoo-native tests only. Offline contract tests run via their standalone runner.

Importing those modules during Odoo discovery resolves their flat ``support``
helper differently and prevents the registry from loading at all.
"""
from ..integration_tests import test_public_key_orm
