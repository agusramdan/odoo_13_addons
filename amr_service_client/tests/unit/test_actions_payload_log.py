"""U07 offline characterization; doubles are not Odoo ORM or security acceptance."""
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest import mock
import requests


class UserError(Exception):
    pass


def load_sources():
    addon = Path(__file__).resolve().parents[2]
    fields = types.ModuleType('odoo.fields')
    for name in ('Boolean', 'Char', 'Many2one', 'One2many', 'Text', 'Selection'):
        setattr(fields, name, lambda *a, **k: None)
    fields.Date = fields.Datetime = types.SimpleNamespace(to_string=str)
    odoo = types.ModuleType('odoo')
    odoo.fields = fields
    odoo.models = types.SimpleNamespace(Model=type('Model', (), {}), AbstractModel=type('AbstractModel', (), {}))
    odoo.api = types.SimpleNamespace(model=lambda f: f, returns=lambda *a, **k: lambda f: f,
                                     constrains=lambda *a: lambda f: f)
    odoo._ = lambda s: s
    tools = types.ModuleType('odoo.tools')
    tools.config = {}
    odoo.tools = tools
    safe = types.ModuleType('odoo.tools.safe_eval')
    def evaluate(code, context, mode='eval', nocopy=False):
        if mode == 'exec':
            exec(code, {}, context)
            return None
        return eval(code, {}, context)
    safe.safe_eval = evaluate
    safe.test_python_expr = lambda *a, **k: None
    exceptions = types.ModuleType('odoo.exceptions')
    exceptions.ValidationError = type('ValidationError', (Exception,), {})
    exceptions.UserError = UserError
    reporting = types.ModuleType('u07.services.sentry_reporting')
    reporting.report_outcome = reporting.report_sentry = lambda *a, **k: None
    modules = {'odoo': odoo, 'odoo.fields': fields, 'odoo.tools': tools,
               'odoo.tools.safe_eval': safe, 'odoo.exceptions': exceptions,
               'u07.services.sentry_reporting': reporting}
    for name, path in (('u07', addon), ('u07.models', addon / 'models'), ('u07.services', addon / 'services')):
        module = types.ModuleType(name)
        module.__path__ = [str(path)]
        modules[name] = module
    result = []
    with mock.patch.dict(sys.modules, modules):
        for filename in ('service_client', 'service_client_log', 'actions_server'):
            spec = importlib.util.spec_from_file_location('u07.models.' + filename, str(addon / 'models' / (filename + '.py')))
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            result.append(module)
    return result


client_mod, log_mod, action_mod = load_sources()


class Payload(client_mod.ServiceClientPayload):
    def __init__(self, rows):
        self.rows = [types.SimpleNamespace(key=k, type=t, value=v) for k, t, v in rows]
    def __iter__(self):
        return iter(self.rows)


class Records:
    def __init__(self, values):
        self.values = values
    def __iter__(self):
        return iter(self.values)
    def with_context(self, context):
        return self


class ActionSink:
    def __init__(self, result=None):
        self.contexts = []
        self.result = result
    def with_context(self, context):
        self.contexts.append(dict(context))
        return self
    def run(self):
        return self.result


class Factory(client_mod.ServiceClientFactory):
    def __init__(self):
        self.env = types.SimpleNamespace(context={}, user=object())
        self.iteration = "response = [{'n': 1}, {'n': 2}]"
        self.code = "path = '/synthetic'; method = 'PUT'"
        self.handle = "handled = response"
        self.active = True
        self.each_record = False
        self.payload_ids = Payload([('n', 'exp', "ctx['n']")])
        self.endpoint_id = object()
        self.credential_id = None
        self.error_handle_id = None
        self.action_next_id = ActionSink('next')
        self.client = types.SimpleNamespace(call=mock.Mock(return_value='ok'), _report_sentry=mock.Mock())
    def ensure_one(self):
        pass
    def get_service_client(self, endpoint, credential=None):
        return self.client


class Log(log_mod.ServiceClientLog):
    def __init__(self):
        self.rows = []
    def sudo(self):
        return self
    def create(self, values):
        self.rows.append(values)
        return values


