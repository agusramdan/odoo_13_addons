from support import *
from unittest import mock
import requests

class Tokens(OfflineCase):
 @classmethod
 def setUpClass(cls): cls.p=load('services/providers.py')
 def _response(self, data=None, error=None, text='synthetic-error-body'):
  r=mock.Mock(); r.raise_for_status.side_effect=error; r.json.side_effect=error or [data]; r.text=text; return r
 def test_client_secret_schema_defaults_and_short_ttl(self):
  response=self._response({'access_token':'synthetic-token','expires_in':10,'token_type':'Other'})
  p=self.p.ClientSecretProvider(None,{'client_id':'id','client_secret':'synthetic-secret','token_uri':'https://issuer.invalid/token','scope':['a','b']})
  with mock.patch.object(self.p.requests,'post',return_value=response) as post: result=p._request_token('aud')
  self.assertEqual(result,{'access_token':'synthetic-token','token_type':'Other','expires_in':10,'cache_ttl':60,'raw_response':{'access_token':'synthetic-token','expires_in':10,'token_type':'Other'}})
  self.assertEqual(post.call_args.kwargs['timeout'],(10,30)); self.assertEqual(post.call_args.kwargs['data'],{'grant_type':'client_credentials','client_id':'id','client_secret':'synthetic-secret','audience':'aud','scope':'a b'})
 def test_client_secret_default_ttl_bearer_and_scope_string(self):
  p=self.p.ClientSecretProvider(None,{'client_id':'id','token_uri':'https://issuer.invalid/token','scope':'read write'})
  with mock.patch.object(self.p.requests,'post',return_value=self._response({'access_token':'synthetic-token'})) as post: result=p._request_token()
  self.assertEqual((result['token_type'],result['expires_in'],result['cache_ttl']),('Bearer',3600,3540)); self.assertEqual(post.call_args.kwargs['data']['scope'],'read write')
  self.assertEqual(result['token_type'],'Bearer')
 def test_client_secret_custom_timeouts_and_token_uri_in_key(self):
  p=self.p.ClientSecretProvider(None,{'client_id':'id','token_uri':'https://issuer.invalid/a','connect_timeout':2,'read_timeout':7})
  with mock.patch.object(self.p.requests,'post',return_value=self._response({'access_token':'t'})) as post: p._request_token()
  self.assertEqual(post.call_args.kwargs['timeout'],(2,7)); q=self.p.ClientSecretProvider(None,{'client_id':'id','token_uri':'https://issuer.invalid/b'}); self.assertNotEqual(p._get_cache_key(),q._get_cache_key())
 def test_service_account_grant_scope_token_and_signing_claims(self):
  p=self.p.ServiceAccountProvider(None,{'client_id':'id','token_uri':'https://issuer.invalid/token','private_key':'synthetic-key','private_key_id':'key-1','scope':['x','y']})
  response=self._response({'access_token':'synthetic-token','expires_in':300,'token_type':'MAC'})
  with mock.patch.object(self.p.time,'time',return_value=100),mock.patch.object(self.p.uuid,'uuid4',return_value='uuid'),mock.patch.object(self.p.jwt,'encode',return_value='assertion') as enc,mock.patch.object(self.p.requests,'post',return_value=response) as post:
   result=p._request_token('resource-x')
  claims=enc.call_args.args[0]; self.assertEqual((claims['iss'],claims['sub'],claims['aud'],claims['iat'],claims['exp'],claims['jti'],claims['resource'],claims['scope']),('id','id','https://issuer.invalid/token',100,400,'uuid','resource-x','x y'))
  self.assertEqual(enc.call_args.args[1],'synthetic-key'); self.assertEqual(enc.call_args.kwargs['algorithm'],'RS256'); self.assertEqual(enc.call_args.kwargs['headers']['kid'],'key-1')
  self.assertEqual(post.call_args.kwargs['data'],{'grant_type':'urn:ietf:params:oauth:grant-type:jwt-bearer','assertion':'assertion','audience':'resource-x','scope':'x y'}); self.assertEqual(post.call_args.kwargs['timeout'],(10,30)); self.assertEqual(result['cache_ttl'],240)
 def test_service_account_algorithm_whitelist_and_kid_fallback(self):
  p=self.p.ServiceAccountProvider(None,{'client_id':'id','token_uri':'https://issuer.invalid/token','private_key':'synthetic-key','kid':'fallback','algorithm':'ES256'})
  with mock.patch.object(self.p.jwt,'encode',return_value='assertion') as enc: p._create_jwt_assertion()
  self.assertEqual(enc.call_args.kwargs['algorithm'],'ES256'); self.assertEqual(enc.call_args.kwargs['headers']['kid'],'fallback')
  p.credential['algorithm']='HS256'
  with mock.patch.object(self.p.jwt,'encode') as enc,self.assertRaisesRegex(ValueError,'Unsupported algorithm'): p._create_jwt_assertion()
  enc.assert_not_called()
 def test_service_account_client_server_kid_gap(self):
  p=self.p.ServiceAccountProvider(None,{'client_id':'id','token_uri':'https://issuer.invalid/token','private_key':'synthetic-key','kid':'client-key'})
  with mock.patch.object(self.p.jwt,'encode',return_value='assertion') as enc: p._create_jwt_assertion()
  self.assertEqual(enc.call_args.kwargs['headers']['kid'],'client-key'); self.assertNotIn('kid',{'access_token':'synthetic-token'})
 def test_missing_token_timeout_connection_and_invalid_json(self):
  p=self.p.ClientSecretProvider(None,{'client_id':'id','token_uri':'https://issuer.invalid/token'})
  with mock.patch.object(self.p.requests,'post',return_value=self._response({'token_type':'Bearer'})),self.assertRaisesRegex(ValueError,'access_token not found'): p._request_token()
  for exc, message in [(requests.Timeout('synthetic timeout'),'OIDC token endpoint timeout'),(requests.ConnectionError('synthetic connection'),'Unable to connect to token endpoint')]:
   with mock.patch.object(self.p.requests,'post',side_effect=exc),self.assertRaisesRegex(ValueError,message): p._request_token()
  bad=self._response(); bad.json.side_effect=ValueError('synthetic parser detail')
  with mock.patch.object(self.p.requests,'post',return_value=bad),self.assertRaisesRegex(ValueError,'Invalid token response') as caught: p._request_token()
  self.assertNotIn('synthetic parser detail',str(caught.exception))
 def test_non_2xx_error_body_is_not_sanitized_characterization(self):
  response=self._response(error=requests.HTTPError('synthetic detail'),text='synthetic-error-body')
  with mock.patch.object(self.p.requests,'post',return_value=response),self.assertRaises(ValueError) as caught: self.p.ClientSecretProvider(None,{'client_id':'id','token_uri':'https://issuer.invalid/token'})._request_token()
  self.assertIn('synthetic-error-body',str(caught.exception))
 def test_get_jwt_ttl_missing_is_characterized_as_unresolved(self):
  self.assertIn('cache_ttl',self.p.GetJWTTokenProvider._get_token.__code__.co_consts)
  self.assertNotIn('cache_ttl',self.p.GetJWTTokenProvider._request_token.__code__.co_consts)
 def test_unsigned_token_decode_is_not_signature_validation(self):
  token='synthetic.jwt.token'
  with mock.patch.object(self.p.time,'time',return_value=100),mock.patch.object(self.p.jwt,'decode',return_value={'exp':200}) as decode: self.assertFalse(self.p.AuthenticationProvider(None,{}).is_token_expired(token))
  self.assertEqual(decode.call_args.kwargs['options'],{'verify_signature':False,'verify_exp':False})
