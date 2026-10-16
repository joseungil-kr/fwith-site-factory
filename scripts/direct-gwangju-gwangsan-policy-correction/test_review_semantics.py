"""Rehash native original documents to test semantic seals; fixtures are not release evidence."""
import copy,json,unittest
from pathlib import Path
from unittest.mock import patch
import production_build as b
import test_production_build as fixtures

class OriginalReviewSemantics(unittest.TestCase):
 def setUp(self):
  context=fixtures.temporary_control_directory();self.d=context.__enter__();self.addCleanup(context.__exit__,None,None,None)
  p=patch.object(b,'DIRECTORY',self.d);p.start();self.addCleanup(p.stop);fixtures.ProductionTests().fixture(self.d)
  self.review=self.d.parents[1]/'docs/direct-gwangju-gwangsan/content-review-20261016';self.binding=json.loads((self.d/'historical-content-review-binding.json').read_text());self.original={p.name:p.read_bytes() for p in self.review.iterdir()}
 def reject(self,name,value):
  for filename,raw in self.original.items():(self.review/filename).write_bytes(raw)
  self.assertFalse(b.same(json.loads(self.original[name]),value));binding=copy.deepcopy(self.binding);b.save(self.review/name,value)
  for row in binding['files']:
   raw=(self.review/Path(row['path']).name).read_bytes();row.update(bytes=len(raw),sha256=b.sha(raw))
  for field,filename in [('customerReviewBindingSHA256','review-bindings.json'),('codeReviewBindingSHA256','code-review-bindings.json')]:
   if filename in self.original:binding[field]=b.sha((self.review/filename).read_bytes())
  b.save(self.d/'historical-content-review-binding.json',binding)
  with patch.object(b,'HISTORICAL_CONTENT_REVIEW_BINDING_SHA',b.sha((self.d/'historical-content-review-binding.json').read_bytes())),self.assertRaises(ValueError):b.verify_historical_content_reviews()
 def test_native_74_file_source_and_unchanged_new_manuscript_verdict(self):
  self.assertEqual(b.verify_historical_content_reviews()['sourceFiles'],74)
  ms=json.loads(self.original['review-result.json']);self.assertEqual(ms['status'],'MANUSCRIPT_REVIEW_ACCEPTED_WITH_RENDER_PENDING')
  self.assertEqual([ms[k] for k in ['historicalScores','authorScores','numericReviewScore','sourceCommitSHA']],[None]*4)
 def test_every_top_level_scalar_semantic_and_type_mutation(self):
  for name,raw in self.original.items():
   if not name.endswith('.json'):continue
   original=json.loads(raw)
   for key,value in original.items():
    if isinstance(value,(list,dict)):continue
    replacement=not value if type(value) is bool else 'MUTATED' if type(value) is str else 0 if value is None else value+1
    if b.same(value,replacement):replacement=True
    with self.subTest(file=name,key=key):self.reject(name,{**original,key:replacement})
 def test_every_top_level_collection_and_schema_mutation(self):
  for name,raw in self.original.items():
   if not name.endswith('.json'):continue
   original=json.loads(raw);self.reject(name,{**original,'unexpectedInventedPass':True})
   for key,value in original.items():
    if type(value) not in (dict,list):continue
    changed=copy.deepcopy(original)
    if type(value) is list:
     if value:changed[key].pop()
     else:changed[key]=['UNRESOLVED_ISSUE']
    else:
     if value:changed[key].pop(next(iter(value)))
     else:changed[key]={'invented':'PASS'}
    with self.subTest(file=name,key=key):self.reject(name,changed)
 def test_nested_review_findings_and_original_denominators(self):
  for name,keys in [('original-row-review.json',['guidanceRows','policyRows','facilityRows']),('customer-context-review.json',['rows']),('question-review.json',['rows'])]:
   for key in keys:
    original=json.loads(self.original[name])
    for index in (0,len(original[key])-1):
     changed=copy.deepcopy(original);changed[key][index]['inventedHistoricPass']='PASS';self.reject(name,changed)
  ms=json.loads(self.original['review-result.json'])
  for key in ms['denominators']:
   changed=copy.deepcopy(ms);changed['denominators'][key]=18;self.reject('review-result.json',changed)
  for field in ['historicalScores','authorScores','numericReviewScore']:
   changed=copy.deepcopy(ms);changed[field]=100;self.reject('review-result.json',changed)
 def test_all_reference_inventory_first_last_hash_bytes_paths(self):
  for name,raw in self.original.items():
   if not name.endswith('.json'):continue
   original=json.loads(raw)
   for key,value in original.items():
    if type(value) is not list or not value or type(value[0]) is not dict:continue
    for index in {0,len(value)-1}:
     for sub,val in [('bytes',True),('sha256','0'*64),('path','other.json')]:
      if sub not in value[index]:continue
      changed=copy.deepcopy(original);changed[key][index][sub]=val;self.reject(name,changed)
 def test_exact_inventory_and_original_paths(self):
  for mutate in [lambda x:x['files'].pop(),lambda x:x['files'][0].update(originalPath='other/original.json'),lambda x:x.update(productionGatePassed=True),lambda x:x.update(staticQualityIsProductionPass=True),lambda x:x.update(sourceFiles=True)]:
   changed=copy.deepcopy(self.binding);mutate(changed);b.save(self.d/'historical-content-review-binding.json',changed)
   with patch.object(b,'HISTORICAL_CONTENT_REVIEW_BINDING_SHA',b.sha((self.d/'historical-content-review-binding.json').read_bytes())),self.assertRaises(ValueError):b.verify_historical_content_reviews()
if __name__=='__main__':unittest.main(verbosity=2)
