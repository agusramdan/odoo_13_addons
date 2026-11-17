# -*- coding: utf-8 -*-
"""Native ORM fixtures for ADDONS13-71 U01-U14; synthetic data only."""
import copy
import uuid
from unittest.mock import Mock, patch

from odoo.exceptions import AccessError
from odoo.service.model import execute
from odoo.tests.common import TransactionCase


class TestUATAddons1371Logging(TransactionCase):
    def setUp(self):
        super(TestUATAddons1371Logging, self).setUp()
        model = self.env["ir.model"].search([("model", "=", "res.partner")], limit=1)
        self.assertTrue(model)
        self.endpoint = self.env["service.endpoint"].create({
            "name": "Synthetic UAT endpoint", "code": "uat_" + uuid.uuid4().hex,
            "source": "value", "base_url_value": "https://example.invalid",
            "active_log": True, "content_type_default": "application/json",
        })
        # Database credential resolves to its real ORM record; no external secret/provider.
        self.credential = self.env["service.credential"].create({
            "name": "Synthetic UAT credential", "source": "database",
            'credential_json': '{"type":"api_key","header":"X-Synthetic","value":"synthetic-only"}',
        })
        self.endpoint.write({"credential_id": self.credential.id})
        self.client = self.env["service.client"].create({
            "name": "Synthetic UAT client", "model_id": model.id,
            "endpoint_id": self.endpoint.id, "credential_id": self.credential.id,
        })
        self.logs = self.env["service.client.log"]
        self.marker = "synthetic-" + uuid.uuid4().hex

    def _dispatch(self, endpoint_flag=True, *, path=None, payload=None, error=None,
                  sender_flag="client", writer_error=None, hook_error=None):
        self.endpoint.write({"active_log": endpoint_flag})
        payload = payload if payload is not None else {"marker": self.marker}
        service = self.client.get_service_client(self.endpoint, path=path or "/" + self.marker, method="POST")
        sender = service.prepare_payload(**payload)
        if sender_flag != "client":
            sender.active_log = sender_flag
        response = Mock(text=self.marker)
        if error == "prepare":
            service.prepare_request_context = Mock(side_effect=ValueError(self.marker))
        transport_error = error == "transport"
        if transport_error:
            transport_result = None
        else:
            transport_result = response
            if error == "http":
                response.raise_for_status.side_effect = ValueError(self.marker)
        before = set(self.logs.search([]).ids)
        writer = self.logs.__class__
        create_log = writer._create_log
        create_error = writer._create_error
        log_patch = patch.object(writer, "_create_log", autospec=True)
        error_patch = patch.object(writer, "_create_error", autospec=True)
        with patch("odoo.addons.amr_service_client.models.service_client.requests.request",
                   side_effect=ValueError(self.marker) if transport_error else None,
                   return_value=None if transport_error else response) as transport, \
             patch.object(service, "_report_sentry", side_effect=(ValueError("hook") if hook_error else None)) as hook, \
             log_patch as log_writer, error_patch as error_writer:
            if writer_error == "success":
                success_failed = [False]

                def fail_first_success(recordset, state, *args, **kwargs):
                    if state == 'done' and not success_failed[0]:
                        success_failed[0] = True
                        raise RuntimeError("synthetic writer failure")
                    return create_log(recordset, state, *args, **kwargs)

                log_writer.side_effect = fail_first_success
            else:
                log_writer.side_effect = lambda recordset, *args, **kwargs: create_log(
                    recordset, *args, **kwargs)
            if writer_error == "error":
                error_writer.side_effect = RuntimeError("synthetic error writer failure")
            else:
                error_writer.side_effect = lambda recordset, *args, **kwargs: create_error(
                    recordset, *args, **kwargs)
            result = sender.dispatch_send()
        rows = self.logs.search([]).filtered(lambda row: row.id not in before)
        return service, sender, response, transport, hook, log_writer, error_writer, result, rows

    def _assert_minimal(self, rows, state):
        self.assertEqual(len(rows), 1)
        row = rows.ensure_one()
        self.assertEqual(row.state, state)
        self.assertEqual(row.client_id, self.client)
        self.assertEqual(row.endpoint_id, self.endpoint)
        self.assertEqual(row.credential_id, self.credential)
        self.assertFalse(row.request_context)
        self.assertFalse(row.response)

    def test_u01_endpoint_on_success_creates_attributed_minimal_row(self):
        service, sender, response, transport, hook, _, _, result, rows = self._dispatch()
        self.assertTrue(sender.active_log)
        self.assertIsNone(result)
        self.assertEqual(transport.call_count, 1)
        self.assertEqual(response.raise_for_status.call_count, 1)
        self.assertEqual(len(rows), 1)
        self._assert_minimal(rows, "done")

    def test_u02_endpoint_off_success_has_no_row(self):
        _, sender, _, transport, _, _, _, result, rows = self._dispatch(False)
        self.assertFalse(sender.active_log)
        self.assertIsNone(result)
        self.assertEqual(transport.call_count, 1)
        self.assertFalse(rows)

    def test_u03_prepare_failure_logs_error_when_endpoint_on_and_off(self):
        for enabled in (True, False):
            _, _, _, transport, hook, _, _, result, rows = self._dispatch(enabled, error="prepare")
            self.assertEqual(transport.call_count, 0)
            self.assertEqual(hook.call_count, 1)
            self.assertIsNone(result)
            self.assertEqual(len(rows), 1)
            self._assert_minimal(rows, "error")

    def test_u04_transport_failure_logs_error_when_endpoint_on_and_off(self):
        for enabled in (True, False):
            _, _, _, transport, hook, _, _, result, rows = self._dispatch(enabled, error="transport")
            self.assertEqual(transport.call_count, 1)
            self.assertEqual(hook.call_count, 1)
            self.assertIsNone(result)
            self.assertEqual(len(rows), 1)
            self._assert_minimal(rows, "error")

    def test_u05_http_failure_logs_error_when_endpoint_on_and_off(self):
        for enabled in (True, False):
            _, _, response, transport, hook, _, _, result, rows = self._dispatch(enabled, error="http")
            self.assertEqual(transport.call_count, 1)
            self.assertEqual(response.raise_for_status.call_count, 1)
            self.assertEqual(hook.call_count, 1)
            self.assertIsNone(result)
            self.assertEqual(len(rows), 1)
            self._assert_minimal(rows, "error")

    def test_u06_sender_explicit_flags_and_none(self):
        from odoo.addons.amr_service_client.models.service_client import ServiceClientSend
        service = self.client.get_service_client(self.endpoint, path="/" + self.marker, method="POST")
        for endpoint_flag, explicit, expected in ((True, True, True), (True, False, False),
                                                  (False, True, True), (False, False, False),
                                                  (True, None, True), (False, None, False)):
            self.endpoint.write({"active_log": endpoint_flag})
            sender = ServiceClientSend(service, {"marker": self.marker}, active_log=explicit,
                                       endpoint_id=self.endpoint, credential_id=self.credential)
            self.assertEqual(sender.active_log, expected)
            before = set(self.logs.search([]).ids)
            with patch("odoo.addons.amr_service_client.models.service_client.requests.request",
                       return_value=Mock(text=self.marker)) as transport:
                with patch.object(service, "_report_sentry"):
                    sender.dispatch_send()
            rows = self.logs.search([]).filtered(lambda row: row.id not in before)
            self.assertEqual(transport.call_count, 1)
            self.assertEqual(len(rows), int(expected))
            if expected:
                self._assert_minimal(rows, "done")
        sender = ServiceClientSend(service, {"marker": self.marker}, endpoint_id=self.endpoint,
                                   credential_id=self.credential)
        self.assertFalse(sender.active_log)
        before = set(self.logs.search([]).ids)
        with patch("odoo.addons.amr_service_client.models.service_client.requests.request",
                   return_value=Mock(text=self.marker)) as transport:
            with patch.object(service, "_report_sentry"):
                sender.dispatch_send()
        self.assertEqual(transport.call_count, 1)
        self.assertFalse(self.logs.search([]).filtered(lambda row: row.id not in before))

    def test_u07_no_endpoint_sender_defaults_off_and_does_not_log(self):
        service = self.env["service.client"].get_service_client(
            False, credential=self.credential, path="/" + self.marker, method="POST")
        sender = service.prepare_payload(marker=self.marker)
        original_authenticate = service.provider.authenticate

        def synthetic_provider(context, audience=None):
            context = original_authenticate(context, audience=audience)
            context["url"] = "https://example.invalid/" + self.marker
            return context

        before = set(self.logs.search([]).ids)
        with patch.object(service.provider, "authenticate", side_effect=synthetic_provider) as provider, \
             patch("odoo.addons.amr_service_client.models.service_client.requests.request",
                   return_value=Mock(text=self.marker)) as transport, \
             patch.object(service, "_report_sentry"):
            result = sender.dispatch_send()
        self.assertFalse(sender.active_log)
        self.assertIsNone(result)
        self.assertEqual(provider.call_count, 1)
        self.assertEqual(transport.call_count, 1)
        self.assertEqual(transport.call_args[1]["url"], "https://example.invalid/" + self.marker)
        self.assertFalse(self.logs.search([]).filtered(lambda row: row.id not in before))

    def test_u08_sender_uses_client_snapshot_after_endpoint_toggle(self):
        for initial, changed in ((True, False), (False, True)):
            self.endpoint.write({"active_log": initial})
            service = self.client.get_service_client(self.endpoint, path="/" + self.marker, method="POST")
            self.endpoint.write({"active_log": changed})
            sender = service.prepare_payload(marker=self.marker)
            before = set(self.logs.search([]).ids)
            with patch("odoo.addons.amr_service_client.models.service_client.requests.request",
                       return_value=Mock(text=self.marker)) as transport, patch.object(service, "_report_sentry"):
                sender.dispatch_send()
            self.assertEqual(transport.call_args[1]["url"], "https://example.invalid/" + self.marker)
            rows = self.logs.search([]).filtered(lambda row: row.id not in before)
            self.assertEqual(sender.active_log, initial)
            self.assertEqual(len(rows), int(initial))

    def test_u09_sender_override_changes_success_log_without_endpoint_mutation(self):
        for override in (True, False):
            self.endpoint.write({"active_log": False})
            before = set(self.logs.search([]).ids)
            self._dispatch(False, sender_flag=override)
            rows = self.logs.search([]).filtered(lambda row: row.id not in before)
            self.assertEqual(self.endpoint.active_log, False)
            self.assertEqual(len(rows), int(override))

    def test_u10_active_log_payload_key_remains_transport_data(self):
        payload = {"active_log": self.marker, "nested": {"marker": self.marker}}
        expected = copy.deepcopy(payload)
        _, sender, _, transport, _, _, _, _, _ = self._dispatch(True, payload=payload)
        self.assertEqual(sender.payload, expected)
        self.assertEqual(transport.call_args[1]["json"], expected)
        self.assertEqual(payload, expected)

    def test_u11_writer_failure_fallback_and_final_writer_exception(self):
        *_, transport, hook, log_writer, error_writer, result, rows = self._dispatch(
            True, writer_error="success")
        self.assertEqual(transport.call_count, 1)
        self.assertEqual(hook.call_count, 1)
        self.assertEqual(log_writer.call_count, 2)
        self.assertEqual([entry[0][1] for entry in log_writer.call_args_list], ['done', 'error'])
        self.assertEqual(error_writer.call_count, 1)
        self.assertIsNone(result)
        self.assertEqual(len(rows), 1)
        self._assert_minimal(rows, "error")
        with self.assertRaises(RuntimeError):
            self._dispatch(True, error="transport", writer_error="error")

    def test_u12_reporting_hook_exception_is_suppressed_and_dispatch_continues(self):
        _, _, _, transport, hook, _, _, result, rows = self._dispatch(True, hook_error=True)
        self.assertEqual(transport.call_count, 1)
        self.assertEqual(hook.call_count, 1)
        self.assertIsNone(result)
        self.assertEqual(len(rows), 1)
        self._assert_minimal(rows, "done")
        _, _, _, transport, hook, _, _, result, rows = self._dispatch(
            False, error="transport", hook_error=True)
        self.assertEqual(transport.call_count, 1)
        self.assertEqual(hook.call_count, 1)
        self.assertIsNone(result)
        self.assertEqual(len(rows), 1)
        self._assert_minimal(rows, "error")

    def test_u13_rpc_cannot_forge_log_and_internal_dispatch_attributes_row(self):
        user = self.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Synthetic ordinary ADDONS13-71 user',
            'login': 'addons13-71-ordinary-' + uuid.uuid4().hex,
            'groups_id': [(6, 0, self.env.ref('base.group_user').ids)],
            'company_id': self.env.company.id,
            'company_ids': [(6, 0, self.env.company.ids)],
        })
        self.assertTrue(user.has_group("base.group_user"))
        self.assertFalse(user.has_group("base.group_system"))
        before = set(self.logs.search([]).ids)
        for method in ("_create_log", "_create_error"):
            with self.assertRaises(AccessError):
                execute(self.env.cr.dbname, user.id, "service.client.log", method, [],
                        state="done", client_id=self.client.id)
        for method in ("create_log", "create_error"):
            with self.assertRaises(AttributeError):
                if method == "create_log":
                    execute(self.env.cr.dbname, user.id, "service.client.log", method,
                            [], "done", client_id=self.client.id)
                else:
                    execute(self.env.cr.dbname, user.id, "service.client.log", method,
                            [], "synthetic", client_id=self.client.id)
        with self.assertRaises(AccessError):
            execute(self.env.cr.dbname, user.id, "service.client.log", "create",
                    [[{"state": "done", "client_id": self.client.id}]])
        self.assertEqual(set(self.logs.search([]).ids), before)
        *_, rows = self._dispatch(True)
        self.assertEqual(len(rows), 1)
        self.assertIs(type(self.client.id), int)
        self._assert_minimal(rows, "done")

    def test_u14_direct_call_and_action_do_not_create_log_sender_reports_once(self):
        service = self.client.get_service_client(self.endpoint, path="/" + self.marker, method="POST")
        before = set(self.logs.search([]).ids)
        with patch("odoo.addons.amr_service_client.models.service_client.requests.request",
                   return_value=Mock(text=self.marker)) as transport, \
             patch.object(service, "_report_sentry") as report:
            service.call(method="POST", path="/direct", payload={"marker": self.marker})
        self.assertEqual(transport.call_count, 1)
        self.assertEqual(report.call_count, 1)
        self.assertEqual(set(self.logs.search([]).ids), before)
        # Exercise the actual server-action runner, not just the post wrapper.
        self.client.write({
            "iteration": "response = [{}]",
            "code": "path = '/action'\nmethod = 'POST'\npayload = {'marker': %r}" % self.marker,
        })
        records = self.env['res.partner'].browse()
        before_action = set(self.logs.search([]).ids)
        from odoo.addons.amr_service_client.models.service_client import ServiceClient
        # Supply a mutable synthetic action context; the action runner and client path remain real.
        action_context = {'ctx': {}, 'env': self.env, 'user': self.env.user}
        with patch.object(type(self.client), '_get_eval_context', return_value=action_context):
            with patch("odoo.addons.amr_service_client.models.service_client.requests.request",
                       return_value=Mock(text=self.marker)) as action_transport:
                with patch.object(ServiceClient, "_report_sentry") as action_report:
                    with patch.object(type(self.client.action_next_id), "run",
                                      return_value="synthetic-next-action") as next_action:
                        action_result = self.client.run_action_service_client(
                            eval_context={"records": records})
        self.assertEqual(action_transport.call_count, 1)
        self.assertEqual(action_transport.call_args[1]["method"], "POST")
        self.assertEqual(action_transport.call_args[1]["json"], {"marker": self.marker})
        self.assertEqual(action_report.call_count, 1)
        self.assertEqual(action_result, "synthetic-next-action")
        next_action.assert_called_once()
        self.assertEqual(set(self.logs.search([]).ids), before_action)

        action_service = self.client.get_service_client(self.endpoint, path="/" + self.marker, method="POST")
        before = set(self.logs.search([]).ids)
        with patch("odoo.addons.amr_service_client.models.service_client.requests.request",
                   return_value=Mock(text=self.marker)) as action_transport, \
             patch.object(action_service, "_report_sentry") as action_report:
            action_service.post(path="/action", payload={"marker": self.marker})
        self.assertEqual(action_transport.call_count, 1)
        self.assertEqual(action_report.call_count, 1)
        self.assertEqual(set(self.logs.search([]).ids), before)
        # Sender reporting contract, including hook failure on both outcomes.
        for failure in (None, "transport"):
            before = set(self.logs.search([]).ids)
            self._dispatch(True, error=failure, hook_error=True)
            rows = self.logs.search([]).filtered(lambda row: row.id not in before)
            self.assertEqual(len(rows), 1)
            self._assert_minimal(rows, "done" if failure is None else "error")
