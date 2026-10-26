# -*- coding: utf-8 -*-

import base64
import json
import logging
import random
import re
import requests
import traceback

from ..services.sentry_reporting import report_outcome, report_sentry

from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import UUID
from odoo import api, fields, models, tools
from odoo.exceptions import ValidationError
from odoo.tools import config
from odoo.fields import Datetime, Date
from odoo.tools.safe_eval import safe_eval, test_python_expr

_logger = logging.getLogger(__name__)

DEFAULT_PYTHON_CODE = """# Available variables:
#  - ctx: Odoo Context on which the action is triggered
#  - env: Odoo Environment on which the action is triggered
#  - user: user 
#  - records : Record
# To return an response, assign: 
# path = ""
# method = ""
# audience = ""
# params = {...}
# headers = {...}
# payload = {...}  


\n\n\n\n
"""

DEFAULT_PYTHON_CODE_HANDLE = """# Available variables:
#  - ctx: Odoo Context on which the action is triggered
#  - env: Odoo Environment on which the action is triggered
#  - user: user 
#  - records : Record
#  - response

\n\n\n\n
"""

DEFAULT_INTERATION_CONTEXT_CODE = """# Available variables:
#  - ctx: Odoo Context on which the action is triggered
#  - env: Odoo Environment on which the action is triggered
#  - user: user 
#  - records : Record
#  - response 
#
#  response = [{'notification_to_user': user} for user in ctx.get('notification_to_users', [])]
response = [{}]
\n\n\n\n
"""


def normalize_json(value):
    """
    Convert Python objects into JSON-serializable types (recursive)
    """
    if value is None:
        return None

    # Primitive JSON-safe
    if isinstance(value, (str, int, float, bool)):
        return value

    # datetime / date
    if isinstance(value, datetime):
        return Datetime.to_string(value)
    if isinstance(value, date):
        return Date.to_string(value)

    if isinstance(value, (bytes, bytearray)):
        return base64.b64encode(value).decode()

    if isinstance(value, UUID):
        return str(value)

    # Decimal → float (atau str kalau mau aman)
    if isinstance(value, Decimal):
        return float(value)

    # dict → recursive
    if isinstance(value, dict):
        return {
            k: normalize_json(v)
            for k, v in value.items()
        }

    # list / tuple / set → list
    if isinstance(value, (list, tuple, set)):
        return [normalize_json(v) for v in value]

    # fallback (object aneh)
    return str(value)


class ServiceClientSend:

    def __init__(self, service_client, payload, active_log=False, endpoint_id=None, credential_id=None):
        self.payload = normalize_json(payload)
        self.service_client = service_client
        self.env = service_client.env
        self.client_id = service_client.client_id
        if endpoint_id is None:
            self.endpoint_id = self.service_client.endpoint_id
        else:
            self.endpoint_id = endpoint_id
        if active_log is None and self.endpoint_id:
            self.active_log = self.endpoint_id.active_log
        else:
            self.active_log = active_log
        if not credential_id and self.endpoint_id:
            self.credential_id = self.endpoint_id.credential_id
        else:
            self.credential_id = credential_id

    def dispatch_send(self):
        response = None
        active_log = self.active_log
        request_context = {'payload': self.payload}
        try:
            request_context = self.service_client.prepare_request_context(**request_context)
            response = requests.request(**request_context)
            response.raise_for_status()
            report_sentry(self.env, "success", response=response)
            if active_log:
                self.env["service.client.log"].create_error(
                    'done', client_id=self.client_id, endpoint_id=self.endpoint_id, credential_id=self.credential_id,
                    request_context=request_context, response_text=response.text
                )

        except Exception as e:
            report_sentry(self.env, "error", response=response, exception=e)
            _logger.exception("error dispatch_send")
            self.env["service.client.log"].create_error(
                e, client_id=self.client_id, endpoint_id=self.endpoint_id, credential_id=self.credential_id,
                request_context=request_context
            )

