# -*- coding: utf-8 -*-
"""Registration and secret issuance contract for confidential OIDC clients."""
import unittest

try:
    import odoo
except ModuleNotFoundError as error:
    if error.name != "odoo":
        raise
    raise unittest.SkipTest("Odoo unavailable; native ORM tests NOT RUN")

from odoo.exceptions import AccessError
from odoo.tests.common import SavepointCase


class TestClientRegistration(SavepointCase):
    def test_new_client_defaults_confidential_true(self):
        client = self.env["oidc.client"].create({"client_id": "registration-defaults"})
        self.assertTrue(getattr(client, "is_confidential", False))

    def test_copy_does_not_copy_allowed_grants(self):
        self.assertIn("oidc.client.grant", self.env.registry.models)
        Client = self.env["oidc.client"]
        grants = self.env["oidc.client.grant"].search([("code", "=", "client_credentials")])
        client = Client.create({"client_id": "registration-grants-copy-source"})
        client.allowed_grants = [(6, 0, grants.ids)]

        copied = client.copy({"client_id": "registration-grants-copy-target"})

        self.assertFalse(copied.allowed_grants)

    def test_allowed_grants_default_and_supported_subset(self):
        Client = self.env["oidc.client"]
        self.assertIn("allowed_grants", Client._fields)
        self.assertIn("oidc.client.grant", self.env.registry.models)
        grants = self.env["oidc.client.grant"].search([])
        self.assertEqual(set(grants.mapped("code")), {
            "client_credentials", "authorization_code", "refresh_token",
        })
        client = Client.create({"client_id": "registration-grants-default"})
        self.assertFalse(client.allowed_grants)
        selected = grants.filtered(lambda grant: grant.code in {
            "client_credentials", "refresh_token",
        })
        client.allowed_grants = [(6, 0, selected.ids)]
        self.assertEqual(set(client.allowed_grants.mapped("code")), {
            "client_credentials", "refresh_token",
        })

    def test_grant_catalog_is_read_only_to_users(self):
        self.assertIn("oidc.client.grant", self.env.registry.models)
        Grant = self.env["oidc.client.grant"]
        user = self.env["res.users"].create({
            "name": "Grant Reader", "login": "grant-reader",
            "groups_id": [(6, 0, [self.env.ref("base.group_user").id])],
        })
        grants = Grant.with_user(user).search([])
        self.assertEqual(len(grants), 3)
        with self.assertRaises(AccessError):
            grants[0].with_user(user).write({"name": "changed"})
        with self.assertRaises(AccessError):
            grants[0].with_user(user).unlink()

    def test_grant_catalog_create_is_denied_to_users(self):
        self.assertIn("oidc.client.grant", self.env.registry.models)
        Grant = self.env["oidc.client.grant"]
        seeded = Grant.search([("code", "=", "refresh_token")])
        self.assertEqual(len(seeded), 1)
        seeded.sudo().unlink()
        user = self.env["res.users"].create({
            "name": "Grant Creator", "login": "grant-creator",
            "groups_id": [(6, 0, [self.env.ref("base.group_user").id])],
        })
        with self.assertRaises(AccessError):
            Grant.with_user(user).create({"code": "refresh_token", "name": "Refresh Token"})

    def test_grants_are_provider_admin_only_on_client(self):
        self.assertIn("oidc.client.grant", self.env.registry.models)
        Client = self.env["oidc.client"]
        user = self.env["res.users"].create({
            "name": "Grant Reader 2", "login": "grant-reader-2",
            "groups_id": [(6, 0, [self.env.ref("base.group_user").id])],
        })
        client = Client.create({"client_id": "registration-grant-acl"})
        with self.assertRaises(AccessError):
            client.with_user(user).read(["allowed_grants"])
        admin_group = self.env.ref("amr_oidc.group_provider_admin")
        admin = self.env["res.users"].create({
            "name": "Provider Admin", "login": "grant-provider-admin",
            "groups_id": [(6, 0, [self.env.ref("base.group_user").id, admin_group.id])],
        })
        grants = self.env["oidc.client.grant"].search([("code", "in", [
            "client_credentials", "authorization_code",
        ])])
        client.with_user(admin).write({"allowed_grants": [(6, 0, grants.ids)]})
        self.assertEqual(set(client.with_user(admin).allowed_grants.mapped("code")), {
            "client_credentials", "authorization_code",
        })

    def test_unsupported_grant_code_is_rejected_by_orm(self):
        self.assertIn("oidc.client.grant", self.env.registry.models)
        with self.assertRaises(ValueError):
            self.env["oidc.client.grant"].create({"code": "password", "name": "Password"})
