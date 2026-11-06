import unittest

try:
    import odoo
except ModuleNotFoundError as error:
    if error.name != "odoo":
        raise
    raise unittest.SkipTest("requires Odoo runtime")

from odoo.tests.common import TransactionCase


class TestPublicKeyOwnership(TransactionCase):
    def test_public_key_is_owned_by_amr_oidc_with_orm_contract(self):
        model = self.env.ref("amr_oidc.model_amr_public_key")
        self.assertEqual(model.model, "amr.public.key")
        keys = self.env["amr.public.key"]
        for method in ("_check_public_key", "load_pem_public_key", "get_private_key",
                       "_read_file", "get_jwks", "generate_token", "validate_token",
                       "action_generate_key"):
            self.assertTrue(hasattr(keys, method), method)
