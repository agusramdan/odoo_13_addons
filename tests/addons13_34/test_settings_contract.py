"""P-03 configuration field and action contract for res.config.settings."""
import unittest
from types import SimpleNamespace
from unittest import mock

from support import ADDON, load_settings_model


class TestResConfigSettingsContract(unittest.TestCase):
    def setUp(self):
        self.assertTrue((ADDON / "models" / "res_config_settings.py").is_file(), "candidate settings model is missing")
        self.module = load_settings_model()
        self.model = self.module.ResConfigSettings

    def test_source_selection_choices_defaults_and_parameters(self):
        algorithm = self.model.amr_token_algorithm
        self.assertEqual({choice[0] for choice in algorithm.args[0]}, {"HS256", "RS256", "ES256"})
        self.assertEqual(algorithm.kwargs["default"], "RS256")
        self.assertEqual(algorithm.kwargs["config_parameter"], "amr_token.algorithm")

        signature = self.model.amr_token_signature_type
        self.assertEqual({choice[0] for choice in signature.args[0]}, {"secret", "public_key"})
        self.assertTrue(signature.kwargs["required"])
        self.assertEqual(signature.kwargs["config_parameter"], "amr_token.signature_type")

        secret_algorithms = self.model.amr_token_secret_algorithm
        self.assertEqual({choice[0] for choice in secret_algorithms.args[0]}, {"HS256", "HS384", "HS512"})
        public_algorithms = self.model.amr_token_public_key_algorithm
        self.assertEqual({choice[0] for choice in public_algorithms.args[0]}, {
            "ES256", "ES256K", "ES384", "ES512", "RS256", "RS384", "RS512", "PS256", "PS384", "PS512",
        })
        self.assertEqual(self.model.amr_token_audience.kwargs["config_parameter"], "database.uuid")

    def test_secret_boolean_computed_from_hs256_algorithm_only(self):
        method = self.model.__dict__.get("_compute_amr_token_using_secret")
        self.assertTrue(callable(method), "candidate secret-mode compute method is missing")
        hmac_record = SimpleNamespace(amr_token_algorithm="HS256", amr_token_using_secret=None)
        rsa_record = SimpleNamespace(amr_token_algorithm="RS256", amr_token_using_secret=None)

        method([hmac_record, rsa_record])

        self.assertTrue(hmac_record.amr_token_using_secret)
        self.assertFalse(rsa_record.amr_token_using_secret)

    def test_create_key_action_delegates_selected_algorithm_to_helper(self):
        action = self.model.__dict__.get("action_create_public_key")
        self.assertTrue(callable(action), "candidate create-key settings action is missing")
        helper = mock.Mock()
        helper.sudo.return_value = helper
        settings = SimpleNamespace(
            env={"amr.token.helper": helper},
            amr_token_public_key_algorithm="ES256",
        )

        action(settings)

        helper.sudo.assert_called_once_with()
        helper.create_public_key.assert_called_once_with("ES256")


if __name__ == "__main__":
    unittest.main()