class ServiceClient:

    def __init__(self, env, endpoint, credential, path=None, method=None, client_id=None):
        self.env = env
        self.endpoint = endpoint
        self.credential_id = credential
        self.loader = env["service.credential.loader"]
        self.credential = self.loader.get_credential(credential or endpoint.credential_id)
        self.credential_data = self.loader.load_credential(credential) if self.credential else None
        self.provider = env["service.auth.factory"].create_service_auth(self.credential_data)
        self.path = path
        self.method = method
        self.active_log = endpoint.active_log
        self.client_id = client_id

    def __enter__(self):
        # self.client.connect()
        return self

    def __exit__(self, *args):
        pass

    def prepare_request_context(self, path=None, method=None, params=None, payload=None, headers=None, audience=None):
        url = self.endpoint.get_url(path or self.path)
        request_context = {
            "url": url,
            "headers": self.endpoint.request_headers_default(headers),
            "params": params,
            "json": normalize_json(payload),
            "timeout": self.endpoint.timeout,
        }
        if method:
            request_context['method'] = method
        elif self.method:
            request_context['method'] = self.method

        request_context = self.provider.authenticate(request_context, audience=audience or self.endpoint.audience)
        return request_context

    def _report_sentry(self, outcome, response=None, exception=None):
        report_sentry(self.env, outcome, response=response, exception=exception)
        # try:
        #     mode = (self.env['ir.config_parameter'].sudo().get_param(
        #         'amr_service_client.sentry_mode', 'none') or 'none').lower()
        #     report_outcome(self.env, mode, bool(getattr(self, 'sentry_opt_in', False)),
        #                    outcome, method=self.method,
        #                    status_code=getattr(response, 'status_code', None))
        # except Exception:
        #     _logger.debug('Sentry reporting configuration unavailable', exc_info=False)

    def call(self, method=None, path=None, params=None, payload=None, headers=None, audience=None, active_log=False):
        request_context = self.prepare_request_context(path, method, params=params, payload=payload, headers=headers)
        try:
            response = requests.request(**request_context)
        except Exception as exc:
            report_sentry(self.env, "error", response=None, exception=exc)
            raise
        if not 200 <= response.status_code < 300:
            report_sentry(self.env, "error", response=response)
        else:
            report_sentry(self.env, "success", response=response)
        return response

    def get(self, path=None, params=None, **kwargs):
        return self.call(method="GET", path=path, params=params, **kwargs)

    def post(self, path=None, payload=None, **kwargs):
        return self.call(method="POST", path=path, payload=payload, **kwargs)

    def put(self, path=None, payload=None, **kwargs):
        return self.call(method="PUT", path=path, payload=payload, **kwargs)

    def delete(self, path=None, **kwargs):
        return self.call(method="DELETE", path=path, **kwargs)

    def prepare_payload(self, **payload):
        return ServiceClientSend(
            self, payload, endpoint_id=self.endpoint, active_log=self.endpoint.active_log
        )


class RemoteObjectProxy:

    def __init__(self, client, model_name, **kwargs):
        self.client = client
        self.model_name = model_name
        self.context = kwargs.get('context', {})
        self.domain = kwargs.get('domain', [])
        self.fields = kwargs.get('fields')
        self.offset = kwargs.get('offset', 0)
        self.limit = kwargs.get('limit', 500)
        self.order = kwargs.get('order', None)

    def __enter__(self):
        # self.client.connect()
        return self

    def __exit__(self, *args):
        pass

    def __getattr__(self, method_name):
        def method(*args, **kwargs):
            return self.call(method_name, args, kwargs)

        return method

    def call(self, method, args, kwargs=None):
        kw = dict(kwargs or {})
        context = self.context or {}
        if 'context' in kw:
            context.update(kw['context'] or {})
        kw['context'] = context
        path = '/api/dataset/call_kw'
        headers = {"Content-Type": "application/json"}
        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {'model': self.model_name, "method": method, "args": args or [], "kwargs": kw},
            "id": 1
        }
        _logger.info("payload %s .", payload)
        resp = self.client.post(
            path=path,
            headers=headers,
            payload=payload
        )
        resp.raise_for_status()
        data = resp.json()

        # JSON-RPC error
        if "error" in data:
            raise RuntimeError(f"Odoo login error: {data['error']}")

        return data.get("result") or []

    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        method = 'search_read'
        args = []
        kw = {
            'domain': domain or self.domain or [],
            'fields': fields or self.fields, 'order': order or self.order,
            'offset': offset or self.offset, 'limit': limit or self.limit,
        }
        return self.call(method, args, kwargs=kw)

    def read(self, *args, fields=None):
        method = 'read'
        # if not args and self.ids and isinstance(self.ids, (list, tuple)):
        #     args = self.ids
        kw = {'fields': fields or self.fields}
        return self.call(method, args, kwargs=kw)

    def search_count(self):
        method = 'search_count'
        args = [self.domain or []]
        return self.call(method, args=args)

    def external_data_callback(self, call_back):
        total = self.search_count()
        offset = 0
        limit = self.limit
        row_count = self.limit
        _logger.info("Start : external_data_callback %s = total %s", self.model_name, total)
        while total and row_count == limit:
            data = self.search_read(offset=offset, limit=limit)
            row_count = len(data) if data else 0
            if row_count == 0:
                break
            _logger.info("Count %s ,Offset %s, Total: %s", row_count, offset, total)
            for item in data:
                offset = offset + 1
                # self.ids = [item.get('id')]
                call_back(item, offset=offset, total=total)

        _logger.info("Done : Offset %s = total %s", offset, total)

    def __str__(self):
        return "remote.RemoteModel({})".format(self.model_name)

    __repr__ = __str__


