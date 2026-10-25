# -*- coding: utf-8 -*-
"""Registration and secret issuance contract for confidential OIDC clients."""
import unittest

try:
    import odoo
except ModuleNotFoundError as error:
    if error.name != "odoo":
        raise
    raise unittest.SkipTest("Odoo unavailable; native ORM tests NOT RUN")

from odoo.tests.common import SavepointCase


class TestClientRegistration(SavepointCase):
    def test_new_client_defaults_confidential_true(self):
        client = self.env["oidc.client"].create({"client_id": "registration-defaults"})
        self.assertTrue(getattr(client, "is_confidential", False))
