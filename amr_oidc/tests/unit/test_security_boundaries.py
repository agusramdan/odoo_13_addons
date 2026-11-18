"""Negative security characterizations for controller and issuer boundaries.

These assertions intentionally express the security contract, not current
implementation behavior. A failure is retained as a product finding.
"""
import ast
import json
from pathlib import Path
import unittest

ADDON = Path(__file__).resolve().parents[2]
REPOSITORY = ADDON.parent


def _function_source(path, class_name, method_name):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for member in node.body:
                if isinstance(member, ast.FunctionDef) and member.name == method_name:
                    lines = path.read_text(encoding="utf-8").splitlines()
                    start = member.lineno - 1
                    indent = len(lines[start]) - len(lines[start].lstrip())
                    while start > 0 and lines[start - 1].lstrip().startswith("@"):
                        start -= 1
                    end = start + 1
                    while end < len(lines):
                        line = lines[end]
                        if (line.strip() and len(line) - len(line.lstrip()) <= indent
                                and not line.lstrip().startswith(("def ", "async def "))):
                            break
                        end += 1
                    return "\\n".join(lines[start:end])
    raise AssertionError("method not found: %s.%s" % (class_name, method_name))


class SecurityBoundaryCharacterization(unittest.TestCase):
    def test_oidc_token_controller_does_not_return_raw_exception_text(self):
        """Token endpoint failures must not expose internal exception details."""
        source = _function_source(ADDON / "controllers" / "main.py",
                                  "ControllerOIDC", "api_oidc_token")
        self.assertNotIn("error_description=str(ex)", source)

    def test_fresh_issuer_is_not_accepted_from_another_company(self):
        """Issuer resolution must remain scoped to the active company context."""
        source = _function_source(ADDON / "models" / "token_helper.py",
                                  "TokenHelper", "_get_fresh_profile_issuer")
        self.assertIn("company_id", source,
                      "fresh issuer lookup has no explicit company boundary")

    def test_controller_unknown_exception_is_not_serialized_verbatim(self):
        """Generic controller errors must not serialize exception messages."""
        source = _function_source(REPOSITORY / "amr_data_sync" / "controllers" / "mixin.py",
                                  "ApiControllerMixin", "handle_exception")
        self.assertNotIn('"error_description": str(ex)', source)


if __name__ == "__main__":
    unittest.main()
