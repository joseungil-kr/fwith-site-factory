from pathlib import Path
from tempfile import TemporaryDirectory
import contextlib,io,json,shutil,unittest
from qa_source_link_amendment import inspect
from minimal_source_evidence import NEW,OLD
ROOT=Path(__file__).resolve().parents[1]
class SourceLinkTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=TemporaryDirectory();cls.root=Path(cls.tmp.name);shutil.copytree(ROOT/'src/data',cls.root/'src/data');shutil.copytree(ROOT/'dist',cls.root/'dist');cls.original={p:p.read_bytes() for p in cls.root.rglob('*') if p.is_file()}
 @classmethod
 def tearDownClass(cls):cls.tmp.cleanup()
 def tearDown(self):
  for p in self.root.rglob('*'):
   if p.is_file() and p not in self.original:p.unlink()
  for p,b in self.original.items():p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
 def reject(self):
  with contextlib.redirect_stdout(io.StringIO()),self.assertRaises((AssertionError,FileNotFoundError,KeyError,ValueError)):inspect(self.root,False)
 def change(self,path,old,new):
  f=self.root/path;s=f.read_text();self.assertIn(old,s);f.write_text(s.replace(old,new,1))
 def test_positive(self):
  with contextlib.redirect_stdout(io.StringIO()):self.assertEqual(inspect(self.root,False)['customerDiffPointers'],['/articles/2/sourceLinks/3/url'])
 def test_old_effective_url(self):self.change('src/data/gangnam-copy.json',NEW,OLD);self.reject()
 def test_second_url_change(self):self.change('src/data/gangnam-copy.json','https://www.coex.co.kr/guide/indoor-navigation/','https://example.invalid/');self.reject()
 def test_body_year_change(self):self.change('src/data/gangnam-copy.json','공식 연결 문서인 2024년 10월','공식 연결 문서인 2025년 10월');self.reject()
 def test_old_html_url(self):self.change('dist/regions/gangnam-event-wreath/index.html',NEW,OLD);self.reject()
 def test_stale_html_snapshot(self):
  p=json.loads((self.root/'src/data/pages.json').read_text())[2];self.change('dist/regions/gangnam-event-wreath/index.html',p['snapshotId'],'local-content-gangnam-event-wreath-d99a84a666c1185ed');self.reject()
 def test_amendment_byte_drift(self):
  f=self.root/'src/data/gangnam-source-link-amendment.json';f.write_bytes(f.read_bytes()+b' ');self.reject()
 def test_full_pdf_reintroduction_rejected(self):
  f=self.root/'src/data/gangnam-current-facts/raw/setec-current-linked-operations.pdf';f.write_bytes(b'%PDF-test dummy');self.reject()
 def test_extract_missing(self):
  (self.root/'src/data/gangnam-current-facts/extracts/article43-page13.txt').unlink();self.reject()
 def test_evidence_manifest_drift(self):
  f=self.root/'src/data/gangnam-current-facts/SELECTION-MANIFEST.json';f.write_bytes(f.read_bytes()+b' ');self.reject()
 def test_extract_byte_drift(self):
  f=self.root/'src/data/gangnam-current-facts/extracts/cover-page1.txt';f.write_bytes(f.read_bytes()+b'changed');self.reject()
 def test_full_text_reintroduction_rejected(self):
  f=self.root/'src/data/gangnam-current-facts/text/setec-current-linked-operations.txt';f.write_bytes(b'test dummy');self.reject()
 def test_unexpected_artifact_rejected(self):
  f=self.root/'src/data/gangnam-current-facts/extra.txt';f.write_bytes(b'test dummy');self.reject()
 def test_extract_selection_drift(self):
  f=self.root/'src/data/gangnam-current-facts/EXTRACT-SELECTION-MANIFEST.json';f.write_bytes(f.read_bytes()+b' ');self.reject()
 def test_minimal_contract_drift(self):
  f=self.root/'src/data/gangnam-minimal-evidence-amendment.json';f.write_bytes(f.read_bytes()+b' ');self.reject()
 def test_original_full_document_validator_still_rejects_absence(self):
  from source_link_amendment import load_amendment as full_document_validator
  with self.assertRaises((AssertionError,FileNotFoundError)):full_document_validator(self.root)
if __name__=='__main__':unittest.main(verbosity=2)
