import importlib
import os
import tempfile
import unittest
from unittest.mock import patch


class TestSentryConfig(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config_module = importlib.import_module("amr_sentry.services.config")
        cls.load_config = staticmethod(cls.config_module.load_config)
        cls.config_error = cls.config_module.SentryConfigError

    def test_yaml_override_maps_sentry_kwargs_and_policy(self):
        with tempfile.NamedTemporaryFile(suffix=".yaml", mode="w", encoding="utf-8") as config:
            config.write("sentry:\n  dsn: marker\nservice_client:\n  enabled: true\n  mode: error\n")
            config.flush()
            with patch.dict(os.environ, {"AMR_SENTRY_CONFIG": config.name}):
                try:
                    actual = self.load_config()
                except self.config_error as error:
                    self.fail("Valid YAML configuration should load: {}".format(error))
        sentry, policy = actual
        self.assertEqual(sentry, {"dsn": "marker"})
        self.assertEqual(policy, {"enabled": True, "mode": "error"})

    def test_json_override_maps_configuration(self):
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", encoding="utf-8") as config:
            config.write('{"sentry":{"sample_rate":0.25},"service_client":{}}')
            config.flush()
            with patch.dict(os.environ, {"AMR_SENTRY_CONFIG": config.name}):
                try:
                    actual = self.load_config()
                except self.config_error as error:
                    self.fail("JSON configuration should be accepted: {}".format(error))
        self.assertEqual(actual, ({"sample_rate": 0.25}, {"enabled": False, "mode": "none"}))

    def test_empty_environment_uses_default_path(self):
        with tempfile.NamedTemporaryFile(suffix=".yaml", mode="w", encoding="utf-8") as config:
            config.write("sentry: {}\nservice_client: {}\n")
            config.flush()
            with patch.dict(os.environ, {"AMR_SENTRY_CONFIG": ""}), patch.object(
                self.config_module, "DEFAULT_CONFIG_PATH", config.name
            ):
                try:
                    actual = self.load_config()
                except self.config_error as error:
                    self.fail("Empty environment should select the default file: {}".format(error))
                self.assertEqual(actual, ({}, {"enabled": False, "mode": "none"}))

    def test_invalid_service_client_policy_is_rejected(self):
        with tempfile.NamedTemporaryFile(suffix=".yaml", mode="w", encoding="utf-8") as config:
            config.write("sentry: {}\nservice_client:\n  enabled: 'true'\n")
            config.flush()
            with patch.dict(os.environ, {"AMR_SENTRY_CONFIG": config.name}):
                with self.assertRaises(self.config_error):
                    self.load_config()


if __name__ == "__main__":
    unittest.main()
