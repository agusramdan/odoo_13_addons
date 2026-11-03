"""Exercise the real optional hook with the skill's limited Odoo import shim."""
import importlib.util
import pathlib
import sys
import types
import unittest
from unittest.mock import Mock, patch

try:
    from mock_odoo import odoo_modules
except ImportError as error:
    raise ImportError(
        'odoo13-unit-test-mock helper is required; run the skill runner '
        'as documented in amr_sentry/tests/README.md'
    ) from error



class SkillMockHookTest(unittest.TestCase):
    def test_success_and_failure_are_forwarded_without_private_arguments(self):
        addon = pathlib.Path(__file__).resolve().parents[2]
        package = types.ModuleType('_sentry_skill_test')
        package.__path__ = [str(addon)]
        models = types.ModuleType('_sentry_skill_test.models')
        models.__path__ = [str(addon / 'models')]
        services = types.ModuleType('_sentry_skill_test.services')
        services.REPORTER = Mock()
        name = '_sentry_skill_test.models.service_client'
        spec = importlib.util.spec_from_file_location(name, addon / 'models' / 'service_client.py')
        module = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {'_sentry_skill_test': package, '_sentry_skill_test.models': models,
                                     '_sentry_skill_test.services': services}), odoo_modules():
            spec.loader.exec_module(module)
            hook = module.ServiceClient()
            client = object()
            hook._report_sentry(service_client=client, method='secret', response='private')
            services.REPORTER.report.assert_called_once_with(success=True, service_client=client, exception=None)
            services.REPORTER.reset_mock()
            error = ValueError('private')
            hook._report_sentry(service_client=client, exception=error, response='private')
            services.REPORTER.report.assert_called_once_with(success=False, service_client=client, exception=error)
            services.REPORTER.report.side_effect = RuntimeError('secret')
            with self.assertLogs(module.__name__, level='WARNING') as logs:
                hook._report_sentry(service_client=client)
            self.assertNotIn('secret', str(logs.output))
