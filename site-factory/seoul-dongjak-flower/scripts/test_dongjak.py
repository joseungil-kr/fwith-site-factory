"""Mutate actual compiled Dongjak output; no browser, provider or external action."""
import json,shutil,tempfile,unittest,re
from pathlib import Path
from qa_dongjak import inspect
class Mutations(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.r=Path(self.tmp.name)
  for p in ['src/data','dist']:shutil.copytree(Path.cwd()/p,self.r/p)
  self.detail=self.r/'dist/regions/dongjak-funeral-wreath/index.html';self.directory=self.r/'dist/regions/index.html';self.home=self.r/'dist/index.html';self.article=json.loads((self.r/'src/data/dongjak-article-copy.json').read_text())
 def tearDown(self):self.tmp.cleanup()
 def mutate(self,f,old,new):
  s=f.read_text();self.assertIn(old,s);f.write_text(s.replace(old,new,1))
 def fail(self,pattern):
  with self.assertRaisesRegex(AssertionError,pattern):inspect(self.r,write=False)
 def test_clean(self):inspect(self.r,write=False)
 def test_article_bytes(self):
  f=self.r/'src/data/dongjak-article-copy.json';f.write_text(f.read_text()+' ');self.fail('copy byte drift')
 def test_common_bytes(self):
  f=self.r/'src/data/dongjak-common-copy.json';f.write_text(f.read_text()+' ');self.fail('copy byte drift')
 def test_h3_anchor_level(self):
  self.mutate(self.detail,'<h3 id="cau-hospital">','<h2 id="cau-hospital">');self.fail('anchor level/text')
 def test_broken_fragment(self):
  self.mutate(self.directory,'#cau-hospital','#wrong-anchor');self.fail('Broken fragment')
 def test_duplicate_anchor(self):
  self.mutate(self.detail,'</main>','<h3 id="cau-hospital">duplicate</h3></main>');self.fail('Duplicate HTML id')
 def test_extra_standalone_route(self):
  f=self.r/'dist/regions/held/index.html';f.parent.mkdir();f.write_text(self.detail.read_text());self.fail('Unexpected standalone')
 def test_admin_facility_link(self):
  s,n=re.subn(r'(<li data-administrative-unit="[^"]+">)',r'\1<a href="/regions/dongjak-funeral-wreath/#boramae-hospital">보라매병원</a>',self.directory.read_text(),count=1);self.assertEqual(n,1);self.directory.write_text(s);self.fail('must not imply')
 def test_admin_geography_drift(self):
  self.mutate(self.directory,'<strong>노량진제1동</strong>:','<strong>가상의동</strong>:');self.fail('relation text drift')
 def test_refund_exception_missing(self):
  self.mutate(self.detail,self.article['sections'][-1]['paragraphs'][-1],'');self.fail('Missing or changed approved body')
 def test_source_note_missing(self):
  self.mutate(self.detail,self.article['sourceNote'],'');self.fail('Source note missing')
 def test_source_destination_drift(self):
  self.mutate(self.detail,'href="https://ch.cauhs.or.kr/funeral/conts/101002000000000.do"','href="https://example.org/"');self.fail('Source label/destination')
 def test_image_dimension(self):
  self.mutate(self.detail,'width="500" height="500"','width="500" height="499"');self.fail('Wrong product dimensions')
 def test_card_price(self):
  self.mutate(self.detail,'<strong>상품 기본가격 59,000원</strong>','<strong>상품 기본가격 59,001원</strong>');self.fail('Exact product price')
 def test_card_destination(self):
  self.mutate(self.detail,'<a href="https://fwith.co.kr/shop/item.php?it_id=B201" data-order-product-key=','<a href="https://fwith.co.kr/" data-order-product-key=');self.fail('Product CTA')
 def test_preview_indexable(self):
  self.mutate(self.home,'content="noindex,nofollow,noarchive"','content="index,follow"');self.fail('Preview robots')
 def test_preview_sitemap(self):
  (self.r/'dist/sitemap-0.xml').write_text('<urlset/>');self.fail('Preview sitemap')
 def test_footer_destination(self):
  self.mutate(self.home,'href="/">꽃이랑 홈','href="https://fwith.co.kr">꽃이랑 홈');self.fail('Footer destination')
 def test_product_bytes(self):
  f=self.r/'dist/images/products/funeral-basic.jpg';f.write_bytes(f.read_bytes()+b'x');self.fail('Product byte drift')
 def test_banner_bytes(self):
  f=self.r/'dist/images/shared-banners/flower-message.webp';f.write_bytes(f.read_bytes()+b'x');self.fail('Banner byte drift')
if __name__=='__main__':unittest.main()
