# -*- coding: utf-8 -*-
"""ORM identity constraints for OIDC clients."""
import unittest

try:
    import odoo
except ModuleNotFoundError as error:
    if error.name != "odoo":
        raise
    raise unittest.SkipTest("Odoo unavailable; native ORM tests NOT RUN")

from psycopg2 import IntegrityError

from odoo.exceptions import ValidationError
from odoo.tests.common import SavepointCase


class TestOidcClientIdentity(SavepointCase):
    def test_missing_and_blank_client_id_are_rejected(self):
        for value in (None, ""):
            with self.subTest(value=value), self.assertRaises((ValidationError, IntegrityError)), self.cr.savepoint():
                self.env["oidc.client"].create({"client_id": value})

    def test_duplicate_client_id_is_rejected(self):
        self.env["oidc.client"].create({"client_id": "identity-duplicate"})
        with self.assertRaises(IntegrityError), self.cr.savepoint():
            self.env["oidc.client"].create({"client_id": "identity-duplicate"})

    def test_duplicate_client_id_is_rejected_when_existing_client_archived(self):
        client = self.env["oidc.client"].create({"client_id": "identity-archived"})
        client.write({"active": False})
        with self.assertRaises(IntegrityError), self.cr.savepoint():
            self.env["oidc.client"].create({"client_id": "identity-archived"})
