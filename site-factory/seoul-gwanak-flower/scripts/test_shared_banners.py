#!/usr/bin/env python3
import unittest,tempfile,shutil,os,json
from pathlib import Path
from unittest.mock import patch
from qa_shared_banners import inspect
class SharedBannerNegativeTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.source=Path.cwd();import re
  self.origin=re.search(r'<link rel="canonical" href="([^"]+)"',(self.source/'dist/index.html').read_text()).group(1).rstrip('/')
  shutil.copytree(self.source/'dist',self.root/'dist');(self.root/'scripts').mkdir(parents=True);(self.root/'src/data').mkdir(parents=True)
  shutil.copy2(self.source/'src/data/architecture.json',self.root/'src/data/architecture.json')
  shutil.copy2(self.source/'src/data/shared-banner-manifest.json',self.root/'src/data/shared-banner-manifest.json')
  shutil.copy2(self.source/'src/data/common-banner-phone-amendment.json',self.root/'src/data/common-banner-phone-amendment.json')
 def tearDown(self):self.temp.cleanup()
 def check(self):
  with patch.dict(os.environ,{'SITE_URL':self.origin,'SITE_INDEXABLE':os.environ.get('SITE_INDEXABLE','false')}):return inspect(self.root)
 def mutate(self,old,new):
  p=self.root/'dist/index.html';s=p.read_text();self.assertIn(old,s);p.write_text(s.replace(old,new,1))
 def test_clean_html_passes(self):self.assertGreater(self.check()['customerHtml'],0)
 def test_wrong_variant_asset_fails(self):
  self.mutate('src="/images/shared-banners/flower-message.webp"','src="/images/shared-banners/flower-budget.webp"')
  with self.assertRaises(AssertionError):self.check()
 def test_foreign_canonical_fails(self):
  self.mutate(f'rel="canonical" href="{self.origin}/"','rel="canonical" href="https://wrong.fwith.kr/"')
  with self.assertRaises(AssertionError):self.check()
 def test_missing_actual_image_fails(self):
  (self.root/'dist/images/shared-banners/flower-budget.webp').unlink()
  with self.assertRaises(AssertionError):self.check()
 def test_mutated_manifest_pin_fails(self):
  p=self.root/'src/data/shared-banner-manifest.json';d=json.loads(p.read_text());d[0]['sha256']='0'*64;p.write_text(json.dumps(d))
  with self.assertRaises(AssertionError):self.check()
 def test_heading_skip_fails(self):
  self.mutate('<h2>','<h4>')
  with self.assertRaises(AssertionError):self.check()
 def test_image_has_no_alt_fails(self):
  p=self.root/'dist/index.html';s=p.read_text();start=s.index('<img src="/images/shared-banners/flower-message.webp"');end=s.index('>',start);tag=s[start:end];import re
  p.write_text(s[:start]+re.sub(r' alt="[^"]*"','',tag)+s[end:])
  with self.assertRaises(AssertionError):self.check()
 def test_extra_shared_image_outside_figure_fails(self):
  self.mutate('</main>','<img src="/images/shared-banners/flower-message.webp" alt="extra"/></main>')
  with self.assertRaises(AssertionError):self.check()
 def test_duplicate_one_banner_missing_another_fails(self):
  p=self.root/'dist/index.html';s=p.read_text();import re
  pattern=r'<img src="/images/shared-banners/flower-message.webp"[^>]*>'
  image=re.search(pattern,s).group(0);s=s.replace(image,image+image,1)
  s=re.sub(r'<img src="/images/shared-banners/flower-budget.webp"[^>]*>','',s,count=1);p.write_text(s)
  with self.assertRaises(AssertionError):self.check()
 def make_thin_listing(self,keep_banners=False):
  import re
  p=self.root/'dist/empty/index.html';p.parent.mkdir()
  html=(self.root/'dist/index.html').read_text().replace(f'rel="canonical" href="{self.origin}/"',f'rel="canonical" href="{self.origin}/empty/"')
  if not keep_banners:html=re.sub(r'<figure class="shared-flower-banner".*?</figure>','',html,flags=re.S)
  p.write_text(html)
  config=self.root/'src/data/architecture.json';data=json.loads(config.read_text());data['hubs'].append({'url':'/empty/','children':0});config.write_text(json.dumps(data))
 def test_thin_listing_has_no_banners_in_preview(self):
  self.make_thin_listing();self.assertFalse(next(r for r in self.check()['files'] if r['path']=='/empty/')['bannerKinds'])
 def test_banner_on_thin_listing_fails(self):
  self.make_thin_listing(keep_banners=True)
  with self.assertRaises(AssertionError):self.check()
 def test_banner_on_404_fails(self):
  import re
  banner=re.search(r'<figure class="shared-flower-banner".*?</figure>',(self.root/'dist/index.html').read_text(),re.S).group(0)
  p=self.root/'dist/404.html';p.write_text(p.read_text().replace('</main>',banner+'</main>',1))
  with self.assertRaises(AssertionError):self.check()
if __name__=='__main__':unittest.main()