class ServiceClientFactory(models.Model):
    _name = 'service.client'
    _description = "Service Client"

    active = fields.Boolean(default=True, help="When unchecked, the rule is hidden and will not be executed.")
    name = fields.Char()
    model_id = fields.Many2one('ir.model', string='Model', required=True, ondelete='cascade')
    endpoint_id = fields.Many2one("service.endpoint")
    credential_id = fields.Many2one("service.credential")
    active_log = fields.Boolean()
    sentry_opt_in = fields.Boolean(string="Report to Sentry", help="Include this client when Sentry mode is Selected.")
    each_record = fields.Boolean(
        string="Each Record",
        default=False,
        help="If checked, the action will be executed for each record in the recordset."
    )
    iteration = fields.Text(
        "Iteration Context",
        default=DEFAULT_INTERATION_CONTEXT_CODE,
        help="Expression returning the interation context"
             "This context will be available in the python code as"
             "ctx.get('iteration')."
    )

    code = fields.Text(
        string='Python Code',
        default=DEFAULT_PYTHON_CODE,
        help="Write Python code that the action will execute. Some variables are "
             "available for use; help about python expression is given in the help tab."
    )

    handle = fields.Text(
        string='Python Code Handle',
        default=DEFAULT_PYTHON_CODE_HANDLE,
        help="Write Python code handle response that the action will execute. Some variables are "
             "available for use; help about python expression is given in the help tab."
    )
    action_next_id = fields.Many2one('ir.actions.server')
    payload_ids = fields.One2many('service.client.payload', 'service_client_id')
    error_handle_id = fields.Many2one('ir.actions.server')

    @api.model
    def _get_eval_context(self):
        """ evaluation context to pass to safe_eval """
        return {
            'ctx': self.env.context,
            'env': self.env,
            'user': self.env.user,
        }

    @api.constrains('iteration')
    def _check_python_iteration(self):
        for action in self.sudo().filtered('iteration'):
            msg = test_python_expr(expr=action.iteration.strip(), mode="exec")
            if msg:
                raise ValidationError(msg)

    def _run_action_iteration(self, eval_context):
        safe_eval(self.iteration.strip(), eval_context, mode="exec", nocopy=True)  # nocopy allows to return 'action'
        return eval_context

    @api.constrains('code')
    def _check_python_code(self):
        for action in self.sudo().filtered('code'):
            msg = test_python_expr(expr=action.code.strip(), mode="exec")
            if msg:
                raise ValidationError(msg)

    def _run_action_code(self, eval_context):
        safe_eval(self.code.strip(), eval_context, mode="exec", nocopy=True)  # nocopy allows to return 'action'
        return eval_context

    @api.constrains('handle')
    def _check_python_handle(self):
        for action in self.sudo().filtered('handle'):
            msg = test_python_expr(expr=action.handle.strip(), mode="exec")
            if msg:
                raise ValidationError(msg)

    def _run_action_handle(self, eval_context):
        safe_eval(self.handle.strip(), eval_context, mode="exec", nocopy=True)  # nocopy allows to return 'action'
        return eval_context

    def send_request(self, records):
        self.ensure_one()
        eval_context = self._get_eval_context()
        eval_context['records'] = records
        self.run_action_service_client(eval_context=eval_context)

    def run_action_service_client(self, eval_context=None):
        self.ensure_one()
        action = None

        def call_records(records):
            eval_context_result = {}
            eval_interation_context = self._get_eval_context()
            eval_interation_context = self._run_action_iteration(eval_interation_context)
            response = eval_interation_context.pop('response', [])
            for int_ctx in response:
                ctx = eval_interation_context.get('ctx', {})
                int_ctx = int_ctx or {}
                ctx.update(int_ctx)
                eval_context_local = dict(eval_context or {})
                eval_context_local['ctx'] = ctx
                record = eval_context_local.get('record')
                if record and record != records:
                    eval_context_local['record'] = record.with_context(ctx)
                eval_context_local['records'] = records.with_context(ctx)
                eval_context_local['payload'] = self.payload_ids.get_payload(eval_context_local)
                eval_context_local.update(self._run_action_code(eval_context_local))
                path = eval_context_local.get('path') or None
                method = eval_context_local.get('method') or "POST"
                params = eval_context_local.get('params') or {}
                headers = eval_context_local.get('headers') or {}
                payload = eval_context_local.get('payload') or {}
                client = self.get_service_client(self.endpoint_id, credential=self.credential_id)
                try:
                    response = client.call(method, path, params, payload, headers)
                    eval_context_local['response'] = response
                    eval_context_local.update(self._run_action_handle(eval_context_local) or {})
                    eval_context_local['action'] = self.action_next_id.with_context(eval_context_local).run()
                except Exception as e:
                    eval_context_local['exception'] = e
                    if self.error_handle_id:
                        self.error_handle_id.with_context(eval_context_local).run()
                    else:
                        raise e
                eval_context_result = eval_context_local

            return eval_context_result

        if self.each_record:
            for rec in eval_context['records']:
                result_context = call_records(rec) or {}
                if 'action' in result_context:
                    action = result_context['action']
        else:
            result_context = call_records(eval_context['records'])
            if 'action' in result_context:
                action = result_context['action']
        return action

    def _get_endpoint(self, code):
        if isinstance(code, int):
            endpoint = self.env["service.endpoint"].browse(code)
        elif isinstance(code, str):
            endpoint = self.env["service.endpoint"].search([("code", "=", code), ("active", "=", True), ], limit=1, )
        else:
            endpoint = code
        if not endpoint:
            raise ValueError("Service '%s' not found" % code)
        return endpoint

    def get_service_client(self, service_code, credential=None, path=None, method=None):
        if self:
            endpoint = self._get_endpoint(service_code or self.endpoint_id)
            credential = credential or endpoint.credential_id or self.credential_id
        else:
            endpoint = self._get_endpoint(service_code)
            credential = credential or endpoint.credential_id

        client = ServiceClient(self.env, endpoint, credential, path=path, method=method)
        client.sentry_opt_in = bool(self and self.sentry_opt_in)
        return client

    def get_remote_object(self, service_code, model_name, credential=None, **kwargs):
        endpoint = self._get_endpoint(service_code)
        credential = credential or endpoint.credential_id
        client = ServiceClient(self.env, endpoint, credential)
        return RemoteObjectProxy(client, model_name, **kwargs)

    def call(self, service, method, path, params=None, payload=None, headers=None, credential=None, audience=None):
        client = self.get_service_client(service, credential=credential)
        return client.call(method=method, path=path, params=params, payload=payload, headers=headers, audience=audience)

    def get(self, service, path, params=None, headers=None, credential=None, audience=None):
        return self.call(
            service=service, method="GET", path=path, params=params, headers=headers,
            credential=credential, audience=audience
        )

    def post(self, service, path, payload=None, headers=None, credential=None, audience=None):
        return self.call(
            service=service, method="POST", path=path, payload=payload, headers=headers,
            credential=credential, audience=audience
        )

    def put(self, service, path, payload=None, headers=None, credential=None, audience=None):
        return self.call(
            service=service, method="PUT", path=path, payload=payload, headers=headers,
            credential=credential, audience=audience
        )

    def delete(self, service, path, headers=None, credential=None, audience=None):
        return self.call(
            service=service, method="DELETE", path=path, headers=headers,
            credential=credential, audience=audience
        )


