"""Real-output mutations. Every mutation starts from an exact private build copy."""
from pathlib import Path
import json,shutil,tempfile,unittest
import qa_naju as q
class TestPrivateOutput(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.c=q.load('customer-copy.json');cls.detail=q.htmlpath(cls.c['detail']['proposedPath']);cls.home='index.html';cls.support='regions/index.html';cls.missing='404.html'
 def mutate(self,name,fn):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp)/'dist';shutil.copytree(q.C/'dist',root);p=root/name
   if p.suffix.lower() in ['.html','.xml','.txt'] or p.name=='_headers':
    before=p.read_text();after=fn(before);self.assertNotEqual(before,after,'Mutation must change bytes');p.write_text(after)
   else:fn(p)
   with self.assertRaises((AssertionError,ValueError,KeyError,FileNotFoundError)):q.check(root)
 def test_baseline(self):self.assertEqual(q.check()['status'],'PASS_PRIVATE_STATIC_ONLY')
 def test_copy_mutation(self):self.mutate(self.detail,lambda s:s.replace(self.c['detail']['lead'][0],'변조된 첫 문장',1))
 def test_missing_faq(self):self.mutate(self.detail,lambda s:s.replace('data-faq-answer','data-removed-answer',1))
 def test_faq_text(self):self.mutate(self.detail,lambda s:s.replace(self.c['detail']['faq'][0]['answer'],'답변 변경',1))
 def test_faq_hidden(self):self.mutate(self.detail,lambda s:s.replace('data-visible-faq','data-visible-faq hidden',1))
 def test_faq_aria_hidden(self):self.mutate(self.detail,lambda s:s.replace('data-visible-faq','data-visible-faq aria-hidden="true"',1))
 def test_faq_css_hidden(self):self.mutate(self.detail,lambda s:s.replace('</head>','<style>#faq{display:none}</style></head>'))
 def test_faq_opacity(self):self.mutate(self.detail,lambda s:s.replace('data-visible-faq','data-visible-faq style="opacity:0"',1))
 def test_faq_template(self):self.mutate(self.detail,lambda s:s.replace('<section id="faq"','<template><section id="faq"',1).replace('data-shared-flower-banner="consultation"','data-shared-flower-banner="consultation"',1))
 def test_product_price(self):self.mutate(self.detail,lambda s:s.replace('상품 기본가격 59,000원','상품 기본가격 49,000원',1))
 def test_product_shipping(self):self.mutate(self.detail,lambda s:s.replace('나주시 추가배송비 10,000원 별도','나주시 무료배송',1))
 def test_product_destination(self):self.mutate(self.detail,lambda s:s.replace('data-order-product-sku="B201" href="https://fwith.co.kr/shop/item.php?it_id=B201"','data-order-product-sku="B201" href="https://fwith.co.kr/shop/item.php?it_id=B203"',1))
 def test_product_alt(self):self.mutate(self.detail,lambda s:s.replace(self.c['productCards'][0]['photoAlt'],'다른 상품사진',1))
 def test_product_photo(self):self.mutate('images/products/B201.jpg',lambda p:p.write_bytes(p.read_bytes()+b'changed'))
 def test_phone(self):self.mutate(self.home,lambda s:s.replace('tel:18440644','tel:0613324461',1))
 def test_foreign_location(self):self.mutate(self.home,lambda s:s.replace(self.c['home']['h1'],'순천 근조화환',1))
 def test_keywords(self):self.mutate(self.home,lambda s:s.replace('</head>','<meta name="keywords" content="나주 꽃배달"></head>'))
 def test_unreviewed_text(self):self.mutate(self.home,lambda s:s.replace('</main>','<p>검수되지 않은 문장</p></main>'))
 def test_unreviewed_chrome(self):self.mutate(self.home,lambda s:s.replace('</footer>','추가문구</footer>'))
 def test_unreviewed_meta(self):self.mutate(self.home,lambda s:s.replace('<title>'+self.c['home']['title']+'</title>','<title>다른 제목</title>'))
 def test_duplicate_title(self):self.mutate(self.home,lambda s:s.replace('</head>','<title>추가 제목</title></head>'))
 def test_duplicate_description(self):self.mutate(self.home,lambda s:s.replace('</head>','<meta name="description" content="추가 설명"></head>'))
 def test_duplicate_h1(self):self.mutate(self.home,lambda s:s.replace('</main>','<h1>둘째 제목</h1></main>'))
 def test_robots(self):self.mutate(self.home,lambda s:s.replace('noindex,follow','index,follow',1))
 def test_canonical(self):self.mutate(self.home,lambda s:s.replace('</head>','<link rel="canonical" href="https://naju.fwith.kr/"></head>'))
 def test_duplicate_id(self):self.mutate(self.home,lambda s:s.replace('</main>','<div id="main-content"></div></main>'))
 def test_js(self):self.mutate(self.home,lambda s:s.replace('</body>','<script>alert(1)</script></body>'))
 def test_form(self):self.mutate(self.home,lambda s:s.replace('</main>','<form></form></main>'))
 def test_iframe(self):self.mutate(self.home,lambda s:s.replace('</main>','<iframe src="https://example.com/"></iframe></main>'))
 def test_banner_bytes(self):self.mutate('images/shared-banners/flower-message.webp',lambda p:p.write_bytes(p.read_bytes()+b'changed'))
 def test_banner_alt(self):self.mutate(self.home,lambda s:s.replace(self.c['sharedBannerAlt']['message'],'다른 배너',1))
 def test_banner_dimensions(self):self.mutate(self.home,lambda s:s.replace('width="1774"','width="1775"',1))
 def test_banner_caption(self):self.mutate(self.home,lambda s:s.replace('</figure>','<figcaption>캡션</figcaption></figure>',1))
 def test_banner_hidden(self):self.mutate(self.home,lambda s:s.replace('data-shared-flower-banner="message"','data-shared-flower-banner="message" hidden',1))
 def test_headers(self):self.mutate('_headers',lambda s:'/*\n')
 def test_sitemap(self):self.mutate('sitemap.xml',lambda s:s.replace('</urlset>','<url><loc>https://naju.fwith.kr/</loc></url></urlset>'))
 def test_robots_file(self):self.mutate('robots.txt',lambda s:s+'Sitemap: https://naju.fwith.kr/sitemap.xml\n')
 def test_notfound_copy(self):self.mutate(self.missing,lambda s:s.replace(self.c['notFound']['body'],'페이지가 존재합니다',1))
 def test_support_copy(self):self.mutate(self.support,lambda s:s.replace(self.c['support']['body'],'새 시설 안내',1))
 def test_copy_hash(self):self.mutate(self.home,lambda s:s.replace('data-copy-sha="'+q.sha((q.I/'customer-copy.json').read_bytes())+'"','data-copy-sha="wrong"',1))
 def test_broken_link(self):self.mutate(self.home,lambda s:s.replace(self.c['detail']['proposedPath'],'/regions/nonexistent/',1))
 def test_broken_anchor(self):self.mutate(self.home,lambda s:s.replace('#sources','#missing',1))
 def test_skip_target(self):self.mutate(self.home,lambda s:s.replace('href="#main-content"','href="#absent"',1))
 def test_focusability(self):self.mutate(self.home,lambda s:s.replace('tabindex="-1"','tabindex="0"',1))
if __name__=='__main__':unittest.main(verbosity=2)
