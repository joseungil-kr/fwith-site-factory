#!/usr/bin/env python3
import unittest,tempfile,shutil,os,json
from pathlib import Path
from unittest.mock import patch
from qa_shared_banners import inspect
class SharedBannerNegativeTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.source=Path.cwd();import re
  self.origin=re.search(r'<link rel="canonical" href="([^"]+)"',(self.source/'dist/index.html').read_text()).group(1).rstrip('/')
  shutil.copytree(self.source/'dist',self.root/'dist');(self.root/'src/data').mkdir(parents=True)
  shutil.copy2(self.source/'src/data/shared-banner-manifest.json',self.root/'src/data/shared-banner-manifest.json')
  shutil.copytree(Path(os.environ['SHARED_BANNER_REFERENCE_DIST']),self.root/'reference-dist')
  shutil.copy2(Path(os.environ['SHARED_BANNER_REFERENCE_MANIFEST']),self.root/'reference.json')
  self.env={'SITE_URL':self.origin,'SITE_INDEXABLE':os.environ['SITE_INDEXABLE'],'SHARED_BANNER_REFERENCE_DIST':str(self.root/'reference-dist'),'SHARED_BANNER_REFERENCE_MANIFEST':str(self.root/'reference.json')}
  shutil.copytree(Path(os.environ['SHARED_BANNER_PREVIEW_REFERENCE_DIST']),self.root/'preview-reference-dist')
  shutil.copy2(Path(os.environ['SHARED_BANNER_PREVIEW_REFERENCE_MANIFEST']),self.root/'preview-reference.json')
  self.env.update(SHARED_BANNER_PREVIEW_REFERENCE_DIST=str(self.root/'preview-reference-dist'),SHARED_BANNER_PREVIEW_REFERENCE_MANIFEST=str(self.root/'preview-reference.json'))
 def tearDown(self):self.temp.cleanup()
 def check(self):
  with patch.dict(os.environ,self.env):return inspect(self.root)
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
 def preview(self):
  import re
  from qa_shared_banners import Page
  self.env['SITE_INDEXABLE']='false'
  for p in (self.root/'dist').rglob('*.html'):
   reference=Page();reference.feed((self.root/'preview-reference-dist'/p.relative_to(self.root/'dist')).read_text())
   p.write_text(re.sub(r'(name="robots" content=")[^"]+',lambda m:m.group(1)+reference.robots_values[0],p.read_text()))
 def test_preview_preserves_reference_exclusions(self):
  self.preview();result=self.check()
  self.assertEqual(sum(len(x['bannerKinds']) for x in result['files']),3*sum(not row['errorPage'] and row['path'] not in [('/' if name=='index.html' else '/'+name.removesuffix('index.html')) for name in result['productionReference']['excludedHtml']] for row in result['files']))
 def test_preview_missing_eligible_banner_fails(self):
  self.preview();import re;p=self.root/'dist/index.html'
  p.write_text(re.sub(r'<figure class="shared-flower-banner"[^>]*>.*?</figure>','',p.read_text(),count=1))
  with self.assertRaises(AssertionError):self.check()
 def production_projection(self):
  import re
  from qa_shared_banners import Page
  origin=os.environ['SHARED_BANNER_REFERENCE_ORIGIN'];self.env.update(SITE_INDEXABLE='true',SITE_URL=origin)
  for p in (self.root/'dist').rglob('*.html'):
   relative=p.relative_to(self.root/'dist');reference=Page();reference.feed((self.root/'reference-dist'/relative).read_text())
   s=re.sub(r'(name="robots" content=")[^"]+',lambda m:m.group(1)+reference.robots_values[0],p.read_text())
   s=re.sub(r'<link rel="canonical" href="[^"]+"[^>]*>',lambda m:'<link rel="canonical" href="'+reference.canonical[0]+'">' if reference.canonical else '',s)
   p.write_text(s)
 def test_production_arbitrary_noindex_fails(self):
  self.production_projection()
  import re
  p=self.root/'dist/index.html';raw=p.read_text();p.write_text(re.sub(r'(name="robots" content=")[^"]+',r'\1noindex,nofollow',raw))
  with self.assertRaises(AssertionError):self.check()
 def test_original_excluded_route_made_indexable_fails(self):
  self.production_projection()
  import re
  for p in (self.root/'dist').rglob('*.html'):
   if 'name="robots" content="noindex' in p.read_text():
    p.write_text(re.sub(r'(name="robots" content=")[^"]+',r'\1index,follow',p.read_text()));break
  else:self.fail('No intrinsic excluded hub')
  with self.assertRaises(AssertionError):self.check()
 def test_route_addition_fails(self):
  p=self.root/'dist/unapproved/index.html';p.parent.mkdir();shutil.copy2(self.root/'dist/index.html',p)
  with self.assertRaises(AssertionError):self.check()
 def test_route_deletion_fails(self):
  next(p for p in (self.root/'dist').rglob('index.html') if p != self.root/'dist/index.html').unlink()
  with self.assertRaises(AssertionError):self.check()
 def test_reference_html_mutation_fails(self):
  p=self.root/'reference-dist/index.html';p.write_text(p.read_text().replace('index,follow','noindex,follow'))
  with self.assertRaises(AssertionError):self.check()
 def test_reference_asset_mutation_fails(self):
  p=self.root/'reference-dist/favicon.svg';p.write_text(p.read_text()+' ')
  with self.assertRaises(AssertionError):self.check()
 def test_reference_route_addition_fails(self):
  shutil.copy2(self.root/'reference-dist/index.html',self.root/'reference-dist/unapproved.html')
  with self.assertRaises(AssertionError):self.check()
 def test_reference_manifest_mutation_fails(self):
  p=self.root/'reference.json';p.write_text(p.read_text()+' ')
  with self.assertRaises(AssertionError):self.check()
 def test_rehashed_reference_cannot_replace_trusted_artifact(self):
  import hashlib
  p=self.root/'reference-dist/index.html';p.write_text(p.read_text()+' ')
  m=self.root/'reference.json';d=json.loads(m.read_text());d['files']['index.html']=hashlib.sha256(p.read_bytes()).hexdigest();d['artifactManifestSha256']=hashlib.sha256(json.dumps(d['files'],sort_keys=True,separators=(',',':')).encode()).hexdigest();m.write_text(json.dumps(d))
  self.env['SHARED_BANNER_REFERENCE_MANIFEST_SHA256']=hashlib.sha256(m.read_bytes()).hexdigest()
  with self.assertRaises(AssertionError):self.check()
 def test_reference_symlink_fails(self):
  p=self.root/'reference-dist/fake.svg';p.symlink_to(self.root/'reference-dist/favicon.svg')
  with self.assertRaises(AssertionError):self.check()
 def test_candidate_symlink_fails(self):
  p=self.root/'dist/fake.svg';p.symlink_to(self.root/'dist/favicon.svg')
  with self.assertRaises(AssertionError):self.check()
 def insert_banner(self,target):
  import re
  banner=re.search(r'<figure class="shared-flower-banner"[^>]*>.*?</figure>',(self.root/'dist/index.html').read_text()).group(0)
  p=self.root/'dist'/target;p.write_text(p.read_text().replace('</main>',banner+'</main>'))
 def test_404_banner_fails(self):
  self.insert_banner('404.html')
  with self.assertRaises(AssertionError):self.check()
 def test_original_excluded_banner_fails(self):
  self.preview()
  from qa_shared_banners import production_reference
  with patch.dict(os.environ,self.env):rows,_=production_reference()
  target=next((name for name,row in rows.items() if row['excludeBanners'] and name!='404.html'),'404.html')
  self.insert_banner(target)
  with self.assertRaises(AssertionError):self.check()
 def test_duplicate_robots_fails(self):
  self.mutate('</head>','<meta name="robots" content="noindex,follow"></head>')
  with self.assertRaises(AssertionError):self.check()
 def test_preview_indexable_route_fails(self):
  self.preview();self.mutate('name="robots" content="noindex,nofollow,noarchive"','name="robots" content="index,follow"')
  with self.assertRaises(AssertionError):self.check()
 def test_invalid_phase_fails(self):
  self.env['SITE_INDEXABLE']='FALSE'
  with self.assertRaises(AssertionError):self.check()
 def test_encoded_separator_canonical_fails(self):
  self.mutate(f'rel="canonical" href="{self.origin}/"',f'rel="canonical" href="{self.origin}/%2f"')
  with self.assertRaises(AssertionError):self.check()
 def test_missing_reference_pin_fails(self):
  self.env['SHARED_BANNER_REFERENCE_MANIFEST_SHA256']=''
  with self.assertRaises(AssertionError):self.check()
 def test_404_canonical_drift_fails(self):
  import re
  p=self.root/'dist/404.html';s=p.read_text()
  if 'rel="canonical"' in s:s=re.sub(r'(<link rel="canonical" href=")[^"]+',r'\1https://wrong.example/404/',s)
  else:s=s.replace('</head>','<link rel="canonical" href="https://wrong.example/404/"/></head>')
  p.write_text(s)
  with self.assertRaises(AssertionError):self.check()
 def test_synthetic_production_policy_projection_passes(self):
  self.production_projection();self.assertGreater(self.check()['customerHtml'],0)
