"""Negative rendered/static contract tests. Mutates temporary fixtures, never source input."""
from pathlib import Path
from tempfile import TemporaryDirectory
import contextlib,io,json,shutil,unittest
from qa_gangnam import inspect
ROOT=Path(__file__).resolve().parents[1]
class Mutations(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=TemporaryDirectory();cls.root=Path(cls.tmp.name);shutil.copytree(ROOT/'src/data',cls.root/'src/data');shutil.copytree(ROOT/'public',cls.root/'public');shutil.copytree(ROOT/'dist',cls.root/'dist');cls.original={p:p.read_bytes() for p in cls.root.rglob('*') if p.is_file()}
 @classmethod
 def tearDownClass(cls):cls.tmp.cleanup()
 def tearDown(self):
  for p,b in self.original.items():p.write_bytes(b)
 def rejects(self,file,old,new):
  p=self.root/file;s=p.read_text();self.assertIn(old,s);p.write_text(s.replace(old,new,1))
  with contextlib.redirect_stdout(io.StringIO()),self.assertRaises((AssertionError,KeyError,ValueError)):
   inspect(self.root,False)
 def test_valid(self):
  with contextlib.redirect_stdout(io.StringIO()):self.assertEqual(inspect(self.root,False)['htmlN'],6)
 def test_wrong_region_h1(self):self.rejects('dist/index.html','강남구 화환, 조의와 축하에 맞춰 준비하는 꽃','관악구 화환, 조의와 축하에 맞춰 준비하는 꽃')
 def test_directory_missing_consultation(self):self.rejects('dist/regions/index.html','data-shared-flower-banner="consultation"','data-wrong-banner="consultation"')
 def test_banner_wrong_alt_phone(self):self.rejects('dist/index.html','전화 1844-0644.','전화 0000-0000.')
 def test_banner_file_byte_drift(self):
  p=self.root/'dist/images/shared-banners/flower-message.webp';p.write_bytes(p.read_bytes()+b'bad')
  with self.assertRaises(AssertionError):inspect(self.root,False)
 def test_faq_missing_visible_answer(self):
  a=json.loads((self.root/'src/data/gangnam-copy.json').read_text())['articles'][0]
  self.rejects('dist/regions/gangnam-funeral-wreath/index.html',a['faq'][0]['answer'],'답변 누락')
 def test_hidden_faq(self):self.rejects('dist/regions/gangnam-funeral-wreath/index.html','data-visible-faq','hidden data-visible-faq')
 def test_wrong_cta(self):self.rejects('dist/regions/gangnam-funeral-wreath/index.html','https://fwith.co.kr/shop/item.php?it_id=B201','https://example.invalid/checkout')
 def test_body_drift(self):
  a=json.loads((self.root/'src/data/gangnam-copy.json').read_text())['articles'][0]
  self.rejects('dist/regions/gangnam-funeral-wreath/index.html',a['sections'][0]['paragraphs'][0],'새로 지어낸 업체 정책')
 def test_fake_canonical(self):self.rejects('dist/index.html','rel="canonical" href="https://seoul-gangnam.local.invalid/"','rel="canonical" href="https://fake.example/"')
 def test_indexable_output(self):self.rejects('dist/index.html','noindex,nofollow,noarchive','index,follow')
 def test_wrong_geo_count(self):self.rejects('dist/regions/index.html','data-legal-unit=','data-incorrect-legal-unit=')
 def test_original_seal_change(self):self.rejects('src/data/gangnam-approved/plan/fixed-plan.json','"originalPlanN": 3','"originalPlanN": 2')
 def test_no_policy_deletion(self):
  a=json.loads((self.root/'src/data/gangnam-copy.json').read_text())['articles'][0];s=next(s for s in a['sections'] if s['id']=='materials')
  self.rejects('dist/regions/gangnam-funeral-wreath/index.html',s['paragraphs'][0],'')
 def test_publication_flag(self):self.rejects('src/data/site-config.json','"productionApproved": false','"productionApproved": true')
if __name__=='__main__':unittest.main(verbosity=2)
