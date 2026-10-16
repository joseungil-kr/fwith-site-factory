"""Real-output mutations. Every mutation starts from an exact private build copy."""
from pathlib import Path
import json,re,shutil,tempfile,unittest
import qa_donggu as q
class TestPrivateOutput(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.c=q.load('customer-copy.json');cls.detail=q.htmlpath(q.routes['detail']);cls.home='index.html';cls.support='regions/index.html';cls.missing='404.html'
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
 def test_support_copy(self):self.mutate(self.support,lambda s:s.replace(self.c['support']['body'],'새 시설 안내',1))
 def test_copy_hash(self):self.mutate(self.home,lambda s:s.replace('data-copy-sha="'+q.sha((q.AMEND/'customer-copy.json').read_bytes())+'"','data-copy-sha="wrong"',1))
 def test_broken_link(self):self.mutate(self.home,lambda s:s.replace(q.routes['detail'],'/regions/nonexistent/',1))
 def test_broken_anchor(self):self.mutate(self.home,lambda s:s.replace('#sources','#missing',1))
 def test_skip_target(self):self.mutate(self.home,lambda s:s.replace('href="#main-content"','href="#absent"',1))
 def test_focusability(self):self.mutate(self.home,lambda s:s.replace('tabindex="-1"','tabindex="0"',1))
 def test_detail_breadcrumb_missing(self):self.mutate(self.detail,lambda s:re.sub(r'<nav class="breadcrumb".*?</nav>','',s,count=1))
 def test_support_breadcrumb_missing(self):self.mutate(self.support,lambda s:re.sub(r'<nav class="breadcrumb".*?</nav>','',s,count=1))
 def test_breadcrumb_hidden(self):self.mutate(self.detail,lambda s:s.replace('class="breadcrumb"','class="breadcrumb" hidden',1))
 def test_breadcrumb_css_hidden(self):self.mutate(self.detail,lambda s:s.replace('</head>','<style>.breadcrumb{display:none}</style></head>'))
 def test_breadcrumb_wrong_parent(self):self.mutate(self.detail,lambda s:s.replace('href="/regions/"','href="/"',1))
 def test_breadcrumb_self_parent(self):self.mutate(self.detail,lambda s:s.replace('href="/regions/"','href="'+q.routes['detail']+'"',1))
 def test_breadcrumb_unreviewed_label(self):self.mutate(self.detail,lambda s:s.replace(self.c['support']['h1'],'광주 광산구 전체 장례식장',1))
 def test_breadcrumb_wrong_aria_label(self):self.mutate(self.detail,lambda s:s.replace('aria-label="'+self.c['sharedUI']['breadcrumbLabel']+'"','aria-label="주요 메뉴"',1))
 def test_breadcrumb_current_missing(self):self.mutate(self.detail,lambda s:s.replace('aria-current="page"','data-not-current="page"',1))
 def test_breadcrumb_current_wrong(self):self.mutate(self.support,lambda s:s.replace('aria-current="page"','aria-current="step"',1))
 def test_breadcrumb_current_link(self):self.mutate(self.detail,lambda s:s.replace('<span aria-current="page">'+self.c['detail']['h1']+'</span>','<a aria-current="page" href="'+q.routes['detail']+'">'+self.c['detail']['h1']+'</a>',1))
 def test_breadcrumb_current_hidden(self):self.mutate(self.detail,lambda s:s.replace('aria-current="page"','aria-current="page" style="opacity:0"',1))
 def test_breadcrumb_separator_exposed(self):self.mutate(self.detail,lambda s:s.replace('aria-hidden="true">›','aria-hidden="false">›',1))
 def test_breadcrumb_duplicate(self):self.mutate(self.detail,lambda s:re.sub(r'(<nav class="breadcrumb".*?</nav>)',r'\1\1',s,count=1))
 def test_breadcrumb_after_article(self):
  def move(s):
   crumb=re.search(r'<nav class="breadcrumb".*?</nav>',s).group();return s.replace(crumb,'',1).replace('</main>',crumb+'</main>',1)
  self.mutate(self.detail,move)
 def test_support_kept_out_main_menu(self):self.mutate(self.home,lambda s:s.replace('<nav class="desktop-navigation" aria-label="주요 메뉴">','<nav class="desktop-navigation" aria-label="주요 메뉴"><a href="/regions/">'+self.c['support']['h1']+'</a>',1))
 def test_notfound_social(self):self.mutate(self.missing,lambda s:s.replace('</head>','<meta property="og:title" content="unexpected"></head>'))
 def test_notfound_twitter(self):self.mutate(self.missing,lambda s:s.replace('</head>','<meta name="twitter:card" content="summary"></head>'))
 def test_home_card_h2(self):self.mutate(self.home,lambda s:s.replace('<h3 data-reviewed-block>'+q.facility_card(self.c)['title']+'</h3>','<h2 data-reviewed-block>'+q.facility_card(self.c)['title']+'</h2>'))
 def test_unverified_operation_claim(self):self.mutate(self.detail,lambda s:s.replace(self.c['detail']['sourceIntro'],'현재 운영과 화환 반입이 가능합니다.',1))
 def test_unverified_shipping_amount(self):self.mutate(self.detail,lambda s:s.replace(self.c['productCards'][0]['shippingLabel'],'광산구 추가배송비 10,000원 별도',1))
 def test_wrong_chonnam_facility(self):self.mutate(self.detail,lambda s:s.replace('광주수완장례식장','그린장례문화원',1))
 def test_unapproved_http_source(self):self.mutate(self.detail,lambda s:s.replace('https://www.data.go.kr/data/15143467/fileData.do','http://nammoon.kr/bbs/content.php?code=about_03',1))
 def test_exact_https_source_variants_rejected(self):
  approved='https://www.data.go.kr/data/15143467/fileData.do'
  variants=[approved.replace('https:','http:'),approved.replace('https:','HTTPS:'),approved.replace('www.','WWW.'),approved.replace('.kr/','.kr:443/'),approved.replace('/data/','/other/'),approved.replace('15143467','15143468'),approved+'?extra=1',approved+'#fragment',approved.replace('fileData','%66ileData'),approved.replace('www.','user@www.'),approved.replace('https:','javascript:'),approved.replace('https:','')]
  for variant in variants:
   with self.subTest(variant=variant):self.mutate(self.detail,lambda s:s.replace(approved,variant,1))
 def test_predecessor_http_sources_rejected(self):
  approved='https://xn--9n2b13p6qa02ip2bca.com/intro/directions'
  variants=['http://www.xn--2i0b08qs5ar2u23fca.com/page/page3','http://www.xn--2i0b08qs5ar2u23fca.com/page/sub006',approved.replace('https:','http:'),approved+'?extra=1',approved+'#fragment',approved.replace('/intro/','/%69ntro/'),approved.replace('.com/','.com:443/'),approved.replace('https://','https://user@')]
  for variant in variants:
   with self.subTest(variant=variant):self.mutate(self.detail,lambda s:s.replace(approved,variant,1))
 def test_fourth_faq_missing_rejected(self):
  self.mutate(self.detail,lambda s:s.replace('<div class="faq-pair"><h3 data-reviewed-block data-faq-question>'+self.c['detail']['faq'][3]['question'], '<div class="faq-pair"><h3 hidden data-reviewed-block data-faq-question>'+self.c['detail']['faq'][3]['question'],1))
 def test_unapproved_service_schema(self):self.mutate(self.home,lambda s:s.replace('</head>','<script type="application/ld+json">{"@type":"Service"}</script></head>',1))
 def test_amendment_upper_weekday(self):self.mutate(self.detail,lambda s:s.replace('평일 기준 익일 오전','익일 오전',1))
 def test_amendment_upper_weekend(self):self.mutate(self.detail,lambda s:s.replace('익일 오후 1시 전후','익일 오전',1))
 def test_amendment_lower_position(self):self.mutate(self.detail,lambda s:s.replace('같은 이미지 하단','일반 안내',1))
 def test_amendment_unresolved_scope(self):self.mutate(self.detail,lambda s:s.replace('적용범위나 예외 관계','확정 일정',1))
 def test_amendment_B060_distinction(self):self.mutate(self.detail,lambda s:s.replace('B060은 별도로 21시 이후','B060은 별도로 19시 이후',1))
 def test_amendment_provider_assistance(self):self.mutate(self.detail,lambda s:s.replace('해당 주문으로 상담해 드립니다','직접 확인하세요',1))
class CopySchemaTests(unittest.TestCase):
 def reject(self,change):
  c=json.loads(json.dumps(q.load('customer-copy.json')));change(c)
  with self.assertRaises((AssertionError,ValueError,KeyError)):q.validate_copy_schema(c)
 def test_selection_first_positive(self):self.assertEqual(q.facility_card(q.load('customer-copy.json'))['href'],q.routes['detail'])
 def test_missing_facility(self):self.reject(lambda c:c['home']['sections'].pop(1))
 def test_duplicate_facility(self):self.reject(lambda c:c['home']['sections'].append(c['home']['sections'][1]))
 def test_missing_card(self):self.reject(lambda c:c['home']['sections'][1].pop('card'))
 def test_null_card(self):self.reject(lambda c:c['home']['sections'][1].update(card=None))
 def test_extra_card(self):self.reject(lambda c:c['home']['sections'][0].update(card=c['home']['sections'][1]['card']))
 def test_extra_null_card(self):self.reject(lambda c:c['home']['sections'][0].update(card=None))
 def test_wrong_card_href(self):self.reject(lambda c:c['home']['sections'][1]['card'].update(href='/'))
 def test_missing_title(self):self.reject(lambda c:c['home']['sections'][1]['card'].pop('title'))
 def test_old_home_order(self):self.reject(lambda c:c['home']['sections'].reverse())
 def test_old_detail_order(self):self.reject(lambda c:c['detail']['sections'].reverse())
if __name__=='__main__':unittest.main(verbosity=2)
