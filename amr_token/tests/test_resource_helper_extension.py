"""Provider-neutrality contract for amr_token."""
import unittest

if __package__:
    from .support import ADDON, load_helper_module
else:
    from support import ADDON, load_helper_module


class TestResourceHelperExtension(unittest.TestCase):
    def setUp(self):
        self.assertTrue((ADDON / "models" / "helper.py").is_file(), "candidate token helper is missing")
        self.module = load_helper_module()

    def test_token_addon_does_not_extend_resource_helper(self):
        self.assertFalse(hasattr(self.module, "ResourceAccessToken"))
        source = (ADDON / "models" / "helper.py").read_text()
        self.assertNotIn("_inherit = 'amr.resource.helper'", source)

    def test_token_generation_remains_on_transitional_token_helper(self):
        self.assertTrue(hasattr(self.module, "TokenHelper"))
        self.assertEqual(self.module.TokenHelper._name, "amr.token.helper")
        self.assertTrue(callable(self.module.TokenHelper.encode))


if __name__ == "__main__":
    unittest.main()
