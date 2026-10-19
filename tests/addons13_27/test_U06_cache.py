from support import *
from datetime import datetime, timedelta
from unittest import mock
class Cache(OfflineCase):
 @classmethod
 def setUpClass(cls): cls.m=load('services/token_cache.py'); cls.providers=load('services/providers.py')
 def setUp(self): super().setUp(); self.m.TOKEN_CACHE.clear(); self.obj=object.__new__(self.m.ServiceTokenCache)
 def test_fresh_and_missing_cache(self):
  now=datetime(2030,1,1)
  with mock.patch.object(self.m,'datetime') as dt:
   dt.now.return_value=now; self.obj.set_cache('k','synthetic',60); self.assertEqual(self.obj.get_cache('k'),'synthetic'); self.assertIsNone(self.obj.get_cache('missing'))
 def test_expired_entry_removed_at_fixed_clock(self):
  now=datetime(2030,1,1)
  with mock.patch.object(self.m,'datetime') as dt:
   dt.now.side_effect=[now,now+timedelta(seconds=60)]; self.obj.set_cache('k','synthetic',60); self.assertIsNone(self.obj.get_cache('k')); self.assertNotIn('k',self.m.TOKEN_CACHE)
 def test_database_scope_and_rotation_collisions_are_characterized(self):
  provider=self.providers.ServiceAccountProvider
  a=provider({'db':'db-a'},{'client_id':'same','token_uri':'https://one.invalid','scope':'read','private_key_id':'k1'})
  b=provider({'db':'db-b'},{'client_id':'same','token_uri':'https://two.invalid','scope':'write','private_key_id':'k2'})
  self.assertEqual(a._get_cache_key(),b._get_cache_key())
 def test_token_uri_collision_for_service_account(self):
  provider=self.providers.ServiceAccountProvider
  a=provider(None,{'client_id':'same','token_uri':'https://one.invalid'}); b=provider(None,{'client_id':'same','token_uri':'https://two.invalid'})
  self.assertEqual(a._get_cache_key(),b._get_cache_key())
 def test_client_secret_token_uri_does_not_collide(self):
  cls=self.providers.ClientSecretProvider
  a=cls(None,{'client_id':'same','token_uri':'https://one.invalid'}); b=cls(None,{'client_id':'same','token_uri':'https://two.invalid'})
  self.assertNotEqual(a._get_cache_key(),b._get_cache_key())
 def test_service_account_short_ttl_roundtrip(self):
  now=datetime(2030,1,1)
  with mock.patch.object(self.m,'datetime') as dt:
   dt.now.return_value=now; self.obj.set_cache('short','synthetic',5); self.assertEqual(self.obj.get_cache('short'),'synthetic'); dt.now.return_value=now+timedelta(seconds=5); self.assertIsNone(self.obj.get_cache('short'))
 def test_provider_identity_key_omits_database_scope_and_rotation(self):
  cls=self.providers.ServiceAccountProvider
  a=cls(None,{'client_id':'same','token_uri':'one'}); b=cls(None,{'client_id':'same','token_uri':'two'}); self.assertEqual(a._get_cache_key(),b._get_cache_key())
 def test_module_global_cache_and_clock_are_used(self):
  self.assertIsInstance(self.m.TOKEN_CACHE,dict); self.assertIn('datetime',self.m.ServiceTokenCache.get_cache.__code__.co_names); self.assertIn('now',self.m.ServiceTokenCache.get_cache.__code__.co_names)
