"""Real Odoo ORM coverage for issuer-profile wizard behavior."""
import json

from odoo.exceptions import AccessError, ValidationError
from odoo.tests.common import SavepointCase


class TestIssuerWizardOrm(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestIssuerWizardOrm, cls).setUpClass()
        cls.trust_group = cls.env.ref('amr_resource.group_oidc_trust_admin')
        cls.trust_admin = cls.env['res.users'].create({
            'name': 'Synthetic Issuer Trust Admin',
            'login': 'synthetic-issuer-trust-admin',
            'email': 'synthetic-issuer-trust-admin@example.invalid',
            'groups_id': [(6, 0, [
                cls.env.ref('base.group_user').id,
                cls.env.ref('base.group_system').id,
                cls.trust_group.id,
            ])],
        })
        cls.issuer_model = cls.env['oidc.issuer.register'].sudo()
        cls.profile = cls.issuer_model.create(cls._profile_values())

    def test_trust_admin_fixture_has_expected_group(self):
        self.assertTrue(
            self.trust_admin.has_group('amr_resource.group_oidc_trust_admin'))

    @staticmethod
    def _profile_values(**changes):
        values = {
            'issuer': 'https://issuer.integration.test',
            'token_profile': 'jwt',
            'client_id': 'integration-client',
            'token_endpoint': 'https://issuer.integration.test/token',
            'metadata_mode': 'manual',
            'verification_source': 'jwks',
            'jwks_uri': 'https://issuer.integration.test/jwks',
            'introspection_source': 'none',
            'azp': 'integration-client',
            'audience_ids': [(0, 0, {'value': 'integration-audience'})],
        }
        values.update(changes)
        return values

    def _wizard(self, user=None, **values):
        wizard_model = self.env['service.credential.wizard']
        if user:
            wizard_model = wizard_model.with_user(user)
        return wizard_model.create(dict({
            'credential_type': 'client_secret',
            'client_id': 'integration-client',
            'client_secret': 'synthetic-secret',
        }, **values))

    def test_profile_and_manual_uri_are_mutually_exclusive(self):
        wizard = self._wizard(user=self.trust_admin, issuer_profile_id=self.profile.id)
        wizard.token_uri = 'https://manual.example/token'
        with self.assertRaises(ValidationError):
            wizard.action_generate()

    def test_inactive_mismatched_and_missing_endpoint_profiles_fail_closed(self):
        cases = [
            {'active': False},
            {'client_id': 'different-client'},
            {'token_endpoint': False},
        ]
        for index, changes in enumerate(cases):
            with self.subTest(changes=changes):
                profile = self.issuer_model.create(self._profile_values(
                    issuer='https://case-%s.integration.test' % index,
                    **changes))
                wizard = self._wizard(user=self.trust_admin, issuer_profile_id=profile.id)
                with self.assertRaises(ValidationError):
                    wizard.action_generate()

    def test_profile_endpoint_is_used_by_real_wizard_generation(self):
        wizard = self._wizard(user=self.trust_admin, issuer_profile_id=self.profile.id)
        wizard.action_generate()
        self.assertEqual(json.loads(wizard.json_content)['token_uri'],
                         'https://issuer.integration.test/token')

    def test_unprivileged_orm_create_and_write_cannot_assign_profile(self):
        user = self.env['res.users'].create({
            'name': 'Issuer Wizard Integration User',
            'login': 'issuer-wizard-integration-user',
            'email': 'issuer-wizard-integration@example.invalid',
            'groups_id': [(6, 0, [self.env.ref('base.group_user').id])],
        })
        with self.assertRaises(AccessError):
            self._wizard(user=user, issuer_profile_id=self.profile.id)
        wizard = self._wizard(user=self.trust_admin)
        with self.assertRaises(AccessError):
            wizard.with_user(user).write({'issuer_profile_id': self.profile.id})
        self.assertFalse(wizard.issuer_profile_id)
