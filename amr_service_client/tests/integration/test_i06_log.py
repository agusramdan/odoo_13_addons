"""Native ORM acceptance for new minimized logs; legacy replay is out of scope."""
import copy
import uuid
from unittest.mock import Mock, patch

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestI06Log(TransactionCase):
    def setUp(self):
        super(TestI06Log, self).setUp()
        partner_model = self.env['ir.model'].search([('model', '=', 'res.partner')], limit=1)
        self.assertTrue(partner_model)
        self.endpoint = self.env['service.endpoint'].create({
            'name': 'I06 endpoint', 'code': 'i06_endpoint',
            'source': 'value', 'base_url_value': 'https://example.invalid',
        })
        self.credential = self.env['service.credential'].create({
            'name': 'I06 credential', 'source': 'database',
        })
        self.client = self.env['service.client'].create({
            'name': 'I06 client', 'model_id': partner_model.id,
            'endpoint_id': self.endpoint.id,
        })
        self.logs = self.env['service.client.log']
        self.markers = [uuid.uuid4().hex for _ in range(4)]
        self.context = {
            'method': 'POST', 'url': 'https://example.invalid/' + self.markers[0],
            'headers': {'X-Synthetic': self.markers[1]},
            'json': {'nested': [self.markers[2]]},
        }
        self.original = copy.deepcopy(self.context)

    def _contains_marker(self, value):
        return any(marker in str(value) for marker in self.markers)

    def _create_and_check(self, error=False):
        self.assertTrue(self._contains_marker(self.markers))
        self.assertFalse(self._contains_marker('clean synthetic control'))
        before = set(self.logs.search([]).ids)
        kwargs = {
            'client_id': self.client, 'endpoint_id': self.endpoint,
            'credential_id': self.credential, 'request_context': self.context,
        }
        if error:
            row = self.logs.create_error(ValueError(self.markers[3]), **kwargs)
            expected_state = 'error'
        else:
            row = self.logs.create_log('done', response_text=self.markers[3], **kwargs)
            expected_state = 'done'
        self.assertEqual(len(row), 1)
        self.logs.flush()
        self.logs.invalidate_cache()
        self.assertEqual(set(self.logs.search([]).ids) - before, {row.id})
        self.assertEqual(row.state, expected_state)
        self.assertEqual(row.client_id.id, self.client.id)
        self.assertEqual(row.endpoint_id.id, self.endpoint.id)
        self.assertEqual(row.credential_id.id, self.credential.id)
        self.assertFalse(row.request_context)
        self.assertFalse(row.response)
        self.assertFalse(self._contains_marker((row.request_context, row.response)))
        self.assertTrue(self.context == self.original)
        return row

    def test_factory_dispatch_success_preserves_payload_without_logging(self):
        """Exercise the factory's production dispatch path with logging disabled."""
        self.endpoint.write({'active_log': False, 'content_type_default': 'application/json'})
        payload = {'nested': [self.markers[2]]}
        original_payload = copy.deepcopy(payload)
        response = Mock(text=self.markers[3])
        client = self.client.get_service_client(
            self.endpoint, path='/' + self.markers[0], method='POST')
        self.assertIs(client.service_client, self.client)
        self.assertIs(type(client.client_id), int)
        sender = client.prepare_payload(**payload)
        self.assertFalse(sender.active_log)
        self.assertTrue(self._contains_marker(self.markers))
        self.assertFalse(self._contains_marker('clean synthetic control'))
        with patch('odoo.addons.amr_service_client.models.service_client.requests.request',
                   return_value=response) as transport, \
                patch.object(client, '_report_sentry'):
            result = sender.dispatch_send()
        self.assertIsNone(result)
        self.assertEqual(transport.call_count, 1)
        self.assertEqual(response.raise_for_status.call_count, 1)
        self.assertEqual(transport.call_args[1], {
            'method': 'POST', 'url': 'https://example.invalid/' + self.markers[0],
            'headers': {'Content-Type': 'application/json', 'Accept': 'application/json'},
            'params': None, 'timeout': 30, 'json': original_payload,
        })
        self.assertEqual(payload, original_payload)
        self.assertEqual(response.text, self.markers[3])

    def test_create_error_minimizes_persisted_request_and_exception(self):
        self._create_and_check(error=True)

    def test_minimized_log_replay_rejected_without_side_effects(self):
        row = self._create_and_check()
        self.logs.flush()
        self.logs.invalidate_cache()
        fields = ['state', 'client_id', 'endpoint_id', 'credential_id',
                  'request_context', 'response', 'write_date', 'write_uid']
        before = row.read(fields)
        before_ids = set(self.logs.search([]).ids)
        with patch.object(type(self.client), 'get_service_client') as get_client, \
                patch('odoo.addons.amr_service_client.models.service_client_log.requests.request') as transport, \
                patch.object(type(row), 'write') as write:
            for method in (row.send, row.dispatch_send):
                with self.assertRaises(UserError) as caught:
                    method()
                self.assertEqual(caught.exception.args, ('Replay is unavailable for this log.', ''))
                self.assertFalse(self._contains_marker(str(caught.exception)))
            get_client.assert_not_called()
            transport.assert_not_called()
            write.assert_not_called()
        self.logs.flush()
        self.logs.invalidate_cache()
        self.assertEqual(set(self.logs.search([]).ids), before_ids)
        self.assertEqual(row.read(fields), before)
