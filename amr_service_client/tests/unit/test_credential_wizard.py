"""Offline wizard characterization using doubles; not ORM, UI or security evidence."""
import base64
import importlib.util
import json
from pathlib import Path
import sys
import types
import unittest
from unittest import mock


def load_wizard():
    # Match the other offline unit modules: load real source with Odoo doubles.
    odoo = types.ModuleType("odoo")
    odoo.models = types.SimpleNamespace(TransientModel=type("TransientModel", (), {}))
    odoo.fields = types.SimpleNamespace(**{
        name: (lambda *args, **kwargs: None)
        for name in ("Selection", "Char", "Text", "Binary")
    })
    exceptions = types.ModuleType("odoo.exceptions")
    exceptions.ValidationError = type("ValidationError", (Exception,), {})
    path = Path(__file__).resolve().parents[2] / "wizards" / "service_credential.py"
    spec = importlib.util.spec_from_file_location("isolated_credential_wizard", str(path))
    module = importlib.util.module_from_spec(spec)
    with mock.patch.dict(sys.modules, {"odoo": odoo, "odoo.exceptions": exceptions}):
        spec.loader.exec_module(module)
    return module.ServiceCredentialWizard


Wizard = load_wizard()


class Environment:
    def __init__(self):
        self.context = {"active_id": 42, "synthetic_context": "context-value"}
        self.record = mock.Mock()
        self.model = mock.Mock()
        self.model.browse.return_value = self.record
        self.requested_models = []

    def __getitem__(self, name):
        self.requested_models.append(name)
        if name != "service.credential":
            raise KeyError(name)
        return self.model


class WizardDouble(Wizard):
    def __init__(self):
        self.env = Environment()
        self.id = 17
        self.credential_type = "get_jwt"
        self.version = "synthetic-version"
        self.username = "synthetic-user"
        self.password = "synthetic-password"
        self.token_uri = "https://synthetic.invalid/manual/token?source=wizard"
        self.json_content = "existing synthetic content"
        self.generated_file = None
        self.generated_filename = None
        self.ensure_one = mock.Mock()


class CredentialWizardCharacterization(unittest.TestCase):
    def setUp(self):
        self.wizard = WizardDouble()

    def assert_generated(self, wizard, action):
        expected = {"version": wizard.version, "type": "get_jwt",
                    "username": wizard.username, "password": wizard.password,
                    "token_uri": wizard.token_uri}
        # Boolean assertions avoid printing credential-shaped synthetic values on failure.
        self.assertTrue(json.loads(wizard.json_content) == expected, "generated JSON differs")
        decoded = base64.b64decode(wizard.generated_file, validate=True).decode("utf-8")
        self.assertTrue(decoded == wizard.json_content, "binary differs from JSON text")
        self.assertEqual(wizard.generated_filename, "get_jwt.json")
        self.assertTrue(action == {
            "type": "ir.actions.act_window", "name": "Service Credential Wizard",
            "res_model": "service.credential.wizard", "res_id": 17,
            "view_mode": "form", "target": "new", "context": wizard.env.context,
        }, "generate action differs")

    def test_get_jwt_generates_manual_uri_json_binary_filename_and_action(self):
        wizard = self.wizard
        action = wizard.action_generate()
        self.assert_generated(wizard, action)
        self.assertEqual(wizard.ensure_one.call_count, 2)  # generate and URI helper
        self.assertEqual(wizard.env.requested_models, [])

    def test_save_writes_existing_content_without_generating_or_changing_source(self):
        wizard = self.wizard
        old_content = wizard.json_content
        with mock.patch.object(wizard, "action_generate", side_effect=AssertionError("unexpected generate")) as generate:
            result = wizard.action_save()
        self.assertEqual(generate.call_count, 0)
        self.assertEqual(wizard.env.requested_models, ["service.credential"])
        wizard.env.model.browse.assert_called_once_with(42)
        self.assertEqual(wizard.env.record.write.call_count, 1)
        self.assertTrue(wizard.env.record.write.call_args[0][0] == {"credential_json": old_content}, "save payload differs")
        self.assertEqual(result, {"type": "ir.actions.act_window_close"})

    def test_save_to_credential_generates_before_single_database_write(self):
        wizard = self.wizard
        old_content = wizard.json_content
        actions = []
        real_generate = wizard.action_generate
        def capture_generate():
            action = real_generate()
            actions.append(action)
            return action
        with mock.patch.object(wizard, "action_generate", side_effect=capture_generate) as generate:
            result = wizard.action_save_to_credential()
        self.assertEqual(generate.call_count, 1)
        self.assertNotEqual(wizard.json_content, old_content)
        self.assert_generated(wizard, actions[0])
        self.assertEqual(wizard.env.requested_models, ["service.credential"])
        wizard.env.model.browse.assert_called_once_with(42)
        self.assertEqual(wizard.env.record.write.call_count, 1)
        self.assertTrue(wizard.env.record.write.call_args[0][0] == {
            "credential_json": wizard.json_content, "source": "database"
        }, "generated save payload differs")
        self.assertEqual(result, {"type": "ir.actions.act_window_close"})

    def test_generation_failure_propagates_without_browse_or_write(self):
        wizard = self.wizard
        failure = ValueError("synthetic generation failure")
        with mock.patch.object(wizard, "action_generate", side_effect=failure) as generate:
            with self.assertRaises(ValueError) as caught:
                wizard.action_save_to_credential()
        self.assertIs(caught.exception, failure)
        self.assertEqual(generate.call_count, 1)
        self.assertEqual(wizard.env.requested_models, [])
        self.assertEqual(wizard.env.model.browse.call_count, 0)
        self.assertEqual(wizard.env.record.write.call_count, 0)

    def test_generation_assertions_detect_wrong_manual_uri_and_binary(self):
        wizard = self.wizard
        action = wizard.action_generate()
        original = wizard.json_content
        changed = json.loads(original)
        changed["token_uri"] = "https://synthetic.invalid/other"
        wizard.json_content = json.dumps(changed)
        wizard.generated_file = base64.b64encode(wizard.json_content.encode("utf-8"))
        with self.assertRaises(AssertionError):
            self.assert_generated(wizard, action)
        wizard.json_content = original
        with self.assertRaises(AssertionError):
            self.assert_generated(wizard, action)


if __name__ == "__main__":
    unittest.main()
