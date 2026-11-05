"""Isolated tests for data-minimizing Sentry reporting policy."""
from support import ROOT
import importlib.util
import sys
import types
import ast
import json
import unittest

_REPORTER_PATH = ROOT / 'amr_service_client/services/sentry_reporting.py'
_spec = importlib.util.spec_from_file_location('sentry_reporting_test', _REPORTER_PATH)
reporter = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(reporter)
_POLICY_PATH = ROOT / 'amr_sentry/services/sentry_reporting.py'
_policy_spec = importlib.util.spec_from_file_location('sentry_policy_test', _POLICY_PATH)
policy = importlib.util.module_from_spec(_policy_spec)
_policy_spec.loader.exec_module(policy)


def extracted_method(path, class_name, method_name, namespace):
    namespace.setdefault('_logger', types.SimpleNamespace(debug=lambda *a, **kw: None))
    tree = ast.parse(path.read_text())
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == class_name)
    method = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == method_name)
    module = ast.Module(body=[method], type_ignores=[])
    exec(compile(module, str(path), 'exec'), namespace)
    return namespace[method_name]


class SentryReporting(unittest.TestCase):
    def test_modes_gate_reporting_and_selected_requires_opt_in(self):
        calls = []
        sdk = types.SimpleNamespace(init=lambda **kw: calls.append(('init', kw)),
            capture_message=lambda *a, **k: calls.append(('message', a, k)),
            capture_exception=lambda *a, **k: calls.append(('exception', a, k)))
        def build(mode):
            return policy.build_reporter({'dsn': 'https://example.invalid/1'},
                {'enabled': True, 'mode': mode}, sdk)
        build('all').report(success=True)
        build('all').report(success=False, exception=RuntimeError('private'))
        self.assertEqual(2, len([c for c in calls if c[0] in ('message', 'exception')]))
        calls[:] = []
        build('error').report(success=True)
        build('error').report(success=False, exception=RuntimeError('private'))
        self.assertEqual(['exception'], [c[0] for c in calls if c[0] != 'init'])
        calls[:] = []
        selected = build('selected')
        selected.report(success=True, service_client=types.SimpleNamespace(sentry_opt_in=False))
        selected.report(success=True, service_client=types.SimpleNamespace(sentry_opt_in=True))
        self.assertEqual(['message'], [c[0] for c in calls if c[0] != 'init'])
        self.assertNotIn('private', repr(calls))

    def test_sentry_failure_is_best_effort(self):
        class FailingSDK:
            def init(self, **kwargs): pass
            def capture_message(self, *args, **kwargs): raise RuntimeError('offline')
            def capture_exception(self, *args, **kwargs): raise RuntimeError('offline')
        best_effort = policy.build_reporter({'dsn': 'https://example.invalid/1'},
            {'enabled': True, 'mode': 'all'}, FailingSDK())
        best_effort.report(success=True)
        best_effort.report(success=False, exception=RuntimeError('transport'))

    def test_real_log_send_reports_http_failure_and_preserves_logged_error(self):
        path = ROOT / 'amr_service_client/models/service_client_log.py'
        events = []
        class Response:
            status_code = 503
            text = 'private response body'
            def raise_for_status(self): raise RuntimeError('http 503')
        class Provider:
            def authenticate(self, context, audience): return context
        class Client:
            provider = Provider()
            def _report_sentry(self, response=None, exception=None, method=None):
                events.append((response, exception, method))
        class Endpoint:
            audience = 'a'
            def request_headers_default(self, headers): return headers
        class Owner:
            def get_service_client(self, *a): return Client()
        class Log:
            client_id, endpoint_id, credential_id = Owner(), Endpoint(), None
            request_context = json.dumps({'url': 'https://example.invalid', 'method': 'POST'})
            updates = None
            def format_error(self, exc): return str(exc)
            def sanitize_sensitive_data(self, value): return value
            def write(self, values): self.updates = values
        response = Response()
        namespace = {'json': json, 'requests': types.SimpleNamespace(request=lambda **kw: response)}
        send = extracted_method(path, 'ServiceClientLog', 'send', namespace)
        result = send(Log())
        self.assertEqual(len(events), 1)
        self.assertIs(events[0][0], response)
        self.assertEqual(events[0][0].status_code, 503)
        self.assertIsInstance(events[0][1], RuntimeError)
        self.assertEqual(str(events[0][1]), 'http 503')
        self.assertEqual(events[0][2], 'POST')
        self.assertEqual(result.updates, {'state': 'error', 'response': 'http 503'})

    def test_real_service_client_call_outcomes_privacy_and_transport_semantics(self):
        path = ROOT / 'amr_service_client/models/service_client.py'
        calls = []
        class Response:
            status_code = 503
            text = 'private response body'
            def raise_for_status(self): raise RuntimeError('http 503')
        def run(response=None, error=None, raise_exception=True):
            namespace = {'requests': types.SimpleNamespace(request=lambda **kw: (_ for _ in ()).throw(error) if error else response)}
            method = extracted_method(path, 'ServiceClient', 'call', namespace)
            class Client:
                method = 'POST'
                def prepare_request_context(self, *a, **kw): return {'url': 'https://example.invalid', 'headers': {'Authorization': 'secret'}}
                def _report_sentry(self, response=None, exception=None, method=None):
                    calls.append({'response': response, 'exception': exception, 'method': method})
            return method(Client(), method='POST', raise_exception=raise_exception)
        failed = Response()
        self.assertIs(run(failed, raise_exception=False), failed)
        self.assertEqual(calls[-1]['method'], 'POST')
        self.assertIsInstance(calls[-1]['exception'], RuntimeError)
        self.assertIsNone(calls[-1]['response'])
        self.assertEqual(set(calls[-1]), {'response', 'exception', 'method'})
        success = types.SimpleNamespace(status_code=200, text='private', raise_for_status=lambda: None)
        self.assertIs(run(success), success)
        self.assertIs(calls[-1]['response'], success)
        self.assertIsNone(calls[-1]['exception'])
        self.assertEqual(calls[-1]['method'], 'POST')
        transport = RuntimeError('transport secret')
        with self.assertRaises(RuntimeError) as caught: run(error=transport)
        self.assertIs(caught.exception, transport)
        self.assertIs(calls[-1]['exception'], transport)
        self.assertIsNone(calls[-1]['response'])
        self.assertEqual(calls[-1]['method'], 'POST')
        self.assertNotIn('private response body', repr(calls))
        self.assertNotIn('Authorization', repr(calls))

    def test_call_pre_response_failure_returns_none_without_masking(self):
        path = ROOT / 'amr_service_client/models/service_client.py'
        for stage in ('preparation', 'transport'):
            error = RuntimeError(stage)
            reports, requests_made = [], []
            def request(**kwargs):
                requests_made.append(kwargs)
                raise error
            class Client:
                def prepare_request_context(self, *args, **kwargs):
                    if stage == 'preparation':
                        raise error
                    return {'method': 'POST'}
                def _report_sentry(self, **kwargs): reports.append(kwargs)
            call = extracted_method(path, 'ServiceClient', 'call', {
                'requests': types.SimpleNamespace(request=request)})
            try:
                result = call(Client(), method='POST', raise_exception=False)
            except Exception as caught:
                self.fail('expected None for %s, got %r' % (stage, caught))
            self.assertIsNone(result)
            self.assertEqual(len(requests_made), int(stage == 'transport'))
            self.assertEqual(len(reports), 1)
            self.assertIs(reports[0]['exception'], error)
            with self.assertRaises(RuntimeError) as caught:
                call(Client(), method='POST', raise_exception=True)
            self.assertIs(caught.exception, error)

    def _exercise_call_outcome(self, stage, raise_exception, sdk_fails):
        # Source-extracted call plus the real bridge and policy; not ORM execution.
        path = ROOT / 'amr_service_client/models/service_client.py'
        original = RuntimeError('synthetic ' + stage)
        requests_made, hooks, delegated, captures = [], [], [], []

        class SDK:
            def init(self, **kwargs):
                pass
            def capture_message(self, *args, **kwargs):
                captures.append(('success', args, kwargs))
                if sdk_fails:
                    raise RuntimeError('SDK offline')
            def capture_exception(self, error):
                captures.append(('failure', error))
                if sdk_fails:
                    raise RuntimeError('SDK offline')

        sdk_reporter = policy.build_reporter(
            {'dsn': 'https://example.invalid/1'},
            {'enabled': True, 'mode': 'all'}, SDK())

        def report(**kwargs):
            delegated.append(kwargs)
            sdk_reporter.report(success=kwargs['exception'] is None,
                                exception=kwargs['exception'])

        class Client:
            def prepare_request_context(self, *args, **kwargs):
                if stage == 'preparation':
                    raise original
                return {'method': 'POST'}
            def _report_sentry(self, response=None, exception=None, method=None):
                kwargs = {'response': response, 'exception': exception, 'method': method}
                hooks.append(kwargs)
                reporter.report_outcome({'service.client': types.SimpleNamespace(
                    _report_sentry=report)}, **kwargs)

        class Response:
            def raise_for_status(self):
                if stage == 'http_error':
                    raise original

        response = Response()
        def request(**kwargs):
            requests_made.append(kwargs)
            if stage == 'transport':
                raise original
            return response

        call = extracted_method(path, 'ServiceClient', 'call', {
            'requests': types.SimpleNamespace(request=request)})
        if stage != 'success' and raise_exception:
            with self.assertRaises(RuntimeError) as caught:
                call(Client(), method='POST', raise_exception=True)
            self.assertIs(caught.exception, original)
        else:
            result = call(Client(), method='POST', raise_exception=raise_exception)
            if stage in ('preparation', 'transport'):
                self.assertIsNone(result)
            else:
                self.assertIs(result, response)

        self.assertEqual(len(requests_made), int(stage != 'preparation'))
        self.assertEqual(len(hooks), 1, 'call boundary hook count')
        self.assertEqual(len(delegated), 1, 'bridge delegation count')
        for event in (hooks[0], delegated[0]):
            self.assertIs(event['exception'], None if stage == 'success' else original)
            self.assertIs(event['response'], response if stage == 'success' else None)
            self.assertEqual(event['method'], 'POST')
        self.assertEqual(len(captures), 1, 'total success and failure captures')
        if stage == 'success':
            self.assertEqual(captures[0][0], 'success')
        else:
            self.assertEqual(captures[0][0], 'failure')
            self.assertIs(captures[0][1], original)

    def test_call_failure_counts_and_sdk_failure_preserve_original_outcomes(self):
        for stage in ('preparation', 'transport'):
            for raise_exception in (False, True):
                for sdk_fails in (False, True):
                    with self.subTest(stage=stage, raise_exception=raise_exception,
                                      sdk_fails=sdk_fails):
                        self._exercise_call_outcome(stage, raise_exception, sdk_fails)

    def test_call_http_counts_and_sdk_failure_preserve_original_outcomes(self):
        for stage in ('success', 'http_error'):
            for raise_exception in (False, True):
                for sdk_fails in (False, True):
                    with self.subTest(stage=stage, raise_exception=raise_exception,
                                      sdk_fails=sdk_fails):
                        self._exercise_call_outcome(stage, raise_exception, sdk_fails)

    def test_real_dispatch_send_success_and_failure_reporting_are_best_effort(self):
        path = ROOT / 'amr_service_client/models/service_client.py'
        dispatch_errors = []
        for status, outcome in ((200, 'success'), (503, 'error')):
            events = []
            hook_calls = []
            log_calls = []
            class Response:
                status_code = status
                text = 'PRIVATE_RESPONSE_BODY_MARKER'
                def raise_for_status(self):
                    if status >= 400: raise RuntimeError('http 503')
            response = Response()
            class Client:
                def prepare_request_context(self, **kwargs):
                    return {'url': 'https://example.invalid', 'method': 'POST',
                            'headers': {'Authorization': 'AUTHORIZATION_MARKER'},
                            'payload': {'token': 'TOKEN_MARKER'}}
                def _report_sentry(self, response=None, exception=None, method=None):
                    hook_calls.append((response, exception, method))
                    raise RuntimeError('reporter offline')
            namespace = {'requests': types.SimpleNamespace(request=lambda **kw: response),
                '_logger': types.SimpleNamespace(exception=lambda *a: None)}
            method = extracted_method(path, 'ServiceClientSend', 'dispatch_send', namespace)
            sender = types.SimpleNamespace(active_log=True, payload={'token': 'TOKEN_MARKER'}, service_client=Client(),
                client_id=None, endpoint_id=None, credential_id=None,
                env={'service.client.log': types.SimpleNamespace(
                    create_log=lambda *a, **kw: log_calls.append((a, kw)),
                    create_error=lambda *a, **kw: log_calls.append((a, kw)))})
            try:
                method(sender)
            except Exception as error:
                dispatch_errors.append((status, error))
                continue
            self.assertEqual(len(hook_calls), 1)
            self.assertEqual(hook_calls[0][0], response)
            self.assertIsNone(hook_calls[0][1] if status == 200 else None)
            if status == 503:
                self.assertIsInstance(hook_calls[0][1], RuntimeError)
                self.assertEqual(str(hook_calls[0][1]), 'http 503')
            else:
                self.assertIsNone(hook_calls[0][1])
            self.assertEqual(hook_calls[0][2], 'POST')
            self.assertNotIn('PRIVATE_RESPONSE_BODY_MARKER', repr(hook_calls))
            self.assertNotIn('AUTHORIZATION_MARKER', repr(hook_calls))
            self.assertNotIn('TOKEN_MARKER', repr(hook_calls))
            self.assertEqual(len(log_calls), 1)
            logged_args, logged_kwargs = log_calls[0]
            if status == 200:
                self.assertEqual(logged_args[0], 'done')
            else:
                self.assertIs(logged_args[0], hook_calls[0][1])
                self.assertIsInstance(logged_args[0], RuntimeError)
                self.assertEqual(str(logged_args[0]), 'http 503')
            self.assertEqual(logged_kwargs.get('response_text'), response.text if status == 200 else None)
        if dispatch_errors:
            status, error = dispatch_errors[0]
            self.fail('dispatch_send failed to preserve outcome after reporter failure (HTTP %s): %r' % (status, error))

    def test_dispatch_error_logging_matrix_component(self):
        # L3 component only: fake log sink, no ORM or transaction assertions.
        for stage in ('preparation', 'transport', 'http'):
            for active_log in (True, False):
                with self.subTest(stage=stage, active_log=active_log):
                    error = RuntimeError('synthetic ' + stage)
                    requests_seen, reports, errors, successes = [], [], [], []
                    payload = {'sample': 'value'}
                    context = {'method': 'POST', 'url': 'https://example.invalid'}
                    client_id, endpoint_id, credential_id = object(), object(), object()

                    class Response:
                        def raise_for_status(self):
                            raise error
                    response = Response()

                    class Client:
                        def prepare_request_context(self, **kwargs):
                            if stage == 'preparation':
                                raise error
                            return context
                        def _report_sentry(self, response=None, exception=None, method=None):
                            reports.append((response, exception, method))

                    def request(**kwargs):
                        requests_seen.append(kwargs)
                        if stage == 'transport':
                            raise error
                        return response

                    def create_error(*args, **kwargs):
                        errors.append((args, kwargs))

                    sender = types.SimpleNamespace(
                        active_log=active_log, payload=payload, service_client=Client(),
                        client_id=client_id, endpoint_id=endpoint_id, credential_id=credential_id,
                        env={'service.client.log': types.SimpleNamespace(
                            create_log=lambda *a, **kw: successes.append((a, kw)),
                            create_error=create_error)})
                    dispatch = extracted_method(
                        ROOT / 'amr_service_client/models/service_client.py',
                        'ServiceClientSend', 'dispatch_send', {
                            'requests': types.SimpleNamespace(request=request),
                            '_logger': types.SimpleNamespace(exception=lambda *a: None)})

                    self.assertIsNone(dispatch(sender))
                    self.assertEqual(requests_seen, [] if stage == 'preparation' else [context])
                    self.assertEqual(len(reports), 1)
                    self.assertIs(reports[0][0], response if stage == 'http' else None)
                    self.assertIs(reports[0][1], error)
                    self.assertEqual(reports[0][2], None if stage == 'preparation' else 'POST')
                    self.assertEqual(len(successes), 0)
                    self.assertEqual(len(errors), 1)
                    args, kwargs = errors[0]
                    self.assertEqual(len(args), 1)
                    self.assertIs(args[0], error)
                    self.assertEqual(set(kwargs), {'client_id', 'endpoint_id', 'credential_id', 'request_context'})
                    self.assertIs(kwargs['client_id'], client_id)
                    self.assertIs(kwargs['endpoint_id'], endpoint_id)
                    self.assertIs(kwargs['credential_id'], credential_id)
                    if stage == 'preparation':
                        self.assertEqual(kwargs['request_context'], {'payload': payload})
                    else:
                        self.assertIs(kwargs['request_context'], context)

    def test_dispatch_success_without_active_log_reports_one_outcome(self):
        # ADDONS13-68 addendum L2: one successful request and eligible success
        # hook, with no success log when active_log is False. Component only.
        response = types.SimpleNamespace(text='ok', raise_for_status=lambda: None)
        requests_seen, reports, logs = [], [], []
        class Client:
            def prepare_request_context(self, **kwargs):
                return {'method': 'POST'}
            def _report_sentry(self, response=None, exception=None, method=None):
                reports.append((response, exception, method))
        def request(**kwargs):
            requests_seen.append(kwargs)
            return response
        sender = types.SimpleNamespace(active_log=False, payload={}, service_client=Client(),
            client_id=None, endpoint_id=None, credential_id=None,
            env={'service.client.log': types.SimpleNamespace(
                create_log=lambda *a, **kw: logs.append(('success', a, kw)),
                create_error=lambda *a, **kw: logs.append(('error', a, kw)))})
        dispatch = extracted_method(ROOT / 'amr_service_client/models/service_client.py',
            'ServiceClientSend', 'dispatch_send', {
                'requests': types.SimpleNamespace(request=request),
                '_logger': types.SimpleNamespace(exception=lambda *a: None),
            })
        before = len(logs)
        self.assertIsNone(dispatch(sender))
        self.assertEqual(requests_seen, [{'method': 'POST'}])
        self.assertEqual(reports, [(response, None, 'POST')])
        self.assertEqual(len(logs), before)

    def test_dispatch_success_log_failure_uses_baseline_error_log_path(self):
        path = ROOT / 'amr_service_client/models/service_client.py'
        business_error = RuntimeError('done log failed')
        response = types.SimpleNamespace(text='ok', raise_for_status=lambda: None)
        reports, logs = [], []
        class Client:
            def prepare_request_context(self, **kwargs):
                return {'method': 'POST'}
            def _report_sentry(self, response=None, exception=None, method=None):
                reports.append((response, exception, method))
        def create_log(*args, **kwargs):
            logs.append((args, kwargs))
            raise business_error
        def create_error(*args, **kwargs):
            logs.append((args, kwargs))
        sender = types.SimpleNamespace(active_log=True, payload={}, service_client=Client(),
            client_id=None, endpoint_id=None, credential_id=None,
            env={'service.client.log': types.SimpleNamespace(create_log=create_log, create_error=create_error)})
        dispatch = extracted_method(path, 'ServiceClientSend', 'dispatch_send', {
            'requests': types.SimpleNamespace(request=lambda **kw: response),
            '_logger': types.SimpleNamespace(exception=lambda *a: None, debug=lambda *a, **kw: None),
        })
        try:
            result = dispatch(sender)
        except RuntimeError as error:
            self.fail('baseline handled the done-log failure, but it escaped: %s' % error)
        self.assertIsNone(result)
        self.assertEqual(len(logs), 2)
        self.assertEqual(logs[0][0][0], 'done')
        self.assertIs(logs[1][0][0], business_error)
        self.assertNotIn('response_text', logs[1][1])
        self.assertEqual(reports, [(response, None, 'POST')])

    def test_create_log_accepts_service_client_integer_id(self):
        path = ROOT / 'amr_service_client/models/service_client_log.py'
        class AbstractModel: pass
        class Log:
            def sudo(self): return self
            def create(self, values): return values
            def sanitize_sensitive_data(self, value): return value
        create = extracted_method(path, 'ServiceClientLog', 'create_log', {
            'json': json, 'models': types.SimpleNamespace(AbstractModel=AbstractModel)})
        try:
            row = create(Log(), 'done', client_id=42,
                         endpoint_id=types.SimpleNamespace(id=7), response_text='ok')
        except Exception as error:
            self.fail('integer client_id from ServiceClient must persist: %r' % error)
        self.assertEqual(row['client_id'], 42)
        self.assertEqual(row['endpoint_id'], 7)
        self.assertEqual(row['state'], 'done')
        self.assertEqual(row['response'], 'ok')

    def test_real_log_send_reports_success(self):
        path = ROOT / 'amr_service_client/models/service_client_log.py'
        events = []
        class Response:
            status_code = 201
            text = 'ok'
            def raise_for_status(self): pass
        class Provider:
            def authenticate(self, context, audience): return context
        class Client:
            provider = Provider()
            def _report_sentry(self, response=None, exception=None, method=None):
                events.append((response, exception, method))
        class Endpoint:
            audience = 'a'
            def request_headers_default(self, headers): return headers
        class Owner:
            def get_service_client(self, *a): return Client()
        class Log:
            client_id, endpoint_id, credential_id = Owner(), Endpoint(), None
            request_context = json.dumps({'url': 'https://example.invalid', 'method': 'POST'})
            def format_error(self, exc): return str(exc)
            def sanitize_sensitive_data(self, value): return value
            def write(self, values): self.updates = values
        response = Response()
        send = extracted_method(path, 'ServiceClientLog', 'send', {'json': json, '_logger': types.SimpleNamespace(debug=lambda *a, **kw: None), 'requests': types.SimpleNamespace(request=lambda **kw: response)})
        result = send(Log())
        self.assertEqual(len(events), 1)
        self.assertIs(events[0][0], response)
        self.assertIsNone(events[0][1])
        self.assertEqual(events[0][2], 'POST')
        self.assertEqual(result.updates['state'], 'done')

        class ErrorResponse:
            status_code = 503
            text = 'private response body'
            def raise_for_status(self): raise RuntimeError('http 503')
        error_response = ErrorResponse()
        error_send = extracted_method(path, 'ServiceClientLog', 'send', {
            'json': json, 'requests': types.SimpleNamespace(request=lambda **kw: error_response)})
        error_result = error_send(Log())
        self.assertEqual(len(events), 2)
        self.assertIs(events[1][0], error_response)
        self.assertEqual(events[1][0].status_code, 503)
        self.assertIsInstance(events[1][1], RuntimeError)
        self.assertEqual(str(events[1][1]), 'http 503')
        self.assertEqual(events[1][2], 'POST')
        self.assertEqual(error_result.updates, {'state': 'error', 'response': 'http 503'})

    def test_real_log_send_reporter_failure_preserves_log_outcome(self):
        path = ROOT / 'amr_service_client/models/service_client_log.py'
        events = []
        class Response:
            status_code = 201
            text = 'ok'
            def raise_for_status(self): pass
        response = Response()
        class Provider:
            def authenticate(self, context, audience): return context
        class Client:
            provider = Provider()
            def _report_sentry(self, response=None, exception=None, method=None):
                events.append((response, exception, method))
                raise RuntimeError('reporter offline')
        class Endpoint:
            audience = 'a'
            def request_headers_default(self, headers): return headers
        class Owner:
            def get_service_client(self, *a): return Client()
        class Log:
            client_id, endpoint_id, credential_id = Owner(), Endpoint(), None
            request_context = json.dumps({'url': 'https://example.invalid', 'method': 'POST'})
            def format_error(self, exc): return str(exc)
            def sanitize_sensitive_data(self, value): return value
            def write(self, values): self.updates = values
        send = extracted_method(path, 'ServiceClientLog', 'send', {'json': json, '_logger': types.SimpleNamespace(debug=lambda *a, **kw: None), 'requests': types.SimpleNamespace(request=lambda **kw: response)})
        result = send(Log())
        self.assertEqual(len(events), 1)
        self.assertIs(events[0][0], response)
        self.assertIsNone(events[0][1])
        self.assertEqual(events[0][2], 'POST')
        self.assertEqual(result.updates['state'], 'done')

        class ErrorResponse:
            status_code = 503
            text = 'private response body'
            def raise_for_status(self): raise RuntimeError('http 503')
        error_response = ErrorResponse()
        error_send = extracted_method(path, 'ServiceClientLog', 'send', {
            'json': json, 'requests': types.SimpleNamespace(request=lambda **kw: error_response)})
        error_result = error_send(Log())
        self.assertEqual(len(events), 2)
        self.assertIs(events[1][0], error_response)
        self.assertEqual(events[1][0].status_code, 503)
        self.assertIsInstance(events[1][1], RuntimeError)
        self.assertEqual(str(events[1][1]), 'http 503')
        self.assertEqual(events[1][2], 'POST')
        self.assertEqual(error_result.updates, {'state': 'error', 'response': 'http 503'})

    def _run_action_service_client_fixture(self, call_behavior, handle_behavior=None):
        path = ROOT / 'amr_service_client/models/service_client.py'
        events = []
        sentinel = RuntimeError('sentinel')
        class Records:
            def with_context(self, ctx): return self
        records = Records()
        class Payloads:
            def get_payload(self, context): return {'data': 'payload'}
        class ErrorHandler:
            def with_context(self, context):
                self.context = context
                return self
            def run(self): events.append(('handled', self.context['exception']))
        class Client:
            def call(self, **kwargs): return call_behavior(self, kwargs)
            fail_reporting = False
            reporter_exception = RuntimeError('reporter failure')
            def _report_sentry(self, response=None, exception=None, method=None):
                events.append(('reported', response, exception, method))
                if self.fail_reporting:
                    raise self.reporter_exception
        client = Client()
        class Action:
            active = True
            each_record = False
            payload_ids = Payloads()
            endpoint_id = credential_id = None
            error_handle_id = ErrorHandler()
            action_next_id = types.SimpleNamespace(with_context=lambda ctx: types.SimpleNamespace(run=lambda: None))
            def ensure_one(self): pass
            def _get_eval_context(self): return {'response': [{'ctx': {}}]}
            def _run_action_iteration(self, context): return context
            def _run_action_code(self, context):
                context.update({'method': 'POST', 'raise_exception': True})
                return context
            def prepare_request(self, records, ctx, eval_context):
                context = dict(eval_context or {})
                context.update({'ctx': ctx, 'records': records.with_context(ctx),
                                'payload': self.payload_ids.get_payload(context)})
                context.update(self._run_action_code(context))
                return context
            def get_service_client(self, *args, **kwargs): return client
            def _run_action_handle(self, context):
                if handle_behavior:
                    return handle_behavior()
                return {}
        namespace = {'_logger': types.SimpleNamespace(debug=lambda *a, **k: None)}
        run = extracted_method(path, 'ServiceClientFactory', 'run_action_service_client', namespace)
        return run, Action(), records, sentinel, events

    def test_run_action_call_exception_is_not_reported_twice(self):
        def call(client, kwargs):
            client._report_sentry(exception=sentinel, method='POST')
            raise sentinel
        # Bind the fixture's sentinel into the fake client behavior after setup.
        run, action, records, sentinel, events = self._run_action_service_client_fixture(lambda c, k: None)
        def call_with_sentinel(client, kwargs):
            client._report_sentry(exception=sentinel, method='POST')
            raise sentinel
        fake_client = types.SimpleNamespace(
            call=None,
            _report_sentry=lambda response=None, exception=None, method=None: events.append(
                ('reported', (), {'response': response, 'exception': exception, 'method': method})))
        fake_client.call = lambda **kwargs: call_with_sentinel(fake_client, kwargs)
        action.get_service_client = lambda *a, **kw: fake_client
        try:
            run(action, {'records': records})
        except TypeError:
            self.fail('handler replaced the original error with malformed reporter call')
        except RuntimeError as caught:
            self.assertIs(caught, sentinel)
        self.assertEqual(len([event for event in events if event[0] == 'reported']), 1)
        report = [event for event in events if event[0] == 'reported'][0]
        self.assertIs(report[2]['exception'], sentinel)
        self.assertEqual(report[2]['method'], 'POST')
        self.assertEqual(events[-1], ('handled', sentinel))

    def test_run_action_handler_exception_is_reported_once_with_valid_keywords(self):
        response = types.SimpleNamespace(status_code=200)
        def succeeds(client, kwargs): return response
        run, action, records, sentinel, events = self._run_action_service_client_fixture(
            succeeds, lambda: (_ for _ in ()).throw(sentinel))
        try:
            run(action, {'records': records})
        except TypeError:
            self.fail('handler replaced the original error with malformed reporter call')
        self.assertEqual(len([event for event in events if event[0] == 'reported']), 1)
        report = [event for event in events if event[0] == 'reported'][0]
        self.assertEqual(report, ('reported', response, sentinel, 'POST'))
        self.assertEqual(events[-1], ('handled', sentinel))

    def test_run_action_success_then_next_action_failure_are_distinct(self):
        # Extracted methods and fake request/reporter: not SDK or ORM evidence.
        path = ROOT / 'amr_service_client/models/service_client.py'
        for reporter_fails in (False, True):
            with self.subTest(reporter_fails=reporter_fails):
                requests_made, outcomes, next_contexts = [], [], []
                response = types.SimpleNamespace(status_code=200, raise_for_status=lambda: None)
                error = RuntimeError('next action failure')
                run, action, records, _, events = self._run_action_service_client_fixture(
                    lambda client, kwargs: None)

                def request(**kwargs):
                    requests_made.append(kwargs)
                    return response

                call = extracted_method(path, 'ServiceClient', 'call', {
                    'requests': types.SimpleNamespace(request=request)})

                class Client:
                    def prepare_request_context(self, *args, **kwargs):
                        return {'method': 'POST'}
                    def call(self, **kwargs):
                        return call(self, **kwargs)
                    def _report_sentry(self, response=None, exception=None, method=None):
                        outcomes.append((response, exception, method))
                        if reporter_fails and exception is not None:
                            raise RuntimeError('reporter failure')

                class NextAction:
                    def with_context(self, context):
                        next_contexts.append(dict(context))
                        return self
                    def run(self):
                        raise error

                action.get_service_client = lambda *args, **kwargs: Client()
                action.action_next_id = NextAction()
                result = run(action, {'records': records})

                self.assertIsNone(result)
                self.assertEqual(requests_made, [{'method': 'POST'}])
                self.assertEqual(len(next_contexts), 1)
                self.assertIs(next_contexts[0]['response'], response)
                self.assertEqual(len(outcomes), 2)
                self.assertIs(outcomes[0][0], response)
                self.assertIsNone(outcomes[0][1])
                self.assertEqual(outcomes[0][2], 'POST')
                self.assertIs(outcomes[1][0], response)
                self.assertIs(outcomes[1][1], error)
                self.assertEqual(outcomes[1][2], 'POST')
                self.assertEqual(len(events), 1)
                self.assertEqual(events[0][0], 'handled')
                self.assertIs(events[0][1], error)

    def test_run_action_reporter_failure_logs_only_safe_diagnostics(self):
        response = types.SimpleNamespace(status_code=200)
        business_error = RuntimeError('business failure with private details')
        reporter_error = RuntimeError('SENTRY_REPORTER_SECRET_MARKER')
        run, action, records, sentinel, events = self._run_action_service_client_fixture(
            lambda client, kwargs: response,
            lambda: (_ for _ in ()).throw(business_error))
        client = action.get_service_client()
        client.fail_reporting = True
        client.reporter_exception = reporter_error
        log_calls = []
        run.__globals__['_logger'] = types.SimpleNamespace(
            debug=lambda *args, **kwargs: log_calls.append((args, kwargs)))

        run(action, {'records': records})

        self.assertEqual(events[-1], ('handled', business_error))
        self.assertGreaterEqual(len(log_calls), 1)
        reporter_logs = [call for call in log_calls if 'report' in str(call[0][0]).lower()]
        self.assertTrue(reporter_logs)
        for args, kwargs in reporter_logs:
            message = ' '.join(str(value) for value in args)
            self.assertNotIn('SENTRY_REPORTER_SECRET_MARKER', message)
            self.assertNotIn(str(business_error), message)
            self.assertFalse(kwargs.get('exc_info', False))
            self.assertTrue(message.strip())
