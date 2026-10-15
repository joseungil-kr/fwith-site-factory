"""Rehashed local fixture attacks only. These are never release or review evidence."""
import copy,json
from pathlib import Path
import unittest
from unittest.mock import patch
import production_build as b
import test_production_build as fixtures

class OriginalReviewSemantics(unittest.TestCase):
 def setUp(self):
  context=fixtures.temporary_control_directory();self.d=context.__enter__();self.addCleanup(context.__exit__,None,None,None)
  p=patch.object(b,'DIRECTORY',self.d);p.start();self.addCleanup(p.stop);fixtures.ProductionTests().fixture(self.d)
  self.review=self.d.parents[1]/'docs/direct-gwangju-namgu/content-review-20261015'
  self.binding=json.loads((self.d/'content-review-binding.json').read_text());self.original={p.name:p.read_bytes() for p in self.review.iterdir()}
 def reseal(self,name,value):
  for filename,raw in self.original.items():(self.review/filename).write_bytes(raw)
  binding=copy.deepcopy(self.binding);b.save(self.review/name,value)
  if name=='independent-code-review.json':
   code=json.loads(self.original['implementation-code-review-binding.json']);code['independentCodeReview'].update(sha256=b.sha((self.review/name).read_bytes()),bytes=(self.review/name).stat().st_size);b.save(self.review/'implementation-code-review-binding.json',code)
  for row in binding['files']:
   raw=(self.review/Path(row['path']).name).read_bytes();row.update(bytes=len(raw),sha256=b.sha(raw))
  for field,filename in [('customerReviewBindingSHA256','implementation-review-binding.public-r1.json'),('codeReviewBindingSHA256','implementation-code-review-binding.json')]:binding[field]=b.sha((self.review/filename).read_bytes())
  b.save(self.d/'content-review-binding.json',binding)
  return patch.object(b,'CONTENT_REVIEW_BINDING_SHA',b.sha((self.d/'content-review-binding.json').read_bytes()))
 def reject(self,name,value,reason=None):
  self.assertFalse(b.same(json.loads(self.original[name]),value),'negative must change actual original JSON including scalar types')
  with self.reseal(name,value):
   if reason:
    with self.assertRaisesRegex(ValueError,reason):b.verify_content_reviews()
   else:
    with self.assertRaises(ValueError):b.verify_content_reviews()
 def fields(self,name,pairs,reason=None):
  for key,value in pairs:
   changed=json.loads(self.original[name]);changed[key]=value
   with self.subTest(file=name,key=key,value=value):self.reject(name,changed,reason)
 def test_original_schema_and_82_source(self):
  self.assertEqual(b.verify_content_reviews()['sourceFiles'],82)
  cp=json.loads(self.original['implementation-review-binding.public-r1.json'])
  self.assertNotIn('result',cp);self.assertNotIn('boundCopyFiles',cp);self.assertIn('originalClauseReview',cp);self.assertNotIn('bound18Review',cp)
 def test_copy_schema_and_required_flags(self):
  name='implementation-review-binding.public-r1.json'
  self.fields(name,[('result','PASS'),('boundCopyFiles',[]),('bound18Review',{})],'original_review_schema_required')
  for key in ['actualBrowserChecked','closingReconciliation','originalClauseReview']:
   value=json.loads(self.original[name]);del value[key];self.reject(name,value,'original_review_schema_required')
 def test_all_review_region_identities(self):
  for name in ['implementation-review-binding.public-r1.json','independent-copy-review-r2.json','implementation-code-review-binding.json','independent-code-review.json']:
   self.fields(name,[('schemaVersion',True),('officialCode','12240'),('nationalOrder',32),('region','seogu')],'review_region_identity_mismatch')
 def test_manuscript_scope_and_unverified_flags(self):
  for name in ['implementation-review-binding.public-r1.json','independent-copy-review-r2.json','original-clause-assessment.json','purchase-intent-assessment.json','render-checklist.json']:
   self.fields(name,[('assessmentScope','PRODUCTION_PASS'),('sourceCommit','a'*40),('revision','namgu-copy-r1-20261015'),('guidanceSourceCommit','b'*40),('coreHubLaunchStatus','PASS'),('fullLaunchStatus','PASS')]+[(key,True) for key in ['actualHTMLChecked','actualBuildChecked','actualBrowserChecked','actualPublicHTTPChecked','publicationEligible']],'manuscript_scope_or_unverified_flags_changed')
 def test_original_manuscript_verdict_and_resolution(self):
  name='independent-copy-review-r2.json';self.fields(name,[('verdict','PASS'),('mustFixRemaining',['x'])],'manuscript_verdict_required')
  original=json.loads(self.original[name]);revision=original['mandatoryRevisions'][0]
  for value in [[],[revision,revision],[{**revision,'status':'PENDING'}],[{**revision,'id':'OTHER'}]]:
   self.reject(name,{**original,'mandatoryRevisions':value},'manuscript_required_revisions_unresolved')
 def test_original_149_clause_13_policy_denominators(self):
  name='original-clause-assessment.json';self.fields(name,[('guidanceClauseCount',18),('policyImageClauseCount',12)],'original_clause_scope_required')
  value=json.loads(self.original[name]);value['guidance'].pop();self.reject(name,value,'original_clause_inventory_required')
  value=json.loads(self.original[name]);value['guidance'][0]['assessment']='PRODUCTION_PASS';self.reject(name,value)
 def test_original_12_pending_render_checks(self):
  name='render-checklist.json';value=json.loads(self.original[name]);value['checks'][0]['actualOutputStatus']='PASS';self.reject(name,value,'original_checklist_cannot_claim_actual_output')
  value=json.loads(self.original[name]);value['checks'].pop();self.reject(name,value,'original_checklist_cannot_claim_actual_output')
 def test_manuscript_does_not_claim_scores_or_indexing(self):
  self.fields('purchase-intent-assessment.json',[(k,90) for k in ['seoScore','geoScore','aeoScore']]+[('rankingOrIndexingVerified',True)],'manuscript_cannot_claim_technical_quality_scores')
 def test_copy_bound_source_reference_mutations(self):
  name='implementation-review-binding.public-r1.json'
  for field in ['customerCopy','renderPlan','metadata','visibleStrings','assetManifest','frozenAuthorManifest','originalClauseReview','renderChecklist','closingReconciliation','humanReview']:
   for key,value in [('path','other.json'),('bytes',1),('sha256','a'*64)]:
    changed=json.loads(self.original[name]);changed[field][key]=value;self.reject(name,changed)
 def test_projection_only_is_not_authorization_or_review(self):
  name='reviewed-input-projection.json';self.fields(name,[('scope','PRODUCTION_PASS'),('successorPackagedPath','wrong.json')],'publication_projection_scope_required')
  original=json.loads(self.original[name]);changed=copy.deepcopy(original);changed['entries'].pop();self.reject(name,changed,'exact_publication_projection_required')
  for key,value in [('packagedPath','inputs/other.json'),('originalPath','other.json'),('originalBytesPreserved',False),('bytes',True),('sha256','b'*64)]:
   changed=copy.deepcopy(original);changed['entries'][0][key]=value;self.reject(name,changed)
 def test_path_reconciliation_preserves_original_closed_judgment(self):
  name='publication-path-reconciliation-r1.json'
  self.fields(name,[('scope','NEW_REVIEW'),('originalVerdict','PASS'),('newContentReviewPerformed',True),('newApplicationTestsPerformed',True),('newBuildBrowserOrPublicVerificationPerformed',True),('originalIndependentChecksNotRerun',0)],'path_reconciliation_cannot_claim_new_review')
  for key,value in [('sha256','a'*64),('bytes',1)]:
   changed=json.loads(self.original[name]);changed['originalClosedBinding'][key]=value;self.reject(name,changed,'closed_original_binding_identity_required')
  changed=json.loads(self.original[name]);changed['exactSemanticDelta'][0]['jsonPointer']='/customerCopy';self.reject(name,changed,'only_path_reconciliation_allowed')
 def test_original_manuscript_hash_is_not_substituted(self):
  name='publication-path-reconciliation-r1.json';changed=json.loads(self.original[name]);changed['originalReview']['sha256']='a'*64;self.reject(name,changed,'original_manuscript_identity_required')
 def test_code_schema_scope_denominators_and_flags(self):
  name='implementation-code-review-binding.json';original=json.loads(self.original[name]);self.fields(name,[('result','PASS'),('sourceFileCount',82)],'original_review_schema_required')
  pairs=[('verdict','PASS'),('assessmentScope','PRODUCTION_PASS'),('sourceFiles',79),('sourceCommit','a'*40),('sourceTreeSHA256','b'*64),('privateTreeSHA256','b'*64)]
  pairs += [(key,not value) for key,value in original.items() if isinstance(value,bool)]
  self.fields(name,pairs,'code_review_identity_or_scope_mismatch')
  self.fields(name,[('mustFixRemaining',['still-open'])],'code_mandatory_revisions_unresolved')
 def test_code_report_flags_and_counts(self):
  name='independent-code-review.json';original=json.loads(self.original[name]);pairs=[('verdict','PASS'),('sourceFiles',79),('privateFiles',64),('adapterFiles',14)]+[(key,not value) for key,value in original.items() if isinstance(value,bool)]
  self.fields(name,pairs,'code_report_identity_or_scope_mismatch')
  self.fields(name,[('mustFixRemaining',['still-open']),('mandatoryRevisions',['still-open'])],'code_mandatory_revisions_unresolved')
  if 'testCounts' in original:
   changed=copy.deepcopy(original);changed['testCounts']={};self.reject(name,changed)
 def test_original_local_test_denominators_are_not_relabelled(self):
  self.fields('implementation-code-review-binding.json',[(key,0) for key in ['nativeCommandCount','nativeTestCases','independentOutputMutationCases','independentRuntimeCases','separateComparisonFixtureCases']],'code_review_identity_or_scope_mismatch')
 def test_original_document_paths_and_inventory_are_exact(self):
  for mutate in [lambda x:x['files'].pop(),lambda x:x['files'][0].update(originalPath='other/original.json'),lambda x:x.update(productionGatePassed=True),lambda x:x.update(staticQualityIsProductionPass=True)]:
   changed=copy.deepcopy(self.binding);mutate(changed);b.save(self.d/'content-review-binding.json',changed)
   with patch.object(b,'CONTENT_REVIEW_BINDING_SHA',b.sha((self.d/'content-review-binding.json').read_bytes())),self.assertRaises(ValueError):b.verify_content_reviews()
if __name__=='__main__':unittest.main(verbosity=2)
