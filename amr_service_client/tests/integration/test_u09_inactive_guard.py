# -*- coding: utf-8 -*-

from unittest.mock import Mock, patch

from odoo.exceptions import UserError
from odoo.tests import TransactionCase


class TestInactiveServiceClientGuard(TransactionCase):

    def setUp(self):
        super(TestInactiveServiceClientGuard, self).setUp()
        self.endpoint = self.env['service.endpoint'].create({
            'name': 'Synthetic inactive-guard endpoint',
            'code': 'synthetic-inactive-guard',
            'source': 'value',
            'base_url_value': 'https://example.invalid',
        })
        model = self.env['ir.model']._get('res.partner')
        self.assertTrue(model, 'res.partner must be present in ir.model')
        self.client = self.env['service.client'].create({
            'name': 'Synthetic inactive-guard client',
            'model_id': model.id,
            'endpoint_id': self.endpoint.id,
            'iteration': 'response = [{}]',
            'code': "path = '/synthetic'\nmethod = 'POST'\npayload = {'synthetic': True}",
        })
        self.records = self.env['res.partner'].browse()

    def _business_side_effect_spies(self):
        patchers = {
            'iteration': patch.object(type(self.client), '_run_action_iteration', autospec=True),
            'payload': patch.object(type(self.client.payload_ids), 'get_payload', autospec=True),
            'code': patch.object(type(self.client), '_run_action_code', autospec=True),
            'get_client': patch.object(type(self.client), 'get_service_client', autospec=True),
            'logger': patch('odoo.addons.amr_service_client.models.service_client._logger.debug'),
            'report': patch.object(type(self.client), '_report_sentry', autospec=True),
            'error_handler': patch.object(type(self.client.error_handle_id), 'run'),
            'action_next': patch.object(type(self.client.action_next_id), 'run'),
        }
        self._active_business_patchers = list(patchers.values())
        return {name: patcher.start() for name, patcher in patchers.items()}

    def _assert_no_business_side_effects(self, spies):
        for name, spy in spies.items():
            self.assertEqual(spy.call_count, 0, '%s was called' % name)

    def test_inactive_client_persists_and_both_entrypoints_raise_before_side_effects(self):
        self.client.write({'active': False})
        self.env['service.client'].flush()
        self.env['service.client'].invalidate_cache()
        client = self.env['service.client'].browse(self.client.id)
        self.assertFalse(client.active)

        eval_context = client._get_eval_context()
        eval_context['records'] = self.records
        spies = self._business_side_effect_spies()
        with patch('odoo.addons.amr_service_client.models.service_client.requests.request',
                   side_effect=AssertionError('transport must not be called')) as transport_mock:
            try:
                with self.assertRaises(UserError) as raised:
                    client.run_action_service_client(eval_context=eval_context)
                self.assertEqual(raised.exception.args, ('Service client is inactive.', ''))
                self.assertNotIn('synthetic', str(raised.exception))
                with self.assertRaises(UserError) as raised:
                    client.send_request(self.records)
                self.assertEqual(raised.exception.args, ('Service client is inactive.', ''))
                self.assertNotIn('synthetic', str(raised.exception))
                self.assertEqual(transport_mock.call_count, 0)
                self._assert_no_business_side_effects(spies)
            finally:
                for patcher in self._active_business_patchers:
                    patcher.stop()
                self._active_business_patchers = []

    def test_active_client_executes_one_business_transport_call(self):
        self.assertTrue(self.client.active)
        response = Mock()
        response.raise_for_status.return_value = None
        with patch('odoo.addons.amr_service_client.models.service_client.requests.request',
                   return_value=response) as transport, \
                patch.object(type(self.client), '_report_sentry') as report, \
                patch.object(type(self.client.action_next_id), 'run', return_value='synthetic-next-action') as next_action:
            with patch.object(type(self.client), '_get_eval_context', return_value={
                'ctx': {}, 'env': self.env, 'user': self.env.user,
            }):
                result = self.client.run_action_service_client(eval_context={
                    'records': self.records,
                })

        self.assertEqual(transport.call_count, 1)
        self.assertEqual(transport.call_args[1].get('json'), {'synthetic': True})
        self.assertEqual(transport.call_args[1].get('method'), 'POST')
        self.assertEqual(result, 'synthetic-next-action')
        next_action.assert_called_once()
        report.assert_called()
