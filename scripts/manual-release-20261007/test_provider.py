import unittest
from provider_check import paginate,settings,inventory
class ProviderTests(unittest.TestCase):
 def test_missing_bindings_rejected(self):
  with self.assertRaises(ValueError):settings({'compatibility_date':'2026-09-29'})
 def test_secret_binding_rejected_without_value(self):
  with self.assertRaises(ValueError) as got:settings({'bindings':[{'type':'plain_text','text':'DO_NOT_LOG'}]})
  self.assertNotIn('DO_NOT_LOG',str(got.exception))
 def test_disabled_observability_equivalence(self):
  a={'bindings':[],'compatibility_date':'2026-09-29'}
  self.assertEqual(settings(a),settings(dict(a,observability={'enabled':False})))
  self.assertNotEqual(settings(a),settings(dict(a,observability={'enabled':True})))
 def test_unknown_setting_rejected(self):
  with self.assertRaises(ValueError):settings({'bindings':[],'compatibility_date':'2026-09-29','unknown':True})
 def test_paginated(self):
  responses=iter([{'result':[1],'result_info':{'total_pages':2,'total_count':2}},{'result':[2],'result_info':{'total_pages':2,'total_count':2}}])
  self.assertEqual(paginate(lambda url:next(responses),'/test'),[1,2])
 def test_truncated_rejected(self):
  with self.assertRaises(ValueError):paginate(lambda url:{'result':[1],'result_info':{'total_pages':1,'total_count':2}},'/test')
 def test_malformed_rejected(self):
  with self.assertRaises(ValueError):paginate(lambda url:{'result':{}},'/test')
 def test_full_inventory(self):
  account='a'*32;zone='b'*32;p={'worker':'existing','productionOrigin':'https://s.fwith.kr'}
  def get(path):
   if path.endswith('/settings'):return {'result':{'bindings':[],'compatibility_date':'2026-09-29','compatibility_flags':[]}}
   if path.endswith('/subdomain'):return {'result':{'enabled':False,'previews_enabled':False}}
   if '/workers/domains' in path:return {'result':[{'id':'domain-id','hostname':'s.fwith.kr','service':'existing','zone_id':zone,'environment':'production'}]}
   if '/workers/routes' in path:raise AssertionError('Denied route endpoint must never be requested')
   if path.startswith('/zones?'):raise AssertionError('Unrelated account zones must not be enumerated')
   raise AssertionError(path)
  state=inventory(get,account,p,'production');self.assertEqual(state['legacyRoutes']['state'],'not_read_not_modified');self.assertFalse(state['workersDev']['enabled'])
if __name__=='__main__':unittest.main()
