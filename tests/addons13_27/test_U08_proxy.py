from support import *
class Proxy(OfflineCase):
 @classmethod
 def setUpClass(cls): cls.m=load('models/service_client.py')
 def test_jsonrpc_envelope_path_args_kwargs_context_and_method(self):
  seen=[]
  class R:
   def raise_for_status(self): pass
   def json(self): return {'result':[1]}
  p=self.m.RemoteObjectProxy(types.SimpleNamespace(post=lambda **kw:(seen.append(kw) or R())),'synthetic.model',context={'lang':'en'})
  self.assertEqual(p.call('read',[4],{'limit':3,'context':{'tz':'UTC'}}),[1]); kw=seen[0]; self.assertEqual(kw['path'],'/api/dataset/call_kw')
  body=kw['payload']; self.assertEqual((body['jsonrpc'],body['method'],body['id']),('2.0','call',1)); self.assertEqual(body['params'],{'model':'synthetic.model','method':'read','args':[4],'kwargs':{'limit':3,'context':{'lang':'en','tz':'UTC'}}})
 def test_result_list_zero_false_none_and_error(self):
  for result,expected in (([3],[3]),(0,[]),(False,[]),(None,[])):
   p=self.m.RemoteObjectProxy(types.SimpleNamespace(post=lambda **kw:types.SimpleNamespace(raise_for_status=lambda:None,json=lambda:{'result':result})),'m'); self.assertEqual(p.call('x',[],{}),expected)
  p=self.m.RemoteObjectProxy(types.SimpleNamespace(post=lambda **kw:types.SimpleNamespace(raise_for_status=lambda:None,json=lambda:{'error':{'message':'x'}})),'m')
  with self.assertRaises(RuntimeError): p.call('x',[],{})
 def test_offset_zero_fallback(self):
  p=self.m.RemoteObjectProxy(None,'m',offset=7); captured=[]; p.call=lambda method,args,kwargs=None:(captured.append(kwargs) or [])
  p.search_read(offset=0); self.assertEqual(captured[0]['offset'],7)
 def test_two_pages_then_empty_pagination(self):
  p=self.m.RemoteObjectProxy(None,'m',limit=2); calls=[]; received=[]
  pages=[[{'id':1},{'id':2}],[{'id':3},{'id':4}],[]]
  def read(**kw): calls.append(kw); return pages[len(calls)-1]
  p.search_count=lambda:5; p.search_read=read
  p.external_data_callback(lambda item,**meta:received.append((item,meta)))
  self.assertEqual(len(calls),3); self.assertEqual([x[0]['id'] for x in received],[1,2,3,4])
  self.assertEqual([x['offset'] for _,x in received],[1,2,3,4])
 def test_callback_exception_propagates(self):
  p=self.m.RemoteObjectProxy(None,'m'); p.search_count=lambda:1; p.search_read=lambda **kw:[{'id':1}]
  with self.assertRaises(RuntimeError): p.external_data_callback(lambda *a,**k:(_ for _ in ()).throw(RuntimeError('synthetic')))
