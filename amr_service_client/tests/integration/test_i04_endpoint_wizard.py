import json
from unittest.mock import patch

from odoo.tests.common import TransactionCase


class _Response:
    status_code = 200

    def json(self):
        return {'ok': True, 'message': 'synthetic response'}

    def raise_for_status(self):
        return None


class TestI04EndpointWizard(TransactionCase):
    def setUp(self):
        super(TestI04EndpointWizard, self).setUp()
        self.endpoint = self.env['service.endpoint'].create({
            'name': 'Synthetic endpoint',
            'code': 'i04_synthetic',
            'source': 'value',
            'base_url_value': 'https://example.invalid',
            'content_type_default': 'application/json',
            'timeout': 17,
        })

    def _wizard(self, params):
        return self.env['service.endpoint.test.wizard'].create({
            'endpoint_id': self.endpoint.id,
            'endpoint_model': 'service.endpoint',
            'method': 'POST',
            'path': '/check',
            'params': params,
            'headers': json.dumps({'X-Test': 'synthetic'}),
            'payload': json.dumps({'item': 'synthetic'}),
        })

    def test_success_persists_response_and_actions(self):
        endpoint_action = self.endpoint.action_test_connection()
        self.assertEqual(endpoint_action['type'], 'ir.actions.act_window')
        self.assertEqual(endpoint_action['res_model'], 'service.endpoint.test.wizard')
        self.assertEqual(endpoint_action['view_mode'], 'form')
        self.assertEqual(endpoint_action['target'], 'new')
        self.assertEqual(endpoint_action['context'], {
            'default_endpoint_id': self.endpoint.id,
            'default_endpoint_model': 'service.endpoint',
        })

        wizard = self._wizard(json.dumps({'page': 2}))
        with patch('odoo.addons.amr_service_client.models.service_client.requests.request',
                   return_value=_Response()) as transport:
            action = wizard.action_test()
        transport.assert_called_once_with(
            method='POST', url='https://example.invalid/check',
            params={'page': 2}, json={'item': 'synthetic'},
            headers={'X-Test': 'synthetic', 'Content-Type': 'application/json',
                     'Accept': 'application/json'}, timeout=17,
        )
        wizard.flush(['response_status', 'response_body', 'success'])
        wizard.invalidate_cache(['response_status', 'response_body', 'success'])
        self.assertEqual(wizard.response_status, 200)
        self.assertEqual(json.loads(wizard.response_body), {'ok': True, 'message': 'synthetic response'})
        self.assertTrue(wizard.success)
        self.assertEqual(action['type'], 'ir.actions.act_window')
        self.assertEqual(action['res_model'], 'service.endpoint.test.wizard')
        self.assertEqual(action['res_id'], wizard.id)
        self.assertEqual(action['view_mode'], 'form')
        self.assertEqual(action['target'], 'new')

    def test_malformed_params_raise_without_response_mutation(self):
        wizard = self._wizard('{')
        wizard.write({'response_status': 201, 'response_body': 'previous response', 'success': True})
        wizard.flush(['response_status', 'response_body', 'success'])
        with patch('odoo.addons.amr_service_client.models.service_client.requests.request') as transport:
            with self.assertRaises(json.JSONDecodeError):
                wizard.action_test()
        transport.assert_not_called()
        wizard.flush(['response_status', 'response_body', 'success'])
        wizard.invalidate_cache(['response_status', 'response_body', 'success'])
        self.assertEqual(wizard.response_status, 201)
        self.assertEqual(wizard.response_body, 'previous response')
        self.assertTrue(wizard.success)
