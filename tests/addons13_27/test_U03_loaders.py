from support import *
import json, unittest.mock as mock
class Loaders(OfflineCase):
 @classmethod
 def setUpClass(cls): cls.m=load('services/credential_loader.py')
 def test_database_scope_merge_and_dedup(self):
  obj=object.__new__(self.m.ServiceCredentialLoaderDatabase); c=types.SimpleNamespace(credential_json='{"type":"bearer","scope":"a b"}',scopes='b c'); d=obj.load_credential(c); self.assertEqual(set(d['scope']),{'a','b','c'})
 def test_database_scope_is_whitespace_not_comma_parser(self):
  obj=object.__new__(self.m.ServiceCredentialLoaderDatabase); c=types.SimpleNamespace(credential_json='{"type":"bearer","scope":"read,write"}',scopes='team,member')
  self.assertEqual(set(obj.load_credential(c)['scope']),{'read,write','team,member'})
 def test_name_lookup_hit_and_xmlid_fallback_bug_characterization(self):
  obj=object.__new__(self.m.ServiceCredentialLoader); name_record=types.SimpleNamespace(id=17); ref_calls=[]
  class Env:
   def __getitem__(self, key):
    self.asserted=key
    def search(domain, limit=None):
     if domain==[("name","=","synthetic-name")] and limit==1: return name_record
     return None
    return types.SimpleNamespace(search=search)
   def ref(self, value): ref_calls.append(value); return None
  obj.env=Env()
  self.assertIs(obj.get_credential('synthetic-name'),name_record)
  with self.assertRaisesRegex(ValueError, r"Credential 'None' not found"):
   obj.get_credential('module.synthetic_xmlid')
  self.assertEqual(ref_calls,[None])  # UAT records this lookup defect; do not promise/fix it here
 def test_each_json_or_path_loader_returns_decoded_data(self):
  m=self.m; expected={'type':'basic','username':'synthetic'}
  for clsname,attrs in [('ServiceCredentialLoaderFilePath',{}),('ServiceCredentialLoaderEnvPath',{'os.getenv': 'synthetic-path'}),('ServiceCredentialLoaderConfigPath',{'config.get':'synthetic-path'}),('ServiceCredentialLoaderParameterPath',{})]:
   obj=object.__new__(getattr(m,clsname)); obj.env={'ir.config_parameter':types.SimpleNamespace(sudo=lambda:types.SimpleNamespace(get_param=lambda k:'synthetic-path'))}
   c=types.SimpleNamespace(reference='SYNTHETIC_REF')
   with mock.patch.object(m,'open',mock.mock_open(read_data=json.dumps(expected)),create=True):
    patches=[]
    if 'os.getenv' in attrs: patches.append(mock.patch.object(m.os,'getenv',return_value=attrs['os.getenv']))
    if 'config.get' in attrs: patches.append(mock.patch.object(m.config,'get',return_value=attrs['config.get']))
    for p in patches: p.start()
    try: self.assertEqual(obj.load_credential(c),expected,clsname)
    finally:
     for p in patches: p.stop()
 def test_env_json_decodes_synthetic_value(self):
  obj=object.__new__(self.m.ServiceCredentialLoaderEnvJson)
  with mock.patch.object(self.m.os,'getenv',return_value='{"type":"api_key"}'):
   self.assertEqual(obj.load_credential(types.SimpleNamespace(reference='SYNTHETIC')),{"type":"api_key"})
 def test_system_parameter_json_and_path_loaders(self):
  expected={'type':'bearer'}; obj=object.__new__(self.m.ServiceCredentialLoaderParameterJson); obj.env={'ir.config_parameter':types.SimpleNamespace(sudo=lambda:types.SimpleNamespace(get_param=lambda k:json.dumps(expected)))}
  self.assertEqual(obj.load_credential(types.SimpleNamespace(reference='SYNTHETIC')),expected)
  obj=object.__new__(self.m.ServiceCredentialLoaderParameterPath); obj.env={'ir.config_parameter':types.SimpleNamespace(sudo=lambda:types.SimpleNamespace(get_param=lambda k:'synthetic-path'))}
  with mock.patch.object(self.m,'open',mock.mock_open(read_data=json.dumps(expected)),create=True): self.assertEqual(obj.load_credential(types.SimpleNamespace(reference='SYNTHETIC')),expected)
 def test_missing_references_and_malformed_json_are_rejected(self):
  m=self.m; c=types.SimpleNamespace(reference='SYNTHETIC')
  for cls in [m.ServiceCredentialLoaderEnvJson,m.ServiceCredentialLoaderEnvPath]:
   with mock.patch.object(m.os,'getenv',return_value=None),self.assertRaises(ValueError): object.__new__(cls).load_credential(c)
  obj=object.__new__(m.ServiceCredentialLoaderConfigPath)
  with mock.patch.object(m.config,'get',return_value=None),self.assertRaises(ValueError): obj.load_credential(c)
  obj=object.__new__(m.ServiceCredentialLoaderParameterJson); obj.env={'ir.config_parameter':types.SimpleNamespace(sudo=lambda:types.SimpleNamespace(get_param=lambda k:None))}
  with self.assertRaises(ValueError): obj.load_credential(c)
  obj=object.__new__(m.ServiceCredentialLoaderParameterPath); obj.env={'ir.config_parameter':types.SimpleNamespace(sudo=lambda:types.SimpleNamespace(get_param=lambda k:None))}
  with self.assertRaises(ValueError): obj.load_credential(c)
  obj=object.__new__(m.ServiceCredentialLoaderEnvJson)
  with mock.patch.object(m.os,'getenv',return_value='{bad'),self.assertRaises(json.JSONDecodeError): obj.load_credential(c)
  obj=object.__new__(m.ServiceCredentialLoaderDatabase)
  with self.assertRaises(json.JSONDecodeError): obj.load_credential(types.SimpleNamespace(credential_json='{bad',scopes=''))
 def test_file_json_malformed_and_database_validation_cases(self):
  obj=object.__new__(self.m.ServiceCredentialLoaderFilePath)
  with mock.patch.object(self.m,'open',mock.mock_open(read_data='{bad'),create=True),self.assertRaises(json.JSONDecodeError): obj.load_credential(types.SimpleNamespace(reference='synthetic-path'))
  obj=object.__new__(self.m.ServiceCredentialLoader)
  for data in ({},{'type':'not-supported'}):
   with self.assertRaises(ValueError): obj._validate(data)
  for kind in self.m.supported: obj._validate({'type':kind})
  with self.assertRaises(ValueError): obj._validate({'type':'none'})
