"""Mutate isolated copies of real compiled Seocho output and require rejection.
No browser, remote write, deployment, or source mutation occurs in these tests.
"""
from pathlib import Path
import copy, html, json, os, re, shutil, tempfile, unittest
from qa_seocho import inspect, read
from release_mode import release_mode

SOURCE=Path.cwd()
RELEASE_MODE=release_mode(SOURCE)
# Expected current paragraphs include only the separately sealed two-field correction.
# inspect() independently reconstructs them from unchanged historical approval bytes.
ARTICLES=read(SOURCE/'src/data/seocho-copy.json')['articles']
COMMON=read(SOURCE/'src/data/seocho-approved/copy/common-visible-copy.rev2.json')['common']
AMENDMENT=read(SOURCE/'src/data/common-banner-phone-amendment.json')

class SeochoMutations(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
  for name in ['src/data','dist','public']:shutil.copytree(SOURCE/name,self.root/name)
  self.detail='dist/regions/seocho-funeral-wreath/index.html';self.celebration='dist/regions/seocho-celebration-wreath/index.html';self.directory='dist/regions/index.html';self.home='dist/index.html'
 def tearDown(self):self.tmp.cleanup()
 def check(self):return inspect(self.root,write=False,quiet=True)
 def rejected(self):
  with self.assertRaises(AssertionError):self.check()
 def replace(self,path,old,new,n=1):
  path=self.root/path;s=path.read_text();self.assertIn(old,s);path.write_text(s.replace(old,new,n))
 def regex(self,path,pattern,fn,n=1):
  path=self.root/path;s,count=re.subn(pattern,fn,path.read_text(),count=n,flags=re.S);self.assertEqual(count,n);path.write_text(s)
 def data(self,name,change):
  p=self.root/'src/data'/(name+'.json');value=read(p);change(value);p.write_text(json.dumps(value,ensure_ascii=False))
 def test_clean_compiled_output(self):self.assertEqual(self.check()['htmlFiles'],5)
 def test_sealed_approval_bytes(self):
  p=self.root/'src/data/seocho-approved/copy/article-copy.rev4.json';p.write_text(p.read_text()+' ');self.rejected()
 def test_floor_correction_falsely_promoted_review(self):
  self.data('publish-manifest',lambda x:x['directRelease'].__setitem__('reviewStatus','COPY_INPUT_PASS_RUNTIME_PENDING'));self.rejected()
 def test_floor_correction_binding_hash_drift(self):
  self.data('publish-manifest',lambda x:x['directRelease']['copyCorrection'].__setitem__('runtimeCopySha256','0'*64));self.rejected()
 def test_floor_correction_old_sentence_in_html(self):
  a=read(self.root/'src/data/seocho-corrections/floor-20261013/amendment.json');self.replace(self.detail,a['newSentence'],a['oldSentence']);self.rejected()
 def test_floor_correction_reverted_runtime(self):
  a=read(self.root/'src/data/seocho-corrections/floor-20261013/amendment.json');self.replace('src/data/seocho-copy.json',a['newSentence'],a['oldSentence']);self.rejected()
 def test_floor_correction_missing_amendment(self):
  (self.root/'src/data/seocho-corrections/floor-20261013/amendment.json').unlink();self.rejected()
 def test_floor_correction_amendment_byte_drift(self):
  p=self.root/'src/data/seocho-corrections/floor-20261013/amendment.json';p.write_bytes(p.read_bytes()+b' ');self.rejected()
 def test_floor_correction_official_evidence_byte_drift(self):
  p=self.root/'src/data/seocho-corrections/floor-20261013/funeral-facilities.html';p.write_bytes(p.read_bytes()+b' ');self.rejected()
 def test_floor_correction_waf_evidence_byte_drift(self):
  p=self.root/'src/data/seocho-corrections/floor-20261013/funeral-floor-1-waf.html';p.write_bytes(b'fake image');self.rejected()
 def test_floor_correction_markdown_only_revert(self):
  a=read(self.root/'src/data/seocho-corrections/floor-20261013/amendment.json')
  self.data('seocho-copy',lambda x:x['articles'][0].__setitem__('contentMarkdown',x['articles'][0]['contentMarkdown'].replace(a['newSentence'],a['oldSentence'])));self.rejected()
 def test_floor_correction_coordinated_unapproved_copy(self):
  a=read(self.root/'src/data/seocho-corrections/floor-20261013/amendment.json')
  for path in ['src/data/seocho-copy.json','src/data/pages.json',self.detail]:
   p=self.root/path;p.write_text(p.read_text().replace(a['newSentence'],'공식 시설 안내는 지하 빈소를 안내합니다.'))
  self.rejected()
 def test_new_unapproved_sentence(self):self.replace(self.detail,'</main>','<p>전국 어디든 두 시간 안에 배송합니다.</p></main>');self.rejected()
 def test_old_region_copy(self):self.replace(self.detail,'</main>','<p>영등포구 화환 안내</p></main>');self.rejected()
 def test_extra_standalone_facility_route(self):
  p=self.root/'dist/regions/snu-faculty/index.html';p.parent.mkdir();p.write_text((self.root/self.detail).read_text());self.rejected()
 def test_missing_detail_route(self):(self.root/self.detail).unlink();self.rejected()
 def test_duplicate_heading_id(self):self.replace(self.detail,'</main>','<h2 id="seoul-st-mary-funeral">서울성모장례식장의 빈소 안내</h2></main>');self.rejected()
 def test_wrong_heading_level(self):self.replace(self.detail,'<h2 id="seoul-st-mary-funeral">','<h3 id="seoul-st-mary-funeral">');self.rejected()
 def test_broken_facility_fragment(self):self.replace(self.directory,'#seoul-st-mary-funeral','#broken');self.rejected()
 def test_paragraph_reordered(self):
  a,b=ARTICLES[0]['sections'][0]['paragraphs'][:2];s=(self.root/self.detail).read_text();self.assertIn(a,s);self.assertIn(b,s);s=s.replace(a,'MUTATION_MARKER',1).replace(b,a,1).replace('MUTATION_MARKER',b,1);(self.root/self.detail).write_text(s);self.rejected()
 def test_first_answer_duplicate(self):self.replace(self.detail,'</main>','<p>'+ARTICLES[0]['firstAnswer']+'</p></main>');self.rejected()
 def test_hidden_paragraph(self):self.replace(self.detail,'<p>'+ARTICLES[0]['sections'][0]['paragraphs'][0],'<p hidden>'+ARTICLES[0]['sections'][0]['paragraphs'][0]);self.rejected()
 def test_hidden_faq(self):self.replace(self.detail,'data-visible-faq','hidden data-visible-faq');self.rejected()
 def test_missing_hero(self):self.regex(self.home,r'<a class="hero-product".*?</a>','');self.rejected()
 def test_duplicate_hero(self):self.regex(self.home,r'<a class="hero-product".*?</a>',lambda m:m[0]+m[0]);self.rejected()
 def test_hero_count_inflates_card_count(self):self.replace(self.home,'class="hero-product"','class="hero-product product-card"');self.rejected()
 def test_directory_card_missing(self):self.regex(self.directory,r'<a class="page-card".*?</a>','');self.rejected()
 def test_directory_card_duplicate(self):self.regex(self.directory,r'<a class="page-card".*?</a>',lambda m:m[0]+m[0]);self.rejected()
 def test_home_card_missing(self):self.regex(self.home,r'<a class="page-card purpose-card".*?</a>','');self.rejected()
 def test_home_product_card_missing(self):self.regex(self.home,r'<article class="product-card".*?</article>','');self.rejected()
 def test_detail_product_card_duplicate(self):self.regex(self.detail,r'<article class="product-card".*?</article>',lambda m:m[0]+m[0]);self.rejected()
 def test_wrong_sku_card(self):self.replace(self.detail,'data-product-key="funeral-basic"','data-product-key="congrats-basic"');self.rejected()
 def test_product_description_missing(self):self.replace(self.detail,COMMON['productCards'][0]['description'],'');self.rejected()
 def test_product_photo_caption_missing(self):self.replace(self.detail,COMMON['productCards'][0]['photoCaption'],'');self.rejected()
 def test_product_image_bytes(self):
  p=self.root/'dist/images/products/B201.jpg';p.write_bytes(p.read_bytes()+b'mutated');self.rejected()
 def test_product_public_image_bytes(self):
  p=self.root/'public/images/products/C204.jpg';p.write_bytes(p.read_bytes()+b'mutated');self.rejected()
 def test_wrong_image_dimensions(self):self.replace(self.detail,'width="500" height="500"','width="500" height="499"');self.rejected()
 def test_hidden_image(self):self.replace(self.detail,'<img src="/images/products/B201.jpg"','<img hidden src="/images/products/B201.jpg"');self.rejected()
 def test_duplicate_image(self):self.regex(self.detail,r'<img src="/images/products/B201.jpg"[^>]*>',lambda m:m[0]+m[0]);self.rejected()
 def test_missing_image(self):self.regex(self.detail,r'<img src="/images/products/B201.jpg"[^>]*>','');self.rejected()
 def test_wrong_image_sku(self):self.replace(self.detail,'src="/images/products/B201.jpg"','src="/images/products/B203.jpg"');self.rejected()
 def test_unapproved_image(self):self.replace(self.detail,'src="/images/products/B201.jpg"','src="https://example.com/ai.jpg"');self.rejected()
 def test_banner_missing(self):self.regex(self.home,r'<figure class="shared-flower-banner"[^>]*data-shared-flower-banner="budget".*?</figure>','');self.rejected()
 def test_banner_duplicate(self):self.regex(self.home,r'<figure class="shared-flower-banner"[^>]*data-shared-flower-banner="budget".*?</figure>',lambda m:m[0]+m[0]);self.rejected()
 def test_banner_wrong_variant(self):self.replace(self.home,'data-shared-flower-banner="message"','data-shared-flower-banner="budget"');self.rejected()
 def test_banner_wrong_bytes(self):
  p=self.root/'dist/images/shared-banners/flower-budget.webp';p.write_bytes(p.read_bytes()+b'changed');self.rejected()
 def test_banner_alt_missing(self):self.replace(self.home,'alt="'+AMENDMENT['assets']['message']['alt']+'"','');self.rejected()
 def test_removed_banner_caption_reintroduced(self):self.replace(self.home,'</figure>','<figcaption>'+COMMON['banners']['caption']+'</figcaption></figure>');self.rejected()
 def test_removed_caption_reintroduced_outside_banner(self):self.replace(self.home,'</main>','<p>'+COMMON['banners']['caption']+'</p></main>');self.rejected()
 def test_unapproved_banner_caption(self):self.replace(self.home,'</figure>','<figcaption>1844-0644</figcaption></figure>');self.rejected()
 def test_banner_phone_alt_missing(self):self.replace(self.home,AMENDMENT['assets']['message']['alt'],AMENDMENT['assets']['message']['alt'].replace('1844-0644',''));self.rejected()
 def test_banner_amendment_missing(self):(self.root/'src/data/common-banner-phone-amendment.json').unlink();self.rejected()
 def test_banner_amendment_bytes(self):
  p=self.root/'src/data/common-banner-phone-amendment.json';p.write_text(p.read_text()+' ');self.rejected()
 def test_banner_amendment_product_scope_expansion(self):
  self.data('common-banner-phone-amendment',lambda a:a.update(productPhotosChanged=True));self.rejected()
 def test_banner_public_bytes(self):
  p=self.root/'public/images/shared-banners/flower-consultation.webp';p.write_bytes(p.read_bytes()+b'changed');self.rejected()
 def test_banners_adjacent(self):
  p=self.root/self.home;s=p.read_text();pattern=r'<figure class="shared-flower-banner"[^>]*data-shared-flower-banner="budget".*?</figure>';banner=re.search(pattern,s,re.S)[0];s=s.replace(banner,'');s=re.sub(r'(<figure class="shared-flower-banner"[^>]*data-shared-flower-banner="message".*?</figure>)',lambda m:m[0]+banner,s,count=1,flags=re.S);p.write_text(s);self.rejected()
 def test_directory_banner_forbidden(self):
  banner=re.search(r'<figure class="shared-flower-banner".*?</figure>',(self.root/self.home).read_text(),re.S)[0];self.replace(self.directory,'</main>',banner+'</main>');self.rejected()
 def test_404_banner_forbidden(self):
  banner=re.search(r'<figure class="shared-flower-banner".*?</figure>',(self.root/self.home).read_text(),re.S)[0];self.replace('dist/404.html','</main>',banner+'</main>');self.rejected()
 def test_unapproved_unassigned_section(self):self.replace(self.directory,'</main>','<section data-district-unassigned></section></main>');self.rejected()
 def test_admin_facility_assignment_html(self):self.regex(self.directory,r'(<li data-administrative-unit="[^"]+"[^>]*>)',lambda m:m[0]+'<a href="/regions/seocho-funeral-wreath/#seoul-st-mary-funeral">서울성모장례식장의 빈소 안내</a>');self.rejected()
 def test_wrong_admin_legal_html(self):self.replace(self.directory,'data-administrative-unit="seoul-seocho-gu/admin/1165051000"','data-administrative-unit="seoul-seocho-gu/admin/1165058000"');self.rejected()
 def test_namhyeon_facility_fabrication(self):self.replace(self.directory,'data-facility-legal-unit="서초구/법정동/반포동"','data-facility-legal-unit="서초구/법정동/잠원동"');self.rejected()
 def test_404_title_h1_conflation(self):self.replace('dist/404.html',COMMON['notFound']['h1'],COMMON['notFound']['title']);self.rejected()
 def test_404_canonical_forbidden(self):self.replace('dist/404.html','</head>','<link rel="canonical" href="https://seoul-seocho.local.invalid/404.html"></head>');self.rejected()
 def test_404_social_forbidden(self):self.replace('dist/404.html','</head>','<meta property="og:title" content="꽃이랑"></head>');self.rejected()
 def test_404_schema_forbidden(self):self.replace('dist/404.html','</head>','<script type="application/ld+json">{}</script></head>');self.rejected()
 def test_404_home_link_wrong(self):self.replace('dist/404.html','href="/">'+COMMON['notFound']['homeLabel'],'href="https://fwith.co.kr/">'+COMMON['notFound']['homeLabel']);self.rejected()
 def test_preview_robots(self):
  old,new=('index,follow','noindex,nofollow,noarchive') if RELEASE_MODE['indexable'] else ('noindex,nofollow,noarchive','index,follow')
  self.replace(self.detail,old,new);self.rejected()
 def test_preview_sitemap_not_empty(self):
  (self.root/'dist/sitemap-mutated.xml').write_text('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>https://seoul-seocho.local.invalid/regions/</loc></url></urlset>');self.rejected()
 def test_extra_seller_facility_address_schema(self):self.replace(self.home,'"@type":"Florist"','"@type":"Florist","address":"서울특별시 관악구 시흥대로572 B1"');self.rejected()
 def test_source_extra(self):self.replace(self.detail,'class="source-references"','class="source-references"');self.regex(self.detail,r'(<section class="source-references"[^>]*>)',lambda m:m[0]+'<a href="https://fwith.co.kr/">꽃이랑 공식몰</a>');self.rejected()
 def test_duplicate_primary_cta(self):
  c=ARTICLES[0]['primaryCta'];self.replace(self.detail,'</main>',f'<a href="{c["href"]}">{c["label"]}</a></main>');self.rejected()
 def test_missing_primary_cta(self):self.replace(self.detail,ARTICLES[0]['primaryCta']['label'],'');self.rejected()
 def test_missing_related_link(self):self.replace(self.detail,ARTICLES[0]['relatedLink']['label'],'');self.rejected()
 def test_whole_body_double_rendered(self):
  body=''.join('<p>'+p+'</p>' for sec in ARTICLES[0]['sections'] for p in sec['paragraphs']);self.replace(self.detail,'</main>',body+'</main>');self.rejected()
 def test_source_h2_regression(self):self.regex(self.detail,r'(<section class="source-card"[^>]*>)<h3>',lambda m:m[1]+'<h2>');self.rejected()
 def test_source_section_h2_missing(self):self.replace(self.detail,'<h2 id="source-references-title">','<h3 id="source-references-title">');self.rejected()
 def test_unapproved_visible_verified_at(self):self.replace(self.detail,'</main>','<time datetime="2026-10-13">2026-10-13</time></main>');self.rejected()
 def test_missing_breadcrumb_aria(self):self.replace(self.detail,'aria-label="현재 위치"','aria-label=""');self.rejected()
 def test_duplicate_paragraph_in_unmarked_span(self):self.replace(self.detail,'</main>','<span>'+ARTICLES[0]['sections'][0]['paragraphs'][0]+'</span></main>');self.rejected()
 def test_duplicate_faq_without_marker(self):self.replace(self.detail,'</main>','<p>'+ARTICLES[0]['faq'][0]['answer']+'</p></main>');self.rejected()
 def test_extra_product_image_outside_card(self):self.replace(self.detail,'</main>','<img src="/images/products/B201.jpg" alt="'+COMMON['productCards'][0]['imageAlt']+'" width="500" height="500"></main>');self.rejected()
 def test_duplicate_html_alt_attribute(self):self.replace(self.detail,'alt="'+COMMON['productCards'][0]['imageAlt']+'"','alt="'+COMMON['productCards'][0]['imageAlt']+'" alt="'+COMMON['productCards'][0]['imageAlt']+'"');self.rejected()
 def test_executable_script_injection(self):self.replace(self.detail,'</main>','<script>alert(1)</script></main>');self.rejected()
 def test_external_script_injection(self):self.replace(self.detail,'</main>','<script src="https://example.com/script.js"></script></main>');self.rejected()
 def test_inline_event_handler(self):self.replace(self.detail,'<h1>','<h1 onclick="alert(1)">');self.rejected()
 def test_iframe_injection(self):self.replace(self.detail,'</main>','<iframe src="https://example.com/"></iframe></main>');self.rejected()
 def test_source_unsafe_url(self):self.replace(self.detail,'href="'+html.escape(ARTICLES[0]['sourceLinks'][0]['url'],quote=True)+'"','href="javascript:alert(1)"');self.rejected()
 def test_source_raw_html(self):
  label=ARTICLES[0]['sourceLinks'][0]['name'];self.replace(self.detail,'>'+label+'</a>','><b>'+label+'</b></a>');self.rejected()
 def test_source_aria_label(self):self.replace(self.detail,'aria-label="'+ARTICLES[0]['sourceLinks'][0]['name']+'"','aria-label="꽃이랑"');self.rejected()
 def test_source_type_attribute(self):self.replace(self.detail,'data-source-type="official"','data-source-type="unverified"');self.rejected()
 def test_source_name_attribute(self):self.replace(self.detail,'data-source-name="'+ARTICLES[0]['sourceLinks'][0]['name']+'"','data-source-name="꽃이랑"');self.rejected()
 def test_source_verified_at_attribute(self):self.replace(self.detail,'data-source-verified-at="2026-10-13"','data-source-verified-at="2026-10-01"');self.rejected()
 def test_og_alt_drift(self):self.regex(self.detail,r'(<meta property="og:image:alt" content=")[^"]*',lambda m:m[1]+'wrong photo');self.rejected()
 def test_twitter_alt_drift(self):self.regex(self.detail,r'(<meta name="twitter:image:alt" content=")[^"]*',lambda m:m[1]+'wrong photo');self.rejected()
 def test_home_hero_base_price_label_missing(self):self.replace(self.home,'<strong>기본가격 59,000원</strong>','<strong>59,000원</strong>');self.rejected()
 def test_detail_hero_base_price_label_missing(self):self.replace(self.detail,'<span>기본가격 59,000원</span>','<span>59,000원</span>');self.rejected()
 def test_home_primary_cta_duplicate(self):
  c=COMMON['home']['phoneCta'];self.replace(self.home,'</main>',f'<a href="{c["href"]}">{c["label"]}</a></main>');self.rejected()
 def test_general_directory_link_missing(self):self.replace(self.directory,COMMON['directory']['generalLinkLabels']['funeral'],'');self.rejected()
 def test_directory_facility_candidate_attribute(self):self.replace(self.directory,'data-candidate-id="seoul-st-mary-funeral"','data-candidate-id="seocho-opening-occasion"');self.rejected()
 def test_shared_policy_duplicate(self):self.replace(self.detail,'</main>','<p>'+COMMON['sharedNotices']['materials']+'</p></main>');self.rejected()

# Every full approved paragraph is independently removed and duplicated. This
# ensures a gate cannot pass by checking only selected snippets or total length.
for article in ARTICLES:
 path='dist'+article['url']+'index.html'
 for section in article['sections']:
  for index,text in enumerate(section['paragraphs']):
   for mode in ['missing','duplicate']:
    def method(self,path=path,text=text,mode=mode):
     old='<p>'+html.escape(text,quote=False)+'</p>';self.replace(path,old,'' if mode=='missing' else old+old);self.rejected()
    setattr(SeochoMutations,f'test_paragraph_{article["id"]}_{section["id"].replace("-","_")}_{index}_{mode}',method)
 for index,entry in enumerate(article['faq']):
  for field in ['question','answer']:
   for mode in ['missing','duplicate']:
    def method(self,path=path,text=entry[field],field=field,mode=mode):
     tag='h3' if field=='question' else 'p';pattern=r'<'+tag+r' data-faq-'+field+r'[^>]*>'+re.escape(html.escape(text,quote=False))+r'</'+tag+'>'
     self.regex(path,pattern,'' if mode=='missing' else lambda m:m[0]+m[0]);self.rejected()
    setattr(SeochoMutations,f'test_faq_{article["id"]}_{index}_{field}_{mode}',method)
 for index,source in enumerate(article['sourceLinks']):
  for mode in ['missing','duplicate']:
   def method(self,path=path,source=source,mode=mode):
    pattern=r'<a href="'+re.escape(html.escape(source['url'],quote=True))+r'"[^>]*>'+re.escape(html.escape(source['name'],quote=False))+r'</a>'
    self.regex(path,pattern,'' if mode=='missing' else lambda m:m[0]+m[0]);self.rejected()
   setattr(SeochoMutations,f'test_source_{article["id"]}_{index}_{mode}',method)
for product in COMMON['productCards']:
 for mode in ['price','alt','cta']:
  def method(self,product=product,mode=mode):
   path=self.detail if product['sku'].startswith('B') else self.celebration
   if mode=='price':self.replace(path,'<strong>'+product['priceLabel']+'</strong>','<strong>기본가격 1원</strong>')
   elif mode=='alt':self.replace(path,'alt="'+product['imageAlt']+'"','alt=""')
   else:
    # Replace only a product-card CTA, preserving hero/source links.
    self.regex(path,r'(<article class="product-card"[^>]*data-product-sku="'+product['sku']+r'".*?href=")'+re.escape(product['cta']['href']),lambda m:m[1]+'https://fwith.co.kr/')
   self.rejected()
  setattr(SeochoMutations,f'test_product_{product["sku"]}_{mode}',method)

RUNTIME_MUTATIONS={
 'copy_article':('seocho-copy',lambda x:x['articles'][0].__setitem__('h1','changed')),
 'copy_common':('seocho-copy',lambda x:x['common']['home'].__setitem__('intro','changed')),
 'page_paragraph':('pages',lambda x:x[0]['sections'][0]['paragraphs'].pop()),
 'page_missing':('pages',lambda x:x.pop()),
 'page_duplicate':('pages',lambda x:x.append(copy.deepcopy(x[0]))),
 'page_candidate':('pages',lambda x:x[0].__setitem__('candidateIds',['seocho-arthall'])),
 'page_intent':('pages',lambda x:x[0].__setitem__('intentKey','seocho-celebration-purchase')),
 'page_facility_unit':('pages',lambda x:x[0]['facilityAnchors'][0].__setitem__('unitKey','서초구/법정동/잠원동')),
 'page_occasion_facility':('pages',lambda x:x[1]['facilityAnchors'].append(copy.deepcopy(x[1]['buyerOccasionAnchors'][0]))),
 'price':('products',lambda x:x[0].__setitem__('price',1)),
 'sku':('products',lambda x:x[0].__setitem__('officialSku','C200')),
 'product_cta':('products',lambda x:x[0].__setitem__('orderUrl','https://fwith.co.kr/')),
 'n_expanded':('architecture',lambda x:next(h for h in x['hubs'] if h['category']=='regions').__setitem__('children',4)),
 'directory_indexable':('architecture',lambda x:next(h for h in x['hubs'] if h['category']=='regions').__setitem__('indexable',True)),
 'facility_wrong_unit':('region-coverage',lambda x:x['facilities'][0].__setitem__('unitKey','서초구/법정동/양재동')),
 'eltower_wrong_unit':('region-coverage',lambda x:x['facilities'][1].__setitem__('unitKey','서초구/법정동/방배동')),
 'facility_admin':('region-coverage',lambda x:x['facilities'][2].__setitem__('administrativeCode','1162058500')),
 'facility_candidate':('region-coverage',lambda x:x['facilities'][0].__setitem__('facilityKey','seocho-arthall')),
 'facility_missing':('region-coverage',lambda x:x['facilities'].pop()),
 'occasion_as_facility':('region-coverage',lambda x:x['facilities'].append(copy.deepcopy(x['buyerOccasions'][0]))),
 'occasion_geography':('region-coverage',lambda x:x['buyerOccasions'][0].__setitem__('unitKey','서초구/법정동/방배동')),
 'occasion_misclassification':('region-coverage',lambda x:x['buyerOccasions'][0].__setitem__('contextType','facility')),
 'relationship':('region-coverage',lambda x:x['administrativeCrosswalk'][0]['relations'][0].__setitem__('unitKey','서초구/법정동/방배동')),
 'legal_denominator':('region-coverage',lambda x:x['units'].pop()),
 'admin_denominator':('region-coverage',lambda x:x['administrativeCrosswalk'].pop()),
 'site_key':('site-config',lambda x:x.__setitem__('siteKey','seoul-yeongdeungpo-flower-direct')),
 'scope_key':('region-coverage',lambda x:x.__setitem__('scopeKey','wrong')),
 'publication':('site-config',lambda x:x.__setitem__('productionApproved',True)),
 'ownership':('site-config',lambda x:x.__setitem__('hostnameOwnershipVerified',True)),
}
RUNTIME_MUTATIONS.update({
 'held_decision_dropped':('seocho-plan-binding',lambda x:x['heldPageDecisions'].pop()),
 'candidate_group_dropped':('seocho-plan-binding',lambda x:x['candidateLedger'].pop()),
 'admin_assignment_list':('region-coverage',lambda x:x['administrativeFacilityAssignments'].append({'facilityKey':'eltower','administrativeCode':'1165065100'})),
 'relationship_23_to_22':('region-coverage',lambda x:x['administrativeCrosswalk'][-1]['relations'].pop()),
 'wrong_facility_address':('region-coverage',lambda x:x['facilities'][0].__setitem__('address','changed')),
})
for name,(file,change) in RUNTIME_MUTATIONS.items():
 def method(self,file=file,change=change):self.data(file,change);self.rejected()
 setattr(SeochoMutations,'test_runtime_'+name,method)

if __name__=='__main__':unittest.main(verbosity=2)
