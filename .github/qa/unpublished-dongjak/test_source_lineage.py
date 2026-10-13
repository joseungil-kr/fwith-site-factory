"""Socket-free exact saved successor lineage regressions; no synthetic commits."""
import copy,json,unittest
from unittest.mock import patch
import adapter

class SourceLineageTests(unittest.TestCase):
 def rows(self):return [adapter.load(adapter.HERE/'frozen-inputs'/p)for p in ('source-file-manifest.original.json','source-file-manifest.final.json')]
 def lineage(self):return adapter.load(adapter.HERE/'source-lineage.json')
 def test_exact_original_and_actual_successor(self):adapter.verify_source_lineage()
 def test_one_reviewed_css_delta_only(self):
  a,b=self.rows();self.assertTrue(adapter.validate_source_lineage(a,b,self.lineage()))
  self.assertEqual(sum(x['sha256']!=y['sha256']for x,y in zip(a,b)),1)
 def test_second_source_delta_rejected(self):
  a,b=self.rows();b[0]['sha256']='0'*64
  with self.assertRaises(AssertionError):adapter.validate_source_lineage(a,b,self.lineage())
 def test_deleted_source_rejected(self):
  a,b=self.rows()
  with self.assertRaises(AssertionError):adapter.validate_source_lineage(a,b[:-1],self.lineage())
 def test_duplicate_source_rejected(self):
  a,b=self.rows();b[-1]=copy.deepcopy(b[0])
  with self.assertRaises(AssertionError):adapter.validate_source_lineage(a,b,self.lineage())
 def test_unreviewed_css_hash_rejected(self):
  a,b=self.rows();next(e for e in b if e['path'].endswith('/src/styles/global.css'))['sha256']='0'*64
  with self.assertRaises(AssertionError):adapter.validate_source_lineage(a,b,self.lineage())
 def test_unreviewed_css_blob_rejected(self):
  a,b=self.rows();next(e for e in b if e['path']==adapter.SITE_PATH+'/src/styles/global.css')['gitBlobSha']='a'*40
  with self.assertRaises(AssertionError):adapter.validate_source_lineage(a,b,self.lineage())
 def test_missing_correction_rejected(self):
  a,b=self.rows()
  with self.assertRaises(AssertionError):adapter.validate_source_lineage(a,a,self.lineage())
 def test_publication_flip_rejected(self):
  a,b=self.rows();l=self.lineage();l['publicationApproved']=True
  with self.assertRaises(AssertionError):adapter.validate_source_lineage(a,b,l)
 def test_different_successor_rejected(self):
  a,b=self.rows();l=self.lineage();l['currentSourceSha']='a'*40
  with self.assertRaises(AssertionError):adapter.validate_source_lineage(a,b,l)
 def test_old_source_spec_rejected(self):
  spec=adapter.load(adapter.HERE/'bound-spec.json');spec['sourceSha']='1570f3866985a1434c2847604840926db92e300b'
  with self.assertRaisesRegex(AssertionError,'Exact saved source'):adapter.validate_spec(spec)
 def test_old_generated_revision_rejected(self):
  from test_dongjak_binding import DongjakBindingTests
  helper=DongjakBindingTests();data=json.dumps({'revision':'1570f3866985a1434c2847604840926db92e300b'},indent=2).encode()
  with self.assertRaisesRegex(AssertionError,'Generated revision bytes differ'):helper.check_bytes(data)
 def test_current_capture_pin_and_upstream_unchanged(self):
  adapter.verify_upstream()
  self.assertEqual(adapter.sha((adapter.HERE/'run_bound_capture.py').read_bytes()),'8ff36ed26f2010d967b1ffc0c17f3d69378c347a92057c9a439d8d780b399534')
if __name__=='__main__':unittest.main()
