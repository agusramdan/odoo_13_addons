from support import *
from decimal import Decimal
from unittest import mock
import datetime, uuid

class Http(OfflineCase):
 @classmethod
 def setUpClass(cls):
  cls.m=load('models/service_client.py'); cls.endpoint_m=load('models/service_endpoint.py')
 def endpoint(self, **kw):
  defaults=dict(get_url=lambda p:'https://invalid.test/base/'+str(p or ''), request_headers_default=lambda h:dict(h or {}), timeout=3, audience='constructor-aud', credential_id=None, active_log=False)
  defaults.update(kw); return types.SimpleNamespace(**defaults)
 def test_normalize_json_types_recursive_and_unknown(self):
  m=self.m
  self.assertEqual(m.normalize_json(b'x'),'eA=='); self.assertEqual(m.normalize_json(bytearray(b'y')),'eQ==')
  self.assertEqual(m.normalize_json(Decimal('1.5')),1.5); self.assertEqual(m.normalize_json(uuid.UUID(int=1)),str(uuid.UUID(int=1)))
  d=datetime.date(2024,1,2); dt=datetime.datetime(2024,1,2,3,4)
  self.assertEqual(m.normalize_json(d),d.isoformat()); self.assertEqual(m.normalize_json(dt),dt.isoformat())
  self.assertEqual(m.normalize_json([b'z',Decimal('2')]),['eg==',2.0]); self.assertEqual(m.normalize_json(object()),str(object()))
 def test_url_path_composition_and_base_path(self):
  endpoint=self.endpoint(get_url=lambda p:'https://invalid.test/root'+('/' + p.lstrip('/') if p else ''))
  c=self.m.ServiceClient({'service.credential.loader':types.SimpleNamespace(get_credential=lambda c:None,load_credential=lambda c:None),'service.auth.factory':types.SimpleNamespace(create_service_auth=lambda c:types.SimpleNamespace(authenticate=lambda ctx,audience=None:ctx))},endpoint,None,path='/constructor',method='GET')
  for path in ('',None,'/child','child'):
   with mock.patch.object(self.m.requests,'request') as req:
    c.call(path=path,method='GET'); self.assertEqual(req.call_args.kwargs['url'],endpoint.get_url(path or '/constructor'))
 def test_endpoint_get_url_actual_path_cases(self):
  endpoint=object.__new__(self.endpoint_m.ServiceEndpointMixin)
  endpoint.url='https://base.example.invalid/current'; endpoint.base_url='https://base.example.invalid/root/'; endpoint.base_path='/api/v1/'
  cases=[(None,'https://base.example.invalid/current'),(False,'https://base.example.invalid/current'),('', 'https://base.example.invalid/root'),('/', 'https://base.example.invalid/root'),('/child/','https://base.example.invalid/root/child'),('child/','https://base.example.invalid/root/api/v1/child')]
  for path, expected in cases: self.assertEqual(endpoint.get_url(path),expected)
  endpoint.base_path=''
  self.assertEqual(endpoint.get_url('child'),'https://base.example.invalid/root/child')
 def test_endpoint_headers_default_and_override_actual_method(self):
  endpoint=object.__new__(self.endpoint_m.ServiceEndpointMixin); endpoint.content_type_default='application/json'
  self.assertEqual(endpoint.request_headers_default(None),{'Content-Type':'application/json','Accept':'application/json'})
  self.assertEqual(endpoint.request_headers_default({'Accept':'text/plain','X-Synthetic':'yes'}),{'Content-Type':'application/json','Accept':'text/plain','X-Synthetic':'yes'})
 def test_factory_endpoint_lookup_filters_active_and_uses_first_duplicate(self):
  factory=object.__new__(self.m.ServiceClientFactory); first=object(); second=object(); calls=[]
  class EndpointModel:
   def search(self, domain, limit=None): calls.append((domain,limit)); return first
   def browse(self, record_id): calls.append(('browse',record_id)); return first
  factory.env={'service.endpoint':EndpointModel()}
  self.assertIs(factory._get_endpoint('SYNTHETIC'),first)
  self.assertEqual(calls[0],([('code','=','SYNTHETIC'),('active','=',True)],1))
  self.assertIs(factory._get_endpoint(7),first)
  self.assertEqual(calls[1],('browse',7))
  class Missing:
   def search(self, domain, limit=None): return None
  factory.env={'service.endpoint':Missing()}
  with self.assertRaisesRegex(ValueError,'not found'): factory._get_endpoint('INACTIVE_OR_MISSING')
  self.assertIsNot(first,second)  # no uniqueness check is performed by this lookup API
 def test_request_headers_overrides_timeout_params_and_json(self):
  endpoint=self.endpoint(request_headers_default=lambda h:{'X-Base':'yes',**(h or {})},timeout=11)
  loader=types.SimpleNamespace(get_credential=lambda c:None,load_credential=lambda c:None)
  factory=types.SimpleNamespace(create_service_auth=lambda c:types.SimpleNamespace(authenticate=lambda ctx,audience=None:ctx))
  c=self.m.ServiceClient({'service.credential.loader':loader,'service.auth.factory':factory},endpoint,None)
  with mock.patch.object(self.m.requests,'request',return_value=object()) as req:
   c.call(path='/p',method='POST',params={'q':1},payload={'a':2},headers={'X-Call':'ok'})
  kw=req.call_args.kwargs; self.assertEqual(kw.get('params'),{'q':1}); self.assertIn('X-Call',kw['headers']); self.assertIn('json',kw); self.assertEqual(kw['timeout'],11)
 def test_response_passthrough_and_transport_error(self):
  endpoint=self.endpoint(); loader=types.SimpleNamespace(get_credential=lambda c:None,load_credential=lambda c:None); factory=types.SimpleNamespace(create_service_auth=lambda c:types.SimpleNamespace(authenticate=lambda ctx,audience=None:ctx))
  c=self.m.ServiceClient({'service.credential.loader':loader,'service.auth.factory':factory},endpoint,None)
  r=types.SimpleNamespace(status_code=204)
  with mock.patch.object(self.m.requests,'request',return_value=r): self.assertIs(c.call(path='/x'),r)
  for code in (200,400,500):
   r=types.SimpleNamespace(status_code=code)
   with mock.patch.object(self.m.requests,'request',return_value=r): self.assertIs(c.call(path='/x'),r)
  with mock.patch.object(self.m.requests,'request',side_effect=self.m.requests.ConnectionError('synthetic')):
   with self.assertRaises(self.m.requests.ConnectionError): c.call(path='/x')
 def test_offline_guards_block_http_dns_socket_file_and_env(self):
  import socket, urllib.request, builtins, os, http.client
  checks=[lambda:self.m.requests.post('https://example.invalid'),lambda:self.m.requests.request('GET','https://example.invalid'),lambda:socket.getaddrinfo('example.invalid',443),lambda:socket.socket(),lambda:urllib.request.urlopen('https://example.invalid'),lambda:http.client.HTTPConnection('example.invalid').connect(),lambda:builtins.open('/tmp/synthetic-credential'),lambda:os.getenv('SYNTHETIC_SECRET')]
  for call in checks:
   with self.subTest(boundary=call), self.assertRaises(AssertionError): call()
 def test_per_call_method_audience_active_log_are_not_applied(self):
  endpoint=self.endpoint(); observed_audiences=[]; loader=types.SimpleNamespace(get_credential=lambda c:None,load_credential=lambda c:None)
  auth=types.SimpleNamespace(authenticate=lambda ctx,audience=None:(observed_audiences.append(audience) or ctx))
  factory=types.SimpleNamespace(create_service_auth=lambda c:auth)
  c=self.m.ServiceClient({'service.credential.loader':loader,'service.auth.factory':factory},endpoint,None,method='GET')
  with mock.patch.object(self.m.requests,'request',return_value=object()) as req: c.call(path='/x',method='PATCH',audience='call-aud',active_log=True)
  self.assertEqual(req.call_args.kwargs['method'],'PATCH')
  self.assertEqual(observed_audiences,['constructor-aud'])  # per-call audience is not forwarded
  self.assertNotIn('audience',req.call_args.kwargs)  # auth boundary stays in headers, not requests kwargs
