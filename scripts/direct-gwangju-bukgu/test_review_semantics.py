"""Rehashed native Bukgu semantic mutations. Fixtures are never actual approval evidence."""
import copy,json,unittest
from pathlib import Path
from unittest.mock import patch
import production_build as b
import test_production_build as fixtures

class OriginalReviewSemantics(unittest.TestCase):
 def setUp(self):
  context=fixtures.temporary_control_directory();self.d=context.__enter__();self.addCleanup(context.__exit__,None,None,None)
  p=patch.object(b,'DIRECTORY',self.d);p.start();self.addCleanup(p.stop);fixtures.ProductionTests().fixture(self.d)
  self.review=self.d.parents[1]/'docs/direct-gwangju-bukgu/content-review-20261015';self.binding=json.loads((self.d/'content-review-binding.json').read_text());self.original={p.name:p.read_bytes() for p in self.review.iterdir()}
 def reject(self,name,value):
  for filename,raw in self.original.items():(self.review/filename).write_bytes(raw)
  self.assertFalse(b.same(json.loads(self.original[name]),value));binding=copy.deepcopy(self.binding);b.save(self.review/name,value)
  for row in binding['files']:
   raw=(self.review/Path(row['path']).name).read_bytes();row.update(bytes=len(raw),sha256=b.sha(raw))
  for field,filename in [('customerReviewBindingSHA256','implementation-review-binding.json'),('codeReviewBindingSHA256','implementation-code-review-binding.json')]:binding[field]=b.sha((self.review/filename).read_bytes())
  b.save(self.d/'content-review-binding.json',binding)
  with patch.object(b,'CONTENT_REVIEW_BINDING_SHA',b.sha((self.d/'content-review-binding.json').read_bytes())),self.assertRaises(ValueError):b.verify_content_reviews()
 def fields(self,name,pairs):
  for key,value in pairs:
   changed=json.loads(self.original[name]);changed[key]=value
   with self.subTest(file=name,key=key,value=value):self.reject(name,changed)
 def test_original_native_schema_83_files_and_unmodified_meaning(self):
  self.assertEqual(b.verify_content_reviews()['sourceFiles'],83)
  cp=json.loads(self.original['implementation-review-binding.json']);self.assertEqual(cp['pathBase'],'THIS_REVIEW_PACKAGE_ROOT');self.assertNotIn('result',cp)
 def test_every_review_scalar_semantic_and_type_mutations(self):
  for name,raw in self.original.items():
   if not name.endswith('.json'):continue
   original=json.loads(raw)
   for key,value in original.items():
    if isinstance(value,(list,dict)):continue
    replacement=not value if type(value) is bool else 'MUTATED' if type(value) is str else 0 if value is None else value+1
    if b.same(value,replacement):replacement=True
    with self.subTest(file=name,key=key):self.reject(name,{**original,key:replacement})
 def test_exact_inventory_and_original_paths(self):
  for mutate in [lambda x:x['files'].pop(),lambda x:x['files'][0].update(originalPath='other/original.json'),lambda x:x.update(productionGatePassed=True),lambda x:x.update(staticQualityIsProductionPass=True)]:
   changed=copy.deepcopy(self.binding);mutate(changed);b.save(self.d/'content-review-binding.json',changed)
   with patch.object(b,'CONTENT_REVIEW_BINDING_SHA',b.sha((self.d/'content-review-binding.json').read_bytes())),self.assertRaises(ValueError):b.verify_content_reviews()
 def test_native_denominators_and_nested_findings(self):
  name='original-clause-assessment.json'
  for key in ['guidanceClauses','merchantPolicyClauses','facilityClauses']:
   x=json.loads(self.original[name]);x[key].pop();self.reject(name,x)
   x=json.loads(self.original[name]);x[key][0]['assessment']='PRODUCTION_PASS';self.reject(name,x)
  x=json.loads(self.original[name]);x['denominator']['guidanceNonemptyNonheadingLines']=149;self.reject(name,x)
  name='visible-string-assessment.json';x=json.loads(self.original[name]);x['strings'].pop();self.reject(name,x)
  name='render-checklist.json';x=json.loads(self.original[name]);x['checks'][0]['status']='PASS';self.reject(name,x)
 def test_every_reference_bytes_paths_and_digests(self):
  for name in ['implementation-review-binding.json','implementation-code-review-binding.json']:
   original=json.loads(self.original[name])
   for key,value in original.items():
    if type(value) is not dict or set(value)!={'path','bytes','sha256'}:continue
    for sub,val in [('path','other.json'),('bytes',True),('sha256','0'*64)]:
     x=copy.deepcopy(original);x[key][sub]=val;self.reject(name,x)
 def test_projection_inventory_and_nested_evidence(self):
  for name,key in [('source-input-projection.json','files'),('reviewed-input-projection.json','files'),('independent-code-review.json','evidence'),('code-review-publication-manifest.json','files')]:
   x=json.loads(self.original[name]);x[key].pop();self.reject(name,x)
   for sub,val in [('bytes',True),('sha256','0'*64)]:
    x=json.loads(self.original[name]);x[key][0][sub]=val;self.reject(name,x)
 def test_original_review_flags_cannot_imply_actual_release(self):
  for name in ['independent-copy-review-r1.json','implementation-review-binding.json','independent-code-review.json','implementation-code-review-binding.json']:
   self.fields(name,[('result','PASS'),('sourceFiles',82),('sourceCommit','a'*40),('mustFixRemaining',['still-open'])])
 def test_type_smuggling_and_code_denominators(self):
  for name in ['implementation-review-binding.json','independent-copy-review-r1.json','implementation-code-review-binding.json','independent-code-review.json']:self.fields(name,[('schemaVersion',True),('nationalOrder','34')])
  self.fields('implementation-code-review-binding.json',[(k,0) for k in ['nativeCommandCount','nativeTestCases','independentOutputMutationCases','independentRuntimeCases','httpExceptionMutationCases']])
  x=json.loads(self.original['implementation-code-review-binding.json']);x['originalAssessmentDenominator']['guidance']=149;self.reject('implementation-code-review-binding.json',x)
if __name__=='__main__':unittest.main(verbosity=2)
