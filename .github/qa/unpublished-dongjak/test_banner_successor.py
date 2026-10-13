"""Offline successor regressions. Fixtures are not a build or saved Git evidence."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import copy, json, os, subprocess, unittest
from contextlib import contextmanager
import adapter,run_bound_capture
import test_adapter
from test_adapter import SOURCE

class BannerSuccessorTests(unittest.TestCase):
 def rows(self):return [adapter.load(adapter.HERE/'frozen-inputs'/name)for name in ('source-file-manifest.approved-before-banner.json','source-file-manifest.banner-phone.json')]
 def lineage(self):return adapter.load(adapter.HERE/'banner-successor-lineage.json')
 def expected(self):return adapter.expectations(SOURCE/adapter.SITE_PATH)
 def test_historical_lineage_and_upstream_unchanged(self):adapter.verify_source_lineage();adapter.verify_upstream()
 def test_exact_successor_manifest_and_local_bytes(self):
  adapter.verify_banner_successor();self.assertEqual(adapter.verify_frozen_bytes(SOURCE,allow_generated=True)['files'],642)
 def test_639_to_642_exact_13_modifications_3_additions(self):
  a,b=self.rows();l=self.lineage();self.assertTrue(adapter.validate_banner_successor(a,b,l));self.assertEqual(len(l['modifiedPaths']),13);self.assertEqual(len(l['addedPaths']),3)
 def test_unapproved_successor_source_identity_rejected(self):
  for key in ('currentSourceSha','sourceTree','repositoryTree','baseSourceSha','historicalQaSourceSha','immediateParentSourceSha'):
   a,b=self.rows();l=self.lineage();l[key]='a'*40
   with self.subTest(key=key),self.assertRaises(AssertionError):adapter.validate_banner_successor(a,b,l)
 def test_approval_and_host_boundaries(self):
  for key,value in [('sourceProductionApproved',False),('hostnameOwnershipVerified',True),('qaPublicationApproved',True),('qaIndexable',True),('captionMustBeAbsent',False),('expectedAltSuffix','wrong'),('phoneTextForIndependentPixelReview','1844-0000')]:
   a,b=self.rows();l=self.lineage();l[key]=value
   with self.subTest(key=key),self.assertRaises(AssertionError):adapter.validate_banner_successor(a,b,l)
 def test_missing_duplicate_extra_and_outside_source_files_rejected(self):
  a,b=self.rows()
  mutations=[b[:-1],b+[b[0]],b[:-1]+[b[0]]]
  outside=copy.deepcopy(b);outside[0]['path']='../escape';mutations.append(outside)
  extra=copy.deepcopy(b);extra[0]['path']=adapter.SITE_PATH+'/new-file';mutations.append(extra)
  for rows in mutations:
   with self.assertRaises(AssertionError):adapter.validate_banner_successor(a,rows,self.lineage())
 def test_changed_unrelated_original_bytes_rejected(self):
  a,b=self.rows();changed=set(self.lineage()['modifiedPaths'])
  next(e for e in b if e['path']not in changed)['sha256']='0'*64
  with self.assertRaises(AssertionError):adapter.validate_banner_successor(a,b,self.lineage())
 def test_symlink_submodule_and_unreviewed_modes_rejected(self):
  for mode in ('120000','160000','100755'):
   a,b=self.rows();target=next(e for e in b if e['path'].endswith('/src/data/site-config.json'));target['mode']=mode
   with self.subTest(mode=mode),self.assertRaises(AssertionError):adapter.validate_banner_successor(a,b,self.lineage())
 def test_frozen_file_and_parent_symlink_rejected(self):
  e=copy.deepcopy(adapter.frozen_entries()[0])
  for parent_link in (False,True):
   with TemporaryDirectory()as temp:
    root=Path(temp);path=root/e['path'];target=root/'outside';target.write_bytes(b'x')
    if parent_link:
     top=root/'site-factory';top.symlink_to(root,target_is_directory=True)
    else:path.parent.mkdir(parents=True);path.symlink_to(target)
    with patch.object(adapter,'frozen_entries',return_value=[e]),self.assertRaisesRegex(AssertionError,'Symlink'):adapter.verify_frozen_bytes(root)
 def test_native_guard_is_identical(self):
  path=SOURCE/adapter.SITE_PATH/'scripts/qa_browser_rendering.py';b=path.read_bytes()
  import hashlib
  self.assertEqual(hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest(),adapter.controls.NATIVE_BLOB)
 def facts(self):
  e=self.expected()
  return {'banners':[{'variant':b['variant'],'src':b['src'],'naturalWidth':1774,'naturalHeight':887,'width':600,'height':300,'alt':b['alt'],'caption':'','figcaptionCount':0}for b in e['banners']],'faq':[],'products':e['homeProducts']}
 def test_absent_caption_accepts_valid_geometry(self):adapter.validate_extra_facts(self.facts(),self.expected(),'/')
 def test_empty_or_hidden_figcaption_element_still_rejected(self):
  for caption,count in [('',1),('',2),('AI 이미지',1),('unexpected',0)]:
   f=self.facts();f['banners'][0].update(caption=caption,figcaptionCount=count)
   with self.subTest(caption=caption,count=count),self.assertRaisesRegex(AssertionError,'absent from DOM'):adapter.validate_extra_facts(f,self.expected(),'/')
 def test_exact_historical_alt_plus_phone_is_required(self):
  historical=adapter.load(SOURCE/adapter.SITE_PATH/'src/data/dongjak-common-copy.json')['bannerPolicy']['banners']
  for expected,original in zip(self.expected()['banners'],historical):
   self.assertEqual(expected['alt'],original['alt']+' 전화 1844-0644.')
   self.assertNotIn('AI 생성',expected['alt'])
  for alt in (historical[0]['alt'],historical[0]['alt']+' 전화 1844-0000.','전화 1844-0644.'):
   f=self.facts();f['banners'][0]['alt']=alt
   with self.subTest(alt=alt),self.assertRaisesRegex(AssertionError,'phone-inclusive'):adapter.validate_extra_facts(f,self.expected(),'/')
 def test_missing_caption_dom_evidence_rejected(self):
  f=self.facts();f['banners'][0].pop('figcaptionCount')
  with self.assertRaises(KeyError):adapter.validate_extra_facts(f,self.expected(),'/')
 def test_alt_asset_dimensions_order_and_geometry_guards_remain(self):
  for key,value in [('alt',''),('src','/bad'),('naturalWidth',887),('naturalHeight',1774),('width',1),('height',100)]:
   f=self.facts();f['banners'][0][key]=value
   with self.subTest(key=key),self.assertRaises(AssertionError):adapter.validate_extra_facts(f,self.expected(),'/')
  f=self.facts();f['banners'].reverse()
  with self.assertRaises(AssertionError):adapter.validate_extra_facts(f,self.expected(),'/')
 def test_exact_phone_image_hashes(self):
  pinned={'message':'a5ecdeb1914566a32d45b084351e2782fc8b234e9a4fbb8635a60a9921cac5f5','budget':'081198095eb005603721be7c778f4d477f4dd93dcf96f0c261f18bf06bb91421','consultation':'d6654aa44c365f64e330d0be2042972d3320fad54231425aaffca1dfdcd25ebc'}
  for b in self.expected()['banners']:
   self.assertEqual(b['sha256'],pinned[b['variant']]);self.assertEqual(adapter.sha((SOURCE/adapter.SITE_PATH/'public'/b['src'].lstrip('/')).read_bytes()),pinned[b['variant']])
 def test_all_nine_banner_viewport_screenshots_remain_selected(self):
  helper=test_adapter.AdapterTests();helper.expected=self.expected()
  with TemporaryDirectory()as temp:
   rows,flows=helper.make_synthetic_screenshots(Path(temp));selected=adapter.screenshot_selection(rows)
   banners={(w,label)for w,route,label in selected if label.startswith('banner-')}
   self.assertEqual(banners,{(w,'banner-'+b['variant'])for w,h in adapter.controls.VIEWPORTS for b in self.expected()['banners']})
   self.assertEqual(len(banners),9);self.assertEqual(self.expected()['captureCount'],12)
 def test_capture_reads_caption_dom_without_mutation(self):
  self.assertIn("figcaptionCount:el.querySelectorAll('figcaption').length",run_bound_capture.EXTRA_FACTS)
  self.assertNotIn('add_style_tag',run_bound_capture.EXTRA_FACTS);self.assertNotIn('.remove(',run_bound_capture.EXTRA_FACTS)
 def native_guard(self,site_url=None,indexable='false'):
  env={**os.environ,'SITE_INDEXABLE':indexable,'SITE_FACTORY_REVISION':'a'*40,'SITE_ORIGIN':adapter.SITE_URL,'ASTRO_TELEMETRY_DISABLED':'1'};env.pop('SITE_URL',None)
  if site_url is not None:env['SITE_URL']=site_url
  return subprocess.run(['node','scripts/assert_preview_boundary.mjs'],cwd=SOURCE/adapter.SITE_PATH,env=env,text=True,capture_output=True)
 def test_native_preview_guard_passes_with_config_default(self):
  result=self.native_guard();self.assertEqual(result.returncode,0,result.stderr)
 def test_native_preview_guard_still_rejects_explicit_wrong_origins(self):
  for url in (adapter.SITE_URL,'https://evil.invalid'):
   result=self.native_guard(url)
   with self.subTest(url=url):self.assertNotEqual(result.returncode,0);self.assertIn('Production origin override',result.stderr)
 def test_only_native_commands_unset_site_url(self):
  workflow=(adapter.HERE.parents[1]/'workflows/unpublished-dongjak-visual-qa.yml').read_text()
  self.assertEqual(workflow.count('env -u SITE_URL'),3)
  for command in ('npm run build','npm test','npm run qa'):self.assertIn('env -u SITE_URL '+command,workflow)
  self.assertIn('SITE_URL: ${{ matrix.url }}',workflow);self.assertIn("indexable: 'false'",workflow)
  self.assertNotIn('unset SITE_INDEXABLE',workflow);self.assertNotIn('env -u SITE_URL python',workflow)
 def test_source_approval_fact_is_separate_from_qa_publication(self):
  e=self.expected();self.assertIs(e['productionApproved'],True);self.assertIs(e['qaPublicationApproved'],False);self.assertIs(e['indexable'],False)
 def test_unbound_commit_tree_repository_placeholders_fail_closed(self):
  spec=adapter.load(adapter.HERE/'bound-spec.json')
  for key in ('sourceSha','sourceTree','repositoryTree'):
   with self.subTest(key=key),self.assertRaises(AssertionError):adapter.validate_spec({**spec,key:'PENDING_UNVERIFIED'})
 @contextmanager
 def bound_fixture(self):
  """Explicit synthetic identity to test validation branches, never saved evidence."""
  spec=adapter.load(adapter.HERE/'bound-spec.json');spec.update(sourceSha='a'*40,sourceTree='b'*40,repositoryTree='c'*40)
  original_load=adapter.load
  def read(path):
   value=original_load(path)
   if Path(path).name=='banner-successor-lineage.json':value={**value,'sourceSavedAndIndependentlyReadBack':True}
   return value
  with patch.object(adapter,'SOURCE_SHA',spec['sourceSha']),patch.object(adapter,'SOURCE_TREE',spec['sourceTree']),patch.object(adapter,'REPOSITORY_TREE',spec['repositoryTree']),patch.object(adapter,'load',side_effect=read):yield spec
 def test_qa_spec_positive_and_negative_boundaries(self):
  with self.bound_fixture()as spec:
   adapter.validate_spec(spec)
   for key,value,message in [('qaPublicationApproved',True,'QA publication'),('indexable',True,'QA publication'),('hostnameOwnershipVerified',True,'Hostname'),('productionApproved',False,'source approval')]:
    with self.subTest(key=key),self.assertRaisesRegex(AssertionError,message):adapter.validate_spec({**spec,key:value})
 def test_qa_environment_requires_exact_preview_and_noindex(self):
  with self.bound_fixture()as spec:
   env={'GITHUB_REF':adapter.controls.BRANCH,'GITHUB_REPOSITORY':'joseungil-kr/fwith-site-factory','GITHUB_SHA':'d'*40,'SITE_FACTORY_REVISION':spec['sourceSha'],'SITE_URL':adapter.SITE_URL,'SITE_ORIGIN':adapter.SITE_URL,'SITE_INDEXABLE':'false'}
   with patch.dict(os.environ,env,clear=True):adapter.validate_environment(spec)
   for key,value in [('SITE_URL',''),('SITE_URL','https://seoul-dongjak.fwith.kr'),('SITE_ORIGIN','https://evil.invalid'),('SITE_INDEXABLE','true'),('GITHUB_REF','refs/heads/main')]:
    with self.subTest(key=key,value=value),patch.dict(os.environ,{**env,key:value},clear=True),self.assertRaises(AssertionError):adapter.validate_environment(spec)
 def test_missing_independent_source_readback_rejected_after_syntax_binding(self):
  with self.bound_fixture()as spec:
   original_load=adapter.load
   def pending(path):return {**original_load(path),'sourceSavedAndIndependentlyReadBack':False}
   with patch.object(adapter,'load',side_effect=pending),self.assertRaisesRegex(AssertionError,'readback is pending'):adapter.validate_spec(spec)
 def test_build_metadata_synthetic_preview_positive_and_production_mutations(self):
  # Tiny synthetic HTML tests only the unchanged artifact validator; no Astro build.
  with self.bound_fixture()as spec,TemporaryDirectory()as temp:
   site=Path(temp);dist=site/'dist';dist.mkdir()
   for route in adapter.ROUTES:
    p=dist/('404.html' if route=='/404.html' else route.lstrip('/')+'index.html');p.parent.mkdir(parents=True,exist_ok=True)
    canonical='' if route=='/404.html' else '<link rel="canonical" href="'+adapter.SITE_URL+route+'">'
    p.write_text('<meta name="robots" content="noindex,nofollow,noarchive"><meta name="site-factory-revision" content="'+spec['sourceSha']+'">'+canonical)
   (dist/'robots.txt').write_text('User-agent: *\nDisallow: /\n');(dist/'_headers').write_text('/*\n  X-Robots-Tag: noindex, nofollow, noarchive\n')
   self.assertEqual(sum(p.endswith('.html')for p in adapter.controls.validate_build(site,spec)),4)
   home=dist/'index.html';original=home.read_text()
   for old,new in [('noindex,nofollow,noarchive','index,follow'),(adapter.SITE_URL,'https://seoul-dongjak.fwith.kr'),(spec['sourceSha'],'e'*40)]:
    home.write_text(original.replace(old,new))
    with self.subTest(new=new),self.assertRaises(AssertionError):adapter.controls.validate_build(site,spec)
   home.write_text(original)
   (dist/'sitemap.xml').write_text('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>https://seoul-dongjak.fwith.kr/</loc></url></urlset>')
   with self.assertRaisesRegex(AssertionError,'sitemap URL set'):adapter.controls.validate_build(site,spec)

if __name__=='__main__':unittest.main()
