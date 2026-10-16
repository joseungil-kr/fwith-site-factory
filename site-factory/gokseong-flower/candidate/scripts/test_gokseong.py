"""Real-output mutations. Every mutation starts from an exact private build copy."""
from pathlib import Path
import json,re,shutil,tempfile,unittest
import qa_gokseong as q
class TestPrivateOutput(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.c=q.load('customer-copy.json');cls.detail='index.html';cls.home='index.html';cls.missing='404.html'
 def mutate(self,name,fn):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp)/'dist';shutil.copytree(q.C/'dist',root);p=root/name
   if p.suffix.lower() in ['.html','.xml','.txt'] or p.name=='_headers':
    before=p.read_text();after=fn(before);self.assertNotEqual(before,after,'Mutation must change bytes');p.write_text(after)
   else:fn(p)
   with self.assertRaises((AssertionError,ValueError,KeyError,FileNotFoundError)):q.check(root)
 def test_baseline(self):self.assertEqual(q.check()['status'],'PASS_PRIVATE_STATIC_ONLY')
 def test_copy_mutation(self):self.mutate(self.detail,lambda s:s.replace(self.c['home']['lead'][0],'변조된 첫 문장',1))
 def test_missing_faq(self):self.mutate(self.detail,lambda s:s.replace('data-faq-answer','data-removed-answer',1))
 def test_faq_text(self):self.mutate(self.detail,lambda s:s.replace(self.c['home']['faq'][0]['answer'],'답변 변경',1))
 def test_faq_hidden(self):self.mutate(self.detail,lambda s:s.replace('data-visible-faq','data-visible-faq hidden',1))
 def test_faq_aria_hidden(self):self.mutate(self.detail,lambda s:s.replace('data-visible-faq','data-visible-faq aria-hidden="true"',1))
 def test_faq_css_hidden(self):self.mutate(self.detail,lambda s:s.replace('</head>','<style>#faq{display:none}</style></head>'))
 def test_faq_opacity(self):self.mutate(self.detail,lambda s:s.replace('data-visible-faq','data-visible-faq style="opacity:0"',1))
 def test_faq_template(self):self.mutate(self.detail,lambda s:s.replace('<section id="faq"','<template><section id="faq"',1).replace('data-shared-flower-banner="consultation"','data-shared-flower-banner="consultation"',1))
 def test_product_price(self):self.mutate(self.detail,lambda s:s.replace('상품 기본가 59,000원','상품 기본가 49,000원',1))
 def test_product_shipping(self):self.mutate(self.detail,lambda s:s.replace(self.c['productCards'][0]['shippingLabel'],'광주 광산구 무료배송',1))
 def test_product_destination(self):self.mutate(self.detail,lambda s:s.replace('data-order-product-sku="B201" href="https://fwith.co.kr/shop/item.php?it_id=B201"','data-order-product-sku="B201" href="https://fwith.co.kr/shop/item.php?it_id=B203"',1))
 def test_product_alt(self):self.mutate(self.detail,lambda s:s.replace(self.c['productCards'][0]['photoAlt'],'다른 상품사진',1))
 def test_product_photo(self):self.mutate('images/products/B201.jpg',lambda p:p.write_bytes(p.read_bytes()+b'changed'))
 def test_phone(self):self.mutate(self.home,lambda s:s.replace('tel:18440644','tel:0613324461',1))
 def test_foreign_location(self):self.mutate(self.home,lambda s:s.replace(self.c['home']['h1'],'순천 근조화환',1))
 def test_keywords(self):self.mutate(self.home,lambda s:s.replace('</head>','<meta name="keywords" content="광주 광산구 꽃배달"></head>'))
 def test_unreviewed_text(self):self.mutate(self.home,lambda s:s.replace('</main>','<p>검수되지 않은 문장</p></main>'))
 def test_unreviewed_chrome(self):self.mutate(self.home,lambda s:s.replace('</footer>','추가문구</footer>'))
 def test_unreviewed_meta(self):self.mutate(self.home,lambda s:s.replace('<title>'+self.c['home']['title']+'</title>','<title>다른 제목</title>'))
 def test_duplicate_title(self):self.mutate(self.home,lambda s:s.replace('</head>','<title>추가 제목</title></head>'))
 def test_duplicate_description(self):self.mutate(self.home,lambda s:s.replace('</head>','<meta name="description" content="추가 설명"></head>'))
 def test_duplicate_h1(self):self.mutate(self.home,lambda s:s.replace('</main>','<h1>둘째 제목</h1></main>'))
 def test_robots(self):self.mutate(self.home,lambda s:s.replace('noindex,nofollow,noarchive','index,follow',1))
 def test_canonical(self):self.mutate(self.home,lambda s:s.replace('</head>','<link rel="canonical" href="https://donggu.fwith.kr/"></head>'))
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
 def test_sitemap(self):self.mutate('sitemap.xml',lambda s:s.replace('</urlset>','<url><loc>https://donggu.fwith.kr/</loc></url></urlset>'))
 def test_robots_file(self):self.mutate('robots.txt',lambda s:s+'Sitemap: https://donggu.fwith.kr/sitemap.xml\n')
 def test_notfound_copy(self):self.mutate(self.missing,lambda s:s.replace(self.c['notFound']['body'],'페이지가 존재합니다',1))
 def test_copy_hash(self):self.mutate(self.home,lambda s:s.replace('data-copy-sha="'+q.sha((q.I/'customer-copy.json').read_bytes())+'"','data-copy-sha="wrong"',1))
 def test_broken_link(self):self.mutate(self.home,lambda s:s.replace('/#products','/regions/nonexistent/',1))
 def test_broken_anchor(self):self.mutate(self.home,lambda s:s.replace('/#faq','/#missing',1))
 def test_skip_target(self):self.mutate(self.home,lambda s:s.replace('href="#main-content"','href="#absent"',1))
 def test_focusability(self):self.mutate(self.home,lambda s:s.replace('tabindex="-1"','tabindex="0"',1))

 def test_notfound_social(self):self.mutate(self.missing,lambda s:s.replace('</head>','<meta property="og:title" content="unexpected"></head>'))
 def test_notfound_twitter(self):self.mutate(self.missing,lambda s:s.replace('</head>','<meta name="twitter:card" content="summary"></head>'))
 def test_reference_total_text(self):self.mutate(self.home,lambda s:s.replace(self.c['productCards'][0]['referenceTotalLabel'],'게시금액 합산 참고예산 59,000원',1))
 def test_reference_total_number(self):self.mutate(self.home,lambda s:s.replace('data-reference-total-krw="69000"','data-reference-total-krw="59000"',1))
 def test_reference_total_hidden(self):self.mutate(self.home,lambda s:s.replace('class="product-reference"','class="product-reference" hidden',1))
 def test_reference_total_css_hidden(self):self.mutate(self.home,lambda s:s.replace('</head>','<style>.product-reference{display:none}</style></head>'))
 def test_product_id(self):self.mutate(self.home,lambda s:s.replace('id="product-B201"','id="product-B202"',1))
 def test_faq_id(self):self.mutate(self.home,lambda s:s.replace('id="faq-3"','id="faq-34"',1))
 def test_third_faq_missing(self):self.mutate(self.home,lambda s:s.replace(self.c['home']['faq'][2]['answer'],'',1))
 def test_dated_facility_limit_missing(self):self.mutate(self.home,lambda s:s.replace(self.c['home']['sections'][3]['afterList'][0],'',1))
 def test_order_late_policy_context_missing(self):self.mutate(self.home,lambda s:s.replace(self.c['home']['sections'][4]['afterList'][1],'',1))
 def test_refund_policy_context_missing(self):self.mutate(self.home,lambda s:s.replace(self.c['home']['faq'][1]['answer'],'전액 환불합니다.',1))
 def test_source_intro_missing(self):self.mutate(self.home,lambda s:s.replace(self.c['home']['sourceIntro'],'',1))
 def test_menu_local_fragment_on404(self):self.mutate(self.missing,lambda s:s.replace('href="/#products"','href="#products"',1))
 def test_fake_regions_link(self):self.mutate(self.home,lambda s:s.replace('href="/#products"','href="/regions/"',1))
 def test_menu_label(self):self.mutate(self.home,lambda s:s.replace(self.c['sharedUI']['productsLink'],'장례식장 목록',1))
 def test_footer_label(self):self.mutate(self.home,lambda s:s.replace(self.c['sharedUI']['footerLabel'],'다른 안내',1))
 def test_extra_html_output(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp)/'dist';shutil.copytree(q.C/'dist',root);(root/'regions').mkdir();shutil.copyfile(root/'index.html',root/'regions/index.html')
   with self.assertRaises(AssertionError):q.check(root)
 def test_extra_asset(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp)/'dist';shutil.copytree(q.C/'dist',root);(root/'extra.txt').write_text('unexpected')
   with self.assertRaises(AssertionError):q.check(root)
 def test_exact_https_source_variants_rejected(self):
  approved='https://www.data.go.kr/data/15143467/fileData.do'
  variants=[approved.replace('https:','http:'),approved.replace('https:','HTTPS:'),approved.replace('www.','WWW.'),approved.replace('.kr/','.kr:443/'),approved.replace('/data/','/other/'),approved.replace('15143467','15143468'),approved+'?extra=1',approved+'#fragment',approved.replace('fileData','%66ileData'),approved.replace('www.','user@www.'),approved.replace('https:','javascript:'),approved.replace('https:','')]
  for variant in variants:
   with self.subTest(variant=variant):self.mutate(self.home,lambda s:s.replace(approved,variant,1))
 def test_unapproved_service_schema(self):self.mutate(self.home,lambda s:s.replace('</head>','<script type="application/ld+json">{"@type":"Service"}</script></head>',1))
 def test_inline_event_attribute(self):self.mutate(self.home,lambda s:s.replace('<body>','<body onload="alert(1)">',1))
 def test_footer_phone_destination(self):
  self.mutate(self.home,lambda s:s.replace('<a href="tel:18440644">'+self.c['sharedUI']['phoneLink']+'</a>','<a href="/">'+self.c['sharedUI']['phoneLink']+'</a>',1))
 def test_brand_destination(self):self.mutate(self.home,lambda s:s.replace('<a class="brand" href="/"','<a class="brand" href="/#products"',1))
 def test_r2_upper_weekday(self):self.mutate(self.home,lambda s:s.replace('평일 기준 익일 오전','익일 오전',1))
 def test_r2_upper_weekend(self):self.mutate(self.home,lambda s:s.replace('익일 오후 1시 전후','익일 오전',1))
 def test_r2_lower_position(self):self.mutate(self.home,lambda s:s.replace('같은 이미지 하단','일반 안내',1))
 def test_r2_unresolved_scope(self):self.mutate(self.home,lambda s:s.replace('적용범위와 예외 관계','확정 일정',1))
 def test_r2_B060_distinction(self):self.mutate(self.home,lambda s:s.replace('B060 하단에는 별도로 21시 이후','B060은 별도로 19시 이후',1))
 def test_r2_provider_assistance(self):self.mutate(self.home,lambda s:s.replace('실제 가능한 일정은 선택 상품과 받는 곳, 희망일시를 기준으로 안내해 드립니다','직접 확인하세요',1))
