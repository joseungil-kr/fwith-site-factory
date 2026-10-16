"""Offline regressions for the new two-page, one-indexable-home contract."""
import copy,json,unittest
from pathlib import Path
from unittest.mock import patch
import production_build as b
import production_output as o
import publish as p
import test_publish as publisher_tests
from test_publish import working
import test_production_build as build_tests
from test_production_build import temporary_control_directory

class NativeReviewTests(unittest.TestCase):
 def test_native_review_verdict_null_scores_and_denominators_unchanged(self):
  bound=b.verify_content_reviews();docs={r['path'].split('content-review-r2-20261016/',1)[1]:r for r in bound['files']}
  ms=json.loads((b.DIRECTORY.parents[1]/docs['independent-review-r2.json']['path']).read_bytes())
  self.assertEqual(ms['verdict'],'MANUSCRIPT_AND_SPEC_READY_FOR_IMPLEMENTATION_NOT_PRODUCTION_PASS')
  self.assertEqual(ms['originalDenominators'],dict(guidance=165,policy=24,currentFacts=16,facilities=3))
  self.assertEqual(ms['plannedStructure']['authoredStrings'],100);self.assertEqual(ms['plannedStructure']['FAQObjects'],4)
  for key in ['sourceCommit','originalAuthorScores','originalIndependentScores','independentNumericScores']:self.assertIsNone(ms[key])
  for key in ['actualHTMLChecked','actualBuildChecked','actualBrowserChecked','actualPublicHTTPChecked','publicationEligible']:self.assertIs(ms[key],False)
 def test_rehashed_outer_review_envelope_cannot_change_native_review(self):
  for field,value in [('verdict','PASS'),('independentNumericScores',99),('sourceCommit','a'*40),('actualHTMLChecked',True),('publicationEligible',True),('originalDenominators',dict(guidance=159,policy=24,currentFacts=16,facilities=2)),('plannedStructure',{'plannedHTMLCount':4})]:
   with self.subTest(field=field),temporary_control_directory() as d,patch.object(b,'DIRECTORY',d):
    build_tests.ProductionTests().fixture(d);path=d.parents[1]/'docs/direct-damyang/content-review-r2-20261016/independent-review-r2.json';ms=json.loads(path.read_bytes());ms[field]=value;b.save(path,ms)
    envelope=json.loads((d/'content-review-binding.json').read_bytes());row=next(r for r in envelope['files'] if r['path'].endswith('/independent-review-r2.json'));row.update(bytes=path.stat().st_size,sha256=b.sha(path.read_bytes()));b.save(d/'content-review-binding.json',envelope)
    with patch.object(b,'CONTENT_REVIEW_BINDING_SHA',b.sha((d/'content-review-binding.json').read_bytes())),self.assertRaisesRegex(ValueError,'original_review_pin_changed'):b.verify_content_reviews()

 def test_rehashed_code_review_cannot_claim_remote_or_public_success(self):
  cases=[('disposition','PASS_PRODUCTION'),('publicationEligible',True),('actualBrowserVerified',True),('actualPublicHTTPVerified',True),('providerOwnershipVerified',True),('IndexNowSubmitted',True),('blockingSourceFindings',['must fix']),('sourceBinding',{'sourceRevision':'a'*40})]
  for field,value in cases:
   with self.subTest(field=field),temporary_control_directory() as d,patch.object(b,'DIRECTORY',d):
    build_tests.ProductionTests().fixture(d);path=d.parents[1]/'docs/direct-damyang/content-review-r2-20261016/code-review/code-review.json';review=json.loads(path.read_bytes());review[field]=value;b.save(path,review)
    envelope=json.loads((d/'content-review-binding.json').read_bytes());row=next(r for r in envelope['files'] if r['path'].endswith('/code-review/code-review.json'));row.update(bytes=path.stat().st_size,sha256=b.sha(path.read_bytes()));b.save(d/'content-review-binding.json',envelope)
    with patch.object(b,'CONTENT_REVIEW_BINDING_SHA',b.sha((d/'content-review-binding.json').read_bytes())),self.assertRaisesRegex(ValueError,'original_review_pin_changed'):b.verify_content_reviews()

