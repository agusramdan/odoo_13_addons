"""Local/remote delegation contract for the amr.resource.helper extension."""
import unittest
from unittest import mock

from support import ADDON, load_helper_module


class TestResourceHelperExtension(unittest.TestCase):
    def setUp(self):
        self.assertTrue((ADDON / "models" / "helper.py").is_file(), "candidate token helper is missing")
        self.module = load_helper_module()
        self.assertTrue(hasattr(self.module, "ResourceAccessToken"), "candidate ResourceAccessToken extension is missing")
        self.resource = object.__new__(self.module.ResourceAccessToken)
        self.helper = mock.Mock()
        self.resource.env = {"amr.token.helper": self.helper}
        self.resource.is_local_token = mock.Mock(return_value=True)

    def test_local_introspection_uses_local_helper_validation(self):
        self.helper.validate.return_value = {"active": True}
        result = self.resource.introspect_token("local-token", audience="client")

        self.assertEqual(result, {"active": True})
        self.helper.validate.assert_called_once_with("local-token")

    def test_remote_introspection_delegates_to_resource_helper(self):
        self.resource.is_local_token.return_value = False

        result = self.resource.introspect_token("remote-token", audience="client")

        self.assertEqual(result, {
            "via": "base.introspect_token",
            "token": "remote-token",
            "kwargs": {"audience": "client"},
        })
        self.helper.validate.assert_not_called()

    def test_local_validate_uses_local_helper_and_remote_validate_delegates(self):
        self.helper.validate.return_value = {"sub": "local"}
        self.assertEqual(self.resource.validate("local-token"), {"sub": "local"})
        self.helper.validate.assert_called_once_with("local-token")

        self.resource.is_local_token.return_value = False
        self.assertEqual(self.resource.validate("remote-token"), {
            "via": "base.validate", "token": "remote-token",
        })

    def test_local_decode_uses_local_helper_and_remote_decode_delegates(self):
        self.helper.decode.return_value = {"sub": "local"}
        self.assertEqual(self.resource.decode("local-token", audience="client"), {"sub": "local"})
        self.helper.decode.assert_called_once_with("local-token", audience="client")

        self.resource.is_local_token.return_value = False
        self.assertEqual(self.resource.decode("remote-token", audience="client"), {
            "via": "base.decode", "token": "remote-token", "kwargs": {"audience": "client"},
        })

    def test_encode_always_uses_local_helper(self):
        self.helper.encode.return_value = "synthetic-encoded"

        result = self.resource.encode(algorithm="RS256", sub="user")

        self.assertEqual(result, "synthetic-encoded")
        self.helper.encode.assert_called_once_with(algorithm="RS256", sub="user")
        self.resource.is_local_token.assert_not_called()


if __name__ == "__main__":
    unittest.main()
