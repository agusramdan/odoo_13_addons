# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from unittest.mock import patch


class TestServiceClientSentry(TransactionCase):
    def setUp(self):
        super(TestServiceClientSentry, self).setUp()
        self.params = self.env['ir.config_parameter'].sudo()
        self.params.set_param('amr_service_client.sentry_mode', 'none')

    def test_none_mode_does_not_emit(self):
        from odoo.addons.amr_service_client.services import sentry
        with patch.dict('sys.modules', {'sentry_sdk': None}):
            sentry.capture_service_event(self.env, 'service.client', 1, 'error')
        self.assertEqual(self.params.get_param('amr_service_client.sentry_mode'), 'none')

    def test_all_and_error_rules_are_explicit(self):
        from odoo.addons.amr_service_client.services import sentry
        class Scope(object):
            def __exit__(self, *args): return False
            tags = None
            def __enter__(self):
                self.tags = {}
                return self
            def set_tag(self, key, value): self.tags[key] = value
        class SDK(object):
            emitted = []
            scopes = []
            @classmethod
            def push_scope(cls):
                scope = Scope()
                cls.scopes.append(scope)
                return scope
            @classmethod
            def capture_message(cls, *args, **kwargs): cls.emitted.append((args, kwargs, dict(cls.scopes[-1].tags)))
        with patch.dict('sys.modules', {'sentry_sdk': SDK}):
            self.params.set_param('amr_service_client.sentry_mode', 'all')
            sentry.capture_service_event(self.env, 'service.client', 1, 'done')
            self.params.set_param('amr_service_client.sentry_mode', 'error')
            sentry.capture_service_event(self.env, 'service.client', 1, 'done')
            sentry.capture_service_event(self.env, 'service.client', 1, 'error')
        self.assertEqual(len(SDK.emitted), 2)
        self.assertEqual(SDK.emitted[0][1]['level'], 'info')
        self.assertEqual(SDK.emitted[1][1]['level'], 'error')
        self.assertNotIn('secret', repr(SDK.emitted))
        self.assertNotIn('service_client.state', getattr(SDK, 'global_tags', {}))

    def test_selected_requires_opted_in_client_and_error(self):
        from odoo.addons.amr_service_client.services import sentry
        class Scope(object):
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def set_tag(self, *args): pass
        class SDK(object):
            emitted = []
            @classmethod
            def push_scope(cls): return Scope()
            @classmethod
            def capture_message(cls, *args, **kwargs): cls.emitted.append(args)
        client = type('Client', (), {'sentry_enabled': True, 'id': 9})()
        with patch.dict('sys.modules', {'sentry_sdk': SDK}):
            self.params.set_param('amr_service_client.sentry_mode', 'selected')
            sentry.capture_service_event(self.env, 'service.client', 1, 'error')
            sentry.capture_service_event(self.env, 'service.client', 1, 'done', client_id=client)
            sentry.capture_service_event(self.env, 'service.client', 1, 'error', client_id=client)
        self.assertEqual(len(SDK.emitted), 1)

    def test_reporting_is_per_model_operation_not_deduplicated(self):
        """A failed call and its separately persisted replay log are two events."""
        from odoo.addons.amr_service_client.services import sentry
        class Scope(object):
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def set_tag(self, *args): pass
        class SDK(object):
            emitted = []
            @classmethod
            def push_scope(cls): return Scope()
            @classmethod
            def capture_message(cls, *args, **kwargs): cls.emitted.append(args)
        with patch.dict('sys.modules', {'sentry_sdk': SDK}):
            self.params.set_param('amr_service_client.sentry_mode', 'error')
            sentry.capture_service_event(self.env, 'service.client', None, 'error', error_type='ConnectionError')
            sentry.capture_service_event(self.env, 'service.client.log', 42, 'error', error_type='ConnectionError')
        self.assertEqual(len(SDK.emitted), 2)
        self.assertEqual(SDK.emitted[0][0], 'Service client request error')
        self.assertEqual(SDK.emitted[1][0], 'Service client request error')
