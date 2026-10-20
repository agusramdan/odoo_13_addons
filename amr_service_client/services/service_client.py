# -*- coding: utf-8 -*-

import base64
import logging
import requests

from odoo import api, models, tools

from odoo.fields import Datetime, Date
from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import UUID


_logger = logging.getLogger(__name__)


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


class ServiceClient:

    def __init__(self, env, endpoint, credential):
        self.env = env
        self.endpoint = endpoint
        self.loader = env["service.credential.loader"]
        self.credential = self.loader.get_credential(credential or endpoint.credential_id)
        self.credential_data = self.loader.load_credential(credential)
        self.provider = env["service.auth.factory"].create_service_auth(self.credential_data)

    def __enter__(self):
        # self.client.connect()
        return self

    def __exit__(self, *args):
        pass

    def prepare_request_context(self,path, method=None, params=None, payload=None, headers=None,audience=None):
        url = self.endpoint.get_url(path)
        request_headers = {}
        # request_headers.update(auth_headers)
        request_headers.update(headers or {})
        # Content - Type: text / plain
        request_headers.setdefault("Content-Type", "text/plain")
        request_headers.setdefault("Accept", "application/json")
        request_context = {
            "url": url,
            "headers": request_headers,
            "params": params,
            "json": normalize_json(payload),
            "timeout": self.endpoint.timeout,
        }
        if method:
            request_context['method'] = method
        request_context = self.provider.authenticate(request_context, audience=audience or self.endpoint.audience, )
        return request_context

    def call(self, method, path, params=None, payload=None, headers=None, audience=None):
        request_context = self.prepare_request_context(path,method,params=params, payload=payload, headers=headers)
        return requests.request(**request_context)

    def get(self, path, params=None, **kwargs):
        return self.call(method="GET", path=path, params=params, **kwargs)

    def post(self, path, payload=None, **kwargs):
        return self.call(method="POST", path=path, payload=payload, **kwargs)

    def put(self, path, payload=None, **kwargs):
        return self.call(method="PUT", path=path, payload=payload, **kwargs)

    def delete(self, path, **kwargs):
        return self.call(method="DELETE", path=path, **kwargs)


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


class ServiceClientFactory(models.AbstractModel):
    _name = 'service.client'
    _description = "Client"

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

    def get_service_client(self, service_code, credential=None):
        endpoint = self._get_endpoint(service_code)
        credential = credential or endpoint.credential_id
        return ServiceClient(self.env, endpoint, credential)

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