class NativeR2ReviewTests(unittest.TestCase):
 def test_r2_native_supersession_and_historical_nulls_preserved(self):
  bound=b.verify_content_reviews();root=b.DIRECTORY.parents[1]/'docs/direct-damyang/content-review-r2-20261016'
  report=json.loads((root/'independent-review-r2.json').read_bytes());prior=json.loads((root/'prior/r1/independent-review-r1.json').read_bytes());context=json.loads((root/'inputs/author/supplemental-policy-context.json').read_bytes())
  self.assertEqual(report['revision'],'damyang-copy-r2-20261016');self.assertEqual(report['supplementalDenominators'],dict(upperImagePolicyClauses=6,applicationScopeFollowupFacts=1))
  self.assertFalse(report['supersession']['r1NoRequiredTimingRevisionRemainsCurrent']);self.assertEqual(prior['revision'],'damyang-copy-r1-20261016');self.assertIsNone(prior['sourceCommit']);self.assertFalse(prior['publicationEligible'])
  self.assertEqual(context['originalDenominators'],dict(guidance=165,policy=24,currentFacts=16,facilities=3));self.assertEqual(len(context['upperPolicyBySKU']),3);self.assertEqual(len(context['applicationScopeFollowupFacts']),1)
 def test_rehashed_native_r2_or_historical_bytes_cannot_change_scope(self):
  changes=[('independent-review-r2.json','supplementalDenominators',dict(upperImagePolicyClauses=6,applicationScopeFollowupFacts=0)),('independent-review-r2.json','supersession',dict(r1NoRequiredTimingRevisionRemainsCurrent=True)),('inputs/author/supplemental-policy-context.json','independentScores',99),('inputs/author/supplemental-policy-context.json','actualRenderingVerified',True),('supplemental-policy-assessment.json','supplementalUpperPolicyClauses',[]),('timing-scope-addendum.json','originalPackagesPreserved',False),('timing-scope-addendum.json','verdict',dict(relationship='PROVEN_POLICY_CONTRADICTION')),('prior/r1/independent-review-r1.json','sourceCommit','a'*40),('inputs/author/version-diff.json','changedCustomerLeafCount',0),('inputs/author/visible-strings.json','count',99)]
  for name,field,value in changes:
   with self.subTest(name=name,field=field),temporary_control_directory() as d,patch.object(b,'DIRECTORY',d):
    build_tests.ProductionTests().fixture(d);path=d.parents[1]/'docs/direct-damyang/content-review-r2-20261016'/name;doc=json.loads(path.read_bytes());doc[field]=value;b.save(path,doc)
    envelope=json.loads((d/'content-review-binding.json').read_bytes());row=next(r for r in envelope['files'] if r['path']=='docs/direct-damyang/content-review-r2-20261016/'+name);row.update(bytes=path.stat().st_size,sha256=b.sha(path.read_bytes()));b.save(d/'content-review-binding.json',envelope)
    with patch.object(b,'CONTENT_REVIEW_BINDING_SHA',b.sha((d/'content-review-binding.json').read_bytes())),self.assertRaisesRegex(ValueError,'original_review_pin_changed'):b.verify_content_reviews()

class NativeDeltaAttributionTests(unittest.TestCase):
 def test_rehashed_delta_cannot_upgrade_source_or_original_reviewer(self):
  changes=[('source-delta-review.json','publicationEligible',True),('source-delta-review.json','actualBrowserVerified',True),('source-delta-review.json','actualPublicHTTPVerified',True),('source-delta-review.json','blockingSourceFindings',['must fix']),('source-delta-review.json','sourceBinding',{'sourceRevision':'a'*40}),('source-delta-binding.json','originalCodeReview',{'originalReviewerReranR2':True}),('source-delta-binding.json','remoteCommitMustBeBoundSeparately',False),('reproduction.json','actualRemoteRunnerExecuted',True)]
  for name,field,value in changes:
   with self.subTest(name=name,field=field),temporary_control_directory() as d,patch.object(b,'DIRECTORY',d):
    build_tests.ProductionTests().fixture(d);path=d.parents[1]/'docs/direct-damyang/content-review-r2-20261016/source-delta-review'/name;doc=json.loads(path.read_bytes());doc[field]=value;b.save(path,doc)
    envelope=json.loads((d/'content-review-binding.json').read_bytes());row=next(r for r in envelope['files'] if r['path']=='docs/direct-damyang/content-review-r2-20261016/source-delta-review/'+name);row.update(bytes=path.stat().st_size,sha256=b.sha(path.read_bytes()));b.save(d/'content-review-binding.json',envelope)
    with patch.object(b,'CONTENT_REVIEW_BINDING_SHA',b.sha((d/'content-review-binding.json').read_bytes())),self.assertRaisesRegex(ValueError,'original_review_pin_changed'):b.verify_content_reviews()

