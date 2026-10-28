"""Behavioral contract for the optional Sentry service-client model hook."""
import importlib.util
import os
import sys
import types
import unittest
from unittest import mock


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
        setattr(odoo, "models", types.SimpleNamespace(Model=object))
        addon = types.ModuleType("amr_sentry")
        addon.__path__ = []
        services = types.ModuleType("amr_sentry.services")
        services.__path__ = []
        setattr(services, "REPORTER", reporter)
        modules = {
            "odoo": odoo,
            "amr_sentry": addon,
            "amr_sentry.services": services,
        }
        with mock.patch.dict(sys.modules, modules):
            spec = importlib.util.spec_from_file_location(
                "amr_sentry_model_under_test", _MODEL_PATH
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
