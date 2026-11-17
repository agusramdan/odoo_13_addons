# -*- coding: utf-8 -*-
"""Native TransactionCase coverage for ADDONS13-71 refactor/factory UAT.

The fixtures use synthetic records and patch only external request/reporting seams.
"""
from unittest.mock import Mock, patch

from odoo.tests.common import TransactionCase


MODULE = 'odoo.addons.amr_service_client.models.service_client'


class TestADDONS1371RefactorPreparation(TransactionCase):

    def setUp(self):
        super(TestADDONS1371RefactorPreparation, self).setUp()
        partner_model = self.env['ir.model'].search([('model', '=', 'res.partner')], limit=1)
        self.assertTrue(partner_model)
        self.endpoint = self.env['service.endpoint'].create({
            'name': 'ADDONS13-71 synthetic endpoint',
            'code': 'addons13_71_synthetic_endpoint',
            'source': 'value',
            'base_url_value': 'https://example.invalid',
            'content_type_default': 'application/json',
            'active_log': False,
        })
        self.credential = self.env['service.credential'].create({
            'name': 'ADDONS13-71 synthetic credential',
            'source': 'database',
            'credential_json': '{"type":"api_key","header":"X-Synthetic","value":"test-only"}',
        })
        self.endpoint.write({'credential_id': self.credential.id})
        self.client_record = self.env['service.client'].create({
            'name': 'ADDONS13-71 synthetic client',
            'model_id': partner_model.id,
            'endpoint_id': self.endpoint.id,
            'credential_id': self.credential.id,
        })
        self.provider = Mock()
        self.provider.authenticate.side_effect = lambda context, audience=None: context
        # Provider is replaced only at its construction seam; ORM/factory remain real.

    def _provider_factory(self):
        return patch.object(
            type(self.client_record), 'get_service_client',
            wraps=self.client_record.get_service_client)

    def test_v01_and_v02_reject_ambiguous_positions_and_preserve_keyword_headers(self):
        client = self._real_service_client()
        self.provider.authenticate.assert_not_called()
        with patch(MODULE + '.requests.request',
                   side_effect=AssertionError('transport called for rejected input')) as transport:
            with self.assertRaises(TypeError):
                client.call('POST', '/p', None, {'x': 1}, {'X-Test': 'v'})
            with self.assertRaises(TypeError):
                client.call('POST', '/p', None, {'x': 1}, False, {'X-Test': 'v'})
            transport.assert_not_called()
        self.provider.authenticate.assert_not_called()
        with self.assertRaises(TypeError):
            client.prepare_request_context('/p', 'POST', None, {'x': 1}, {'X-Test': 'v'})
        self.assertEqual(client.prepare_request_context(
            path='/p', method='POST', payload={'x': 1}, headers={'X-Test': 'v'}
        )['headers']['X-Test'], 'v')
        self.provider.authenticate.assert_called_once()
        self.provider.authenticate.reset_mock()
        with self.assertRaises(TypeError):
            client.call('POST', method='GET')
        self.provider.authenticate.assert_not_called()

    def test_v03_and_f01_f06_factory_and_model_entry_whitelists(self):
        with self._patched_provider_factory():
            service = self.client_record.get_service_client(
                self.endpoint, credential=self.credential, path='/stored', method='POST')
            self.assertEqual(service.credential, self.credential)
            factory = self._provider_factory()
            with factory as factory_spy:
                with patch(MODULE + '.requests.request',
                           side_effect=AssertionError('transport called for rejected model options')) as transport:
                    with self.assertRaises(TypeError):
                        self.client_record.call(self.endpoint, 'POST', unexpected_opt=True)
                    factory_spy.assert_not_called()
                    with self.assertRaises(TypeError):
                        self.client_record.call(
                            self.endpoint, 'POST', unexpected_opt=True, raise_exception=False)
                    factory_spy.assert_not_called()
                    with self.assertRaises(TypeError):
                        self.client_record.get(self.endpoint, url='https://example.invalid')
                    with self.assertRaises(TypeError):
                        self.client_record.post(self.endpoint, params={'q': 'x'})
                    with self.assertRaises(TypeError):
                        self.client_record.put(self.endpoint, params={'q': 'x'})
                    with self.assertRaises(TypeError):
                        self.client_record.delete(self.endpoint)
                    with self.assertRaises(TypeError):
                        self.client_record.delete(self.endpoint, self.endpoint, payload={'x': 1})
                    transport.assert_not_called()

    def test_v04_and_f07_raw_none_normalizer_and_d3_empty_method_failure(self):
        client = self._real_service_client()
        normalizer = Mock(return_value={'X-Normalized': 'yes'})
        with patch.object(type(self.endpoint), 'request_headers_default', autospec=True,
                          side_effect=lambda endpoint, value: normalizer(value)):
            context = client.prepare_request_context(
                path=None, method='POST', payload={'nested': [1]}, headers=None,
                audience='synthetic-audience')
        normalizer.assert_called_once_with(None)
        self.assertEqual(context['headers'], {'X-Normalized': 'yes'})
        self.assertEqual(self.provider.authenticate.call_args[1]['audience'], 'synthetic-audience')
        self.provider.authenticate.reset_mock()
        client.method = None
        self.assertIsNone(client.method)
        with patch(MODULE + '.requests.request',
                   side_effect=AssertionError('transport called for empty method')) as transport:
            with self.assertRaises(ValueError):
                client.call()
            transport.assert_not_called()
        self.provider.authenticate.assert_not_called()

    def test_v05_and_f08_f12_direct_wrappers_validate_before_transport(self):
        client = self._real_service_client()
        response = Mock()
        response.raise_for_status.return_value = None
        with patch(MODULE + '.requests.request', return_value=response) as transport:
            client.get('/read', params={'q': 'x'}, payload={'ignored': True})
            client.post('/write', params={'q': 'x'}, payload={'v': 1})
            client.put('/update', payload={'v': 2})
            client.delete('/remove', payload={'ignored': True})
            calls = [entry[1] for entry in transport.call_args_list]
        self.assertEqual([entry['method'] for entry in calls], ['GET', 'POST', 'PUT', 'DELETE'])
        self.assertNotIn('json', calls[0])
        self.assertEqual(calls[1]['json'], {'v': 1})
        self.assertEqual(calls[2]['json'], {'v': 2})
        self.assertNotIn('json', calls[3])
        with patch(MODULE + '.requests.request', return_value=response) as transport:
            for invoke in (lambda: client.get('/p', method='POST'),
                           lambda: client.post('/p', method='PUT'),
                           lambda: client.put('/p', method='POST'),
                           lambda: client.delete('/p', method='GET'),
                           lambda: client.call(method='POST', unexpected_opt=1, raise_exception=False)):
                with self.assertRaises(TypeError):
                    invoke()
            transport.assert_not_called()

    def test_v06_reports_effective_provider_method_and_fallback_input(self):
        client = self._real_service_client()
        response = Mock()
        response.raise_for_status.return_value = None
        client.provider.authenticate.side_effect = lambda context, audience=None: dict(context, method='PUT')
        with patch(MODULE + '.requests.request', return_value=response), \
                patch(MODULE + '.report_outcome') as report:
            client.call(method='POST', path='/p')
        self.assertEqual(report.call_args[1]['method'], 'PUT')
        client.provider.authenticate.side_effect = RuntimeError('synthetic preparation failure')
        with patch(MODULE + '.report_outcome') as report:
            with self.assertRaises(RuntimeError):
                client.call(method='POST', path='/p')
        self.assertEqual(report.call_args[1]['method'], 'POST')

    def test_v07_resolved_credential_record_reaches_sender_attribution(self):
        with self._patched_provider_factory():
            service = self.client_record.get_service_client(self.endpoint)
        self.assertEqual(service.credential, self.credential)
        sender = service.prepare_payload(active_log='payload-data', nested={'x': 1})
        self.assertEqual(sender.payload, {'active_log': 'payload-data', 'nested': {'x': 1}})
        self.assertEqual(sender.credential_id, self.credential)
        self.assertEqual(sender.endpoint_id, self.endpoint)

    def test_v08_and_f14_sender_domain_data_and_real_orm_log_writer(self):
        with self._patched_provider_factory():
            service = self.client_record.get_service_client(
                self.endpoint, path='/send', method='POST')
        sender = service.prepare_payload(
            active_log='payload-data', nested={'marker': 'synthetic'})
        sender.active_log = True
        response = Mock(text='synthetic response')
        before = set(self.env['service.client.log'].search([]).ids)
        with patch(MODULE + '.requests.request', return_value=response), \
                patch.object(service, '_report_sentry'):
            result = sender.dispatch_send()
        self.assertIsNone(result)
        created = self.env['service.client.log'].search([]).filtered(
            lambda row: row.id not in before)
        self.assertEqual(len(created), 1)
        self.assertEqual(created.state, 'done')
        self.assertEqual(created.client_id.id, self.client_record.id)
        self.assertEqual(created.endpoint_id.id, self.endpoint.id)
        self.assertEqual(created.credential_id.id, self.credential.id)
        self.assertFalse(created.request_context)
        self.assertFalse(created.response)

    def test_f13_eighth_model_audience_positional_rejected_pre_factory(self):
        factory = self._provider_factory()
        with factory as factory_spy:
            with patch(MODULE + '.requests.request',
                       side_effect=AssertionError('transport called for rejected positional audience')) as transport:
                with self.assertRaises(TypeError):
                    self.client_record.call(
                        self.endpoint, 'POST', '/p', None, {'v': 1}, {},
                        self.credential, 'synthetic-audience')
                factory_spy.assert_not_called()
                transport.assert_not_called()

    def test_f14_proxy_config_whitelist_and_remote_kwargs_remain_payload(self):
        factory = self._provider_factory()
        with factory as factory_spy:
            with self.assertRaises(TypeError):
                self.client_record.get_remote_object(self.endpoint, 'res.partner', unexpected_opt=True)
            factory_spy.assert_not_called()
        with self._patched_provider_factory():
            configured = self.client_record.get_remote_object(
                self.endpoint, 'res.partner', self.credential,
                context={'lang': 'id'}, domain=[('active', '=', True)],
                fields=['name'], offset=1, limit=2, order='name')
        self.assertEqual(configured.context, {'lang': 'id'})
        self.assertEqual(configured.domain, [('active', '=', True)])
        self.assertEqual(configured.fields, ['name'])
        self.assertEqual((configured.offset, configured.limit, configured.order), (1, 2, 'name'))
        proxy_type = __import__(MODULE, fromlist=['RemoteObjectProxy']).RemoteObjectProxy
        remote_client = Mock()
        proxy = proxy_type(
            remote_client, 'res.partner', context={'lang': 'id'}, domain=[],
            fields=['name'], offset=0, limit=10, order='name')
        with self.assertRaises(TypeError):
            proxy_type(remote_client, 'res.partner', unexpected_opt=True)
        remote_client.post.return_value.raise_for_status.return_value = None
        remote_client.post.return_value.json.return_value = {'result': []}
        proxy.custom_remote_method(custom_remote_kw=1)
        sent = remote_client.post.call_args[1]['payload']
        self.assertEqual(sent['params']['kwargs']['custom_remote_kw'], 1)

    def test_f15_factory_url_headers_audience_and_data_are_not_transport_options(self):
        with self._patched_provider_factory():
            service = self.client_record.get_service_client(self.endpoint)
        normalized = Mock(return_value={'X-Test': 'yes'})
        with patch.object(type(self.endpoint), 'request_headers_default', autospec=True,
                          side_effect=lambda endpoint, value: normalized(value)), \
                patch(MODULE + '.requests.request', return_value=Mock(raise_for_status=Mock())) as transport:
            service.call(method='POST', path='/child', url='https://override.invalid/x',
                         headers=None, audience='synthetic-audience', payload={'active_log': 1},
                         raise_exception=False)
        normalized.assert_called_once_with(None)
        sent = transport.call_args[1]
        self.assertEqual(sent['url'], 'https://override.invalid/x')
        self.assertEqual(sent['headers'], {'X-Test': 'yes'})
        self.assertEqual(sent['json'], {'active_log': 1})
        self.assertNotIn('audience', sent)
        self.assertNotIn('credential', sent)
        self.provider.authenticate.reset_mock()
        response = Mock()
        response.raise_for_status.return_value = None
        with self._patched_provider_factory():
            with patch(MODULE + '.requests.request', return_value=response) as model_transport:
                with patch(MODULE + '.report_outcome'):
                    self.client_record.call(
                        self.endpoint, 'POST', '/child', None, {'active_log': 2},
                        {'X-Model': 'yes'}, self.credential,
                        audience='synthetic-audience', url='https://override.invalid/model',
                        raise_exception=False)
        self.assertEqual(model_transport.call_count, 1)
        model_sent = model_transport.call_args[1]
        self.assertEqual(model_sent['url'], 'https://override.invalid/model')
        self.assertEqual(model_sent['headers']['X-Model'], 'yes')
        self.assertEqual(model_sent['json'], {'active_log': 2})
        self.assertNotIn('audience', model_sent)
        self.assertEqual(self.provider.authenticate.call_args[1]['audience'], 'synthetic-audience')

    def test_d5_model_call_duplicate_binding_rejected_before_factory(self):
        factory = self._provider_factory()
        with factory as factory_spy:
            with self.assertRaises(TypeError):
                self.client_record.call(self.endpoint, 'POST', '/p', None, {'v': 1}, {},
                                        self.credential, method='PUT')
            factory_spy.assert_not_called()

    def test_d5_direct_http_wrappers_accept_only_their_declared_options(self):
        client = self._real_service_client()
        response = Mock()
        response.raise_for_status.return_value = None
        direct_calls = (
            lambda: client.get('/read', params={'q': 'get'}, payload={'ignored': 1},
                               headers={'X-Case': 'get'}, url='https://override.invalid/get',
                               audience='aud-get', raise_exception=False),
            lambda: client.post('/write', payload={'v': 'post'}, params={'q': 'post'},
                                headers={'X-Case': 'post'}, url='https://override.invalid/post',
                                audience='aud-post', raise_exception=False),
            lambda: client.put('/update', payload={'v': 'put'}, params={'q': 'put'},
                               headers={'X-Case': 'put'}, url='https://override.invalid/put',
                               audience='aud-put', raise_exception=False),
            lambda: client.delete('/remove', payload={'ignored': 1}, params={'q': 'delete'},
                                  headers={'X-Case': 'delete'}, url='https://override.invalid/delete',
                                  audience='aud-delete', raise_exception=False),
        )
        with patch(MODULE + '.requests.request', return_value=response) as transport:
            with patch.object(client, '_report_sentry'):
                for invoke in direct_calls:
                    invoke()
        self.assertEqual(transport.call_count, 4)
        direct_requests = [entry[1] for entry in transport.call_args_list]
        self.assertEqual([entry['method'] for entry in direct_requests],
                         ['GET', 'POST', 'PUT', 'DELETE'])
        self.assertEqual([entry['url'] for entry in direct_requests], [
            'https://override.invalid/get', 'https://override.invalid/post',
            'https://override.invalid/put', 'https://override.invalid/delete'])
        self.assertEqual([entry['params'] for entry in direct_requests], [
            {'q': 'get'}, {'q': 'post'}, {'q': 'put'}, {'q': 'delete'}])
        self.assertNotIn('json', direct_requests[0])
        self.assertEqual(direct_requests[1]['json'], {'v': 'post'})
        self.assertEqual(direct_requests[2]['json'], {'v': 'put'})
        self.assertNotIn('json', direct_requests[3])
        self.assertEqual([call[1]['audience'] for call in self.provider.authenticate.call_args_list],
                         ['aud-get', 'aud-post', 'aud-put', 'aud-delete'])

    def test_d5_model_http_wrappers_preserve_declared_options(self):
        response = Mock()
        response.raise_for_status.return_value = None
        with self._patched_provider_factory():
            with patch(MODULE + '.requests.request', return_value=response) as transport:
                with patch(MODULE + '.report_outcome'):
                    self.client_record.get(
                        self.endpoint, '/read', {'q': 'get'}, {'X-Case': 'get'},
                        self.credential, 'aud-get')
                    self.client_record.post(
                        self.endpoint, '/write', {'v': 'post'}, {'X-Case': 'post'},
                        self.credential, 'aud-post')
                    self.client_record.put(
                        self.endpoint, '/update', {'v': 'put'}, {'X-Case': 'put'},
                        self.credential, 'aud-put')
                    self.client_record.delete(
                        self.endpoint, '/remove', {'X-Case': 'delete'},
                        self.credential, 'aud-delete')
        self.assertEqual(transport.call_count, 4)
        requests_sent = [entry[1] for entry in transport.call_args_list]
        self.assertEqual([entry['method'] for entry in requests_sent],
                         ['GET', 'POST', 'PUT', 'DELETE'])
        self.assertEqual([entry['url'] for entry in requests_sent], [
            'https://example.invalid/read', 'https://example.invalid/write',
            'https://example.invalid/update', 'https://example.invalid/remove'])
        self.assertEqual([entry['headers']['X-Case'] for entry in requests_sent],
                         ['get', 'post', 'put', 'delete'])
        self.assertEqual(requests_sent[0]['params'], {'q': 'get'})
        self.assertEqual(requests_sent[1]['json'], {'v': 'post'})
        self.assertEqual(requests_sent[2]['json'], {'v': 'put'})
        self.assertNotIn('json', requests_sent[3])
        self.assertEqual([call[1]['audience'] for call in self.provider.authenticate.call_args_list],
                         ['aud-get', 'aud-post', 'aud-put', 'aud-delete'])

    def test_d5_model_call_first_seven_positional_bindings_are_preserved(self):
        response = Mock()
        response.raise_for_status.return_value = None
        with self._patched_provider_factory():
            with patch(MODULE + '.requests.request', return_value=response) as transport:
                self.client_record.call(
                    self.endpoint, 'POST', '/position', {'q': 'synthetic'},
                    {'marker': 'synthetic'}, {'X-Positional': 'yes'}, self.credential)
        self.assertEqual(transport.call_count, 1)
        request = transport.call_args[1]
        self.assertEqual(request['method'], 'POST')
        self.assertEqual(request['url'], 'https://example.invalid/position')
        self.assertEqual(request['params'], {'q': 'synthetic'})
        self.assertEqual(request['json'], {'marker': 'synthetic'})
        self.assertEqual(request['headers']['X-Positional'], 'yes')
        self.assertEqual(request['headers']['Content-Type'], 'application/json')

    def test_d5_entrypoint_unknown_and_duplicate_options_fail_before_provider_or_transport(self):
        client = self._real_service_client()
        self.provider.authenticate.reset_mock()
        direct_calls = [
            lambda: client.prepare_request_context(method='GET', unexpected_opt=True),
            lambda: client.call(method='POST', unexpected_opt=True, raise_exception=False),
            lambda: client.call(method='POST', unexpected_opt=True, raise_exception=True),
            lambda: client.get('/p', unexpected_opt=True),
            lambda: client.post('/p', payload={'v': 1}, unexpected_opt=True),
            lambda: client.put('/p', payload={'v': 1}, unexpected_opt=True),
            lambda: client.delete('/p', unexpected_opt=True),
            lambda: client.get('/p', method='POST'),
            lambda: client.post('/p', method='PUT'),
            lambda: client.put('/p', method='POST'),
            lambda: client.delete('/p', method='GET'),
        ]
        direct_args = ('POST', '/p', {}, {'v': 1})
        for index, name in enumerate(('method', 'path', 'params', 'payload')):
            duplicate_value = {'method': 'PUT', 'path': '/duplicate',
                               'params': {'q': 'duplicate'}, 'payload': {'duplicate': True}}[name]
            direct_calls.append(
                lambda index=index, name=name, duplicate_value=duplicate_value:
                    client.call(*direct_args[:index + 1], **{name: duplicate_value}))
        preparation_args = ('/p', 'POST', {}, {'v': 1})
        for index, name in enumerate(('path', 'method', 'params', 'payload')):
            duplicate_value = {'path': '/duplicate', 'method': 'PUT',
                               'params': {'q': 'duplicate'}, 'payload': {'duplicate': True}}[name]
            direct_calls.append(
                lambda index=index, name=name, duplicate_value=duplicate_value:
                    client.prepare_request_context(
                        *preparation_args[:index + 1], **{name: duplicate_value}))
        with patch(MODULE + '.requests.request', side_effect=AssertionError('transport called')) as transport:
            for invoke in direct_calls:
                self.provider.authenticate.reset_mock()
                with self.assertRaises(TypeError):
                    invoke()
                self.provider.authenticate.assert_not_called()
            transport.assert_not_called()

        provider_factory = patch.object(
            type(self.env['service.auth.factory']), 'create_service_auth',
            return_value=self.provider)
        with provider_factory as auth_factory:
            service_client_type = __import__(MODULE, fromlist=['ServiceClient']).ServiceClient
            model_calls = [
                lambda: service_client_type(
                    self.env, self.endpoint, self.credential, unexpected_opt=True),
                lambda: service_client_type(
                    self.env, self.endpoint, self.credential, endpoint=self.endpoint),
                lambda: self.client_record.get_service_client(self.endpoint, unexpected_opt=True),
                lambda: self.client_record.get_service_client(
                    self.endpoint, service_code=self.endpoint),
                lambda: self.client_record.get_service_client(
                    self.endpoint, self.credential, credential=self.credential),
                lambda: self.client_record.get_service_client(
                    self.endpoint, self.credential, '/p', path='/q'),
                lambda: self.client_record.get_service_client(
                    self.endpoint, self.credential, '/p', 'GET', method='POST'),
                lambda: self.client_record.call(self.endpoint, 'POST', unexpected_opt=True),
                lambda: self.client_record.call(
                    self.endpoint, 'POST', unexpected_opt=True, raise_exception=False),
                lambda: self.client_record.call(
                    self.endpoint, 'POST', unexpected_opt=True, raise_exception=True),
                lambda: self.client_record.get(self.endpoint, '/p', url='https://example.invalid'),
                lambda: self.client_record.post(self.endpoint, '/p', {'v': 1}, params={'q': 'x'}),
                lambda: self.client_record.put(self.endpoint, '/p', {'v': 1}, params={'q': 'x'}),
                lambda: self.client_record.delete(self.endpoint, '/p', payload={'v': 1}),
                lambda: self.client_record.get(self.endpoint, '/p', path='/q'),
                lambda: self.client_record.post(
                    self.endpoint, '/p', {'v': 1}, payload={'duplicate': True}),
                lambda: self.client_record.put(
                    self.endpoint, '/p', {'v': 1}, payload={'duplicate': True}),
                lambda: self.client_record.delete(self.endpoint, '/p', path='/q'),
                lambda: self.client_record.get_remote_object(
                    self.endpoint, 'res.partner', unexpected_opt=True),
            ]
            model_args = (self.endpoint, 'POST', '/p', {}, {'v': 1}, {}, self.credential)
            model_names = ('service', 'method', 'path', 'params', 'payload', 'headers', 'credential')
            for index, name in enumerate(model_names):
                duplicate_value = model_args[index]
                model_calls.append(
                    lambda index=index, name=name, duplicate_value=duplicate_value:
                        self.client_record.call(
                            *model_args[:index + 1], **{name: duplicate_value}))
            with patch(MODULE + '.requests.request',
                       side_effect=AssertionError('transport called for rejected factory option')) as transport:
                for invoke in model_calls:
                    auth_factory.reset_mock()
                    with self.assertRaises(TypeError):
                        invoke()
                    auth_factory.assert_not_called()
                transport.assert_not_called()

    def _real_service_client(self):
        with self._patched_provider_factory():
            return self.client_record.get_service_client(self.endpoint)

    def _patched_provider_factory(self):
        return patch.object(
            type(self.env['service.auth.factory']), 'create_service_auth',
            return_value=self.provider)
