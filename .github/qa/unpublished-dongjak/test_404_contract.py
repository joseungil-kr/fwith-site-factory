"""Exact observed 404 replay and negative regressions; no browser/network/DOM edits."""
import copy,unittest
from unittest.mock import patch
import adapter,run_bound_capture
from test_adapter import SOURCE

class NotFoundContractTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.expected=adapter.expectations(SOURCE/adapter.SITE_PATH)
  # Replay the immutable historical capture under its own exact revision;
  # fresh runner captures separately enforce the successor revision.
  cls.spec={**adapter.load(adapter.HERE/'bound-spec.json'),'sourceSha':adapter.HISTORICAL_SOURCE_SHA}
  cls.observed=adapter.load(adapter.HERE/'frozen-inputs/observed-404-facts.run38341440858.json')
 def facts(self,width=320):return copy.deepcopy(next(x['facts']for x in self.observed['observedRows']if x['width']==width))
 def check(self,facts,route='/404.html',width=320):run_bound_capture.assert_bound_facts(facts,self.spec,route,[],width,self.expected)
 def mutate(self,fn):
  facts=self.facts();fn(facts)
  with self.assertRaises(AssertionError):self.check(facts)
 def test_original_failure_is_reproducible_all_widths(self):
  for w in (320,390,1280):
   with self.subTest(width=w),self.assertRaisesRegex(AssertionError,'CTA order href'):run_bound_capture.ORIGINAL_ASSERT_FACTS(self.facts(w),self.spec,'/404.html',[],w)
 def test_actual_source_contract_passes_without_fact_mutation(self):
  for w in (320,390,1280):
   facts=self.facts(w);before=copy.deepcopy(facts);self.check(facts,width=w);self.assertEqual(facts,before)
 def test_non404_missing_store_still_fails(self):
  for route in ('/','/regions/','/regions/dongjak-funeral-wreath/'):
   f=self.facts();f['canonical']=adapter.SITE_URL+route
   with self.subTest(route=route),self.assertRaisesRegex(AssertionError,'CTA order href'):self.check(f,route=route)
 def test_missing_phone_rejected(self):self.mutate(lambda f:f.update(anchors=[x for x in f['anchors']if not x['href'].startswith('tel:')]))
 def test_wrong_phone_rejected(self):self.mutate(lambda f:f['anchors'][5].update(href='tel:123'))
 def test_missing_guide_rejected(self):self.mutate(lambda f:f['anchors'].pop(6))
 def test_missing_home_rejected(self):self.mutate(lambda f:f['anchors'].pop(8))
 def test_missing_directory_rejected(self):self.mutate(lambda f:f['anchors'].pop(-1))
 def test_wrong_link_text_rejected(self):self.mutate(lambda f:f['anchors'][6].update(text='임의 문구'))
 def test_wrong_h1_rejected(self):self.mutate(lambda f:f.update(h1=['다른 안내']))
 def test_external_or_unexpected_store_link_rejected(self):
  for href in ['https://evil.invalid/','https://fwith.co.kr/','https://fwith.co.kr.evil.invalid/']:
   with self.subTest(href=href):self.mutate(lambda f:f['anchors'].append({'href':href,'text':'추가'}))
 def test_bad_host_on_customer_route_still_fails(self):
  f=self.facts();f['canonical']=adapter.SITE_URL+'/';f['anchors'].append({'href':'https://fwith.co.kr.evil.invalid/','text':'주문'})
  with self.assertRaisesRegex(AssertionError,'CTA order href'):self.check(f,route='/')
 def test_fonts_after_order_assertion_remain_required(self):self.mutate(lambda f:f.update(fontStatus='loading'))
 def test_horizontal_overflow_still_fails(self):self.mutate(lambda f:f.update(scrollWidth=330))
 def test_wrong_revision_still_fails(self):self.mutate(lambda f:f.update(revision='wrong'))
 def test_404_indexable_canonical_banner_mutations_fail(self):
  for key,value in [('robots','index,follow'),('canonical',adapter.SITE_URL+'/404.html'),('banners',1),('images',[{'src':'fake'}])]:
   with self.subTest(key=key):self.mutate(lambda f:f.update({key:value}))
 def test_other_assertion_is_never_suppressed(self):
  for error in [AssertionError('Fonts incomplete'),AssertionError('CTA phone href'),AssertionError('CTA order href','extra')]:
   with patch.object(run_bound_capture,'ORIGINAL_ASSERT_FACTS',side_effect=error),self.assertRaises(AssertionError):self.check(self.facts())
 def test_nonassertion_is_never_suppressed(self):
  with patch.object(run_bound_capture,'ORIGINAL_ASSERT_FACTS',side_effect=RuntimeError('unexpected')),self.assertRaises(RuntimeError):self.check(self.facts())
 def test_fixture_is_exact_failed_original_run(self):
  self.assertEqual(self.observed['sourceSha'],adapter.HISTORICAL_SOURCE_SHA);self.assertEqual(self.observed['runId'],'38341440858')
  self.assertTrue(all(r['issues']for r in self.observed['observedRows']))

if __name__=='__main__':unittest.main()
