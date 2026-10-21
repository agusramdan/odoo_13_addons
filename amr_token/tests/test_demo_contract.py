"""P-08 synthetic public-only fixture; no Odoo install/publication evidence."""
import unittest
import xml.etree.ElementTree as ET
from types import SimpleNamespace
from unittest import mock

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

if __package__:
    from .support import ADDON, load_public_key_model
else:
    from support import ADDON, load_public_key_model


class TestDemoContract(unittest.TestCase):
    def test_demo_is_valid_inactive_public_only_and_excluded_by_source_filter(self):
        path = ADDON / "demo/public_key_demo.xml"
        self.assertTrue(path.is_file(), "missing synthetic public-only demo fixture")
        root = ET.parse(path).getroot()
        self.assertEqual(root.tag, "odoo")
        self.assertEqual(root.attrib, {"noupdate": "1"})
        self.assertEqual(len(root), 1)
        record = root[0]
        self.assertEqual(record.tag, "record")
        self.assertEqual(record.attrib, {"id": "demo_public_key_inactive", "model": "amr.public.key"})
        fields = {field.get("name"): field for field in record}
        self.assertEqual(len(record), len(fields))
        self.assertEqual(set(fields), {"name", "kid", "source", "algorithm", "public_key", "active", "is_signing"})
        self.assertEqual(fields["name"].text, "Synthetic public-only demo (inactive)")
        self.assertEqual(fields["kid"].text, "synthetic-demo-not-for-signing")
        self.assertEqual(fields["source"].text, "database")
        self.assertEqual(fields["algorithm"].text, "RS256")
        for name in ("active", "is_signing"):
            self.assertEqual(fields[name].attrib, {"name": name, "eval": "False"})
            self.assertIsNone(fields[name].text)
        pem = fields["public_key"].text
        assert pem is not None, "demo public PEM is missing"
        public = serialization.load_pem_public_key(pem.encode("ascii"))
        assert isinstance(public, rsa.RSAPublicKey), "demo key must be RSA"
        self.assertEqual(public.key_size, 2048)
        self.assertNotIn("PRIVATE", path.read_text())
        model = load_public_key_model().PublicKey
        synthetic = SimpleNamespace(public_key=pem, active=False, is_signing=False)
        model._check_public_key([synthetic])
        records = SimpleNamespace(search=mock.Mock(side_effect=lambda domain: [synthetic] if synthetic.active else []))
        self.assertEqual(model.get_jwks(records), [])
        records.search.assert_called_once_with([("active", "=", True)])
