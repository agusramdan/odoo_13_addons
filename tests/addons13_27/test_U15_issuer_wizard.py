"""Offline tests for issuer-backed wizard credential generation."""
from support import *
import json


class IssuerWizardTests(OfflineCase):
    def test_core_has_no_resource_or_issuer_profile_dependency(self):
        from pathlib import Path
        import ast
        addon = Path(__file__).resolve().parents[2] / 'amr_service_client'
        manifest = ast.literal_eval((addon / '__manifest__.py').read_text())
        self.assertNotIn('amr_resource', manifest['depends'])
        for path in addon.rglob('*'):
            if path.is_file() and path.suffix in ('.py', '.xml', '.csv'):
                text = path.read_text()
                self.assertNotIn('oidc.issuer.register', text, str(path))
                self.assertNotIn('amr_resource.', text, str(path))

    def test_optional_addon_is_registered_with_orm_inheritance_and_view(self):
        from pathlib import Path
        import ast
        addon = Path(__file__).resolve().parents[2] / 'amr_service_client_profile'
        manifest = ast.literal_eval((addon / '__manifest__.py').read_text())
        self.assertEqual(set(manifest['depends']), {'amr_service_client', 'amr_resource'})
        self.assertEqual(manifest['data'], ['views/service_credential.xml'])
        model = (addon / 'wizards/service_credential.py').read_text()
        self.assertIn("_inherit = 'service.credential.wizard'", model)
        self.assertNotIn('_name =', model)
        view = (addon / 'views/service_credential.xml').read_text()
        self.assertIn('inherit_id', view)
        self.assertIn('issuer_profile_id', view)
        self.assertIn('from . import wizards', (addon / '__init__.py').read_text())
        self.assertIn('from . import service_credential', (addon / 'wizards/__init__.py').read_text())

    @classmethod
    def setUpClass(cls):
        import sys
        install_odoo_stubs()
        sys.modules['odoo'].models.TransientModel = type('TransientModel', (), {})
        cls.m = load('wizards/service_credential.py')
        cls.profile = load('../amr_service_client_profile/wizards/service_credential.py')
        cls.m.ServiceCredentialWizard._oauth_token_uri = cls.profile.ServiceCredentialWizard._oauth_token_uri

    def wizard(self, profile=None, manual=None, kind='client_secret', client_id='cid'):
        obj = object.__new__(self.m.ServiceCredentialWizard)
        obj.ensure_one = lambda: None
        obj.id = 1
        obj._description = 'Wizard'
        obj._name = 'service.credential.wizard'
        obj.env = types.SimpleNamespace(context={})
        obj.env.user = types.SimpleNamespace(has_group=lambda group: True)
        obj.credential_type = kind
        obj.version = '1.0'
        obj.client_id = client_id
        obj.client_secret = 'secret'
        obj.private_key_id = 'kid'
        obj.private_key = None
        obj.private_key_file = None
        obj.token_uri = manual
        obj.issuer_profile_id = profile
        return obj

    def test_unauthorized_user_cannot_attach_profile_during_create_or_write(self):
        wizard = object.__new__(self.profile.ServiceCredentialWizard)
        wizard.env = types.SimpleNamespace(user=types.SimpleNamespace(has_group=lambda group: False))
        for operation, values in (('create', [{'issuer_profile_id': 7}]),
                                  ('write', {'issuer_profile_id': 7})):
            with self.subTest(operation=operation):
                try:
                    getattr(self.profile.ServiceCredentialWizard, operation)(wizard, values)
                except AccessError:
                    pass
                except Exception as exc:
                    self.fail('expected AccessError for %s, got %r' % (operation, exc))
                else:
                    self.fail('unauthorized %s accepted issuer_profile_id' % operation)

    def test_unauthorized_user_cannot_use_selected_profile(self):
        wizard = self.wizard(types.SimpleNamespace(active=True, client_id='cid', token_endpoint='https://issuer.example/token'))
        wizard.env.user.has_group = lambda group: False
        with self.assertRaises(AccessError):
            wizard.action_generate()

    def test_save_persists_generated_profile_endpoint_and_database_source(self):
        wizard = self.wizard(types.SimpleNamespace(active=True, client_id='cid', token_endpoint='https://issuer.example/token'))
        writes = []
        credential = types.SimpleNamespace(write=lambda values: writes.append(values))
        class CredentialModel:
            def browse(self, record_id):
                self.record_id = record_id
                return credential
        model = CredentialModel()
        class Environment:
            context = {'active_id': 42}
            user = types.SimpleNamespace(has_group=lambda group: True)
            def __getitem__(self, key):
                return model
        wizard.env = Environment()
        wizard.action_save_to_credential()
        self.assertEqual(writes, [{'credential_json': wizard.json_content, 'source': 'database'}])
        self.assertEqual(json.loads(writes[0]['credential_json'])['token_uri'], 'https://issuer.example/token')

    def test_save_rejects_invalid_or_conflicting_profile_without_write(self):
        profiles = [
            (types.SimpleNamespace(active=False, client_id='cid', token_endpoint='https://issuer.example/token'), None),
            (types.SimpleNamespace(active=True, client_id='other', token_endpoint='https://issuer.example/token'), None),
            (types.SimpleNamespace(active=True, client_id='cid', token_endpoint='https://issuer.example/token'), 'https://manual.example/token'),
        ]
        for profile, manual in profiles:
            with self.subTest(profile=profile, manual=manual):
                wizard = self.wizard(profile, manual=manual)
                writes = []
                credential = types.SimpleNamespace(write=lambda values: writes.append(values))
                class CredentialModel:
                    def browse(self, record_id): return credential
                class Environment:
                    context = {'active_id': 42}
                    user = types.SimpleNamespace(has_group=lambda group: True)
                    def __getitem__(self, key): return CredentialModel()
                wizard.env = Environment()
                with self.assertRaises(ValidationError):
                    wizard.action_save_to_credential()
                self.assertEqual(writes, [])

    def test_selected_profile_supplies_token_uri_for_supported_oauth_credentials(self):
        for kind in ('client_secret', 'service_account'):
            wizard = self.wizard(types.SimpleNamespace(active=True, client_id='cid', token_endpoint='https://issuer.example/token'), kind=kind)
            wizard.action_generate()
            data = json.loads(wizard.json_content)
            self.assertEqual(data['token_uri'], 'https://issuer.example/token')

    def test_manual_token_uri_remains_supported_without_profile(self):
        wizard = self.wizard(manual='https://legacy.example/token')
        wizard.action_generate()
        self.assertEqual(json.loads(wizard.json_content)['token_uri'], 'https://legacy.example/token')

    def test_empty_profile_endpoint_fails_closed(self):
        wizard = self.wizard(types.SimpleNamespace(active=True, client_id='cid', token_endpoint=False))
        with self.assertRaises(ValidationError):
            wizard.action_generate()

    def test_profile_does_not_change_non_oauth_credential_output(self):
        for kind in ('api_key', 'bearer', 'basic'):
            wizard = self.wizard(types.SimpleNamespace(active=False, client_id='wrong', token_endpoint=False), kind=kind)
            wizard.action_generate()
            self.assertEqual(json.loads(wizard.json_content)['type'], kind)

    def test_profile_and_manual_uri_conflict_fails_closed(self):
        wizard = self.wizard(types.SimpleNamespace(active=True, client_id='cid', token_endpoint='https://issuer.example/token'), manual='https://legacy.example/token')
        with self.assertRaises(ValidationError):
            wizard.action_generate()

    def test_inactive_or_client_mismatch_profile_fails_closed(self):
        for profile in (types.SimpleNamespace(active=False, client_id='cid', token_endpoint='https://issuer.example/token'),
                        types.SimpleNamespace(active=True, client_id='other', token_endpoint='https://issuer.example/token')):
            with self.subTest(profile=profile):
                with self.assertRaises(ValidationError):
                    self.wizard(profile).action_generate()