class ReproducedCanonicalBoundaries(unittest.TestCase):
 setUp=SharedBannerNegativeTests.setUp
 tearDown=SharedBannerNegativeTests.tearDown
 check=SharedBannerNegativeTests.check
 mutate=SharedBannerNegativeTests.mutate
 def test_canonical_case_and_ascii_token_forms_are_recognized(self):
  p=self.root/'dist/index.html';original=p.read_text()
  for rel in ['CANONICAL','Canonical','alternate canonical','canonical alternate','alternate\tCANONICAL']:
   p.write_text(original.replace('rel="canonical"','rel="'+rel+'"',1));self.check()
 def test_additional_case_or_token_canonical_is_not_ignored(self):
  p=self.root/'dist/index.html';original=p.read_text()
  for rel in ['CANONICAL','alternate canonical','canonical alternate']:
   p.write_text(original.replace('</head>','<link rel="'+rel+'" href="https://outside.example/"></head>',1))
   with self.assertRaises(AssertionError):self.check()
 def test_partial_rel_token_is_not_canonical(self):
  self.mutate('rel="canonical"','rel="canonical-extra"')
  with self.assertRaises(AssertionError):self.check()
 def test_raw_url_controls_are_rejected_before_urlsplit(self):
  p=self.root/'dist/index.html';original=p.read_text()
  for control in [' ','\x00','\t','\n','\r','\x7f']:
   for url in [control+self.origin+'/',self.origin+control+'/',self.origin+'/'+control]:
    p.write_text(original.replace('rel="canonical" href="'+self.origin+'/', 'rel="canonical" href="'+url,1))
    with self.subTest(url=repr(url)),self.assertRaises(AssertionError):self.check()
 def test_duplicate_attributes_are_rejected_before_dict(self):
  p=self.root/'dist/index.html';original=p.read_text()
  for before,after in [('name="robots" content="','name="robots" content="index,follow" content="'),('rel="canonical" href="','rel="canonical" href="https://outside.example/" href="'),('rel="canonical"','rel="alternate" REL="canonical"'),('alt="꽃이랑','ALT="Wrong" alt="꽃이랑')]:
   self.assertIn(before,original);p.write_text(original.replace(before,after,1))
   with self.assertRaises(AssertionError):self.check()
