"""Offline controls and explicitly synthetic negative fixtures; never browser QA."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from contextlib import contextmanager
import copy,json,os,shutil,struct,subprocess,unittest,zlib
import adapter as a
import run_bound_capture as runner
from dom_helper import DOM,has,cls
SOURCE=Path(os.environ['SOURCE_ROOT']);SITE=SOURCE/a.SITE_PATH
DIST=Path(os.environ.get('SYNTHETIC_DIST_ROOT',str(SITE/'dist')))

def static_facts(route):
 rel='404.html'if route=='/404.html'else route.lstrip('/')+'index.html';root=DOM((DIST/rel).read_text()).root
 banners=[]
 for n in root.all(has('data-shared-flower-banner')):
  i=n.first(lambda x:x.tag=='img');banners.append({'variant':n.attrs['data-shared-flower-banner'],'src':i.attrs['src'],'naturalWidth':int(i.attrs['width']),'naturalHeight':int(i.attrs['height']),'width':1774,'height':887,'alt':i.attrs['alt'],'caption':''.join(x.text()for x in n.all(lambda x:x.tag=='figcaption')),'figcaptionCount':len(n.all(lambda x:x.tag=='figcaption'))})
 faq=[{'question':n.first(has('data-faq-question')).text(),'answer':n.first(has('data-faq-answer')).text()}for n in root.all(has('data-faq-entry'))]
 products=[{'key':n.attrs['data-product-key'],'href':n.first(has('data-order-product-key')).attrs['href'],'priceLabel':n.first(lambda x:x.tag=='strong').text()}for n in root.all(cls('product-card'))]
 expected=a.expectations(SITE);ids=[f['anchor']for p in expected['pages'].values()for f in p['facilities']]
 facilities=[{'id':n.attrs['id'],'heading':n.text(),'tag':n.tag.upper()}for n in root.all(lambda n:n.tag in ('h2','h3')and n.attrs.get('id')in ids)]
 guides=[n.attrs['href']for section in root.all(has('data-region-district'))for n in section.all(cls('page-card'))]
 legal=root.all(has('data-legal-unit'));admins=root.all(has('data-administrative-unit'))
 return {'banners':banners,'faq':faq,'products':products,'facilities':facilities,'guideLinks':guides,'legalUnits':[n.attrs['data-legal-unit']for n in legal],
 'legalLinks':[{'unitKey':n.attrs['data-legal-unit'],'href':x.attrs['href'],'candidateId':x.attrs['data-candidate-id']}for n in legal for x in n.all(has('data-candidate-id'))],
 'adminRows':[{'key':n.attrs['data-administrative-unit'],'relations':[x.text()for x in n.children if hasattr(x,'tag')and x.tag=='span'and 'administrative-purchase-links'not in x.attrs.get('class','')and not x.text().startswith('(')]}for n in admins],
 'adminFacilityLinks':[x.attrs['href']for n in admins for x in n.all(lambda x:x.tag=='a')]}

@contextmanager
def fixture():
 # Copy ONLY frozen manifest entries, not source/dist/.astro/reports or pycache.
 with TemporaryDirectory()as tmp:
  root=Path(tmp)
  for e in a.frozen_entries():
   dst=root/e['path'];dst.parent.mkdir(parents=True,exist_ok=True);raw=(SOURCE/e['path']).read_bytes()
   if e['path']==a.GENERATED_REVISION and a.sha(raw)!=e['sha256']:
    raw=subprocess.check_output(['git','-C',str(SOURCE),'show','HEAD:'+e['path']])
   assert a.sha(raw)==e['sha256'];dst.write_bytes(raw);dst.chmod(int(e['mode'],8)&0o777)
  yield root

def fake_saved():
 return {**a.load(a.HERE/'bound-spec.json'),'sourceSha':'a'*40,'sourceTree':a.C['sourceTree'],'repositoryTree':'c'*40,'sourceSavedAndIndependentlyReadBack':True}

def png(width=390,height=844):
 def chunk(k,b):return struct.pack('>I',len(b))+k+b+struct.pack('>I',zlib.crc32(k+b)&0xffffffff)
 return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',width,height,8,2,0,0,0))+chunk(b'IDAT',zlib.compress((b'\0'+b'\xff\xff\xff'*width)*height))+chunk(b'IEND',b'')

def native_fixture(site,evidence):
 report={'localOrigin':'http://127.0.0.1:12345','scope':'Local static artifact only; not public HTTP verification','checks':[{'route':r,'width':w,'height':h,'http':200,'issues':[]}for w,h in a.controls.VIEWPORTS for r in a.ROUTES],'errors':[]}
 generated=site/'browser-rendering-qa';generated.mkdir()
 for name in a.native_output_names():(generated/name).write_bytes(json.dumps(report).encode()if name=='report.json'else png())
 shutil.copytree(generated,evidence)

class SuccessorTests(unittest.TestCase):
 def test_restored_paint_deadline_rejects_nonpainting_dom(self):
  js='global.requestAnimationFrame=f=>{};const fn=('+runner.BOUNDED_PAINT+');fn({timeoutMs:20}).then(()=>process.exit(9),e=>{if(!String(e).includes("Restored paint deadline exceeded"))process.exit(8);});'
  r=subprocess.run(['node','-e',js],capture_output=True,text=True,timeout=2)
  self.assertEqual(r.returncode,0,r.stderr)
 def test_restored_paint_happens_after_scroll_restore(self):
  from unittest.mock import MagicMock,call
  page=MagicMock();page.locator.return_value.all.return_value=[];page.evaluate.return_value={'x':0,'y':123}
  result=runner.ready_preserving_scroll(page)
  calls=page.evaluate.call_args_list
  self.assertLess(calls.index(call('(p)=>scrollTo({left:p.x,top:p.y,behavior:"instant"})',{'x':0,'y':123})),calls.index(call(runner.BOUNDED_PAINT,{'timeoutMs':10000})))
  self.assertEqual(result['restoredPaintFrames'],2)
 def test_screenshot_readiness_loads_pending_images_before_bounded_decode_and_restores(self):
  from unittest.mock import MagicMock
  page=MagicMock();image=MagicMock();image.evaluate.return_value=False
  page.locator.return_value.all.return_value=[image];page.evaluate.return_value={'x':0,'y':123}
  result=runner.ready_preserving_scroll(page)
  image.scroll_into_view_if_needed.assert_called_once_with(timeout=10000)
  page.evaluate.assert_any_call(runner.BOUNDED_DECODE,{'timeoutMs':10000})
  page.evaluate.assert_any_call('(p)=>scrollTo({left:p.x,top:p.y,behavior:"instant"})',{'x':0,'y':123})
  self.assertEqual(result['originalScroll'],result['restoredScroll'])
  self.assertTrue(all(c.kwargs['timeout']==10000 for c in page.wait_for_function.call_args_list))
 def test_screenshot_readiness_failure_is_not_swallowed_and_restores_scroll(self):
  from unittest.mock import MagicMock
  page=MagicMock();page.locator.return_value.all.return_value=[];page.evaluate.return_value={'x':0,'y':123}
  page.wait_for_function.side_effect=[RuntimeError('unloaded image'),None]
  with self.assertRaisesRegex(RuntimeError,'unloaded image'):runner.ready_preserving_scroll(page)
  page.evaluate.assert_any_call('(p)=>scrollTo({left:p.x,top:p.y,behavior:"instant"})',{'x':0,'y':123})
 def test_screenshot_decode_javascript_rejects_hanging_decode(self):
  # Synthetic DOM promise, no browser, server, package installation or network.
  js='global.document={fonts:{ready:Promise.resolve()},images:[{decode:()=>new Promise(()=>{})}]};global.requestAnimationFrame=f=>f();const fn=('+runner.BOUNDED_DECODE+');fn({timeoutMs:20}).then(()=>process.exit(9),e=>{if(!String(e).includes("deadline exceeded"))process.exit(8);});'
  r=subprocess.run(['node','-e',js],capture_output=True,text=True,timeout=2)
  self.assertEqual(r.returncode,0,r.stderr)
 def test_screenshot_decode_javascript_propagates_broken_image(self):
  js='global.document={fonts:{ready:Promise.resolve()},images:[{decode:()=>Promise.reject(new Error("broken image"))}]};global.requestAnimationFrame=f=>f();const fn=('+runner.BOUNDED_DECODE+');fn({timeoutMs:1000}).then(()=>process.exit(9),e=>{if(!String(e).includes("broken image"))process.exit(8);});'
  r=subprocess.run(['node','-e',js],capture_output=True,text=True,timeout=2)
  self.assertEqual(r.returncode,0,r.stderr)
 def test_first_anchor_has_preload_facts_and_post_restore_checks(self):
  code=Path(runner.__file__).read_text()
  self.assertIn("flow['captureFacts']=loc.evaluate(FOCUS_FACTS)",code)
  self.assertIn("assert_focus(flow['captureFacts'])",code)
  self.assertIn("'First landing geometry changed while loading images'",code)
 def expected(self):return a.expectations(SITE)
 def test_global_clean_checkout_passes(self):
  with patch.object(a.controls,'git',return_value=''),patch.object(a.subprocess,'check_output',return_value=b''):
   self.assertTrue(a.verify_global_checkout(SOURCE))
 def test_global_unstaged_tracked_drift_rejected(self):
  with patch.object(a.controls,'git',return_value='README.md'),self.assertRaisesRegex(AssertionError,'Global tracked'):
   a.verify_global_checkout(SOURCE)
 def test_global_staged_tracked_drift_rejected(self):
  with patch.object(a.controls,'git',side_effect=['','README.md']),self.assertRaisesRegex(AssertionError,'Global staged'):
   a.verify_global_checkout(SOURCE)
 def test_global_untracked_outside_source_rejected(self):
  with patch.object(a.controls,'git',return_value=''),patch.object(a.subprocess,'check_output',return_value=b'extra-root-file\0'),self.assertRaisesRegex(AssertionError,'outside source'):
   a.verify_global_checkout(SOURCE)
 def test_global_ignored_outside_source_rejected(self):
  with patch.object(a.controls,'git',return_value=''),patch.object(a.subprocess,'check_output',side_effect=[b'',b'.ignored-root-file\0']),self.assertRaisesRegex(AssertionError,'outside source'):
   a.verify_global_checkout(SOURCE)
 def test_global_source_generated_files_remain_phase_guarded(self):
  with patch.object(a.controls,'git',return_value=''),patch.object(a.subprocess,'check_output',return_value=(a.SITE_PATH+'/dist/index.html\0').encode()):
   self.assertTrue(a.verify_global_checkout(SOURCE))
 def test_global_guard_required_at_binding_and_reverification(self):
  spec=a.saved()
  with patch.object(a,'verify_global_checkout',side_effect=AssertionError('global guard sentinel')):
   with self.assertRaisesRegex(AssertionError,'global guard sentinel'):a.make_binding(SOURCE,spec['sourceSha'])
   with self.assertRaisesRegex(AssertionError,'global guard sentinel'):a.bound_verify_source(SOURCE,spec,True)
 def test_upstream_bytes_and_native_blob_exact(self):
  a.verify_upstream();raw=(SITE/'scripts/qa_browser_rendering.py').read_bytes()
  import hashlib
  self.assertEqual(hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest(),a.controls.NATIVE_BLOB)
 def test_frozen_lineage_and_manifest_counts(self):self.assertEqual(len(a.frozen_entries()),a.C['sourceFileCount'])
 def test_exact_prebuild_manifest_fixture(self):
  with fixture()as r:self.assertEqual(a.verify_frozen_bytes(r)['files'],a.C['sourceFileCount'])
 def test_no_extra_prebuild_report_or_dir(self):
  for name in ['.astro','dist','node_modules','browser-rendering-qa',*a.C['nativeGeneratedReports']]:
   with self.subTest(name=name),fixture()as r:
    p=r/a.SITE_PATH/name;p.write_text('{}')if name.endswith('.json')else p.mkdir()
    with self.assertRaisesRegex(AssertionError,'Unreviewed source root'):a.verify_frozen_bytes(r)
 def test_nested_extra_source_file_rejected(self):
  with fixture()as r:
   (r/a.SITE_PATH/'src/data/injected.json').write_text('{}')
   with self.assertRaisesRegex(AssertionError,'Unreviewed/missing'):a.verify_frozen_bytes(r)
 def test_changed_article_css_plan_and_product_rejected(self):
  for rel in ['src/data/pages.json','src/data/products.json','src/styles/global.css',f'src/data/{a.REGION}-plan-binding.json']:
   with self.subTest(rel=rel),fixture()as r:
    p=r/a.SITE_PATH/rel;p.write_bytes(p.read_bytes()+b' ')
    with self.assertRaisesRegex(AssertionError,'Frozen source changed'):a.verify_frozen_bytes(r)
 def test_missing_source_file_rejected(self):
  with fixture()as r:
   (r/a.frozen_entries()[0]['path']).unlink()
   with self.assertRaises(AssertionError):a.verify_frozen_bytes(r)
 def test_source_file_mode_drift_rejected(self):
  with fixture()as r:
   (r/a.SITE_PATH/'src/data/site-config.json').chmod(0o755)
   with self.assertRaisesRegex(AssertionError,'mode'):a.verify_frozen_bytes(r)
 def test_source_symlink_and_parent_symlink_rejected(self):
  with fixture()as r:
   p=r/a.SITE_PATH/'src/data/site-config.json';p.unlink();p.symlink_to('/tmp')
   with self.assertRaisesRegex(AssertionError,'link'):a.verify_frozen_bytes(r)
 def test_postbuild_exact_generated_revision_and_scoped_reports(self):
  with fixture()as r,patch.object(a,'saved',return_value=fake_saved()),patch.object(a.controls,'git',return_value='a'*40):
   p=r/a.GENERATED_REVISION;p.write_text(json.dumps({'revision':'a'*40},indent=2))
   for d in ('dist','.astro','node_modules'):(r/a.SITE_PATH/d).mkdir()
   for f in a.C['nativeGeneratedReports']:(r/a.SITE_PATH/f).write_text('{}')
   self.assertEqual(a.verify_frozen_bytes(r,True)['phase'],'postbuild')
   with self.assertRaises(AssertionError):a.verify_frozen_bytes(r)
   p.write_text('{"revision":"'+('a'*40)+'"}')
   with self.assertRaisesRegex(AssertionError,'revision'):a.verify_frozen_bytes(r,True)
 def test_unknown_postbuild_output_rejected(self):
  with fixture()as r:
   (r/a.SITE_PATH/'other-qa.json').write_text('{}')
   with self.assertRaisesRegex(AssertionError,'Unreviewed source root'):a.verify_scoped_source_tree(r,True)
 def test_native_output_requires_explicit_separate_evidence(self):
  with fixture()as r,TemporaryDirectory()as tmp:
   s=r/a.SITE_PATH;e=Path(tmp)/'native';native_fixture(s,e);(r/a.GENERATED_REVISION).write_text('{}')
   with self.assertRaisesRegex(AssertionError,'Unreviewed source root'):a.verify_scoped_source_tree(r,True)
   self.assertTrue(a.verify_scoped_source_tree(r,True,native_evidence=e))
   with self.assertRaisesRegex(AssertionError,'prebuild'):a.verify_scoped_source_tree(r,False,native_evidence=e)
   with self.assertRaisesRegex(AssertionError,'separate'):a.verify_native_output(s,s/'browser-rendering-qa')
 def test_native_names_are_exact_region_outputs(self):self.assertEqual(len(a.native_output_names()),8)
 def test_native_extra_missing_nested_and_links_rejected(self):
  for mode in ['extra','missing','nested','link']:
   with self.subTest(mode=mode),fixture()as r,TemporaryDirectory()as tmp:
    s=r/a.SITE_PATH;e=Path(tmp)/'native';native_fixture(s,e);g=s/'browser-rendering-qa'
    if mode=='extra':(g/'extra.png').write_bytes(png())
    elif mode=='missing':(g/'home-mobile.png').unlink()
    elif mode=='nested':(g/'subdir').mkdir()
    else:(g/'home-mobile.png').unlink();(g/'home-mobile.png').symlink_to(e/'home-mobile.png')
    with self.assertRaises(AssertionError):a.verify_native_output(s,e)
 def test_native_crc_copy_and_report_grid_mutations_rejected(self):
  for mode in ['crc','copy','grid','origin','errors']:
   with self.subTest(mode=mode),fixture()as r,TemporaryDirectory()as tmp:
    s=r/a.SITE_PATH;e=Path(tmp)/'native';native_fixture(s,e);g=s/'browser-rendering-qa'
    if mode in ['crc','copy']:
     raw=bytearray((g/'home-mobile.png').read_bytes());raw[25]^=1;(g/'home-mobile.png').write_bytes(raw)
     if mode=='crc':(e/'home-mobile.png').write_bytes(raw)
    else:
     x=a.load(g/'report.json')
     if mode=='grid':x['checks'].pop()
     if mode=='origin':x['localOrigin']='https://seoul-geumcheon.fwith.kr'
     if mode=='errors':x['errors']=[{}]
     for p in (g,e):(p/'report.json').write_text(json.dumps(x))
    with self.assertRaises(AssertionError):a.verify_native_output(s,e)
 def test_binding_is_fail_closed_until_saved_readback(self):
  spec=a.load(a.HERE/'bound-spec.json')
  if spec['sourceSavedAndIndependentlyReadBack']is False:
   with self.assertRaises(AssertionError):a.validate_spec(spec)
  else:a.validate_spec(spec)
 def test_forged_identity_syntax_never_authorizes_pending_binding(self):
  original=a.load
  for key,value in [('sourceSha','a'*40),('sourceTree','b'*40),('repositoryTree','c'*40)]:
   spec={**original(a.HERE/'bound-spec.json'),key:value,'sourceSavedAndIndependentlyReadBack':False}
   with patch.object(a,'load',side_effect=lambda p:spec if Path(p).name=='bound-spec.json'else original(p)),self.assertRaises(AssertionError):a.saved()
 def test_synthetic_saved_spec_mutations(self):
  spec=fake_saved()
  with patch.object(a,'saved',return_value=spec):
   a.validate_spec(spec)
   for k,v in [('indexable',True),('qaPublicationApproved',True),('hostnameOwnershipVerified',True),('productionApproved',False),('sourceSha','d'*40),('sitemapRoutes',['/']),('siteUrl','https://evil.invalid'),('routes',['/'])]:
    with self.subTest(k=k),self.assertRaises(AssertionError):a.validate_spec({**spec,k:v})
 def test_environment_scope_and_noindex(self):
  spec=fake_saved();env={'GITHUB_ACTIONS':'true','GITHUB_REF':a.controls.BRANCH,'GITHUB_REPOSITORY':'joseungil-kr/fwith-site-factory','GITHUB_SHA':'d'*40,'SITE_FACTORY_REVISION':spec['sourceSha'],'SITE_URL':a.SITE_URL,'SITE_ORIGIN':a.SITE_URL,'SITE_INDEXABLE':'false'}
  with patch.object(a,'saved',return_value=spec):
   with patch.dict(os.environ,env,clear=True):a.validate_environment(spec)
   for k,v in [('GITHUB_ACTIONS','false'),('GITHUB_REF','refs/heads/main'),('GITHUB_REPOSITORY','wrong/repo'),('SITE_INDEXABLE','true'),('SITE_URL','https://evil.invalid'),('SITE_FACTORY_REVISION','d'*40)]:
    with self.subTest(k=k),patch.dict(os.environ,{**env,k:v},clear=True),self.assertRaises(AssertionError):a.validate_environment(spec)
 def test_static_original_structure_plus_explicit_banner_fixture(self):
  for route in a.ROUTES:
   with self.subTest(route=route):a.validate_extra_facts(static_facts(route),self.expected(),route)
 def test_no_caption_including_hidden_or_empty_node(self):
  for caption,n in [('',1),('removed text',0),('AI disclosure',1)]:
   f=static_facts('/');f['banners'][0].update(caption=caption,figcaptionCount=n)
   with self.assertRaisesRegex(AssertionError,'absent from DOM'):a.validate_extra_facts(f,self.expected(),'/')
 def test_exact_old_alt_plus_phone(self):
  for alt in ['',self.expected()['banners'][0]['alt'].removesuffix(' 전화 1844-0644.'),'전화 1844-0644.',self.expected()['banners'][0]['alt'].replace('1844-0644','1844-0645')]:
   f=static_facts('/');f['banners'][0]['alt']=alt
   with self.assertRaisesRegex(AssertionError,'phone-inclusive'):a.validate_extra_facts(f,self.expected(),'/')
 def test_order_asset_geometry_and_dimensions_rejected(self):
  for k,v in [('src','/bad'),('naturalWidth',887),('naturalHeight',1774),('width',1),('height',0)]:
   f=static_facts('/');f['banners'][0][k]=v
   with self.assertRaises((AssertionError,ZeroDivisionError)):a.validate_extra_facts(f,self.expected(),'/')
 def test_exact_three_phone_asset_hashes(self):
  expected={'message':'a5ecdeb1914566a32d45b084351e2782fc8b234e9a4fbb8635a60a9921cac5f5','budget':'081198095eb005603721be7c778f4d477f4dd93dcf96f0c261f18bf06bb91421','consultation':'d6654aa44c365f64e330d0be2042972d3320fad54231425aaffca1dfdcd25ebc'}
  for b in self.expected()['banners']:
   self.assertEqual(b['sha256'],expected[b['variant']]);self.assertEqual(a.sha((SITE/'public'/b['src'].lstrip('/')).read_bytes()),b['sha256'])
 def test_geography_facility_faq_products_mutations(self):
  for route,key in [('/regions/','legalUnits'),('/regions/','adminRows'),('/regions/','legalLinks'),(a.ROUTES[2],'facilities'),(a.ROUTES[2],'faq'),(a.ROUTES[2],'products'),('/','products')]:
   f=static_facts(route);f[key]=[]
   with self.subTest(route=route,key=key),self.assertRaises(AssertionError):a.validate_extra_facts(f,self.expected(),route)
 def test_admin_links_preserve_region_specific_source(self):
  f=static_facts('/regions/');self.assertEqual(f['adminFacilityLinks'],self.expected()['adminFacilityLinks'])
  f['adminFacilityLinks']=['/wrong/']
  with self.assertRaises(AssertionError):a.validate_extra_facts(f,self.expected(),'/regions/')
 def test_fullroute_focus_grid_and_nine_primary_banner_views(self):
  e=self.expected();rows=[{'width':w,'height':h,'route':route,'label':label,'facts':{'renderSignature':label,'width':w,'height':30},'issues':[]}for w,h in a.controls.VIEWPORTS for route in a.ROUTES for label in a.focus_labels(e,route)]
  selected=a.screenshot_selection(rows);banners={(w,label)for w,route,label in selected if label.startswith('banner-')}
  self.assertEqual(banners,{(w,'banner-'+b['variant'])for w,h in a.controls.VIEWPORTS for b in e['banners']})
  self.assertEqual(len([k for k in selected if k[1]=='/'and k[2].startswith('banner-')]),9)
  self.assertEqual(e['captureCount'],len(a.ROUTES)*3)
 def test_rendering_difference_requires_more_evidence(self):
  rows=[{'width':320,'route':'/','label':'banner-message','facts':{'renderSignature':'a','width':300,'height':150}},{'width':320,'route':a.ROUTES[2],'label':'banner-message','facts':{'renderSignature':'b','width':300,'height':150}}]
  self.assertEqual(len(a.screenshot_selection(rows)),2)
 def supplemental_fixture(self,root):
  e=self.expected();rows=[{'width':w,'height':h,'route':route,'label':label,'facts':{'renderSignature':label,'width':w,'height':30},'issues':[]}for w,h in a.controls.VIEWPORTS for route in a.ROUTES for label in a.focus_labels(e,route)];selected=a.screenshot_selection(rows)
  def shot(row,n):
   rel=f'supplemental/synthetic-{n}.jpg';p=root/rel;p.parent.mkdir(exist_ok=True)
   raw=b'\xff\xd8\xff\xc0\x00\x11\x08'+row['height'].to_bytes(2,'big')+row['width'].to_bytes(2,'big')+b'\x03';p.write_bytes(raw)
   row.update(screenshot=rel,screenshotSha256=a.sha(raw),dimensions={'width':row['width'],'height':row['height']},imageReadiness='decode-completed-and-two-paint-frames-awaited')
  for i,r in enumerate(rows):
   key=(r['width'],r['route'],r['label']);r['screenshotReasons']=selected.get(key,[])
   if key in selected:shot(r,'focus-'+str(i))
  flows=[]
  for w,h in a.controls.VIEWPORTS:
   flows.append({'width':w,'flow':'admin-open-close-reopen','passed':True})
   for x in e['legalLinks']:
    row={'width':w,'height':h,'flow':'legal-facility-anchor-first-landing','href':x['href'],'issues':[]};shot(row,'flow-'+str(len(flows)));flows.append(row)
  return rows,flows
 def test_supplemental_evidence_integrity_and_readiness(self):
  with TemporaryDirectory()as tmp:
   root=Path(tmp);rows,flows=self.supplemental_fixture(root);a.validate_supplemental_evidence(rows,flows,self.expected(),root)
   for mode in ['missing-row','duplicate-row','missing-shot','hash','dimensions','readiness','reason','flow','flow-pass']:
    rs=copy.deepcopy(rows);fs=copy.deepcopy(flows);r=next(x for x in rs if 'screenshot'in x)
    if mode=='missing-row':rs.pop()
    elif mode=='duplicate-row':rs[-1]=rs[0]
    elif mode=='missing-shot':r.pop('screenshot')
    elif mode=='hash':r['screenshotSha256']='0'*64
    elif mode=='dimensions':r['dimensions']['height']=1
    elif mode=='readiness':r.pop('imageReadiness')
    elif mode=='reason':r['screenshotReasons']=[]
    elif mode=='flow':fs.pop()
    elif mode=='flow-pass':fs[0]['passed']=False
    with self.subTest(mode=mode),self.assertRaises((AssertionError,KeyError)):a.validate_supplemental_evidence(rs,fs,self.expected(),root)
 def test_exact_saved_parent_is_required(self):
  text=(a.HERE/'adapter.py').read_text();self.assertIn("[source_sha,C['baseSourceSha']]",text)
 def test_native_generated_revision_cannot_be_pregenerated(self):
  with fixture()as r:
   (r/a.GENERATED_REVISION).write_text(json.dumps({'revision':'a'*40},indent=2))
   with self.assertRaisesRegex(AssertionError,'Unreviewed/missing'):a.verify_frozen_bytes(r)
 def test_minimal_synthetic_build_noindex_origin_routes_and_asset_pins(self):
  with fixture()as r:
   site=r/a.SITE_PATH;dist=site/'dist';dist.mkdir();spec=fake_saved()
   for route in a.ROUTES:
    p=dist/('404.html'if route=='/404.html'else route.lstrip('/')+'index.html');p.parent.mkdir(parents=True,exist_ok=True)
    canonical=''if route=='/404.html'else '<link rel="canonical" href="'+a.SITE_URL+route+'">'
    p.write_text('<meta name="robots" content="noindex,nofollow,noarchive"><meta name="site-factory-revision" content="'+spec['sourceSha']+'">'+canonical)
   (dist/'robots.txt').write_text('User-agent: *\nDisallow: /\n');(dist/'_headers').write_text('/*\n  X-Robots-Tag: noindex, nofollow, noarchive\n')
   for b in self.expected()['banners']:
    rel=b['src'].lstrip('/');p=dist/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((site/'public'/rel).read_bytes())
   a.validate_bound_build(site,spec);home=dist/'index.html';original=home.read_text()
   for old,new in [('noindex,nofollow,noarchive','index,follow'),(a.SITE_URL,'https://evil.invalid'),(spec['sourceSha'],'e'*40)]:
    home.write_text(original.replace(old,new))
    with self.subTest(new=new),self.assertRaises(AssertionError):a.validate_bound_build(site,spec)
   home.write_text(original);(dist/'extra.html').write_text(original)
   with self.assertRaises(AssertionError):a.validate_bound_build(site,spec)
   (dist/'extra.html').unlink();(dist/'sitemap.xml').write_text('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>'+a.SITE_URL+'/</loc></url></urlset>')
   with self.assertRaisesRegex(AssertionError,'sitemap'):a.validate_bound_build(site,spec)
   (dist/'sitemap.xml').unlink();p=dist/self.expected()['banners'][0]['src'].lstrip('/');p.write_bytes(p.read_bytes()+b'x')
   with self.assertRaisesRegex(AssertionError,'banner bytes'):a.validate_bound_build(site,spec)
 def test_browser_disabled_outside_runner_and_bound_sha(self):
  with patch.dict(os.environ,{'GITHUB_ACTIONS':'false'},clear=True),patch('sys.argv',['run','--binding',str(a.HERE/'bound-spec.json'),'--allow-loopback-runner']),self.assertRaisesRegex(AssertionError,'local browser prohibited'):runner.main()
 def test_capture_does_not_rewrite_dom_or_drop_upstream_checks(self):
  text=(a.HERE/'run_bound_capture.py').read_text();self.assertIn("figcaptionCount:el.querySelectorAll('figcaption').length",text);self.assertIn('original_assert_facts(facts,specification,route,faq,width)',text)
  for token in ['add_style_tag(','.remove(',"error.args!=('CTA order href',)"]:self.assertNotIn(token,text)
 def test_native_preview_guard_and_explicit_unapproved_origin(self):
  env={**os.environ,'SITE_INDEXABLE':'false','SITE_FACTORY_REVISION':'a'*40};env.pop('SITE_URL',None)
  r=subprocess.run(['node','scripts/assert_preview_boundary.mjs'],cwd=SITE,env=env,capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr)
  env['SITE_URL']='https://evil.invalid';r=subprocess.run(['node','scripts/assert_preview_boundary.mjs'],cwd=SITE,env=env,capture_output=True,text=True);self.assertNotEqual(r.returncode,0)
 def test_future_workflow_native_env_scope_and_failclosed_order(self):
  root=a.HERE
  while root.name!='.github':root=root.parent
  wf=(root/f'workflows/unpublished-{a.REGION}-visual-qa.yml').read_text()
  self.assertEqual(wf.count('env -u SITE_URL'),3)
  for cmd in ['npm run build','npm test','npm run qa']:self.assertIn('env -u SITE_URL '+cmd,wf)
  self.assertLess(wf.index('Fail closed until'),wf.index('Check out exact saved unpublished source'))
  self.assertIn('          ref: ${{ matrix.source }}\n          fetch-depth: 2\n          path: source',wf)
  self.assertNotIn('guro',wf);self.assertNotIn('secrets.',wf);self.assertIn('persist-credentials: false',wf)

if __name__=='__main__':unittest.main()
