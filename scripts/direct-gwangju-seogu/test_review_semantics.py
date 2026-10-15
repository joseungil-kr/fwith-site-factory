"""Offline meaning mutations. Rehashed fixture evidence is never release approval."""
import copy,json
from pathlib import Path
import unittest
from unittest.mock import patch
import production_build as b
import test_production_build as build_tests

class OriginalReviewSemantics(unittest.TestCase):
 def setUp(self):
  self.context=build_tests.temporary_control_directory();self.d=self.context.__enter__();self.addCleanup(self.context.__exit__,None,None,None)
  self.patch=patch.object(b,'DIRECTORY',self.d);self.patch.start();self.addCleanup(self.patch.stop)
  build_tests.ProductionTests().fixture(self.d)
  self.review=self.d.parents[1]/'docs/direct-gwangju-seogu/content-review-20261015'
  self.binding=json.loads((self.d/'content-review-binding.json').read_text())
  self.original={p.name:p.read_bytes() for p in self.review.iterdir()}
 def reseal(self,name,value):
  for filename,raw in self.original.items():(self.review/filename).write_bytes(raw)
  binding=copy.deepcopy(self.binding);b.save(self.review/name,value)
  if name=='independent-code-review.json':
   code=json.loads(self.original['implementation-code-review-binding.json'])
   code['independentCodeReview'].update(sha256=b.sha((self.review/name).read_bytes()),bytes=(self.review/name).stat().st_size)
   b.save(self.review/'implementation-code-review-binding.json',code)
  for row in binding['files']:
   raw=(self.review/Path(row['path']).name).read_bytes();row.update(bytes=len(raw),sha256=b.sha(raw))
  for field,filename in [('customerReviewBindingSHA256','implementation-review-binding.json'),('codeReviewBindingSHA256','implementation-code-review-binding.json')]:binding[field]=b.sha((self.review/filename).read_bytes())
  b.save(self.d/'content-review-binding.json',binding)
  return patch.object(b,'CONTENT_REVIEW_BINDING_SHA',b.sha((self.d/'content-review-binding.json').read_bytes()))
 def reject_fields(self,name,mutations,reason):
  baseline=json.loads(self.original[name])
  for key,value in mutations:
   changed=copy.deepcopy(baseline);changed[key]=value
   with self.subTest(file=name,key=key,value=value),self.reseal(name,changed),self.assertRaisesRegex(ValueError,reason):b.verify_content_reviews()
 def test_exact_original_schema_without_fabricated_result(self):
  self.assertEqual(b.verify_content_reviews()['sourceFiles'],79)
  cp=json.loads(self.original['implementation-review-binding.json']);code=json.loads(self.original['implementation-code-review-binding.json'])
  self.assertNotIn('result',cp);self.assertNotIn('boundCopyFiles',cp);self.assertNotIn('result',code)
 def test_copy_schema_rejects_legacy_fields_and_missing_flags(self):
  self.reject_fields('implementation-review-binding.json',[('result','PASS_EXACT_FINAL_COPY_ONLY'),('boundCopyFiles',[])],'original_copy_binding_schema_required')
  cp=json.loads(self.original['implementation-review-binding.json']);del cp['actualBrowserChecked']
  with self.reseal('implementation-review-binding.json',cp),self.assertRaisesRegex(ValueError,'original_copy_binding_schema_required'):b.verify_content_reviews()
 def test_copy_scope_and_flags_are_not_production_approval(self):
  fields=[('schemaVersion',True),('officialCode','12210'),('nationalOrder',31),('region','donggu')]
  self.reject_fields('implementation-review-binding.json',fields,'review_region_identity_mismatch')
  fields=[('assessmentScope','PRODUCTION_PASS'),('sourceCommit','a'*40),('revision','seogu-copy-r1-20261015'),('guidanceSourceCommit','b'*40),('coreHubLaunchStatus','PASS'),('fullLaunchStatus','PASS')]+[(key,True) for key in ['actualHTMLChecked','actualBuildChecked','actualBrowserChecked','actualPublicHTTPChecked','publicationEligible']]
  self.reject_fields('implementation-review-binding.json',fields,'manuscript_scope_or_unverified_flags_changed')
 def test_manuscript_real_verdict_and_resolved_changes_required(self):
  self.reject_fields('independent-copy-review-r2.json',[('verdict','PASS_EXACT_FINAL_MANUSCRIPT_AND_RENDER_PLAN_ONLY')],'manuscript_verdict_required')
  base=json.loads(self.original['independent-copy-review-r2.json'])
  for value in [[],[base['mandatoryRevisions'][0]], [{**row,'status':'PENDING'} for row in base['mandatoryRevisions']]]:
   changed={**base,'mandatoryRevisions':value}
   with self.subTest(value=value),self.reseal('independent-copy-review-r2.json',changed),self.assertRaisesRegex(ValueError,'manuscript_required_revisions_unresolved'):b.verify_content_reviews()
 def test_original_supporting_reviews_keep_pending_production_scope(self):
  for name in ['bounded-18-clause-review.json','a04-manuscript-assessment.json','render-checklist.json']:
   self.reject_fields(name,[('publicationEligible',True),('actualBrowserChecked',True),('sourceCommit','a'*40)],'manuscript_scope_or_unverified_flags_changed')
  self.reject_fields('a04-manuscript-assessment.json',[(key,100) for key in ['SEO','GEO','AEO']],'a04_cannot_claim_technical_quality_scores')
  self.reject_fields('render-checklist.json',[('status','PASS')],'original_checklist_cannot_claim_actual_output')
  self.reject_fields('bounded-18-clause-review.json',[('verdict','PASS'),('checkCount',17)],'bounded_manuscript_scope_required')
 def test_copy_reference_cannot_point_to_other_original(self):
  cp=json.loads(self.original['implementation-review-binding.json'])
  cp['customerCopy']['path']='seogu-customer-copy-20261015/other.json'
  with self.reseal('implementation-review-binding.json',cp),self.assertRaisesRegex(ValueError,'copy_source_reference_schema'):b.verify_content_reviews()
 def test_code_original_verdict_source_denominators_and_flags(self):
  fields=[('verdict','PASS_EXACT_LOCAL_CODE_AND_OUTPUT_ONLY'),('assessmentScope','PRODUCTION_PASS'),('namespace','gwangju-donggu'),('sourceFiles',76),('mandatoryChangesRemaining',True),('sourceCommit','a'*40),('sourceTreeSHA256','b'*64),('privateTreeSHA256','b'*64),('adapterTreeSHA256','b'*64),('manuscriptBindingSHA256','b'*64),('manuscriptReviewSHA256','b'*64),('originalAssetImagesOpened',6),('actualLocalBuildChecked',False),('actualStaticHTMLChecked',False)]
  fields += [(key,True) for key in ['actualRemoteSourceChecked','actualActionsChecked','actualBrowserChecked','actualPublicHTTPChecked','providerOwnershipChecked','publicationEligible']]
  self.reject_fields('implementation-code-review-binding.json',fields,'code_review_identity_or_scope_mismatch')
  self.reject_fields('implementation-code-review-binding.json',[('result','PASS_EXACT_LOCAL_CODE_AND_OUTPUT_ONLY'),('sourceFileCount',79)],'original_code_binding_schema_required')
 def test_code_report_cannot_claim_actions_or_pixels(self):
  fields=[('verdict','PASS'),('sourceFiles',76),('privateFiles',61),('adapterFiles',14),('mandatoryChangesRemaining',True),('coreHubLaunchStatus','PASS'),('fullLaunchStatus','PASS')]+[(key,True) for key in ['actualActionsVerified','actualBrowserVerified','actualPublicHTTPVerified','actual404HTTPVerified','providerOwnershipVerified','indexNowSubmitted','publicationEligible']]
  self.reject_fields('independent-code-review.json',fields,'code_report_identity_or_scope_mismatch')
 def test_code_actual_local_output_denominators_required(self):
  base=json.loads(self.original['independent-code-review.json'])
  for key,value in [('stringsEachMode',113),('bodyParity',3),('staticAssetParity',8),('independentNegativeTests',0)]:
   changed=copy.deepcopy(base);changed['testCounts'][key]=value
   with self.subTest(key=key),self.reseal('independent-code-review.json',changed),self.assertRaisesRegex(ValueError,'code_output_review_required'):b.verify_content_reviews()
if __name__=='__main__':unittest.main(verbosity=2)
