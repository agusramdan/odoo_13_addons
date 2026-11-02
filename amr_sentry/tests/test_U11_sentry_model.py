"""Behavioral contract for the optional Sentry service-client model hook."""
import importlib.util
import os
import sys
import types
import unittest
from unittest import mock

from test_U11_sentry_behavior import ROOT, extracted_method, policy


class _Recordset(object):
    """Offline ORM shape: model access is empty, a bound client is singleton."""

    def __init__(self, size=0, sentry_opt_in=False):
        self._size = size
        self.sentry_opt_in = sentry_opt_in

    def __len__(self):
        return self._size


_MODEL_PATH = os.path.join(
    os.path.dirname(__file__), "../../amr_sentry/models/service_client.py"
)


class _Reporter(object):
    def __init__(self, error=None):
        self.calls = []
        self.error = error

    def report(self, success, service_client=None, exception=None):
        self.calls.append((success, service_client, exception))
        if self.error is not None:
            raise self.error


class TestOptionalSentryModelHook(unittest.TestCase):
    def load_model(self, reporter):
        """Load the optional source with Odoo and addon imports isolated."""
        self.assertTrue(
            os.path.isfile(_MODEL_PATH),
            "optional Sentry model module must exist at amr_sentry/models/service_client.py",
        )
        odoo = types.ModuleType("odoo")
        setattr(odoo, "models", types.SimpleNamespace(Model=_Recordset))
        odoo_addons = types.ModuleType("odoo.addons")
        odoo_addons.__path__ = []
        addon = types.ModuleType("odoo.addons.amr_sentry")
        addon.__path__ = []
        models = types.ModuleType("odoo.addons.amr_sentry.models")
        models.__path__ = []
        services = types.ModuleType("odoo.addons.amr_sentry.services")
        services.__path__ = []
        setattr(services, "REPORTER", reporter)
        modules = {
            "odoo": odoo,
            "odoo.addons": odoo_addons,
            "odoo.addons.amr_sentry": addon,
            "odoo.addons.amr_sentry.models": models,
            "odoo.addons.amr_sentry.services": services,
        }
        with mock.patch.dict(sys.modules, modules):
            spec = importlib.util.spec_from_file_location(
                "odoo.addons.amr_sentry.models.service_client", _MODEL_PATH
            )
            if spec is None or spec.loader is None:
                raise AssertionError("could not create source loader for optional model module")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module

    def get_hook(self, reporter):
        module = self.load_model(reporter)
        model_class = getattr(module, "ServiceClient", None)
        self.assertIsNotNone(
            model_class,
            "optional Sentry model must define ServiceClient at the model boundary",
        )
        hook = getattr(model_class, "_report_sentry", None)
        self.assertTrue(
            callable(hook),
            "optional ServiceClient must override _report_sentry",
        )
        return model_class, hook

    def selected_model(self):
        events = []
        sdk = types.SimpleNamespace(
            init=lambda **kw: None,
            capture_message=lambda *a, **kw: events.append(('message', a, kw)),
            capture_exception=lambda error: events.append(('exception', error)),
        )
        reporter = policy.build_reporter(
            {'dsn': 'https://example.invalid/1'},
            {'enabled': True, 'mode': 'selected'}, sdk,
        )
        model_class, _hook = self.get_hook(reporter)
        return model_class, events

    def dispatch(self, client, error):
        """Execute the actual dispatch body with its bound optional model hook."""
        response = types.SimpleNamespace(text='ok')

        def raise_for_status():
            if error is not None:
                raise error

        response.raise_for_status = raise_for_status
        client.prepare_request_context = lambda **kw: {
            'url': 'https://example.invalid', 'method': 'POST',
        }
        logs = []
        sender = types.SimpleNamespace(
            active_log=False, payload={}, service_client=client,
            client_id=None, endpoint_id=None, credential_id=None,
            env={'service.client.log': types.SimpleNamespace(
                create_error=lambda *a, **kw: logs.append((a, kw)))},
        )
        dispatch = extracted_method(
            ROOT / 'amr_service_client/models/service_client.py',
            'ServiceClientSend', 'dispatch_send', {
                'requests': types.SimpleNamespace(request=lambda **kw: response),
                '_logger': types.SimpleNamespace(exception=lambda *a: None),
            },
        )
        self.assertIsNone(dispatch(sender))
        self.assertEqual(len(logs), int(error is not None))
        if error is not None:
            self.assertIs(logs[0][0][0], error)

    def test_selected_dispatch_bound_opted_in_singleton_reports_once(self):
        for error in (None, RuntimeError('http failure')):
            with self.subTest(outcome='error' if error else 'success'):
                model_class, events = self.selected_model()
                client = model_class(size=1, sentry_opt_in=True)
                self.assertEqual(len(client), 1)
                self.assertTrue(client)
                self.dispatch(client, error)
                expected = ([('exception', error)] if error is not None else [
                    ('message', ('Service client request completed',), {'level': 'info'}),
                ])
                self.assertEqual(events, expected)

    def test_selected_dispatch_suppresses_opted_out_and_empty_recordsets(self):
        for size in (0, 1):
            for error in (None, RuntimeError('http failure')):
                with self.subTest(size=size, outcome='error' if error else 'success'):
                    model_class, events = self.selected_model()
                    client = model_class(size=size, sentry_opt_in=False)
                    self.assertEqual(len(client), size)
                    self.assertEqual(bool(client), bool(size))
                    self.dispatch(client, error)
                    self.assertEqual(events, [])

    def test_selected_explicit_client_takes_precedence_over_bound_client(self):
        for bound_opt_in, explicit_size, explicit_opt_in in (
                (True, 1, False), (False, 1, True), (True, 0, False)):
            for error in (None, RuntimeError('http failure')):
                with self.subTest(bound=bound_opt_in, explicit=explicit_opt_in,
                                  size=explicit_size,
                                  outcome='error' if error else 'success'):
                    model_class, events = self.selected_model()
                    bound = model_class(size=1, sentry_opt_in=bound_opt_in)
                    explicit = model_class(size=explicit_size, sentry_opt_in=explicit_opt_in)
                    bound._report_sentry(service_client=explicit, exception=error)
                    expected = []
                    if explicit_opt_in:
                        expected = ([('exception', error)] if error is not None else [
                            ('message', ('Service client request completed',), {'level': 'info'}),
                        ])
                    self.assertEqual(events, expected)

    def test_success_reports_once_with_exact_service_client(self):
        reporter = _Reporter()
        model_class, hook = self.get_hook(reporter)
        client = object()

        model_class()._report_sentry(service_client=client)

        self.assertEqual(len(reporter.calls), 1)
        self.assertEqual(reporter.calls[0][0], True)
        self.assertIs(reporter.calls[0][1], client)
        self.assertIsNone(reporter.calls[0][2])
        self.assertEqual(getattr(model_class, "_inherit", None), "service.client")

    def test_missing_service_client_uses_core_hook_default(self):
        reporter = _Reporter()
        model_class, hook = self.get_hook(reporter)
        if model_class is None or hook is None:
            raise AssertionError("optional hook is unavailable")

        try:
            hook(model_class())
        except TypeError as error:
            self.fail("optional hook must preserve the base method's default: {}".format(error))

        self.assertEqual(reporter.calls, [(True, None, None)])

    def test_exception_reports_failure_without_forwarding_private_arguments(self):
        reporter = _Reporter()
        model_class, hook = self.get_hook(reporter)
        client = object()
        error = RuntimeError("private exception text")
        private_values = {
            "response": object(), "method": "POST", "request_context": object(),
            "payload": object(), "body": object(), "headers": object(),
            "credentials": object(), "extra_secret": object(),
        }

        model_class()._report_sentry(
            service_client=client, exception=error, **private_values
        )

        self.assertEqual(len(reporter.calls), 1)
        self.assertEqual(reporter.calls[0][0], False)
        self.assertIs(reporter.calls[0][1], client)
        self.assertIs(reporter.calls[0][2], error)

    def test_reporter_failure_does_not_escape_hook(self):
        reporter = _Reporter(error=RuntimeError("reporting unavailable"))
        model_class, hook = self.get_hook(reporter)
        client = object()

        with self.assertLogs(level="WARNING") as captured:
            model_class()._report_sentry(service_client=client)

        self.assertEqual(len(reporter.calls), 1)
        self.assertIs(reporter.calls[0][1], client)
        output = "\n".join(captured.output)
        self.assertIn("Sentry reporting failed", output)
        self.assertNotIn("reporting unavailable", output)


if __name__ == "__main__":
    unittest.main()