class UrlIdentityTests(unittest.TestCase):
 def test_utf8_only_representation_is_equivalent(self):
  from qa_shared_banners import url_identity
  self.assertEqual(url_identity('https://a.test/%ED%99%94%EC%84%B1/'),url_identity('https://a.test/화성/'))
 def test_encoded_space_remains_valid_while_raw_space_is_rejected(self):
  from qa_shared_banners import url_identity
  self.assertEqual(url_identity('https://a.test/a%20b/')[2],'/a b/')
  for url in [' https://a.test/','https://a.test/a b/']:
   with self.assertRaises(AssertionError):url_identity(url)
 def test_origin_query_fragment_exact_path_and_slash_remain_distinct(self):
  from qa_shared_banners import url_identity
  base=url_identity('https://a.test/화성/')
  for url in ['http://a.test/화성/','https://b.test/화성/','https://a.test/화성/?x=1','https://a.test/화성/#x','https://a.test/화성','https://a.test/다른/']:
   self.assertNotEqual(base,url_identity(url))
 def test_credentials_separators_double_encoding_malformed_and_invalid_utf8_fail(self):
  from qa_shared_banners import url_identity
  for url in ['https://user@a.test/','https://a.test/%2f','https://a.test/%2F','https://a.test/%5c','https://a.test/%00','https://a.test/%01','https://a.test/%7f','https://a.test/%252f','https://a.test/%25ED%2599%2594','https://a.test/%FF','https://a.test/%','https://a.test/%QZ']:
   with self.subTest(url=url),self.assertRaises((AssertionError,UnicodeDecodeError,ValueError)):url_identity(url)
