"""P-05 file-source helper contract with temporary synthetic text only."""
import pathlib
import tempfile
import unittest
from types import SimpleNamespace

from support import load_public_key_model


class TestPrivateFileRead(unittest.TestCase):
    def test_read_file_returns_text_from_configured_path(self):
        model = load_public_key_model().PublicKey
        self.assertTrue(callable(getattr(model, "_read_file", None)), "candidate private-file reader is missing")
        marker = "SYNTHETIC-NOT-KEY-MATERIAL"
        with tempfile.TemporaryDirectory(prefix="amr-token-test-") as directory:
            path = pathlib.Path(directory) / "synthetic.txt"
            path.write_text(marker, encoding="utf-8")
            result = model._read_file(SimpleNamespace(), str(path))

        self.assertEqual(result, marker)

    def test_read_file_rejects_missing_path(self):
        module = load_public_key_model()
        self.assertTrue(callable(getattr(module.PublicKey, "_read_file", None)), "candidate private-file reader is missing")

        with self.assertRaisesRegex(ValueError, "Private key path not configured"):
            module.PublicKey._read_file(SimpleNamespace(), "")


if __name__ == "__main__":
    unittest.main()
