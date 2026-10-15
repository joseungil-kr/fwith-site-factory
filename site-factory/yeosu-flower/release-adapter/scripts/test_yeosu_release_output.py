"""Production output mutations. Actual local files required; fixture revision is not remote evidence."""
import unittest,tempfile,shutil,re
from pathlib import Path
import yeosu_release_output as o
class OutputTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)/'dist';shutil.copytree(Path(__file__).resolve().parents[2]/'portable/yeosu-portable-build-inputs-20261015/yeosu-local-implementation-20261015/candidate/dist',self.root)
  text=(self.root/'index.html').read_text();m=re.search(r'<meta name="site-factory-revision" content="([0-9a-f]{40})">',text);self.assertIsNotNone(m,'Build production first');self.mode=dict(mode='production',indexable=True,origin=o.ORIGIN,revision=m.group(1))
 def check(self):return o.inspect_dist(self.root,self.mode)
 def edit(self,name,old,new):
  p=self.root/name;s=p.read_text();self.assertIn(old,s);p.write_text(s.replace(old,new,1))
 def reject(self):
  with self.assertRaises(AssertionError):self.check()
 def test_actual_output(self):self.assertEqual(self.check()['htmlFiles'],4)
 def test_extra_html(self):(self.root/'extra.html').write_text('');self.reject()
 def test_extra_asset(self):(self.root/'extra.txt').write_text('');self.reject()
 def test_missing_main_focus(self):self.edit('index.html',' tabindex="-1"','');self.reject()
 def test_wrong_main_focus(self):self.edit('index.html','tabindex="-1"','tabindex="0"');self.reject()
 def test_home_noindex(self):self.edit('index.html','content="index,follow"','content="noindex,follow"');self.reject()
 def test_support_index(self):self.edit('regions/index.html','content="noindex,follow"','content="index,follow"');self.reject()
 def test_404_canonical(self):self.edit('404.html','</head>','<link rel="canonical" href="'+o.ORIGIN+'/404.html"></head>');self.reject()
 def test_404_social(self):self.edit('404.html','</head>','<meta property="og:title" content="extra"></head>');self.reject()
 def test_foreign_canonical(self):self.edit('index.html','rel="canonical" href="'+o.ORIGIN,'rel="canonical" href="https://wrong.invalid');self.reject()
 def test_foreign_og_url(self):self.edit('index.html','property="og:url" content="'+o.ORIGIN,'property="og:url" content="https://wrong.invalid');self.reject()
 def test_duplicate_robots(self):self.edit('index.html','</head>','<meta name="robots" content="index,follow"></head>');self.reject()
 def test_revision(self):self.edit('index.html',self.mode['revision'],'f'*40);self.reject()
 def test_support_sitemap(self):self.edit('sitemap-0.xml','</urlset>','<url><loc>'+o.ORIGIN+'/regions/</loc></url></urlset>');self.reject()
 def test_missing_article_sitemap(self):self.edit('sitemap-0.xml',o.ORIGIN+o.ROUTES[1],o.ORIGIN+'/regions/');self.reject()
 def test_sitemap_cycle(self):self.edit('sitemap-index.xml','sitemap-0.xml','sitemap-index.xml');self.reject()
 def test_foreign_sitemap(self):self.edit('sitemap-index.xml',o.ORIGIN,'https://wrong.invalid');self.reject()
 def test_orphan_xml(self):(self.root/'orphan.xml').write_text('<urlset/>');self.reject()
 def test_robots_block(self):(self.root/'robots.txt').write_text('User-agent: *\nDisallow: /\n');self.reject()
 def test_global_noindex(self):(self.root/'_headers').write_text('/*\n X-Robots-Tag: noindex\n');self.reject()
 def test_response_refresh_redirect(self):(self.root/'_headers').write_text('/*\n Refresh: 0; url=https://wrong.invalid\n');self.reject()
 def test_arbitrary_response_header(self):(self.root/'_headers').write_text('/*\n X-Content-Type-Options: nosniff\n');self.reject()
 def mutate_social(self,mode):
  keys=['og:image','og:image:alt','twitter:card','twitter:title','twitter:description','twitter:image','twitter:image:alt']
  for name in ['index.html','regions/index.html','regions/yeosu-jeonnam-hospital-funeral-wreath/index.html']:
   target=self.root/name;raw=target.read_text()
   for key in keys:
    with self.subTest(mode=mode,path=name,key=key):
     pattern=r'<meta '+('property' if key.startswith('og:') else 'name')+'="'+key+r'" content="[^"]*">'
     matches=re.findall(pattern,raw);self.assertEqual(len(matches),1);tag=matches[0]
     replacement='' if mode=='missing' else tag+tag if mode=='duplicate' else re.sub(r'content="[^"]*"','content="wrong"',tag)
     try:target.write_text(raw.replace(tag,replacement,1));self.reject()
     finally:target.write_text(raw)
 def test_missing_social_fields(self):self.mutate_social('missing')
 def test_duplicate_social_fields(self):self.mutate_social('duplicate')
 def test_changed_social_fields(self):self.mutate_social('changed')
 def test_foreign_social_images(self):
  for attr,key in [('property','og:image'),('name','twitter:image')]:
   target=self.root/'index.html';raw=target.read_text()
   try:self.edit('index.html',attr+'="'+key+'" content="'+o.ORIGIN,attr+'="'+key+'" content="https://wrong.invalid');self.reject()
   finally:target.write_text(raw)
 def test_missing_social_asset(self):(self.root/'images/products/B201.jpg').unlink();self.reject()
 def test_404_twitter(self):self.edit('404.html','</head>','<meta name="twitter:card" content="summary"></head>');self.reject()
 def test_wrong_social_attribute(self):self.edit('index.html','name="twitter:card"','property="twitter:card"');self.reject()
 def test_dual_or_extra_social_attributes(self):
  for old,new in [('property="og:title"','property="og:title" name="twitter:site"'),('name="twitter:card"','name="twitter:card" property="unrelated"'),('name="twitter:card"','name="twitter:card" data-extra="unapproved"')]:
   target=self.root/'index.html';raw=target.read_text()
   with self.subTest(new=new):
    try:self.edit('index.html',old,new);self.reject()
    finally:target.write_text(raw)
 def test_hidden_unapproved_social_namespace(self):self.edit('index.html','</head>','<meta property="unrelated" name="twitter:site" content="@invented"></head>');self.reject()
 def test_unapproved_social_account(self):self.edit('index.html','</head>','<meta name="twitter:site" content="@invented"></head>');self.reject()
 def test_proof_bytes(self):(self.root/o.PROOF['path'].lstrip('/')).write_text('altered\n');self.reject()
 def test_symlink(self):
  p=self.root/'favicon.svg';p.unlink();p.symlink_to(self.root/'robots.txt');self.reject()
if __name__=='__main__':unittest.main(verbosity=2)