class ExactOriginalPhaseReferenceTests(unittest.TestCase):
 setUp=SharedBannerNegativeTests.setUp
 tearDown=SharedBannerNegativeTests.tearDown
 check=SharedBannerNegativeTests.check
 # Inherit only setup and utility methods below; inherited base regressions remain in their own class.
 def test_original_preview_asset_mutation_fails(self):
  p=self.root/'preview-reference-dist/favicon.svg';p.write_text(p.read_text()+' ')
  with self.assertRaises(AssertionError):self.check()
 def test_original_preview_manifest_mutation_fails(self):
  p=self.root/'preview-reference.json';p.write_text(p.read_text()+' ')
  with self.assertRaises(AssertionError):self.check()
 def test_original_preview_route_removed_fails(self):
  (self.root/'preview-reference-dist/index.html').unlink()
  with self.assertRaises(AssertionError):self.check()
 def test_original_preview_rehash_cannot_replace_pinned_artifact(self):
  import hashlib
  p=self.root/'preview-reference-dist/index.html';p.write_text(p.read_text()+' ')
  m=self.root/'preview-reference.json';d=json.loads(m.read_text());d['files']['index.html']=hashlib.sha256(p.read_bytes()).hexdigest();d['artifactManifestSha256']=hashlib.sha256(json.dumps(d['files'],sort_keys=True,separators=(',',':')).encode()).hexdigest();m.write_text(json.dumps(d));self.env['SHARED_BANNER_PREVIEW_REFERENCE_MANIFEST_SHA256']=hashlib.sha256(m.read_bytes()).hexdigest()
  with self.assertRaises(AssertionError):self.check()
 def test_candidate_preview_origin_changed_fails(self):
  self.env['SITE_URL']='http://127.0.0.1:9999'
  with self.assertRaises(AssertionError):self.check()
 def test_original_preview_pin_missing_fails(self):
  self.env['SHARED_BANNER_PREVIEW_REFERENCE_ARTIFACT_SHA256']=''
  with self.assertRaises(AssertionError):self.check()
 def test_original_preview_symlink_fails(self):
  (self.root/'preview-reference-dist/fake.svg').symlink_to(self.root/'preview-reference-dist/favicon.svg')
  with self.assertRaises(AssertionError):self.check()
 def test_preview_robots_changed_to_another_noindex_value_fails(self):
  import re
  p=next((p for p in (self.root/'dist').rglob('index.html') if 'content="noindex,follow,max-image-preview:large"' in p.read_text()),self.root/'dist/index.html');p.write_text(re.sub(r'(name="robots" content=")[^"]+',r'\1noindex,nofollow',p.read_text()))
  with self.assertRaises(AssertionError):self.check()
 def test_merged_canonical_or_indexable_target_path_drift_fails(self):
  from qa_shared_banners import Page
  import re
  target=self.root/'dist/index.html'
  for p in (self.root/'dist').rglob('index.html'):
   doc=Page();doc.feed(p.read_text());route='/' if p==self.root/'dist/index.html' else '/'+str(p.relative_to(self.root/'dist')).removesuffix('index.html')
   if doc.canonical and doc.canonical[0]!=self.origin+route:target=p;break
  target.write_text(re.sub(r'(<link rel="canonical" href=")[^"]+',r'\1'+self.origin+'/not-an-original-path/',target.read_text()))
  with self.assertRaises(AssertionError):self.check()
if __name__=='__main__':unittest.main()
