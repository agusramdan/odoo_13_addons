"""Disposable Odoo shell probe; execute via stdin, never on a live database."""
import unittest
from unittest.mock import patch
import requests
from odoo import api, SUPERUSER_ID
from odoo.addons.amr_service_client.models import service_client as sc

class RealClientProbe(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.credential = env['service.credential'].create({'name': 'probe68', 'source': 'database', 'credential_json': '{"type":"api_key","header":"X-Probe","value":"synthetic"}'})
        cls.endpoint = env['service.endpoint'].create({'name': 'probe68', 'code': 'probe68', 'base_url_value': 'https://example.invalid', 'credential_id': cls.credential.id})
        cls.owner = env['service.client'].create({'name': 'probe68', 'model_id': env['ir.model']._get('res.partner').id, 'endpoint_id': cls.endpoint.id, 'credential_id': cls.credential.id})
        env.cr.commit()

    def client(self):
        return self.owner.get_service_client(self.endpoint, credential=self.credential, method='POST')

    def rows(self):
        with env.registry.cursor() as cr:
            fresh = api.Environment(cr, SUPERUSER_ID, {})
            return fresh['service.client.log'].search_read([('client_id', '=', self.owner.id)], ['id', 'state', 'response', 'request_context', 'client_id', 'endpoint_id', 'credential_id'], order='id')

    def test_call_identity_and_failing_telemetry(self):
        client = self.client()
        response = requests.Response(); response.status_code = 200
        reports = []
        def report_success(*args, **kwargs):
            reports.append(kwargs)
            raise RuntimeError('synthetic sdk failure')
        with patch.object(sc.requests, 'request', return_value=response) as request, patch.object(type(env['service.client']), '_report_sentry', new=report_success):
            self.assertIs(client.call(method='POST'), response)
        self.assertEqual(request.call_count, 1)
        self.assertEqual(len(reports), 1)
        self.assertIs(reports[0]['response'], response)
        self.assertIsNone(reports[0]['exception'])
        for stage in ('preparation', 'transport', 'http'):
            for raises in (False, True):
                client = self.client()
                error = requests.HTTPError('synthetic-http') if stage == 'http' else RuntimeError(stage)
                response = requests.Response()
                response.status_code = 503 if stage == 'http' else 200
                if stage == 'http':
                    response.raise_for_status = lambda: (_ for _ in ()).throw(error)
                reports, calls = [], []
                def reporting(*args, **kwargs):
                    reports.append(kwargs)
                    raise RuntimeError('synthetic sdk failure')
                def request(**kwargs):
                    calls.append(kwargs)
                    if stage == 'transport':
                        raise error
                    return response
                prep = patch.object(client, 'prepare_request_context', side_effect=error) if stage == 'preparation' else patch.object(client, 'prepare_request_context', wraps=client.prepare_request_context)
                with prep, patch.object(sc.requests, 'request', side_effect=request), patch.object(type(env['service.client']), '_report_sentry', new=reporting):
                    if raises:
                        with self.assertRaises(type(error)) as caught:
                            client.call(method='POST', raise_exception=True)
                        self.assertIs(caught.exception, error)
                    else:
                        result = client.call(method='POST', raise_exception=False)
                        self.assertIs(result, response if stage == 'http' else None)
                self.assertEqual(len(calls), 0 if stage == 'preparation' else 1)
                self.assertEqual(len(reports), 1)
                self.assertIs(reports[0]['exception'], error)

    def test_dispatch_fresh_cursor(self):
        for active in (False, True):
            for stage in ('success', 'preparation', 'transport', 'http', 'log_failure'):
                if stage == 'log_failure' and not active:
                    continue
                before = self.rows()
                client = self.client()
                error = RuntimeError(stage)
                response = requests.Response(); response.status_code = 200; response._content = b'probe-response'
                if stage == 'http':
                    response.raise_for_status = lambda: (_ for _ in ()).throw(error)
                calls, reports, log_errors = [], [], []
                def request(**kwargs):
                    calls.append(kwargs)
                    if stage == 'transport': raise error
                    return response
                def reporting(*args, **kwargs):
                    reports.append(kwargs)
                    raise RuntimeError('synthetic sdk failure')
                prep = patch.object(client, 'prepare_request_context', side_effect=error) if stage == 'preparation' else patch.object(client, 'prepare_request_context', wraps=client.prepare_request_context)
                model = type(env['service.client.log'])
                original_log, original_error = model.create_log, model.create_error
                def create_log(recordset, state, *args, **kwargs):
                    if stage == 'log_failure' and state == 'done': raise error
                    return original_log(recordset, state, *args, **kwargs)
                def create_error(recordset, exc, **kwargs):
                    log_errors.append(exc)
                    return original_error(recordset, exc, **kwargs)
                sender = sc.ServiceClientSend(client, {'value': 'probe'}, active_log=active, endpoint_id=self.endpoint)
                with prep, patch.object(sc.requests, 'request', side_effect=request), patch.object(type(env['service.client']), '_report_sentry', new=reporting), patch.object(model, 'create_log', new=create_log), patch.object(model, 'create_error', new=create_error):
                    self.assertIsNone(sender.dispatch_send())
                env.cr.commit()
                after = self.rows(); new = after[len(before):]
                is_error = stage != 'success'
                self.assertEqual(len(calls), 0 if stage == 'preparation' else 1)
                self.assertEqual(len(reports), 1)
                self.assertIs(reports[0]['exception'], error if is_error and stage != 'log_failure' else None)
                self.assertEqual(log_errors, [error] if is_error else [])
                self.assertEqual(len(new), int(is_error or active))
                if new:
                    row = new[0]
                    self.assertEqual(row['state'], 'error' if is_error else 'done')
                    self.assertEqual(row['client_id'][0], self.owner.id)
                    self.assertEqual(row['endpoint_id'][0], self.endpoint.id)
                    self.assertEqual(row['credential_id'][0], self.credential.id)
                    self.assertIn(stage if is_error else 'probe-response', row['response'])
                    self.assertIn('payload' if stage == 'preparation' else 'url', row['request_context'])

result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(RealClientProbe))
print('PROBE68_RESULT tests=%d failures=%d errors=%d' % (result.testsRun, len(result.failures), len(result.errors)), flush=True)
if not result.wasSuccessful():
    raise SystemExit(1)
