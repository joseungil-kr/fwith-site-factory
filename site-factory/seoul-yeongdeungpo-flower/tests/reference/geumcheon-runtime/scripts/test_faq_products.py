#!/usr/bin/env python3
import json,re,shutil,tempfile,unittest
from pathlib import Path
from qa_faq_products import inspect
class FaqProductNegativeTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);source=Path.cwd()
        shutil.copytree(source/'dist',self.root/'dist');(self.root/'src/data').mkdir(parents=True)
        for file in ['pages.json','products.json']:shutil.copy2(source/'src/data'/file,self.root/'src/data'/file)
        self.pages=json.loads((self.root/'src/data/pages.json').read_text())
        self.page=next(p for p in self.pages if p.get('faq') and p.get('contentMarkdown'))
        self.html=self.root/'dist'/self.page['url'].strip('/')/'index.html'
    def tearDown(self):self.temp.cleanup()
    def inspect(self):return inspect(self.root,write_report=False)
    def test_clean_output(self):self.assertGreater(self.inspect()['visibleFaq'],0)
    def test_legacy_array_faq_matches_same_visible_html(self):
        for p in self.pages:p['faq']=[[f['question'],f['answer']] if isinstance(f,dict) else f for f in p.get('faq',[])]
        (self.root/'src/data/pages.json').write_text(json.dumps(self.pages));self.inspect()
    def test_hidden_faq_fails(self):
        self.html.write_text(self.html.read_text().replace('data-visible-faq','hidden data-visible-faq',1))
        with self.assertRaises(AssertionError):self.inspect()
    def test_collapsed_faq_fails(self):
        self.html.write_text(self.html.read_text().replace('<section class="faq"','<details><section class="faq"',1))
        with self.assertRaises(AssertionError):self.inspect()
    def test_missing_answer_fails(self):
        s=self.html.read_text();s,count=re.subn(r'(<p data-faq-answer[^>]*>).*?(</p>)',r'\1\2',s,count=1);self.assertEqual(count,1);self.html.write_text(s)
        with self.assertRaises(AssertionError):self.inspect()
    def test_homepage_product_link_fails(self):
        s=self.html.read_text();s,count=re.subn(r'(<a href=")[^"]+(" data-order-product-key=)',r'\1https://fwith.co.kr/\2',s,count=1);self.assertEqual(count,1);self.html.write_text(s)
        with self.assertRaises(AssertionError):self.inspect()
    def test_hero_cta_homepage_fails(self):
        s=self.html.read_text();s,count=re.subn(r'(<a class="btn dark" href=")[^"]+(" data-order-product-key=)',r'\1https://fwith.co.kr/\2',s,count=1);self.assertEqual(count,1);self.html.write_text(s)
        with self.assertRaises(AssertionError):self.inspect()
    def test_catalog_homepage_fallback_fails(self):
        p=self.root/'src/data/products.json';rows=json.loads(p.read_text());rows[0]['orderUrl']='https://fwith.co.kr';p.write_text(json.dumps(rows))
        with self.assertRaises(AssertionError):self.inspect()
if __name__=='__main__':unittest.main()
