"""Offline characterization for payload/action/log branches (no Odoo runtime)."""
from support import *
import json
from unittest import mock


class Actions(OfflineCase):
    @classmethod
    def setUpClass(cls):
        cls.m = load('models/service_client.py')

    class PayloadSet(list):
        pass

    class Records:
        def __init__(self, label='records'):
            self.label = label
            self.contexts = []

        def with_context(self, context):
            self.contexts.append(dict(context or {}))
            return self

    class Action:
        def __init__(self, result='synthetic-next'):
            self.result = result
            self.run_count = 0
            self.context = None

        def with_context(self, context):
            self.context = context
            return self

        def run(self):
            self.run_count += 1
            return self.result

    class LogModel:
        def __init__(self, rows):
            self.rows = rows

        def sudo(self):
            return self

        def create(self, values):
            self.rows.append(values)
            return values

    class LogEnv(dict):
        pass

    def _safe_eval(self, expression, context, mode='eval', **kwargs):
        """Closed interpreter for only the synthetic expressions used by tests."""
        expression = expression.strip()
        if mode == 'exec':
            if expression == 'response = [{}]':
                context['response'] = [{}]
            elif expression == 'response = [{}, {}]':
                context['response'] = [{}, {}]
            elif expression == 'response = None':
                context['response'] = None
            elif expression == 'method = "PATCH"':
                context['method'] = 'PATCH'
            elif expression:
                raise AssertionError('unexpected synthetic exec expression')
            return None
        if expression == '6 * 7':
            return 42
        if expression == "ctx['name']":
            return context['ctx']['name']
        if expression == 'invalid-expression':
            raise ValueError('synthetic invalid expression')
        raise AssertionError('unexpected synthetic eval expression')

    def _payload_set(self, rows):
        cls = type('PayloadSet', (list,), {
            'get_payload': self.m.ServiceClientPayload.get_payload,
            'custom_render': self.m.ServiceClientPayload.custom_render,
        })
        return cls(rows)

    def test_payload_fixed_expression_template_random_invalid_none_negative_and_duplicate(self):
        rows = [
            types.SimpleNamespace(key='fixed', type='fix', value='synthetic'),
            types.SimpleNamespace(key='expression', type='exp', value='6 * 7'),
            types.SimpleNamespace(key='template', type='exp', value='hello ${ctx[\'name\']}'),
            types.SimpleNamespace(key='invalid_template', type='exp', value='${invalid-expression}'),
            types.SimpleNamespace(key='random', type='random_int', value='3'),
            types.SimpleNamespace(key='negative', type='random_int', value='-3'),
            types.SimpleNamespace(key='duplicate', type='fix', value='first'),
            types.SimpleNamespace(key='duplicate', type='fix', value='last'),
        ]
        payloads = self._payload_set(rows)
        context = {'ctx': {'name': 'synthetic-name'}}
        with mock.patch.object(self.m, 'safe_eval', side_effect=self._safe_eval), mock.patch.object(self.m.random, 'randint', return_value=2) as randint:
            payload = payloads.get_payload(context)
        self.assertEqual(payload['fixed'], 'synthetic')
        self.assertEqual(payload['expression'], 42)
        self.assertEqual(payload['template'], 'hello synthetic-name')
        self.assertEqual(payload['invalid_template'], '')
        self.assertEqual((payload['random'], payload['negative']), (2, 2))
        self.assertEqual(payload['duplicate'], 'last')
        self.assertEqual(randint.call_args_list[0].args, (0, 3))
        self.assertEqual(randint.call_args_list[1].args, (0, 1000))
        with self.assertRaises(AttributeError):
            self._payload_set([types.SimpleNamespace(key='none', type='random_int', value=None)]).get_payload({})

    def _factory(self, client, *, iteration='response = [{}]', code='', handle='', each_record=False):
        factory = object.__new__(self.m.ServiceClientFactory)
        factory.ensure_one = lambda: None
        factory._get_eval_context = lambda: {'ctx': {}}
        factory.iteration = iteration
        factory.code = code
        factory.handle = handle
        factory.each_record = each_record
        factory.payload_ids = self._payload_set([])
        factory.endpoint_id = 'synthetic-endpoint'
        factory.credential_id = 'synthetic-credential'
        factory.action_next_id = self.Action()
        factory.error_handle_id = False
        factory.get_service_client = lambda *args, **kwargs: client
        return factory

    def test_action_iteration_next_action_and_each_record_duplicate_replay(self):
        calls = []
        client = types.SimpleNamespace(call=lambda *args: (calls.append(args) or 'synthetic-response'))
        factory = self._factory(client, iteration='response = [{}, {}]', each_record=True)
        records = [self.Records('one'), self.Records('two')]
        with mock.patch.object(self.m, 'safe_eval', side_effect=self._safe_eval):
            result = factory.run_action_service_client({'records': records, 'ctx': {}})
        self.assertEqual(len(calls), 4)
        self.assertEqual(result, 'synthetic-next')
        self.assertEqual(factory.action_next_id.run_count, 4)

    def test_error_handler_present_swallows_and_absent_reraises(self):
        client = types.SimpleNamespace(call=mock.Mock(side_effect=RuntimeError('synthetic-call-error')))
        records = self.Records()
        factory = self._factory(client)
        handler = self.Action(result='synthetic-handled')
        factory.error_handle_id = handler
        with mock.patch.object(self.m, 'safe_eval', side_effect=self._safe_eval):
            self.assertIsNone(factory.run_action_service_client({'records': records, 'ctx': {}}))
        self.assertEqual(handler.run_count, 1)
        factory.error_handle_id = False
        with mock.patch.object(self.m, 'safe_eval', side_effect=self._safe_eval):
            with self.assertRaisesRegex(RuntimeError, 'synthetic-call-error'):
                factory.run_action_service_client({'records': records, 'ctx': {}})

    def test_malformed_iteration_response_none_raises_without_remote_call(self):
        calls = []
        client = types.SimpleNamespace(call=lambda *args: calls.append(args))
        factory = self._factory(client, iteration='response = None')
        with mock.patch.object(self.m, 'safe_eval', side_effect=self._safe_eval):
            with self.assertRaises(TypeError):
                factory.run_action_service_client({'records': self.Records(), 'ctx': {}})
        self.assertEqual(calls, [])

    def test_send_request_does_not_enforce_active_flag(self):
        factory = object.__new__(self.m.ServiceClientFactory)
        factory.active = False
        factory.ensure_one = lambda: None
        factory._get_eval_context = lambda: {'ctx': {}}
        seen = []
        factory.run_action_service_client = lambda eval_context=None: seen.append(eval_context)
        records = self.Records()
        factory.send_request(records)
        self.assertEqual(len(seen), 1)
        self.assertIs(seen[0]['records'], records)

    def _send(self, active_log=True):
        rows = []
        send = object.__new__(self.m.ServiceClientSend)
        send.active_log = active_log
        send.payload = {'body': 'synthetic-body'}
        send.service_client = types.SimpleNamespace(prepare_request_context=lambda **kwargs: {
            'url': 'https://resource.example.invalid/path',
            'headers': {'Authorization': 'synthetic-header'},
            'params': {'query': 'synthetic-query'},
            'json': {'body': 'synthetic-body'},
            'timeout': 3,
        })
        send.env = self.LogEnv({'service.client.log': self.LogModel(rows)})
        send.client_id = send.endpoint_id = send.credential_id = None
        return send, rows

    def test_dispatch_log_removes_headers_but_keeps_url_params_json(self):
        send, rows = self._send(active_log=True)
        response = types.SimpleNamespace(text='synthetic-response', raise_for_status=lambda: None)
        with mock.patch.object(self.m.requests, 'request', return_value=response) as request:
            created = send.dispatch_send()
        self.assertEqual(len(rows), 1)
        self.assertIs(created, rows[0])
        row = rows[0]
        self.assertEqual(row['state'], 'done')
        saved = json.loads(row['request_context'])
        self.assertNotIn('headers', saved)
        self.assertEqual(saved['url'], 'https://resource.example.invalid/path')
        self.assertEqual(saved['params'], {'query': 'synthetic-query'})
        self.assertEqual(saved['json'], {'body': 'synthetic-body'})
        self.assertEqual(request.call_args.kwargs['headers']['Authorization'], 'synthetic-header')

    def test_http_500_is_logged_as_error_and_forces_logging(self):
        send, rows = self._send(active_log=False)
        response = types.SimpleNamespace(text='synthetic-error-body')
        error = self.m.requests.HTTPError('synthetic-http-error')
        error.response = response
        response.raise_for_status = mock.Mock(side_effect=error)
        with mock.patch.object(self.m.requests, 'request', return_value=response):
            send.dispatch_send()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['state'], 'error')
        self.assertIn('synthetic-error-body', rows[0]['response'])
        self.assertNotIn('headers', json.loads(rows[0]['request_context']))

    def test_active_log_false_success_does_not_create_log(self):
        send, rows = self._send(active_log=False)
        response = types.SimpleNamespace(text='synthetic-response', raise_for_status=lambda: None)
        with mock.patch.object(self.m.requests, 'request', return_value=response):
            self.assertIsNone(send.dispatch_send())
        self.assertEqual(rows, [])

    def test_unexpected_error_with_no_response_raises_attribute_error(self):
        send, rows = self._send(active_log=False)
        with mock.patch.object(self.m.requests, 'request', side_effect=RuntimeError('synthetic-error')):
            with self.assertRaises(AttributeError):
                send.dispatch_send()
        self.assertEqual(rows, [])
