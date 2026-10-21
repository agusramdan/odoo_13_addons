"""P-03 field/default/selection contract on the candidate model."""
import unittest

from support import ADDON, load_public_key_model


class TestPublicKeyFieldContract(unittest.TestCase):
    def test_model_declares_source_field_contract(self):
        model_path = ADDON / "models" / "public_key.py"
        self.assertTrue(model_path.is_file(), "candidate public-key model is missing")
        model = load_public_key_model().PublicKey

        self.assertEqual(model._name, "amr.public.key")
        self.assertEqual(model._description, "OIDC JWKS Key")
        self.assertEqual(model.name.kind, "Char")
        self.assertFalse(model.name.kwargs.get("required", False))
        self.assertEqual(model.kid.kwargs, {"required": True, "index": True})
        self.assertEqual(model.source.kind, "Selection")
        self.assertEqual(model.source.kwargs.get("required"), True)
        self.assertEqual(model.source.kwargs.get("default"), "database")
        self.assertEqual(
            [value for value, _label in model.source.args[0]],
            [
                "database", "hsm", "file_path", "env_pem", "env_path",
                "config_path", "config_pem", "system_parameter_pem",
                "system_parameter_path",
            ],
        )
        self.assertEqual(model.algorithm.kwargs.get("default"), "RS256")
        self.assertEqual(
            [value for value, _label in model.algorithm.args[0]],
            ["ES256", "ES256K", "ES384", "ES512", "RS256", "RS384", "RS512", "PS256", "PS384", "PS512"],
        )
        self.assertEqual(model.public_key.kind, "Text")
        self.assertEqual(model.public_key.kwargs.get("required"), True)
        self.assertEqual(model.private_key.kind, "Text")
        self.assertEqual(model.active.kwargs.get("default"), True)
        self.assertEqual(model.is_signing.kwargs.get("default"), False)
        self.assertEqual(model.created_at.kind, "Datetime")
        self.assertEqual(model.expires_at.kind, "Datetime")


if __name__ == "__main__":
    unittest.main()
