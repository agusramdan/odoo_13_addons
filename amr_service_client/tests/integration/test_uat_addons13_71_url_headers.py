# -*- coding: utf-8 -*-
"""Native ORM UAT source for ADDONS13-71 URL/header amendments.

All URLs use example.invalid and all HTTP transport is patched. The fixture uses
synthetic ORM records; no external HTTP request is intended.
"""
from unittest.mock import patch

from odoo.tests.common import TransactionCase


class TestUatAddons1371UrlHeaders(TransactionCase):
    def setUp(self):
        super(TestUatAddons1371UrlHeaders, self).setUp()
        self.endpoint = self.env['service.endpoint'].create({
            'name': 'AU URL headers endpoint',
            'code': 'au_url_headers_endpoint',
            'source': 'value',
            'base_url_value': 'https://example.invalid',
            'content_type_default': 'text/plain',
        })
        partner_model = self.env['ir.model'].search(
            [('model', '=', 'res.partner')], limit=1)
        self.assertTrue(partner_model)
        self.client_record = self.env['service.client'].create({
            'name': 'AU URL headers client',
            'model_id': partner_model.id,
            'endpoint_id': self.endpoint.id,
        })

    def _client(self, endpoint=True, path='stored'):
        record = self.client_record if endpoint else self.env['service.client']
        endpoint_record = self.endpoint if endpoint else self.env['service.endpoint']
        return record.get_service_client(endpoint_record, path=path, method='GET')

    def _endpoint_method_patch(self, method_name, **kwargs):
        endpoint_class = type(self.endpoint)
        if not kwargs:
            kwargs['side_effect'] = getattr(endpoint_class, method_name)
        return patch.object(endpoint_class, method_name, autospec=True, **kwargs)

    def _identity_provider(self, client):
        return patch.object(client.provider, 'authenticate',
                            side_effect=lambda context, audience=None: context)

    def test_au01_endpoint_url_override_bypasses_path_and_keeps_header_defaults(self):
        client = self._client(path='stored')
        with self._endpoint_method_patch('get_url') as get_url, \
                self._identity_provider(client):
            context = client.prepare_request_context(
                method='GET', path='child', url='https://override.invalid/x')
        self.assertEqual(context['url'], 'https://override.invalid/x')
        get_url.assert_not_called()
        self.assertEqual(context['headers'], {
            'Content-Type': 'text/plain', 'Accept': 'application/json'})

    def test_au02_without_endpoint_truthy_override_ignores_both_paths(self):
        client = self._client(endpoint=False, path='stored')
        with self._identity_provider(client):
            context = client.prepare_request_context(
                method='GET', path='child', url='https://override.invalid/x')
        self.assertEqual(context['url'], 'https://override.invalid/x')
        self.assertNotIn('timeout', context)

    def test_au03_endpoint_none_url_uses_per_call_child_path(self):
        client = self._client(path='stored')
        with self._endpoint_method_patch('get_url',
                          side_effect=lambda endpoint, path: 'https://example.invalid/result') as get_url, \
                self._identity_provider(client):
            context = client.prepare_request_context(method='GET', path='child', url=None)
        self.assertEqual(get_url.call_args[0], (self.endpoint, 'child'))
        self.assertEqual(context['url'], 'https://example.invalid/result')

    def test_au04_empty_override_and_path_fall_back_to_stored_path(self):
        client = self._client(path='stored')
        with self._endpoint_method_patch('get_url',
                          side_effect=lambda endpoint, path: 'https://example.invalid/stored') as get_url, \
                self._identity_provider(client):
            context = client.prepare_request_context(method='GET', path='', url='')
        self.assertEqual(get_url.call_args[0], (self.endpoint, 'stored'))
        self.assertEqual(context['url'], 'https://example.invalid/stored')

    def test_au05_none_paths_call_endpoint_and_omit_none_url_result(self):
        client = self._client(path=None)
        with self._endpoint_method_patch('get_url',
                side_effect=[None, 'https://example.invalid/truthy']) as get_url, \
                self._identity_provider(client):
            context = client.prepare_request_context(method='GET', path=None, url=None)
            truthy_context = client.prepare_request_context(
                method='GET', path=None, url=None)
        self.assertEqual(get_url.call_args_list[0][0], (self.endpoint, None))
        self.assertEqual(get_url.call_args_list[1][0], (self.endpoint, None))
        self.assertNotIn('url', context)
        self.assertEqual(truthy_context['url'], 'https://example.invalid/truthy')

    def test_au06_without_endpoint_omits_falsy_url_and_ignores_paths(self):
        client = self._client(endpoint=False, path='stored')
        with self._identity_provider(client):
            for url in (None, ''):
                context = client.prepare_request_context(
                    method='GET', path='child', url=url)
                self.assertNotIn('url', context)

    def test_au07_params_are_included_only_when_truthy(self):
        client = self._client(endpoint=False)
        with self._identity_provider(client):
            truthy = client.prepare_request_context(
                method='GET', url='https://example.invalid/x', params={'q': 'x'})
            empty = client.prepare_request_context(
                method='GET', url='https://example.invalid/x', params={})
            none = client.prepare_request_context(
                method='GET', url='https://example.invalid/x', params=None)
        self.assertEqual(truthy['params'], {'q': 'x'})
        self.assertNotIn('params', empty)
        self.assertNotIn('params', none)

    def test_au08_real_endpoint_normalizes_none_and_empty_headers(self):
        client = self._client()
        with self._identity_provider(client):
            for headers in (None, {}):
                context = client.prepare_request_context(
                    method='GET', path='child', headers=headers)
                self.assertEqual(context['headers'], {
                    'Content-Type': 'text/plain', 'Accept': 'application/json'})

    def test_au09_real_endpoint_preserves_custom_headers_and_adds_accept(self):
        client = self._client()
        supplied = {'Content-Type': 'application/json', 'X-Test': 'v'}
        with self._identity_provider(client):
            context = client.prepare_request_context(
                method='GET', path='child', headers=supplied)
        self.assertEqual(context['headers'], {
            'Content-Type': 'application/json', 'X-Test': 'v',
            'Accept': 'application/json'})

    def test_au10_normalizer_receives_original_truthy_and_falsy_values(self):
        client = self._client()
        sent = []
        def empty_normalizer(value):
            sent.append(value)
            return {}
        with self._endpoint_method_patch('request_headers_default',
                          side_effect=lambda endpoint, value: empty_normalizer(value)), self._identity_provider(client):
            truthy_context = client.prepare_request_context(
                method='GET', path='child', headers={'X-Test': 'v'})
            none_context = client.prepare_request_context(
                method='GET', path='child', headers=None)
        self.assertEqual(len(sent), 2)
        self.assertEqual(sent[0], {'X-Test': 'v'})
        self.assertIsNone(sent[1])
        self.assertNotIn('headers', truthy_context)
        self.assertNotIn('headers', none_context)

    def test_au11_without_endpoint_preserves_only_truthy_headers(self):
        client = self._client(endpoint=False)
        supplied = {'X-Test': 'v'}
        with self._identity_provider(client):
            truthy = client.prepare_request_context(
                method='GET', url='https://example.invalid/x', headers=supplied)
            empty = client.prepare_request_context(
                method='GET', url='https://example.invalid/x', headers={})
            none = client.prepare_request_context(
                method='GET', url='https://example.invalid/x', headers=None)
        self.assertIs(truthy['headers'], supplied)
        self.assertNotIn('headers', empty)
        self.assertNotIn('headers', none)

    def test_au12_provider_can_add_authorization_after_preparation(self):
        client = self._client(endpoint=False)
        observed = []
        def provider(context, audience=None):
            observed.append(dict(context))
            context.setdefault('headers', {})['Authorization'] = 'synthetic-token'
            return context
        with patch.object(client.provider, 'authenticate', side_effect=provider):
            result = client.prepare_request_context(
                method='GET', url='https://example.invalid/x', headers=None)
        self.assertNotIn('headers', observed[0])
        self.assertEqual(result['headers'], {'Authorization': 'synthetic-token'})

    def test_au13_strict_headers_provider_exposes_missing_key(self):
        client = self._client(endpoint=False)
        # Candidate-only assertion; pinned baseline comparison is external.
        def strict_provider(context, audience=None):
            return context['headers']
        with patch.object(client.provider, 'authenticate', side_effect=strict_provider):
            with self.assertRaises(KeyError) as caught:
                client.prepare_request_context(
                    method='GET', url='https://example.invalid/x', headers=None)
        self.assertEqual(caught.exception.args, ('headers',))

    def test_au14_strict_url_provider_exposes_missing_key(self):
        client = self._client(endpoint=False)
        # Candidate-only assertion; pinned baseline comparison is external.
        def strict_provider(context, audience=None):
            return context['url']
        with patch.object(client.provider, 'authenticate', side_effect=strict_provider):
            with self.assertRaises(KeyError) as caught:
                client.prepare_request_context(method='GET', url=None)
        self.assertEqual(caught.exception.args, ('url',))
