#!/usr/bin/env python3
"""Mutate actual compiled output; no live site or provider action."""
import json,re,shutil,tempfile,unittest
from pathlib import Path
from qa_static import check
class OutputBindingTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
  for name in ['dist','src/data','public']:shutil.copytree(Path.cwd()/name,self.root/name)
  self.pages=json.loads((self.root/'src/data/pages.json').read_text());self.detail=self.root/'dist'/self.pages[0]['url'].strip('/')/'index.html'
 def tearDown(self):self.temp.cleanup()
 def test_clean_actual_output(self):check(self.root)
 def test_og_alt_drift_fails(self):
  s,n=re.subn(r'(<meta property="og:image:alt" content=")[^"]*',r'\1wrong photo',self.detail.read_text(),count=1);self.assertEqual(n,1);self.detail.write_text(s)
  with self.assertRaisesRegex(AssertionError,'Reviewed OG alt'):check(self.root)
 def test_twitter_alt_drift_fails(self):
  s,n=re.subn(r'(<meta name="twitter:image:alt" content=")[^"]*',r'\1wrong photo',self.detail.read_text(),count=1);self.assertEqual(n,1);self.detail.write_text(s)
  with self.assertRaisesRegex(AssertionError,'Reviewed Twitter alt'):check(self.root)
 def test_home_hero_base_price_label_missing_fails(self):
  p=self.root/'dist/index.html';s=p.read_text();self.assertIn('<strong>기본가격 ',s);p.write_text(s.replace('<strong>기본가격 ','<strong>',1))
  with self.assertRaisesRegex(AssertionError,'base-price label missing'):check(self.root)
 def test_detail_base_price_label_missing_fails(self):
  s=self.detail.read_text();self.assertIn('<span>기본가격 ',s);self.detail.write_text(s.replace('<span>기본가격 ','<span>',1))
  with self.assertRaisesRegex(AssertionError,'base-price label missing'):check(self.root)
if __name__=='__main__':unittest.main()
