# -*- coding: utf-8 -*-

import json
import re
import requests
import logging
import traceback

from odoo import api, fields, models
from ..services.sentry import capture_service_event
from ..services.request_errors import request_exception_text

_logger = logging.getLogger(__name__)


class ServiceClientLog(models.Model):
    _name = "service.client.log"
    _description = "Integration Log"
    _order = "id desc"

    state = fields.Selection([('outgoing', 'Outgoing'), ('done', 'Done'), ('error', 'Error')])
    endpoint_id = fields.Many2one("service.endpoint")
    credential_id = fields.Many2one("service.credential")
    client_id = fields.Many2one("service.client")
    request_context = fields.Text()
    response = fields.Text()

    def dispatch_send(self):
        # asynchronous mode
        self.send()
        return self

    def send(self):
        response_text = None
        error = None
        try:
            client = self.client_id.get_service_client(self.endpoint_id, self.credential_id)
            request_context = json.loads(self.request_context)
            request_context["headers"] = self.endpoint_id.request_headers_default(request_context.get("headers"))
            request_context = client.provider.authenticate(request_context, self.endpoint_id.audience)
            response = requests.request(**request_context)
            response.raise_for_status()
            state = 'done'
            response_text = response.text
        except requests.RequestException as e:
            error = e
            _logger.error("Failed to resend request (exception type: %s)", type(e).__name__)
            response_text = request_exception_text(e)
            state = 'error'
        except Exception as e:
            error = e
            response_text = self.format_error(e)
            state = 'error'

        self.write({
            "state": state,
            "response": self.sanitize_sensitive_data(response_text)
        })
        capture_service_event(
            self.env, 'service.client.log', self.id, state,
            endpoint_id=self.endpoint_id.id if self.endpoint_id else None,
            client_id=self.client_id,
            error_type=type(error).__name__ if error else None,
        )
        return self

    @api.model
    def format_error(self, e: Exception, extra_params=None):
        # 1. Ambil stack trace lengkap sebagai string
        tb_str = traceback.format_exc()

        # 2. Susun informasi parameter tambahan
        param_info = ""
        log_texts = [f"EXCEPTION TYPE: {type(e).__name__}\n", f"MESSAGE: {str(e)}\n", f"{param_info}\n"]
        if extra_params:
            param_info = "\n--- PARAMETER ---\n"
            for key, value in extra_params.items():
                param_info += f"{key}: {value}\n"

        if isinstance(e, requests.RequestException):
            request_body_raw = getattr(e.request, 'body', None)
            if request_body_raw:
                # Jika berbentuk bytes, decode ke utf-8
                if isinstance(request_body_raw, bytes):
                    request_body_text = request_body_raw.decode('utf-8')
                else:
                    request_body_text = str(request_body_raw)
                log_texts.append(f"--- REQUEST TEXT ---\n{request_body_text}")
            else:
                # Tidak ada request body (misal: Method GET)"
                log_texts.append("--- NO REQUEST TEXT ---")

            # Ambil juga Response Body dari server (jika ada)
            if hasattr(e, 'response'):
                response_body_text = getattr(e.response, 'text', "")
                log_texts.append(f"--- RESPONSE TEXT ---\n{response_body_text}")
            else:
                log_texts.append("--- NO RESPONSE TEXT ---")

        # 3. Gabungkan semuanya menjadi satu teks log utuh
        if tb_str:
            log_texts.append(f"--- STACK TRACE ---\n{tb_str}")
        return "\n".join(log_texts)

    def create_error(self, e: Exception, **kwargs):
        kwargs['response_text'] = self.format_error(e, extra_params=kwargs.get('extra_params', None))
        return self.sudo().create_log('error', **kwargs)

    def create_log(self, state, client_id=None, endpoint_id=None, credential_id=None, request_context=None, **kwargs):

        if request_context:
            if isinstance(credential_id, models.AbstractModel) and credential_id._name == 'service.credential':
                request_context = credential_id.sanitizer_request_context(request_context)
            else:
                request_context.pop('headers', None)

        return self.sudo().create({
            'state': state,
            'client_id': client_id.id if client_id else None,
            'endpoint_id': endpoint_id.id if endpoint_id else None,
            'credential_id': credential_id.id if credential_id else None,
            'request_context': json.dumps(request_context, indent=4) if request_context else None,
            'response': self.sanitize_sensitive_data(kwargs.get('response_text', None)),
        })

    @api.model
    def sanitize_sensitive_data(self, text):
        """
        Fungsi untuk menyamarkan data sensitif menggunakan Regex
        sebelum disimpan ke field text/database.
        """
        if text is None:
            return None

        if not isinstance(text, str):
            text = str(text)

        # 1. Masking untuk Header Authorization (Bearer Token / Basic Auth)
        text = re.sub(r'(Authorization:\s*["\']?)(Bearer\s+[^\s"\']+|Basic\s+[^\s"\']+)(["\']?)',
                      r'\1[REDACTED_TOKEN]\3', text, flags=re.IGNORECASE)

        # 2. Masking untuk Key JSON umum (password, secret, api_key, token, pin)
        # Contoh: "password": "12345secret" -> "password": "******"
        patterns = [
            r'(["\']?(?:password|passwd|pwd|secret|api_key|apikey|token|auth_token|access_token|pin)["\']?\s*[:=]\s*["\'])([^"\']+)(["\'])',
        ]
        for pattern in patterns:
            text = re.sub(pattern, r'\1******\3', text, flags=re.IGNORECASE)

        return text
