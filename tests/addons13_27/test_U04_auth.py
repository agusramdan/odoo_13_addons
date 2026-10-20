from support import *
import base64
class Auth(OfflineCase):
 @classmethod
 def setUpClass(cls): cls.p=load('services/providers.py'); cls.f=load('services/auth_factory.py'); cls.l=load('services/credential_loader.py')
 def test_api_key_bearer_basic_headers(self):
  c={}; self.p.ApiKeyProvider(None,{'header':'X-Synthetic','value':'v'}).authenticate(c); self.assertEqual(c['headers']['X-Synthetic'],'v')
  c={}; self.p.BearerProvider(None,{'token':'v'}).authenticate(c); self.assertEqual(c['headers']['Authorization'],'Bearer v')
  c={}; self.p.BasicProvider(None,{'username':'u','password':'p'}).authenticate(c); self.assertEqual(c['headers']['Authorization'],'Basic '+base64.b64encode(b'u:p').decode())
 def test_factory_dispatches_provider_types_and_none(self):
  f=object.__new__(self.f.ServiceAuthFactory); f.env=None
  cases={'api_key':self.p.ApiKeyProvider,'bearer':self.p.BearerProvider,'basic':self.p.BasicProvider,'none':self.p.NoneAuthProvider}
  for kind,provider in cases.items(): self.assertIsInstance(f.create_service_auth({'type':kind}),provider)
 def test_loader_and_wizard_type_mismatch(self):
  for kind in self.l.supported: self.l.ServiceCredentialLoader._validate(object.__new__(self.l.ServiceCredentialLoader),{'type':kind})
  with self.assertRaises(ValueError): object.__new__(self.l.ServiceCredentialLoader)._validate({'type':'get_jwt'})
  self.assertIn('get_jwt',self.f.ServiceAuthFactory.PROVIDERS)
 def test_wizard_and_loader_each_expose_only_five_auth_types(self):
  import ast
  tree=ast.parse((ADDON/'wizards/service_credential.py').read_text())
  wizard=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='ServiceCredentialWizard')
  assignment=next(n for n in wizard.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='credential_type' for t in n.targets))
  wizard_types={item[0] for item in ast.literal_eval(assignment.value.args[0])}
  self.assertEqual(wizard_types,set(self.l.supported))
  self.assertNotIn('none',wizard_types); self.assertNotIn('get_jwt',wizard_types)
 def test_get_jwt_cache_ttl_contract_mismatch_is_characterized(self):
  cache=types.SimpleNamespace(get_cache=lambda key:None, set_cache=lambda *args:None)
  provider=self.p.GetJWTTokenProvider({'service.token.cache':cache},{'username':'synthetic-user','token_uri':'https://issuer.example.invalid/token'})
  provider._request_token=lambda audience=None:{'access_token':'synthetic-token'}
  with self.assertRaisesRegex(KeyError,'cache_ttl'):
   provider._get_token()
 def test_base_test_credential_raises_user_error(self):
  with self.assertRaises(UserError): self.p.AuthenticationProvider(None,{}).test_credential()
