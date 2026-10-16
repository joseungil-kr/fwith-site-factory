"""Current amendment and historical review scopes remain distinct; all writes are temp fixtures."""
import copy,json,unittest
from pathlib import Path
from unittest.mock import patch
import production_build as b
import test_production_build as fixtures

class CurrentReviewSemantics(unittest.TestCase):
 def setUp(self):
  context=fixtures.temporary_control_directory();self.d=context.__enter__();self.addCleanup(context.__exit__,None,None,None)
  p=patch.object(b,'DIRECTORY',self.d);p.start();self.addCleanup(p.stop);fixtures.ProductionTests().fixture(self.d)
  self.binding=json.loads((self.d/'content-review-binding.json').read_text())
 def rewrite(self,relative,mutate,semantic=False):
  path=self.d.parents[1]/'docs/direct-gwangju-gwangsan-policy-correction'/relative;value=json.loads(path.read_text());mutate(value);b.save(path,value)
  binding=copy.deepcopy(self.binding)
  for row in binding['files']:
   data=(self.d.parents[1]/row['path']).read_bytes();row.update(bytes=len(data),sha256=b.sha(data))
  b.save(self.d/'content-review-binding.json',binding)
  contexts=[patch.object(b,'CONTENT_REVIEW_BINDING_SHA',b.sha((self.d/'content-review-binding.json').read_bytes()))]
  if semantic:
   digest=b.sha(json.dumps(binding['files'],ensure_ascii=False,sort_keys=True,separators=(',',':')).encode());contexts.append(patch.object(b,'CURRENT_REVIEW_INVENTORY_SHA',digest))
  return contexts
 def reject(self,relative,mutate,semantic=False):
  import contextlib
  with contextlib.ExitStack() as stack:
   for context in self.rewrite(relative,mutate,semantic):stack.enter_context(context)
   with self.assertRaises(ValueError):b.verify_content_reviews()
 def test_separate_current92_and_original74_with_nulls(self):
  current=b.verify_content_reviews();historical=b.verify_historical_content_reviews()
  self.assertEqual(current['sourceFiles'],92);self.assertEqual(historical['sourceFiles'],74)
  self.assertEqual(current['originalDenominators']['guidance'],159);self.assertEqual(current['originalDenominators']['policy'],24);self.assertEqual(current['originalDenominators']['facility'],2)
  self.assertEqual(current['supplementalDenominators'],{'upperImagePolicyClauses':6,'applicationScopeFollowupFacts':1});self.assertFalse(current['pendingFindingResolved'])
 def test_wrapper_flags_counts_and_sources_reject_rehashed_changes(self):
  for key,val in [('sourceFiles',74),('privateFiles',59),('sourceRevision',b.BASE_SOURCE_REVISION),('copySHA256',self.binding['originalCopySHA256']),('pendingFindingResolved',True),('productionGatePassed',True),('customerCopyLeavesChanged',2),('originalReviewBytesUnchanged',False),('originalDenominators',{'guidance':165,'policy':25,'facility':2}),('supplementalDenominators',{'upperImagePolicyClauses':7,'applicationScopeFollowupFacts':0}),('extra','PASS')]:
   changed=copy.deepcopy(self.binding);changed[key]=val;b.save(self.d/'content-review-binding.json',changed)
   with self.subTest(key=key),patch.object(b,'CONTENT_REVIEW_BINDING_SHA',b.sha((self.d/'content-review-binding.json').read_bytes())),self.assertRaises(ValueError):b.verify_content_reviews()
 def test_native_null_scores_cannot_be_promoted(self):self.reject('amendment-review/independent-review-r2.json',lambda x:x.update(numericReviewScore=100),True)
 def test_native_prior_review_not_full_site_rereview(self):self.reject('amendment-review/independent-review-r2.json',lambda x:x.update(notAFullSiteReReview=False),True)
 def test_native_source_commit_must_remain_null(self):self.reject('amendment-review/independent-review-r2.json',lambda x:x.update(successorSourceCommit=b.REVIEWED_SOURCE_REVISION),True)
 def test_native_html_pending_must_remain_false(self):self.reject('amendment-review/independent-review-r2.json',lambda x:x.update(actualSuccessorHTMLVerified=True),True)
 def test_native_supplements_cannot_change_historical_denominators(self):self.reject('amendment-review/independent-review-r2.json',lambda x:x['originalDenominators'].update(guidance=165,policy=25),True)
 def test_native_copy_scope_cannot_expand(self):self.reject('amendment-review/independent-review-r2.json',lambda x:x.update(copyPointer='/detail'),True)
 def test_new_copy_other_leaf_mutation_rejects(self):self.reject('amendment-review/inputs/customer-copy.json',lambda x:x['home'].update(h1='UNAPPROVED'))
 def test_new_copy_old_paragraph_rejects(self):
  before=json.loads((self.d.parents[1]/'docs/direct-gwangju-gwangsan-policy-correction/amendment-review/inputs/original-customer-copy.json').read_text())
  self.reject('amendment-review/inputs/customer-copy.json',lambda x:x['detail']['sections'][4]['afterList'].__setitem__(0,before['detail']['sections'][4]['afterList'][0]))
 def test_source_delta_native_commit_must_remain_null(self):self.reject('source-delta-review/source-delta-review.json',lambda x:x.update(sourceRevision=b.REVIEWED_SOURCE_REVISION))
 def test_source_delta_browser_cannot_be_promoted(self):self.reject('source-delta-review/source-delta-review.json',lambda x:x.update(actualBrowserVerified=True))
 def test_source_delta_pending_finding_cannot_be_closed(self):self.reject('source-delta-review/source-delta-binding.json',lambda x:x.update(pendingFindingResolved=True))
 def test_source_delta_old_reviewer_cannot_be_reassigned(self):self.reject('source-delta-review/source-delta-binding.json',lambda x:x['originalCodeReview'].update(originalReviewerReranAmendment=True))
 def test_separate_remote_commit_rejects_old_source(self):self.reject('source-save/source-readback-verification.json',lambda x:x.update(sourceRevision=b.BASE_SOURCE_REVISION))
 def test_remote_readback_row_rejects_false_positive(self):self.reject('source-save/source-readback-verification.json',lambda x:x['rows'][0].update(exactReviewedBytes=False))
 def test_output_delta_requires_exact_one_paragraph_and_four_markers(self):self.reject('source-save/downloaded-output-delta.json',lambda x:x.update(customerLeavesChanged=2,copyDigestMarkersChangedPerBuild=3))
 def test_review_symlink_rejected(self):
  row=self.binding['files'][0];p=self.d.parents[1]/row['path'];outside=self.d/'outside-review.json';outside.write_bytes(p.read_bytes());p.unlink();p.symlink_to(outside)
  with self.assertRaisesRegex(ValueError,'source_parent_symlink'):b.verify_content_reviews()
 def test_review_reference_removed_rejects(self):
  binding=copy.deepcopy(self.binding);binding['files'].pop();b.save(self.d/'content-review-binding.json',binding)
  with patch.object(b,'CONTENT_REVIEW_BINDING_SHA',b.sha((self.d/'content-review-binding.json').read_bytes())),self.assertRaises(ValueError):b.verify_content_reviews()
if __name__=='__main__':unittest.main(verbosity=2)
