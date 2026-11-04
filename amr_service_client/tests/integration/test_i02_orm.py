from odoo.tests.common import TransactionCase


class _RollbackSentinel(Exception):
    pass


class TestI02Orm(TransactionCase):
    def test_create_update_relations_and_savepoint_rollback(self):
        partner_model = self.env['ir.model'].search([('model', '=', 'res.partner')], limit=1)
        self.assertTrue(partner_model)
        endpoint = self.env['service.endpoint'].create({
            'name': 'I02 endpoint', 'code': 'i02_endpoint',
            'source': 'value', 'base_url_value': 'https://example.invalid',
        })
        client = self.env['service.client'].create({
            'name': 'I02 client', 'model_id': partner_model.id,
            'endpoint_id': endpoint.id,
        })
        payload = self.env['service.client.payload'].create({
            'service_client_id': client.id, 'key': 'i02_key',
            'value': 'initial', 'type': 'fix',
        })

        # Odoo 13 flush() without field limits flushes every model; likewise,
        # invalidate_cache() without arguments clears the entire environment cache.
        endpoint.flush()
        endpoint.invalidate_cache()
        self.assertEqual((endpoint.name, endpoint.code, endpoint.source, endpoint.base_url_value),
                         ('I02 endpoint', 'i02_endpoint', 'value', 'https://example.invalid'))
        self.assertEqual((client.name, client.model_id.id, client.endpoint_id.id),
                         ('I02 client', partner_model.id, endpoint.id))
        self.assertEqual((payload.key, payload.value, payload.type, payload.service_client_id.id),
                         ('i02_key', 'initial', 'fix', client.id))
        self.assertEqual(client.payload_ids.ids, [payload.id])

        endpoint.write({'name': 'I02 endpoint updated'})
        client.write({'name': 'I02 client updated'})
        payload.write({'value': 'persisted'})
        endpoint.flush()
        endpoint.invalidate_cache()
        snapshot = (endpoint.name, endpoint.code, endpoint.source, endpoint.base_url_value,
                    client.name, client.model_id.id, client.endpoint_id.id,
                    payload.key, payload.value, payload.type, payload.service_client_id.id,
                    tuple(client.payload_ids.ids))
        self.assertEqual(snapshot, (
            'I02 endpoint updated', 'i02_endpoint', 'value', 'https://example.invalid',
            'I02 client updated', partner_model.id, endpoint.id,
            'i02_key', 'persisted', 'fix', client.id, (payload.id,),
        ))

        with self.assertRaises(_RollbackSentinel):
            with self.cr.savepoint():
                endpoint.write({'name': 'temporary endpoint'})
                client.write({'name': 'temporary client'})
                payload.write({'value': 'temporary value'})
                second = self.env['service.client.payload'].create({
                    'service_client_id': client.id, 'key': 'i02_second',
                    'value': 'temporary second', 'type': 'fix',
                })
                second_id = second.id
                self.assertEqual((endpoint.name, client.name, payload.value),
                                 ('temporary endpoint', 'temporary client', 'temporary value'))
                self.assertEqual((second.key, second.value, second.type, second.service_client_id.id),
                                 ('i02_second', 'temporary second', 'fix', client.id))
                self.assertEqual(set(client.payload_ids.ids), {payload.id, second_id})
                raise _RollbackSentinel()

        endpoint.invalidate_cache()
        self.assertEqual((endpoint.name, endpoint.code, endpoint.source, endpoint.base_url_value,
                          client.name, client.model_id.id, client.endpoint_id.id,
                          payload.key, payload.value, payload.type, payload.service_client_id.id,
                          tuple(client.payload_ids.ids)), snapshot)
        self.assertFalse(self.env['service.client.payload'].browse(second_id).exists())