class SingleHomeMutationTests(unittest.TestCase):
 def setUp(self):
  self.fixture=publisher_tests.PublisherTests();self.fixture.setUp();self.addCleanup(self.fixture.doCleanups)
  self.release,self.dist=self.fixture.fixture_release();self.mode=dict(mode='production',indexable=True,origin=o.ORIGIN,revision='a'*40)
 def inspect(self):return o.inspect_dist(self.dist,self.mode)
 def test_exact_current_inventory_and_old_four_route_rejected(self):
  result=self.inspect();self.assertEqual((result['htmlFiles'],len(result['files']),len(result['sitemapUrls'])),(2,16,1))
  for name in ['regions/index.html','regions/suwan-funeral-wreath/index.html']:
   q=self.dist/name;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes((self.dist/'index.html').read_bytes())
  with self.assertRaisesRegex(AssertionError,'Exact index.html and 404.html required'):self.inspect()
 def test_critical_home_structure_mutations(self):
  page=self.dist/'index.html';original=page.read_text()
  changes=[('data-product-sku="B060"','data-product-sku="B999"'),('data-product-sku="B060"','data-old-product="B060"'),('data-faq-question="faq-3"','data-old-question="faq-3"'),('data-faq-answer="faq-3"','data-old-answer="faq-3"'),('data-faq-answer="faq-3"','hidden data-faq-answer="faq-3"'),('data-faq-question="faq-3"','aria-hidden="true" data-faq-question="faq-3"'),('data-reference-total-krw="159000"','data-reference-total-krw="149000"'),('data-shared-flower-banner="budget"','data-shared-flower-banner="other"'),('<img src="','<img hidden src="'),('href="/#products"','href="/regions/"'),('content="ko_KR"','content="en_US"'),('rel="canonical"','rel="alternate"'),('name="robots" content="index,follow"','name="robots" content="noindex,follow"')]
  for old,new in changes:
   with self.subTest(old=old,new=new):
    self.assertIn(old,original);page.write_text(original.replace(old,new,1))
    with self.assertRaises(AssertionError):self.inspect()
    page.write_text(original)
 def test_canonical_and_social_duplicates_rejected(self):
  page=self.dist/'index.html';original=page.read_text()
  for tag in ['<link rel="canonical" href="'+o.ORIGIN+'/">','<meta property="og:url" content="'+o.ORIGIN+'/">','<meta name="robots" content="index,follow">']:
   page.write_text(original.replace('</head>',tag+'</head>'))
   with self.subTest(tag=tag),self.assertRaises(AssertionError):self.inspect()
   page.write_text(original)
 def test_404_purchase_social_schema_and_index_mutations(self):
  page=self.dist/'404.html';original=page.read_text()
  for added in ['<meta property="og:title" content="Invalid">','<script type="application/ld+json">{}</script>','<link rel="canonical" href="'+o.ORIGIN+'/404.html">','<img src="/images/products/B201.jpg" alt="Invalid">']:
   page.write_text(original.replace('</head>',added+'</head>'))
   with self.subTest(added=added),self.assertRaises(AssertionError):self.inspect()
   page.write_text(original)
 def test_exact_one_nonempty_sitemap_and_no_foreign_missing_duplicate_extra_urls(self):
  page=self.dist/'sitemap-0.xml';original=page.read_text();ns='http://www.sitemaps.org/schemas/sitemap/0.9'
  for urls in [[],[o.ORIGIN+'/regions/'],[o.ORIGIN+'/',o.ORIGIN+'/regions/'],[o.ORIGIN+'/']*2,['https://foreign.invalid/']]:
   page.write_text('<urlset xmlns="'+ns+'">'+''.join('<url><loc>'+x+'</loc></url>' for x in urls)+'</urlset>')
   with self.subTest(urls=urls),self.assertRaises(AssertionError):self.inspect()
  page.write_text(original);self.assertEqual(self.inspect()['sitemapUrls'],[o.ORIGIN+'/'])
 def test_sitemap_xml_header_and_file_count_mutations(self):
  for name,value in [('_headers','/*\n  X-Robots-Tag: noindex\n'),('robots.txt','User-agent: *\nDisallow: /\n'),('sitemap-index.xml','<urlset/>')]:
   path=self.dist/name;raw=path.read_bytes();path.write_text(value)
   with self.subTest(name=name),self.assertRaises(AssertionError):self.inspect()
   path.write_bytes(raw)
  extra=self.dist/'sitemap-extra.xml';extra.write_text('<urlset/>')
  with self.assertRaises(AssertionError):self.inspect()
if __name__=='__main__':unittest.main(verbosity=2)
