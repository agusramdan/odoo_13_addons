import builtins
import importlib.util
import os
import unittest
from unittest import mock


class _ConfigParameters(object):
    def sudo(self):
        return self

    def get_param(self, key, default=None):
        return "all"


class _ServiceClientModel(object):
    def __init__(self, error=None):
        self.calls = []
        self.error = error

    def _report_sentry(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error


class _Environment(object):
    def __init__(self, model):
        self.model = model

    def __getitem__(self, name):
        if name == "ir.config_parameter":
            return _ConfigParameters()
        if name == "service.client":
            return self.model
        raise KeyError(name)


class TestSentryBridge(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = os.path.join(os.path.dirname(__file__), "../../amr_service_client/services/sentry_reporting.py")
        spec = importlib.util.spec_from_file_location("sentry_reporting_under_test", path)
        cls.reporting = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.reporting)

    def test_delegates_fixed_arguments_without_importing_sentry_sdk(self):
        model = _ServiceClientModel()
        env = _Environment(model)
        service = object()
        response = object()
        exception = RuntimeError("private detail")
        imports = []
        original_import = builtins.__import__

        def import_spy(name, *args, **kwargs):
            if name == "sentry_sdk":
                imports.append(name)
                raise AssertionError("bridge must not import sentry_sdk")
            return original_import(name, *args, **kwargs)

        with unittest.mock.patch.object(builtins, "__import__", side_effect=import_spy):
            self.reporting.report_outcome(env, service, response, exception, "POST", status_code=502)

        self.assertEqual(model.calls, [{
            "service_client": service,
            "response": response,
            "exception": exception,
            "method": "POST",
            "status_code": 502,
        }])
        self.assertEqual(imports, [])

    def test_hook_failure_does_not_escape(self):
        model = _ServiceClientModel(error=RuntimeError("hook unavailable"))
        env = _Environment(model)
        self.reporting.report_outcome(env, method="GET")
        self.assertEqual(model.calls, [{
            "service_client": None,
            "response": None,
            "exception": None,
            "method": "GET",
        }])


if __name__ == "__main__":
    unittest.main()
