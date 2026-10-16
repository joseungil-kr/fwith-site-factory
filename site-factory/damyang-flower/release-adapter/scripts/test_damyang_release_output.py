"""Production output mutations. Actual local files required; fixture revision is not remote evidence."""
import unittest,tempfile,shutil,re
from pathlib import Path
import damyang_release_output as o
import damyang_adapter as adapter
class OutputTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)/'dist';adapter.inspect_output(adapter.CANDIDATE/'dist',self.root)
  text=(self.root/'index.html').read_text();m=re.search(r'<meta name="site-factory-revision" content="(local-inspection)">',text);self.assertIsNotNone(m,'Build production first');self.mode=dict(mode='offline-inspection',indexable=True,origin=o.ORIGIN,revision=m.group(1))
 def check(self):return o.inspect_dist(self.root,self.mode)
 def edit(self,name,old,new):
  p=self.root/name;s=p.read_text();self.assertIn(old,s);p.write_text(s.replace(old,new,1))
 def reject(self):
  with self.assertRaises(AssertionError):self.check()
 def test_offline_marker_cannot_authorize_production(self):
  self.mode.update(mode='production',revision='local-inspection');self.reject()
 def test_actual_output(self):self.assertEqual(self.check()['htmlFiles'],2)
 def test_extra_html(self):(self.root/'extra.html').write_text('');self.reject()
 def test_extra_asset(self):(self.root/'extra.txt').write_text('');self.reject()
 def test_missing_main_focus(self):self.edit('index.html',' tabindex="-1"','');self.reject()
 def test_wrong_main_focus(self):self.edit('index.html','tabindex="-1"','tabindex="0"');self.reject()
 def test_home_noindex(self):self.edit('index.html','content="index,follow"','content="noindex,follow"');self.reject()
 def test_404_index(self):self.edit('404.html','content="noindex,follow"','content="index,follow"');self.reject()
 def test_404_canonical(self):self.edit('404.html','</head>','<link rel="canonical" href="'+o.ORIGIN+'/404.html"></head>');self.reject()
 def test_404_social(self):self.edit('404.html','</head>','<meta property="og:title" content="extra"></head>');self.reject()
 def test_foreign_canonical(self):self.edit('index.html','rel="canonical" href="'+o.ORIGIN,'rel="canonical" href="https://wrong.invalid');self.reject()
 def test_foreign_og_url(self):self.edit('index.html','property="og:url" content="'+o.ORIGIN,'property="og:url" content="https://wrong.invalid');self.reject()
 def test_duplicate_robots(self):self.edit('index.html','</head>','<meta name="robots" content="index,follow"></head>');self.reject()
 def test_revision(self):self.edit('index.html',self.mode['revision'],'f'*40);self.reject()
 def test_support_sitemap(self):self.edit('sitemap-0.xml','</urlset>','<url><loc>'+o.ORIGIN+'/regions/</loc></url></urlset>');self.reject()
 def test_missing_home_sitemap(self):self.edit('sitemap-0.xml',o.ORIGIN+'/',o.ORIGIN+'/regions/');self.reject()
 def test_empty_sitemap(self):
  p=self.root/'sitemap-0.xml';s=p.read_text();p.write_text(re.sub(r'<url>.*?</url>','',s));self.reject()
 def test_duplicate_home_sitemap(self):self.edit('sitemap-0.xml','</urlset>','<url><loc>'+o.ORIGIN+'/</loc></url></urlset>');self.reject()
 def test_404_sitemap(self):self.edit('sitemap-0.xml','</urlset>','<url><loc>'+o.ORIGIN+'/404.html</loc></url></urlset>');self.reject()
 def test_facility_html(self):
  p=self.root/'regions/suwan-funeral-wreath/index.html';p.parent.mkdir(parents=True);p.write_text('unapproved');self.reject()
 def test_regions_html(self):
  p=self.root/'regions/index.html';p.parent.mkdir(parents=True);p.write_text('unapproved');self.reject()
 def test_sitemap_cycle(self):self.edit('sitemap-index.xml','sitemap-0.xml','sitemap-index.xml');self.reject()
 def test_foreign_sitemap(self):self.edit('sitemap-index.xml',o.ORIGIN,'https://wrong.invalid');self.reject()
 def test_orphan_xml(self):(self.root/'orphan.xml').write_text('<urlset/>');self.reject()
 def test_robots_block(self):(self.root/'robots.txt').write_text('User-agent: *\nDisallow: /\n');self.reject()
 def test_global_noindex(self):(self.root/'_headers').write_text('/*\n X-Robots-Tag: noindex\n');self.reject()
 def test_redirect_header(self):(self.root/'_headers').write_text('/*\n  Refresh: 0; url=https://unreviewed.invalid/\n');self.reject()
 def test_unknown_header(self):(self.root/'_headers').write_text('/*\n  X-Unknown: injected\n');self.reject()
 def test_proof_bytes(self):(self.root/o.PROOF['path'].lstrip('/')).write_text('altered\n');self.reject()
 def test_symlink(self):
  p=self.root/'favicon.svg';p.unlink();p.symlink_to(self.root/'robots.txt');self.reject()
 def test_customer_body_text(self):self.edit('index.html','<body','<body data-unreviewed="true"');self.reject()
 def test_customer_body_claim(self):self.edit('index.html','</main>','<p>추가 배송 보장</p></main>');self.reject()
 def test_customer_body_hidden(self):self.edit('index.html','<main id="main-content"','<main hidden id="main-content"');self.reject()
 def test_title_changed(self):self.edit('index.html','<title>','<title>extra');self.reject()
 def test_description_changed(self):self.edit('index.html','name="description" content="','name="description" content="extra');self.reject()
 def test_extra_schema(self):self.edit('index.html','</head>','<script type="application/ld+json">{}</script></head>');self.reject()
 def test_css_bytes(self):
  p=next((self.root/'_astro').glob('*.css'));p.write_bytes(p.read_bytes()+b'body{display:none}');self.reject()
 def test_product_image_bytes(self):
  p=self.root/'images/products/B201.jpg';p.write_bytes(p.read_bytes()+b'tampered');self.reject()
 def test_banner_image_bytes(self):
  p=self.root/'images/shared-banners/flower-message.webp';p.write_bytes(p.read_bytes()+b'tampered');self.reject()
 def test_banner_alt(self):self.edit('index.html','alt="','alt="changed ');self.reject()
 def test_required_faq_missing(self):
  p=self.root/'index.html';s=p.read_text();self.assertIn('data-faq-question',s);p.write_text(s.replace('data-faq-question','data-faq-question hidden',1));self.reject()
 def test_wrong_product_cta(self):
  n='index.html';self.edit(n,'https://fwith.co.kr/shop/item.php?it_id=B201','https://fwith.co.kr/');self.reject()
 def test_twitter_card_missing(self):self.edit('index.html','<meta name="twitter:card" content="summary">','');self.reject()
 def test_twitter_card_wrong(self):self.edit('index.html','name="twitter:card" content="summary"','name="twitter:card" content="summary_large_image"');self.reject()
 def test_twitter_title_wrong(self):self.edit('index.html','name="twitter:title" content="','name="twitter:title" content="changed ');self.reject()
 def test_twitter_description_missing(self):
  p=self.root/'index.html';s=p.read_text();new,n=re.subn(r'<meta name="twitter:description" content="[^"]*">','',s);self.assertEqual(n,1);p.write_text(new);self.reject()
 def test_twitter_image_foreign(self):self.edit('index.html','name="twitter:image" content="'+o.ORIGIN,'name="twitter:image" content="https://wrong.invalid');self.reject()
 def test_twitter_image_missing(self):
  p=self.root/'index.html';s=p.read_text();new,n=re.subn(r'<meta name="twitter:image" content="[^"]*">','',s);self.assertEqual(n,1);p.write_text(new);self.reject()
 def test_twitter_duplicate(self):self.edit('index.html','</head>','<meta name="twitter:card" content="summary"></head>');self.reject()
 def test_og_image_missing(self):
  p=self.root/'index.html';s=p.read_text();new,n=re.subn(r'<meta property="og:image" content="[^"]*">','',s);self.assertEqual(n,1);p.write_text(new);self.reject()
 def test_og_image_dimensions(self):self.edit('index.html','property="og:image:width" content="500"','property="og:image:width" content="1774"');self.reject()
 def test_social_alt_wrong(self):self.edit('index.html','name="twitter:image:alt" content="','name="twitter:image:alt" content="wrong ');self.reject()
 def test_404_twitter(self):self.edit('404.html','</head>','<meta name="twitter:card" content="summary"></head>');self.reject()
 def test_home_twitter_missing(self):
  n='index.html';self.edit(n,'<meta name="twitter:card" content="summary">','');self.reject()
 def test_og_type_missing(self):self.edit('index.html','<meta property="og:type" content="website">','');self.reject()
 def test_og_locale_missing(self):self.edit('index.html','<meta property="og:locale" content="ko_KR">','');self.reject()
 def test_unknown_social_tag(self):self.edit('index.html','</head>','<meta property="og:video" content="https://wrong.invalid/x"></head>');self.reject()
 def test_og_image_height(self):self.edit('index.html','property="og:image:height" content="500"','property="og:image:height" content="887"');self.reject()
 def test_404_product_card(self):self.edit('404.html','</main>','<article data-product-sku="B201">unreviewed</article></main>');self.reject()
 def test_404_banner(self):self.edit('404.html','</main>','<figure data-shared-flower-banner="message"></figure></main>');self.reject()
class IndexNowFixtureTests(unittest.TestCase):
 def test_one_home_payload(self):
  payload=o.indexnow_payload([o.ORIGIN+'/']);self.assertEqual(payload['urlList'],[o.ORIGIN+'/']);self.assertEqual(payload['keyLocation'],o.ORIGIN+o.PROOF['path']);self.assertEqual(payload['host'],'damyang.fwith.kr')
 def test_empty_extra_duplicate_foreign_404_and_nonlist_fail_closed(self):
  for value in [[],[o.ORIGIN+'/',o.ORIGIN+'/regions/'],[o.ORIGIN+'/',o.ORIGIN+'/'],['https://wrong.invalid/'],[o.ORIGIN+'/404.html'],(o.ORIGIN+'/',),None]:
   with self.subTest(value=value),self.assertRaises(AssertionError):o.indexnow_payload(value)
 def test_foreign_proof_fails(self):
  with self.assertRaises(AssertionError):o.indexnow_payload([o.ORIGIN+'/'],{**o.PROOF,'origin':'https://wrong.invalid'})

if __name__=='__main__':unittest.main(verbosity=2)
