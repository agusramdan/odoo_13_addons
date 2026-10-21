"""P-05 characterization of private-key source lookup; no real keys are used."""
import os
import pathlib
import tempfile
import unittest
from unittest import mock

from support import load_public_key_model

MARKER = "SYNTHETIC-NOT-KEY-MATERIAL"


class _Parameters:
    def __init__(self, values):
        self.values = values

    def sudo(self):
        return self

    def get_param(self, name):
        return self.values.get(name)


def _record(model, source, reference=None, *, private_key=MARKER, params=None):
    instance = object.__new__(model)
    instance.source = source
    instance.reference = reference
    instance.private_key = private_key
    instance.env = {"ir.config_parameter": params or _Parameters({})}
    return instance


class TestPrivateKeySourceLookup(unittest.TestCase):
    def _model(self):
        module = load_public_key_model()
        self.assertTrue(callable(getattr(module.PublicKey, "get_private_key", None)), "candidate private-key source lookup is missing")
        return module

    def test_database_source_returns_model_field(self):
        module = self._model()
        record = _record(module.PublicKey, "database")
        self.assertEqual(module.PublicKey.get_private_key(record), MARKER)

    def test_env_pem_source_reads_named_environment_value(self):
        module = self._model()
        record = _record(module.PublicKey, "env_pem", "AMR_TOKEN_TEST_PEM")
        with mock.patch.dict(os.environ, {"AMR_TOKEN_TEST_PEM": MARKER}):
            self.assertEqual(module.PublicKey.get_private_key(record), MARKER)

    def test_config_pem_source_reads_named_config_value(self):
        module = self._model()
        record = _record(module.PublicKey, "config_pem", "test.private.pem")
        with mock.patch.object(module.config, "get", return_value=MARKER):
            self.assertEqual(module.PublicKey.get_private_key(record), MARKER)

    def test_system_parameter_pem_source_reads_parameter(self):
        module = self._model()
        record = _record(
            module.PublicKey, "system_parameter_pem", "test.private.pem",
            params=_Parameters({"test.private.pem": MARKER}),
        )
        self.assertEqual(module.PublicKey.get_private_key(record), MARKER)

    def test_file_path_source_reads_reference_path(self):
        module = self._model()
        with tempfile.TemporaryDirectory(prefix="amr-token-test-") as directory:
            path = pathlib.Path(directory) / "synthetic.txt"
            path.write_text(MARKER, encoding="utf-8")
            record = _record(module.PublicKey, "file_path", str(path))
            self.assertEqual(module.PublicKey.get_private_key(record), MARKER)

    def test_env_path_source_reads_file_named_by_environment(self):
        module = self._model()
        with tempfile.TemporaryDirectory(prefix="amr-token-test-") as directory:
            path = pathlib.Path(directory) / "synthetic.txt"
            path.write_text(MARKER, encoding="utf-8")
            record = _record(module.PublicKey, "env_path", "AMR_TOKEN_TEST_PATH")
            with mock.patch.dict(os.environ, {"AMR_TOKEN_TEST_PATH": str(path)}):
                self.assertEqual(module.PublicKey.get_private_key(record), MARKER)

    def test_config_path_source_reads_configured_file(self):
        module = self._model()
        with tempfile.TemporaryDirectory(prefix="amr-token-test-") as directory:
            path = pathlib.Path(directory) / "synthetic.txt"
            path.write_text(MARKER, encoding="utf-8")
            record = _record(module.PublicKey, "config_path", "test.private.path")
            with mock.patch.object(module.config, "get", return_value=str(path)):
                self.assertEqual(module.PublicKey.get_private_key(record), MARKER)

    def test_system_parameter_path_source_reads_parameter_file(self):
        module = self._model()
        with tempfile.TemporaryDirectory(prefix="amr-token-test-") as directory:
            path = pathlib.Path(directory) / "synthetic.txt"
            path.write_text(MARKER, encoding="utf-8")
            record = _record(
                module.PublicKey, "system_parameter_path", "test.private.path",
                params=_Parameters({"test.private.path": str(path)}),
            )
            self.assertEqual(module.PublicKey.get_private_key(record), MARKER)

    def test_hsm_source_remains_unsupported(self):
        module = self._model()
        record = _record(module.PublicKey, "hsm", "hsm-key-id")
        with self.assertRaisesRegex(ValueError, "Unsupported source: hsm"):
            module.PublicKey.get_private_key(record)


if __name__ == "__main__":
    unittest.main()
