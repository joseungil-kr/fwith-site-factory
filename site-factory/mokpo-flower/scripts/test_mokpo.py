import unittest,tempfile,shutil,json
from pathlib import Path
from qa_mokpo import check,C,QAError
class NegativeFixtures(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)/'dist';shutil.copytree(C/'dist',self.root)
 def tearDown(self):self.tmp.cleanup()
 def mutate(self,path,old,new):
  p=self.root/path;s=p.read_text();self.assertIn(old,s);p.write_text(s.replace(old,new,1))
 def reject(self,code):
  with self.assertRaisesRegex(QAError,code):check(self.root)
 def test_baseline(self):self.assertEqual(check(self.root)['status'],'PASS_PRIVATE_STATIC_ONLY')
 def test_extra_html_denominator(self):(self.root/'invented.html').write_text('fake');self.reject('HTML_DENOMINATOR')
 def test_index_enabled(self):self.mutate('index.html','noindex,follow','index,follow');self.reject('ROBOTS_META')
 def test_canonical_selected(self):self.mutate('index.html','</head>','<link rel="canonical" href="https://example.com/"/></head>');self.reject('NO_CANONICAL_ORIGIN')
 def test_sitemap_host(self):self.mutate('sitemap.xml','</urlset>','<url><loc>https://example.com/</loc></url></urlset>');self.reject('EMPTY_PREVIEW_SITEMAP')
 def test_block_noindex_read(self):(self.root/'robots.txt').write_text('User-agent: *\nDisallow: /regions/\n');self.reject('ROBOTS_READABLE')
 def test_banner_wrong_variant(self):self.mutate('index.html','data-shared-flower-banner="message"','data-shared-flower-banner="budget"');self.reject('BANNER_SET')
 def test_banner_alt_wrong_phone(self):self.mutate('index.html','전화 1844-0644.','전화 1844-0645.');self.reject('BANNER_ALT')
 def test_banner_alt_duplicate_phone(self):self.mutate('index.html','전화 1844-0644.','전화 1844-0644. 전화 1844-0644.');self.reject('BANNER_ALT')
 def test_banner_alt_missing_phone(self):self.mutate('index.html','전화 1844-0644.','전화 상담.');self.reject('BANNER_ALT')
 def test_banner_alt_caption_reinserted(self):self.mutate('index.html','전화 1844-0644.','AI 생성 이미지 전화 1844-0644.');self.reject('REMOVED_CAPTION_ALT')
 def test_banner_bytes(self):p=self.root/'images/shared-banners/flower-message.webp';p.write_bytes(p.read_bytes()+b'bad');self.reject('BANNER_BYTES')
 def test_banner_caption(self):self.mutate('index.html','</figure>','<figcaption>설명</figcaption></figure>');self.reject('BANNER_CAPTION')
 def test_product_home_fallback(self):self.mutate('index.html','https://fwith.co.kr/shop/item.php?it_id=B201','https://fwith.co.kr/');self.reject('PRODUCT_CTA')
 def test_product_image(self):p=self.root/'images/products/B201.jpg';p.write_bytes(p.read_bytes()+b'bad');self.reject('PRODUCT_IMAGE')
 def test_missing_faq(self):self.mutate('regions/hankook-hospital-funeral-wreath/index.html','data-faq-entry','data-removed-faq-entry');self.reject('FAQ_COUNT')
 def test_hidden_faq(self):self.mutate('regions/hankook-hospital-funeral-wreath/index.html','data-visible-faq','hidden data-visible-faq');self.reject('FAQ_VISIBLE')
 def test_draft_text_loss(self):self.mutate('index.html','조문을 함께하지 못하는 때에도 위로를 전할 방법을 찾게 됩니다.','다른 문장.');self.reject('FIRST_ANSWER')
 def test_h1_duplicate(self):self.mutate('index.html','</main>','<h1>추가 제목</h1></main>');self.reject('H1')
 def test_support_in_menu(self):self.mutate('index.html','href="/regions/hankook-hospital-funeral-wreath/"','href="/regions/"');self.reject('SUPPORT_MENU')
 def test_unmarked_duplicate_first_answer(self):
  spec=json.loads((C/'src/data/frozen/content-spec.ko.json').read_text());text=spec['pages'][0]['content']['firstAnswer']
  self.mutate('index.html','</h1>','</h1><p>'+text+'</p>');self.reject('FIRST_ANSWER_ONCE')
 def test_unmarked_duplicate_faq_answer(self):
  spec=json.loads((C/'src/data/frozen/content-spec.ko.json').read_text());text=spec['faqs'][0]['answer']
  self.mutate('regions/hankook-hospital-funeral-wreath/index.html','</h1>','</h1><p>'+text+'</p>');self.reject('FAQ_ONCE')
 def test_unmarked_duplicate_faq_question(self):
  spec=json.loads((C/'src/data/frozen/content-spec.ko.json').read_text());text=spec['faqs'][0]['question']
  self.mutate('regions/hankook-hospital-funeral-wreath/index.html','</h1>','</h1><p>'+text+'</p>');self.reject('FAQ_ONCE')
 def test_unmarked_support_banner(self):
  self.mutate('regions/index.html','</main>','<img src="/images/shared-banners/flower-message.webp" alt="꽃 배너" width="1774" height="887"></main>');self.reject('BANNER_IMAGE_COUNT')
 def test_unmarked_duplicate_product(self):
  self.mutate('index.html','</main>','<img src="/images/products/B201.jpg" alt="상품" width="500" height="500"></main>');self.reject('PRODUCT_IMAGE_COUNT')
 def test_sibling_duplicate_first_answer(self):
  spec=json.loads((C/'src/data/frozen/content-spec.ko.json').read_text());text=spec['pages'][0]['content']['firstAnswer']
  self.mutate('index.html','</main>','<p>'+text+'</p></main>');self.reject('FIRST_ANSWER_ONCE')
 def test_sibling_duplicate_faq_answer(self):
  spec=json.loads((C/'src/data/frozen/content-spec.ko.json').read_text());text=spec['faqs'][0]['answer']
  self.mutate('regions/hankook-hospital-funeral-wreath/index.html','</main>','<p>'+text+'</p></main>');self.reject('FAQ_ONCE')
 def test_core_launch_promotion(self):
  m=json.loads((C/'src/data/page-map.json').read_text());m['coreHubLaunchStatus']='PASS'
  with self.assertRaisesRegex(QAError,'LAUNCH_SCOPE'):check(self.root,page_map=m)
 def test_public_origin(self):
  m=json.loads((C/'src/data/page-map.json').read_text());m['origin']='https://example.com'
  with self.assertRaisesRegex(QAError,'BOUNDARY'):check(self.root,page_map=m)
if __name__=='__main__':unittest.main(verbosity=2)