class U07(unittest.TestCase):
    def test_inactive_client_rejected_before_side_effects(self):
        for entrypoint in ('run_action_service_client', 'send_request'):
            factory = Factory()
            factory.active = False
            factory._run_action_iteration = mock.Mock(return_value={'response': []})
            factory.payload_ids = mock.Mock(get_payload=mock.Mock(return_value={}))
            factory._run_action_code = mock.Mock(return_value=None)
            factory._run_action_handle = mock.Mock(return_value=None)
            factory.get_service_client = mock.Mock(return_value=factory.client)
            factory.client.call = mock.Mock(return_value='ok')
            factory.action_next_id = ActionSink('next')
            factory.error_handle_id = ActionSink()
            with mock.patch.object(client_mod._logger, 'debug') as logger:
                method = getattr(factory, entrypoint)
                with self.assertRaises(UserError) as caught:
                    if entrypoint == 'send_request':
                        method(Records([1]))
                    else:
                        method({'records': Records([1])})
            self.assertEqual(str(caught.exception), 'Service client is inactive.')
            factory._run_action_iteration.assert_not_called()
            factory.payload_ids.get_payload.assert_not_called()
            factory._run_action_code.assert_not_called()
            factory._run_action_handle.assert_not_called()
            factory.get_service_client.assert_not_called()
            factory.client.call.assert_not_called()
            self.assertEqual(factory.action_next_id.contexts, [])
            self.assertEqual(factory.error_handle_id.contexts, [])
            logger.assert_not_called()

    def test_active_client_control_executes_request_and_action(self):
        factory = Factory()
        context = factory._get_eval_context()
        context['records'] = Records([1])
        self.assertEqual(factory.run_action_service_client(context), 'next')
        self.assertEqual(factory.client.call.call_count, 2)
        self.assertEqual(len(factory.action_next_id.contexts), 2)

    def test_payload_types_duplicates_and_random_bounds(self):
        p = Payload([('fixed', 'fix', 'text'), ('expr', 'exp', 'x + 2'),
                     ('template', 'exp', 'v=${x}'), ('r', 'random_int', '7'),
                     ('fallback', 'random_int', '-1'), ('fixed', 'fix', 'last'),
                     ('unknown', 'other', 'ignored')])
        with mock.patch.object(client_mod.random, 'randint', side_effect=[3, 8]) as rand:
            self.assertEqual(p.get_payload({'x': 4}), {'fixed': 'last', 'expr': 6, 'template': 'v=4', 'r': 3, 'fallback': 8, 'unknown': None})
        self.assertEqual(rand.call_args_list, [mock.call(0, 7), mock.call(0, 1000)])
        error = ZeroDivisionError('division by zero')
        with self.assertRaises(ZeroDivisionError) as caught:
            Payload([('bad', 'exp', '1 / 0')]).get_payload({})
        self.assertEqual(str(caught.exception), str(error))
        with mock.patch.object(client_mod._logger, 'error') as logger:
            self.assertEqual(Payload([('bad', 'exp', '${missing}')]).get_payload({}), {'bad': ''})
            self.assertEqual(logger.call_count, 1)

    def test_random_int_none_value_raises_attribute_error(self):
        with self.assertRaises(AttributeError):
            Payload([('none', 'random_int', None)]).get_payload({})

    def action_contract(self):
        factory = Factory()
        context = factory._get_eval_context()
        self.assertIs(context['service_client'], factory)
        context['records'] = Records([1])
        self.assertEqual(factory.run_action_service_client(context), 'next')
        self.assertEqual(factory.client.call.call_count, 2)
        calls = factory.client.call.call_args_list
        self.assertEqual([c[1]['payload'] for c in calls], [{'n': 1}, {'n': 2}])
        self.assertEqual([c[1]['method'] for c in calls], ['PUT', 'PUT'])
        self.assertEqual(len(factory.action_next_id.contexts), 2)
        self.assertIs(factory.action_next_id.contexts[0]['service_client'], factory)

    def test_iteration_action_context_and_next(self):
        self.action_contract()

    def test_each_record_replays_iteration_for_every_record(self):
        factory = Factory()
        factory.each_record = True
        records = [types.SimpleNamespace(name='first', with_context=mock.Mock(return_value='first-context')),
                   types.SimpleNamespace(name='second', with_context=mock.Mock(return_value='second-context'))]
        context = factory._get_eval_context()
        context['records'] = Records(records)

        self.assertEqual(factory.run_action_service_client(context), 'next')
        self.assertEqual(factory.client.call.call_count, 4)
        self.assertEqual([call[1]['payload'] for call in factory.client.call.call_args_list],
                         [{'n': 1}, {'n': 2}, {'n': 1}, {'n': 2}])
        self.assertEqual([call[1]['method'] for call in factory.client.call.call_args_list],
                         ['PUT', 'PUT', 'PUT', 'PUT'])
        self.assertEqual(len(factory.action_next_id.contexts), 4)
        self.assertTrue(all(item['service_client'] is factory for item in factory.action_next_id.contexts))

    def test_none_iteration_response_raises_before_remote_call(self):
        factory = Factory()
        factory.iteration = 'response = None'
        context = factory._get_eval_context()
        context['records'] = Records([1])

        with self.assertRaises(TypeError):
            factory.run_action_service_client(context)
        factory.client.call.assert_not_called()

    def test_mutation_control_iteration_is_observable(self):
        original = client_mod.safe_eval
        def mutant(code, context, mode='eval', nocopy=False):
            if code.startswith('response ='):
                context['response'] = [{'n': 1}]
                return None
            return original(code, context, mode=mode, nocopy=nocopy)
        with mock.patch.object(client_mod, 'safe_eval', mutant):
            with self.assertRaises(AssertionError):
                self.action_contract()

    def test_invalid_iteration_and_handler_characterization(self):
        factory = Factory()
        context = factory._get_eval_context()
        context['records'] = Records([1])
        factory.iteration = 'response = [42]'
        with self.assertRaises(TypeError):
            factory.run_action_service_client(context)
        self.assertEqual(factory.client.call.call_count, 0)
        factory.iteration = 'response = [{}]'
        factory.payload_ids = Payload([])
        failure = ValueError('synthetic failure')
        factory.client.call.side_effect = failure
        with self.assertRaises(ValueError) as caught:
            factory.run_action_service_client(context)
        self.assertIs(caught.exception, failure)
        self.assertEqual(factory.client.call.call_count, 1)
        self.assertEqual(factory.action_next_id.contexts, [])
        factory.error_handle_id = ActionSink()
        self.assertIsNone(factory.run_action_service_client(context))
        self.assertIs(factory.error_handle_id.contexts[0]['exception'], failure)
        self.assertEqual(len(factory.action_next_id.contexts), 0)

    def test_server_action_delegation_and_recompute(self):
        target = types.SimpleNamespace(run_action_service_client=mock.Mock(return_value='done'))
        action = types.SimpleNamespace(service_client_id=target)
        server = action_mod.ServerActions()
        server._is_recompute = lambda action: False
        ctx = {'records': 'synthetic'}
        self.assertEqual(server.run_action_service_client_multi(action, ctx), 'done')
        target.run_action_service_client.assert_called_once_with(eval_context=ctx)
        server._is_recompute = lambda action: True
        self.assertIs(server.run_action_service_client_multi(action, ctx), False)
        self.assertEqual(target.run_action_service_client.call_count, 1)

    def test_log_creation_helpers_are_private(self):
        self.assertFalse(hasattr(log_mod.ServiceClientLog, 'create_log'))
        self.assertFalse(hasattr(log_mod.ServiceClientLog, 'create_error'))
        self.assertTrue(callable(getattr(log_mod.ServiceClientLog, '_create_log', None)))
        self.assertTrue(callable(getattr(log_mod.ServiceClientLog, '_create_error', None)))

    def test_log_minimizes_data_preserves_input_and_relations(self):
        import copy
        log = Log()
        context = {'url': 'https://example.invalid/x', 'headers': {'X': 'synthetic'}, 'params': {'a': 1}, 'json': {'b': 2}}
        original = copy.deepcopy(context)
        client, endpoint, credential = (types.SimpleNamespace(id=i) for i in (11, 12, 13))
        log._create_log('done', client_id=client, endpoint_id=endpoint, credential_id=credential,
                       request_context=context, response_text='ok')
        row = log.rows[0]
        self.assertEqual((row['state'], row['client_id'], row['endpoint_id'], row['credential_id']), ('done', 11, 12, 13))
        self.assertTrue(row['request_context'] is None)
        self.assertTrue(row['response'] is None)
        self.assertTrue(context == original)

    def test_log_adversarial_inputs_and_controls(self):
        import copy
        markers = ['SYNTH_U07_PATH_11', 'SYNTH_U07_QUERY_12', 'SYNTH_U07_KEY_13',
                   'SYNTH_U07_PARAM_14', 'SYNTH_U07_BODY_15', 'SYNTH_U07_HEADER_16',
                   'SYNTH_U07_RESPONSE_17']
        context = {'url': 'https://example.invalid/' + markers[0] + '?' + markers[1],
                   'params': {markers[2]: {'nested': [markers[3]]}},
                   'json': {'nested': [markers[4]]}, 'headers': {'X': markers[5]}}
        original = copy.deepcopy(context)
        log = Log()
        log._create_log('error', request_context=context, response_text=markers[6])
        row = log.rows[0]
        sensor = lambda value: any(marker in str(value) for marker in markers)
        self.assertTrue(sensor(markers))  # positive control
        self.assertFalse(sensor('clean'))  # negative control
        self.assertFalse(any(sensor(value) for value in row.values()))
        self.assertTrue(context == original)
        self.assertEqual(row['state'], 'error')
        self.assertTrue(row['request_context'] is None)
        self.assertTrue(row['response'] is None)
        for request, response in ((None, None), ({}, b'\xff'), (['malformed'], {'nested': markers[6]})):
            log._create_log('outgoing', request_context=request, response_text=response)
            self.assertTrue(log.rows[-1]['request_context'] is None)
            self.assertTrue(log.rows[-1]['response'] is None)

    def leak_observation(self, marker):
        log = Log()
        log._create_log('error', request_context={'url': 'https://example.invalid/' + marker}, response_text=marker)
        return tuple(marker in str(log.rows[0].get(key)) for key in ('request_context', 'response'))

    def test_synthetic_marker_sensor_and_minimized_log(self):
        # Historical baseline independently observed (True, True), before remediation.
        marker = 'SYNTHETIC_U07_MARKER_8c42'
        self.assertEqual((marker in marker, marker in marker), (True, True))
        self.assertEqual((marker in 'clean', marker in ''), (False, False))
        self.assertEqual(self.leak_observation(marker), (False, False))

    def test_owner_target_no_secret_in_log(self):
        # Regression oracle for the accepted minimized-log target.
        self.assertEqual(self.leak_observation('SYNTHETIC_U07_TARGET_5a17'), (False, False))

    def test_minimized_new_log_replay_is_rejected_without_side_effects(self):
        log = Log()
        marker = 'SYNTHETIC_SECRET_REPLAY_987'
        row = log._create_log('outgoing', request_context={'headers': {'Authorization': marker}}, response_text=marker)
        log.request_context = row['request_context']
        client = types.SimpleNamespace(provider=types.SimpleNamespace(authenticate=mock.Mock()), _report_sentry=mock.Mock())
        log.client_id = types.SimpleNamespace(get_service_client=mock.Mock(return_value=client))
        log.endpoint_id = types.SimpleNamespace(request_headers_default=mock.Mock(), audience=marker)
        log.credential_id = object()
        log.write = mock.Mock()
        with mock.patch.object(log_mod.requests, 'request') as transport:
            with self.assertRaises(UserError) as caught:
                log.send()
        self.assertNotIn(marker, str(caught.exception))
        self.assertTrue(str(caught.exception))
        log.client_id.get_service_client.assert_not_called()
        log.endpoint_id.request_headers_default.assert_not_called()
        client.provider.authenticate.assert_not_called()
        client._report_sentry.assert_not_called()
        transport.assert_not_called()
        log.write.assert_not_called()

    def test_valid_legacy_log_replay_remains_reachable(self):
        import json
        log = Log()
        context = {'method': 'POST', 'url': 'https://example.invalid/', 'headers': {'X': 'legacy'}, 'json': {'n': 3}}
        log.request_context = json.dumps(context)
        provider = types.SimpleNamespace(authenticate=mock.Mock(side_effect=lambda ctx, audience: ctx))
        client = types.SimpleNamespace(provider=provider, _report_sentry=mock.Mock())
        log.client_id = types.SimpleNamespace(get_service_client=mock.Mock(return_value=client))
        log.endpoint_id = types.SimpleNamespace(request_headers_default=mock.Mock(side_effect=lambda headers: headers), audience='audience')
        log.credential_id = object()
        log.write = mock.Mock()
        response = types.SimpleNamespace(text='ok', raise_for_status=mock.Mock())
        with mock.patch.object(log_mod.requests, 'request', return_value=response) as transport:
            self.assertIs(log.send(), log)
        log.client_id.get_service_client.assert_called_once_with(log.endpoint_id, log.credential_id)
        log.endpoint_id.request_headers_default.assert_called_once_with({'X': 'legacy'})
        provider.authenticate.assert_called_once_with(context, 'audience')
        transport.assert_called_once_with(**context)
        log.write.assert_called_once_with({'state': 'done', 'response': 'ok'})
        client._report_sentry.assert_called_once_with(response=response, exception=None, method='POST')

    def test_before_response_and_log_failure_characterization(self):
        log = Log()
        service = types.SimpleNamespace(env={'service.client.log': log}, client_id=None,
            endpoint_id=None, prepare_request_context=mock.Mock(side_effect=ValueError('synthetic')),
            _report_sentry=mock.Mock())
        sender = client_mod.ServiceClientSend(service, {}, active_log=False)
        with mock.patch.object(client_mod.requests, 'request') as transport, mock.patch.object(client_mod._logger, 'exception'):
            sender.dispatch_send()
        self.assertEqual(transport.call_count, 0)
        self.assertEqual([row['state'] for row in log.rows], ['error'])
        service.prepare_request_context.side_effect = None
        service.prepare_request_context.return_value = {'method': 'POST', 'url': 'https://example.invalid/'}
        service.env['service.client.log'] = types.SimpleNamespace(
            _create_log=mock.Mock(side_effect=RuntimeError('log failed')),
            _create_error=mock.Mock(side_effect=RuntimeError('log failed')))
        response = types.SimpleNamespace(text='ok', raise_for_status=lambda: None)
        with mock.patch.object(client_mod.requests, 'request', return_value=response), mock.patch.object(client_mod._logger, 'exception'):
            with self.assertRaisesRegex(RuntimeError, 'log failed'):
                client_mod.ServiceClientSend(service, {}, active_log=True).dispatch_send()
        self.assertEqual(service.env['service.client.log']._create_error.call_count, 1)

    def test_dispatch_success_and_http_failure_rows(self):
        for active, failing, expected in ((False, False, 0), (True, False, 1), (False, True, 1)):
            log = Log()
            response = types.SimpleNamespace(text='ok', raise_for_status=mock.Mock())
            if failing:
                response.raise_for_status.side_effect = requests.HTTPError('synthetic failure')
            service = types.SimpleNamespace(env={'service.client.log': log}, client_id=None,
                endpoint_id=None, prepare_request_context=lambda **kw: {'method': 'POST', 'url': 'https://example.invalid/', 'headers': {'X-Test': 'synthetic'}, 'json': kw['payload']},
                _report_sentry=mock.Mock())
            sender = client_mod.ServiceClientSend(service, {'value': 3}, active_log=active)
            with mock.patch.object(client_mod.requests, 'request', return_value=response) as transport, mock.patch.object(client_mod._logger, 'exception'):
                sender.dispatch_send()
            transport.assert_called_once_with(method='POST', url='https://example.invalid/',
                                              headers={'X-Test': 'synthetic'}, json={'value': 3})
            self.assertEqual(len(log.rows), expected)
            if expected:
                self.assertEqual(log.rows[0]['state'], 'error' if failing else 'done')


if __name__ == '__main__':
    unittest.main()
