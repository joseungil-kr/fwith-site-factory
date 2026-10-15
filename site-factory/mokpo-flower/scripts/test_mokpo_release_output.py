"""Production output mutations. Actual local files required; fixture revision is not remote evidence."""
import unittest,tempfile,shutil,re
from pathlib import Path
import mokpo_release_output as o
class OutputTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)/'dist';shutil.copytree(Path(__file__).resolve().parents[1]/'dist',self.root)
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
 def test_proof_bytes(self):(self.root/o.PROOF['path'].lstrip('/')).write_text('altered\n');self.reject()
 def test_symlink(self):
  p=self.root/'favicon.svg';p.unlink();p.symlink_to(self.root/'robots.txt');self.reject()
if __name__=='__main__':unittest.main(verbosity=2)