class ServiceClientPayload(models.Model):
    _name = 'service.client.payload'

    key = fields.Char('Key')
    value = fields.Text('Value')
    type = fields.Selection([
        ('fix', 'Fixed Value'),
        ('exp', 'Expression'),
        ('random_int', 'Random Integer'),
    ], 'Type', default="fix")
    service_client_id = fields.Many2one('service.client')

    def get_type_display(self):
        labels = {'fix': 'Fixed', 'record': 'Expression', 'random_int': 'Random Int'}
        return labels.get(self.type, self.type or '')

    @api.model
    def custom_render(self, template_str, context):
        pattern = re.compile(r'\${(.*?)}')

        def replacer(match):
            expr = match.group(1)
            try:
                return str(safe_eval(expr, context))
            except Exception as e:
                _logger.error("Error rendering expression '%s': %s", expr, e)
                return ''

        return pattern.sub(replacer, template_str)

    def get_payload(self, context=None):
        payload = {}
        for param in self:
            value = None
            if param.type == 'fix':
                value = param.value
            elif param.type == 'exp':
                if '${' in param.value:
                    value = self.custom_render(param.value, context)
                else:
                    value = safe_eval(param.value, context)
            elif param.type == 'random_int':
                value = random.randint(0, int(param.value) if param.value.isdigit() else 1000)
            payload[param.key] = value
        return payload