class FooterTouchCSSTests(unittest.TestCase):
 def test_actual_output_declarations(self):
  css='\n'.join(p.read_text() for p in (q.C/'dist/_astro').glob('*.css'))
  self.assertTrue(q.footer_touch_css_contract(css))
 def test_each_touch_declaration_regression_rejected(self):
  for prop,value in {'display':'inline','align-items':'stretch','min-height':'0','min-width':'0'}.items():
   with self.subTest(property=prop),tempfile.TemporaryDirectory() as tmp:
    root=Path(tmp)/'dist';shutil.copytree(q.C/'dist',root);p=next((root/'_astro').glob('*.css'))
    p.write_text(p.read_text()+'footer a{'+prop+':'+value+'}')
    with self.assertRaisesRegex(q.QAError,'FOOTER_TOUCH_CSS_CONTRACT'):q.check(root)

class CopySchemaTests(unittest.TestCase):
 def reject(self,change):
  c=json.loads(json.dumps(q.load('customer-copy.json')));change(c)
  with self.assertRaises((AssertionError,ValueError,KeyError)):q.validate_copy_schema(c)
 def test_native_five_keys_positive(self):self.assertTrue(q.validate_copy_schema(q.load('customer-copy.json')))
 def test_extra_detail(self):self.reject(lambda c:c.update(detail={}))
 def test_extra_support(self):self.reject(lambda c:c.update(support={}))
 def test_fake_card(self):self.reject(lambda c:c['home']['sections'][1].update(card={}))
 def test_wrong_order(self):self.reject(lambda c:c['home']['sections'].reverse())
 def test_missing_third_faq(self):self.reject(lambda c:c['home']['faq'].pop())
 def test_wrong_reference(self):self.reject(lambda c:c['productCards'][0].update(referenceTotalKRW=59000))
 def test_nonnull_final_price(self):self.reject(lambda c:c['productCards'][0].update(finalPriceKRW=69000))
if __name__=='__main__':unittest.main(verbosity=2)
