"""P-06 key-generation action delegates to helper and omits its source selector."""
import unittest
from types import SimpleNamespace
from unittest import mock

if __package__:
    from .support import load_public_key_model
else:
    from support import load_public_key_model


class TestGenerateKeyAction(unittest.TestCase):
    def test_action_writes_helper_payload_without_source(self):
        model = load_public_key_model().PublicKey
        self.assertTrue(callable(getattr(model, "action_generate_key", None)), "candidate key-generation action is missing")
        helper = mock.Mock()
        helper.generate_key.return_value = {
            "kid": "synthetic-kid",
            "algorithm": "RS256",
            "private_key": "SYNTHETIC-NOT-KEY-MATERIAL",
            "source": "database",
        }
        record = SimpleNamespace(
            env={"amr.token.helper": helper},
            algorithm="RS256",
            write=mock.Mock(),
        )

        model.action_generate_key(record)

        helper.generate_key.assert_called_once_with("RS256")
        record.write.assert_called_once_with({
            "kid": "synthetic-kid",
            "algorithm": "RS256",
            "private_key": "SYNTHETIC-NOT-KEY-MATERIAL",
        })


if __name__ == "__main__":
    unittest.main()
