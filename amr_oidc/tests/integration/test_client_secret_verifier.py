# -*- coding: utf-8 -*-
"""Behavioral ORM checks for protected OIDC client-secret verifiers."""
import base64
import unittest

try:
    import odoo
except ModuleNotFoundError as error:
    if error.name != "odoo":
        raise
    raise unittest.SkipTest("Odoo unavailable; native ORM tests NOT RUN")

from odoo.exceptions import AccessError
from odoo.tests.common import SavepointCase


class TestClientSecretVerifier(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestClientSecretVerifier, cls).setUpClass()
        cls.client = cls.env["oidc.client"].create({"client_id": "secret-verifier-client"})
        cls.secret = "synthetic-client-secret"
        ctx = cls.env["res.users"]._crypt_context()
        cls.verifier = ctx.hash(cls.secret)
        if "client_secret_hash" in cls.client._fields:
            cls.client.sudo().write({"client_secret_hash": cls.verifier})

    def test_secret_is_stored_and_verified_only_as_restricted_hash(self):
        Client = self.env["oidc.client"]
        self.assertNotIn("client_secret", Client._fields)
        field = Client._fields["client_secret_hash"]
        self.assertEqual(field.groups, "amr_oidc.group_provider_admin")
        self.assertTrue(self.client.check_credentials(self.secret))
        with self.assertRaises(ValueError):
            self.client.check_credentials("wrong-secret")
        with self.assertRaises(ValueError):
            self.client.check_credentials("")
        self.client.sudo().write({"client_secret_hash": self.secret})
        with self.assertRaises(ValueError):
            self.client.check_credentials(self.secret)

    def test_copy_does_not_copy_secret_verifier(self):
        copied = self.client.copy({"client_id": "secret-verifier-client-copy"})
        self.assertFalse(copied.client_secret_hash)

    def test_client_auth_rejects_inactive_client(self):
        self.client.write({"active": False})
        token = base64.b64encode(("secret-verifier-client:" + self.secret).encode()).decode()
        self.assertFalse(self.env["oidc.client"].with_context(active_test=False).client_auth(token))

    def test_ordinary_user_can_read_client_but_not_verifier(self):
        user = self.env["res.users"].create({
            "name": "Verifier ordinary user", "login": "verifier-ordinary",
            "groups_id": [(6, 0, [self.env.ref("base.group_user").id])],
        })
        client = self.client.with_user(user)
        self.assertEqual(client.read(["client_id"])[0]["client_id"], "secret-verifier-client")
        with self.assertRaises(AccessError):
            client.read(["client_secret_hash"])

    def test_client_auth_accepts_hash_and_rejects_wrong_secret(self):
        token = base64.b64encode(("secret-verifier-client:" + self.secret).encode()).decode()
        wrong = base64.b64encode(b"secret-verifier-client:wrong-secret").decode()
        self.assertEqual(self.env["oidc.client"].client_auth(token), self.client)
        self.assertFalse(self.env["oidc.client"].client_auth(wrong))
