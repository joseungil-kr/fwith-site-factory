#!/usr/bin/env python3
"""Offline negative tests; fixture geometry is synthetic, never real browser proof."""
from pathlib import Path
from unittest.mock import patch, MagicMock
import copy,json,os,shutil,tempfile,unittest,subprocess
import adapter as a
import run_bound_capture as runner
F=a.load(a.HERE/'frozen-inputs/static-dom-fixtures.json');EX=F['expectations'];BASE=F['facts'];SPEC={'sourceSha':'test-synthetic-sha','siteUrl':a.SITE_URL,'indexable':False}
class GwanakContract(unittest.TestCase):
 def check(self,route,facts):runner.assert_bound_facts(facts,SPEC,route,EX['pages'].get(route,{}).get('faq',[]),320,EX)
 def reject(self,route,change):
  f=copy.deepcopy(BASE[route]);change(f)
  with self.assertRaises(AssertionError):self.check(route,f)
 def test_all_five_actual_html_contracts_synthetic_geometry(self):
  for route in a.ROUTES:
   with self.subTest(route=route):self.check(route,BASE[route])
 def test_all_upstream_failure_classes_still_rejected(self):
  for route in a.ROUTES:
   mutations={
    'phone-missing':lambda f:f.update(anchors=[x for x in f['anchors']if not x['href'].startswith('tel:')]),
    'phone-wrong':lambda f:next(x for x in f['anchors']if x['href'].startswith('tel:')).update(href='tel:00000000'),
    'phone-old-format':lambda f:[x.update(href='tel:18440644')for x in f['anchors']if x['href'].startswith('tel:')],
    'order-missing':lambda f:f.update(anchors=[x for x in f['anchors']if not x['href'].startswith('https://fwith.co.kr')]),
    'order-spoof-domain':lambda f:next(x for x in f['anchors']if x['href'].startswith('https://fwith.co.kr')).update(href='https://fwith.co.kr.evil.test/'),
    'font-incomplete':lambda f:f.update(fontStatus='loading'),
    'empty-h1':lambda f:f.update(h1=[]),
    'overflow':lambda f:f.update(scrollWidth=3210),
    'revision-wrong':lambda f:f.update(revision='different'),
    'canonical-wrong':lambda f:f.update(canonical='https://unapproved.invalid'),
    'robots-indexable':lambda f:f.update(robots='index,follow'),
    'title-wrong':lambda f:f['extra'].update(title='not approved'),
    'meta-wrong':lambda f:f['extra'].update(description='not approved'),
    'footer-wrong':lambda f:f['extra']['footer'].update(brand='other'),
   }
   for name,change in mutations.items():
    with self.subTest(route=route,mutation=name):self.reject(route,change)
 def test_404_exact_13_anchors_and_no_exception(self):
  self.assertEqual(len(EX['notFoundContract']['anchors']),13)
  self.assertNotEqual(EX['notFoundContract']['h1'][0],EX['notFoundContract']['title'])
  for change in [lambda f:f['anchors'].reverse(),lambda f:f['anchors'][0].update(text='wrong'),lambda f:f.update(banners=1),lambda f:f['extra'].update(schema=[{}]),lambda f:f['extra'].update(title=EX['notFoundContract']['h1'][0]),lambda f:f.update(images=[{'complete':True,'width':1,'height':1,'alt':'x'}])]:self.reject('/404.html',change)
 def test_product_and_banner_mutations(self):
  for route in ['/',a.ROUTES[2],a.ROUTES[3]]:
   changes={
    'missing-product':lambda f:f['extra']['products'].pop(),
    'wrong-SKU':lambda f:f['extra']['products'][0].update(sku='OTHER'),
    'wrong-price':lambda f:f['extra']['products'][0].update(priceLabel='1원'),
    'wrong-photo':lambda f:f['extra']['productImages'][0].update(src='/fake.webp'),
    'photo-size':lambda f:f['extra']['productImages'][0].update(width=1774),
    'photo-alt':lambda f:f['extra']['productImages'][0].update(alt=''),
    'product-caption':lambda f:f['extra']['products'][0].update(caption='AI'),
    'wrapped-currency':lambda f:f['extra']['priceRuns'][0].update(valid=False),
    'missing-price-check':lambda f:f['extra']['priceRuns'].pop(),
    'banner-order':lambda f:f['extra']['banners'].reverse(),
    'banner-alt':lambda f:f['extra']['banners'][0].update(alt='generic'),
    'banner-caption':lambda f:f['extra']['banners'][0].update(caption='actual photo'),
    'banner-caption-element':lambda f:f['extra']['banners'][0].update(captionElements=1),
    'removed-caption-anywhere':lambda f:f['extra'].update(removedBannerCaptionOccurrences=1),
    'banner-phone-alt':lambda f:f['extra']['banners'][0].update(alt=f['extra']['banners'][0]['alt'].replace('1844-0644','')),
    'banner-size':lambda f:f['extra']['banners'][0].update(naturalWidth=500),
    'banner-crop':lambda f:f['extra']['banners'][0].update(height=50),
   }
   for name,fn in changes.items():
    with self.subTest(route=route,mutation=name):self.reject(route,fn)
 def test_detail_copy_facility_faq_sources(self):
  for route in a.ROUTES[2:4]:
   changes={
    'paragraph-missing':lambda f:f['extra']['sections'][0]['paragraphs'].pop(),
    'section-order':lambda f:f['extra']['sections'].reverse(),
    'first-answer':lambda f:f['extra'].update(firstAnswer='wrong'),
    'facility-H3':lambda f:f['extra']['facilities'][0].update(tag='H3'),
    'duplicate-anchor':lambda f:f['extra']['facilities'][0].update(count=2),
    'FAQ-copy':lambda f:f['extra']['faq'][0].update(answer='wrong'),
    'FAQ-hidden':lambda f:f['faq'][0].update(visible=False),
    'source-name':lambda f:f['extra']['sources'][0].update(name='wrong'),
    'source-note':lambda f:f['extra'].update(sourceNote='wrong'),
    'related-link':lambda f:f['extra']['relatedLink'].update(href='/fake/'),
   }
   for name,fn in changes.items():
    with self.subTest(route=route,mutation=name):self.reject(route,fn)
  self.reject(a.ROUTES[3],lambda f:f['extra'].update(sources=[x for x in f['extra']['sources']if '?page=2'not in x['url']]))
  self.reject(a.ROUTES[3],lambda f:f['extra']['occasions'].clear())
 def test_thin_directory_and_geography(self):
  changes={
   'fake-third-card':lambda f:f['extra']['guideCards'].append(f['extra']['guideCards'][0]),
   'hidden-card':lambda f:f['extra']['guideCards'].pop(),
   'banner-enabled':lambda f:f['extra']['banners'].append(BASE['/']['extra']['banners'][0]),
   'legal-expanded':lambda f:f['extra']['legalUnits'].append('fake'),
   'admin-missing':lambda f:f['extra']['adminRows'].pop(),
   'relation-wrong':lambda f:f['extra']['adminRows'][0].update(unitKey='wrong'),
   'faculty-forced-dong':lambda f:f['extra']['legalLinks'].append({'unitKey':EX['legalUnits'][0],**f['extra']['unassignedLinks'][0]}),
   'faculty-missing':lambda f:f['extra']['unassignedLinks'].clear(),
   'admin-facility':lambda f:f['extra']['adminFacilityLinks'].append(a.ROUTES[2]+'#wooshin-funeral'),
  }
  for name,fn in changes.items():
   with self.subTest(mutation=name):self.reject('/regions/',fn)
 def test_exact_source_and_native_identity(self):
  a.verify_upstream();entries=a.frozen_entries();self.assertEqual(len(entries),679)
  self.assertEqual(next(e['gitBlobSha']for e in entries if e['path'].endswith('/scripts/qa_browser_rendering.py')),a.NATIVE_BLOB)
  self.assertIn(a.GENERATED_REVISION,[e['path']for e in entries])
 def test_frozen_and_generated_phase_guards(self):
  source=Path(os.environ.get('SOURCE_ROOT','/workspace/shared/gwanak-factory'));entries=a.frozen_entries()
  with tempfile.TemporaryDirectory()as temp:
   root=Path(temp)
   for e in entries:
    dest=root/e['path'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source/e['path'],dest)
   revision=root/a.GENERATED_REVISION;revision.write_bytes((a.HERE/'frozen-inputs/prebuild-revision.json').read_bytes());a.verify_frozen_bytes(root)
   revision.write_text('{"revision":"arbitrary"}')
   with self.assertRaises(AssertionError):a.verify_frozen_bytes(root)
   exact='1'*40
   with patch.object(a,'saved',return_value={'sourceSha':exact}),patch.object(a.controls,'git',return_value=exact):
    with self.assertRaises(AssertionError):a.verify_frozen_bytes(root,allow_generated=True)
    revision.write_bytes(json.dumps({'revision':exact},indent=2).encode());a.verify_frozen_bytes(root,allow_generated=True)
    revision.chmod(0o755)
    with self.assertRaises(AssertionError):a.verify_frozen_bytes(root,allow_generated=True)
    revision.chmod(0o644)
    for payload in [revision.read_bytes()+b'\n',json.dumps({'revision':'2'*40},indent=2).encode(),b'{}']:
     revision.write_bytes(payload)
     with self.assertRaises(AssertionError):a.verify_frozen_bytes(root,allow_generated=True)
    revision.write_bytes(json.dumps({'revision':exact},indent=2).encode())
    other=root/(a.SITE_PATH+'/src/pages/404.astro');other.write_bytes(other.read_bytes()+b' ')
    with self.assertRaises(AssertionError):a.verify_frozen_bytes(root,allow_generated=True)
 def test_source_guard_preserves_upstream_identity_after_failure(self):
  with patch.object(a,'validate_spec'),patch.object(a,'verify_frozen_bytes'),patch.object(a,'verify_approved_render_boundary'),patch.object(a.controls,'verify_source',side_effect=AssertionError('expected wrong tree')):
   with self.assertRaises(AssertionError):a.bound_verify_source(Path('/tmp'),{})
  self.assertEqual(a.controls.NATIVE_BLOB,'41ee8a757b7a742b6125ef15b5356e0eca47c01f')
 def test_source_tree_cache_symlink_and_dependency_boundaries(self):
  source=Path(os.environ['SOURCE_ROOT'])/a.SITE_PATH
  with tempfile.TemporaryDirectory()as tmp:
   root=Path(tmp)/'repo';site=root/a.SITE_PATH;shutil.copytree(source,site,ignore=shutil.ignore_patterns('dist','node_modules','.astro','__pycache__','faq-product-qa.json','shared-banner-qa.json','directory-spacing-qa.json','gwanak-static-qa.json'))
   a.verify_scoped_source_tree(root)
   for phase in [False,True]:
    p=site/'scripts/__pycache__';p.mkdir();(p/'bad.pyc').write_bytes(b'not executable')
    with self.assertRaises(AssertionError):a.verify_scoped_source_tree(root,phase)
    shutil.rmtree(p)
    link=site/'public/dangling';link.symlink_to('/nonexistent-banner-target')
    with self.assertRaises(AssertionError):a.verify_scoped_source_tree(root,phase)
    link.unlink()
    link=site/'public/untracked-dir';link.symlink_to(site/'src',target_is_directory=True)
    with self.assertRaises(AssertionError):a.verify_scoped_source_tree(root,phase)
    link.unlink()
    link=site/'node_modules';link.symlink_to(site/'src',target_is_directory=True)
    with self.assertRaises(AssertionError):a.verify_scoped_source_tree(root,phase)
    link.unlink()
    parent_link=Path(tmp)/'parent-link';parent_link.symlink_to(root,target_is_directory=True)
    with self.assertRaises(AssertionError):a.verify_scoped_source_tree(parent_link,phase)
    parent_link.unlink()
   modules=site/'node_modules';(modules/'.bin').mkdir(parents=True);(modules/'astro').mkdir();(modules/'astro/astro.js').write_text('fixture only');(modules/'.bin/astro').symlink_to('../astro/astro.js')
   a.verify_scoped_source_tree(root,True)
   with self.assertRaises(AssertionError):a.verify_scoped_source_tree(root,False)
 def test_generated_fixture_roots_remain_forbidden_in_prebuild(self):
  source=Path(os.environ['SOURCE_ROOT'])/a.SITE_PATH
  generated=['node_modules','dist','.astro','faq-product-qa.json','shared-banner-qa.json','directory-spacing-qa.json','gwanak-static-qa.json']
  with tempfile.TemporaryDirectory()as tmp:
   root=Path(tmp)/'repo';site=root/a.SITE_PATH
   shutil.copytree(source,site,ignore=shutil.ignore_patterns(*generated,'__pycache__'))
   a.verify_scoped_source_tree(root)
   for name in generated:
    with self.subTest(generated=name):
     p=site/name
     if name in ['node_modules','dist','.astro']:p.mkdir()
     else:p.write_text('{}')
     with self.assertRaises(AssertionError):a.verify_scoped_source_tree(root,False)
     a.verify_scoped_source_tree(root,True)
     if p.is_dir():p.rmdir()
     else:p.unlink()
   (site/'unreviewed-root.json').write_text('{}')
   for phase in [False,True]:
    with self.assertRaises(AssertionError):a.verify_scoped_source_tree(root,phase)
 def test_production_capable_source_stays_nonindexable_loopback_qa(self):
  source=Path(os.environ['SOURCE_ROOT'])/a.SITE_PATH
  result=a.verify_approved_render_boundary(source)
  self.assertEqual(result,{'sourcePreviewUrl':a.PREVIEW_URL,'renderedOrigin':a.SITE_URL,'indexable':False,'transport':'existing dynamic loopback only'})
  cases=[('src/data/site-config.json',lambda x:x.update(previewUrl=a.SITE_URL)),
         ('src/data/site-config.json',lambda x:x.update(productionApproved=False)),
         ('src/data/release-approval.json',lambda x:x.update(hostname='other.fwith.kr')),
         ('src/data/release-approval.json',lambda x:x.update(origin='https://other.fwith.kr')),
         ('src/data/release-approval.json',lambda x:x.update(approvedRuntimeDataSha256='0'*64)),
         ('src/data/release-approval.json',lambda x:x['evidenceReferences'].update(publication='changed')),
         ('src/data/release-approval.json',lambda x:x.update(providerExistenceVerified=True))]
  for rel,change in cases:
   with self.subTest(path=rel),tempfile.TemporaryDirectory()as tmp:
    root=Path(tmp)/'site';shutil.copytree(source,root,ignore=shutil.ignore_patterns('dist','node_modules','__pycache__'))
    p=root/rel;v=a.load(p);change(v);p.write_text(json.dumps(v))
    with self.assertRaises(AssertionError):a.verify_approved_render_boundary(root)
 def test_source_spec_is_distinct_fixed_preview_copy_and_upstream_stays_strict(self):
  spec={'siteUrl':a.SITE_URL,'productionApproved':True,'indexable':False,'nested':{'x':1}};before=copy.deepcopy(spec)
  with patch.object(a,'validate_spec'),patch.object(a,'verify_frozen_bytes'),patch.object(a,'verify_approved_render_boundary'),patch.object(a.controls,'verify_source',return_value='passed')as upstream:
   self.assertEqual(a.bound_verify_source(Path('/tmp'),spec,pristine=True),'passed')
   actual=upstream.call_args.args[1];self.assertEqual(actual,{**spec,'siteUrl':a.PREVIEW_URL});self.assertIsNot(actual,spec)
  self.assertEqual(spec,before)
  with patch.object(a,'validate_spec'),patch.object(a,'verify_frozen_bytes'),patch.object(a,'verify_approved_render_boundary'),patch.object(a.controls,'verify_source',side_effect=AssertionError('upstream-failure')):
   with self.assertRaisesRegex(AssertionError,'upstream-failure'):a.bound_verify_source(Path('/tmp'),spec)
  self.assertEqual(spec,before)
 def test_rendered_origin_or_indexable_env_cannot_expand_boundary(self):
  identity={'sourceSha':'1'*40,'sourceTree':'2'*40,'repositoryTree':'3'*40,'sourceManifestSha256':a.MANIFEST_SHA}
  spec={k:identity[k]for k in ['sourceSha','sourceTree','repositoryTree']};spec.update(path=a.SITE_PATH,siteUrl=a.SITE_URL,productionApproved=True,indexable=False,routes=a.ROUTES,sitemapRoutes=[],frozenManifestSha256=a.MANIFEST_SHA)
  env={'GITHUB_REF':'refs/heads/qa/unpublished-regional-visual-20261012','GITHUB_REPOSITORY':'joseungil-kr/fwith-site-factory','GITHUB_SHA':'4'*40,'SITE_FACTORY_REVISION':identity['sourceSha'],'SITE_URL':a.SITE_URL,'SITE_ORIGIN':a.SITE_URL,'SITE_INDEXABLE':'false'}
  with patch.object(a,'saved',return_value=identity),patch.dict(os.environ,env):
   a.validate_environment(spec)
   for key,value in [('SITE_URL',a.PREVIEW_URL),('SITE_ORIGIN','https://other.fwith.kr'),('SITE_INDEXABLE','true')]:
    with patch.dict(os.environ,{key:value}),self.assertRaises(AssertionError):a.validate_environment(spec)
   for change in [{'siteUrl':a.PREVIEW_URL},{'productionApproved':False},{'indexable':True}]:
    with self.assertRaises(AssertionError):a.validate_spec({**spec,**change})
  self.assertFalse(a.controls.allowed_request(a.SITE_URL+'/','GET','http://127.0.0.1:12345'))
  self.assertTrue(a.controls.allowed_request('http://127.0.0.1:12345/','GET','http://127.0.0.1:12345'))
 def test_geometry_negative_contracts(self):
  base=dict(visible=True,width=100,height=80,left=0,right=100,top=80,bottom=160,safeTop=70,safeBottom=600,viewportWidth=320,hitTests=[True]*9)
  a.assert_focus(base)
  for key,value in [('visible',False),('width',0),('left',-1),('right',321),('top',69),('bottom',601),('hitTests',[False])]:
   with self.subTest(key=key),self.assertRaises(AssertionError):a.assert_focus(dict(base,**{key:value}))
 def test_javascript_syntax_without_browser(self):
  scripts=[runner.EXTRA_FACTS,runner.FOCUS_FACTS,runner.PRODUCT_FACTS,runner.RENDER_SNAPSHOT,runner.capture.FACTS]
  code='for(const source of '+json.dumps(scripts)+'){new Function("return ("+source+")");} console.log("5 browser expressions parsed; none executed");'
  result=subprocess.run(['node','-e',code],text=True,capture_output=True)
  self.assertEqual(result.returncode,0,result.stderr)
 def test_metadata_and_duplicate_id_mutations(self):
  for route in a.ROUTES:
   self.reject(route,lambda f:f['extra'].update(duplicateIds=['main-content']))
  for route in a.ROUTES[:-1]:
   for key in BASE[route]['extra']['social']:
    with self.subTest(route=route,field=key):self.reject(route,lambda f,k=key:f['extra']['social'].update({k:'wrong'}))
   self.reject(route,lambda f:f['extra']['schema'][0].update(areaServed='서울대학교 교수회관'))
 def test_keyboard_partial_sticky_occlusion_rejected(self):
  f={'tag':'A','visible':True,'width':100,'height':80,'left':20,'right':120,'top':100,'bottom':180,'viewportWidth':320,'viewportHeight':740,'region':'content','safeTop':70,'safeBottom':640,'fragmentCount':1,'hitTests':[True]*9,'focusVisible':True,'outlineWidth':3,'outlineStyle':'solid'}
  a.assert_keyboard_focus(f)
  for mutation in [{'top':69},{'bottom':641},{'hitTests':[True]*8+[False]},{'hitTests':[True]},{'fragmentCount':0},{'focusVisible':False},{'region':'unknown'},{'left':-1}]:
   with self.subTest(mutation=mutation),self.assertRaises(AssertionError):a.assert_keyboard_focus({**f,**mutation})
  for region,top,bottom in [('header',0,70),('mobile-bar',640,740),('skip',0,740)]:
   g={**f,'region':region,'safeTop':top,'safeBottom':bottom,'top':top+10,'bottom':bottom-10};a.assert_keyboard_focus(g)
   with self.assertRaises(AssertionError):a.assert_keyboard_focus({**g,'bottom':bottom+1})
 def test_all_flow_screenshots_required_and_actual_counts(self):
  rows=[{'width':w,'height':h,'route':route,'label':label,'issues':[],'facts':{'width':100,'height':80,'renderSignature':label}}for w,h in a.controls.VIEWPORTS for route in a.ROUTES for label in a.focus_labels(EX,route)]
  for row in rows:
   if row['label'].startswith('product-'):row.update(self.product_row())
  next(r for r in rows if r['label'].startswith('product-')).update(self.product_row(True))
  selection=a.screenshot_selection(rows)
  flows=[]
  for w,h in a.controls.VIEWPORTS:
   for route in a.ROUTES:
    if route=='/regions/':flows.extend({'width':w,'flow':'anchor-first-landing','href':x['href'],'passed':True}for x in EX['anchorFlows'])
    flows.append({'width':w,'route':route,'flow':'keyboard-tab-focus','passed':True})
  with tempfile.TemporaryDirectory()as temp:
   root=Path(temp)
   def shot(row,key):
    w=row['width'];h=dict(a.controls.VIEWPORTS)[w];rel='supplemental/'+key+'.jpg';p=root/rel;p.parent.mkdir(parents=True,exist_ok=True)
    b=b'\xff\xd8\xff\xc0\x00\x11\x08'+h.to_bytes(2,'big')+w.to_bytes(2,'big')+b'\x03';p.write_bytes(b)
    row.update(screenshot=rel,screenshotSha256=a.sha(b),dimensions={'width':w,'height':h})
   for i,r in enumerate(rows):
    key=(r['width'],r['route'],r['label']);r['screenshotReasons']=selection.get(key,[])
    if key in selection:shot(r,'row-'+str(i))
   for i,r in enumerate(rows):
    if r.get('oversizedProduct'):
     for j,segment in enumerate(r['productSegments']):
      segment['width']=r['width'];shot(segment,f'segment-{i}-{j}')
   for i,f in enumerate(flows):shot(f,'flow-'+str(i))
   result=a.validate_supplemental_evidence(rows,flows,EX,root)
   self.assertEqual(result['anchorScreenshots'],15);self.assertEqual(result['keyboardScreenshots'],15)
   self.assertEqual(result['productContentChecks'],288);self.assertEqual(result['oversizedProductSegmentScreenshots'],6)
   product_index=next(i for i,r in enumerate(rows)if r.get('oversizedProduct'))
   for j in range(6):
    for field in ['screenshot','screenshotSha256','dimensions']:
     broken=copy.deepcopy(rows);del broken[product_index]['productSegments'][j][field]
     with self.subTest(segment=j,field=field),self.assertRaises(AssertionError):a.validate_supplemental_evidence(broken,flows,EX,root)
   for i in range(30):
    for field in ['screenshot','screenshotSha256','dimensions']:
     broken=copy.deepcopy(flows);del broken[i][field]
     with self.subTest(flow=i,field=field),self.assertRaises(AssertionError):a.validate_supplemental_evidence(rows,broken,EX,root)
   broken=copy.deepcopy(flows)
   for f in broken:
    for field in ['screenshot','screenshotSha256','dimensions']:f.pop(field)
   with self.assertRaises(AssertionError):a.validate_supplemental_evidence(rows,broken,EX,root)
 def product_row(self,oversized=False):
  f=dict(visible=True,width=100,height=80,left=20,right=120,top=90,bottom=170,safeTop=63,safeBottom=682,viewportWidth=320,viewportHeight=740,hitTests=[True]*9)
  image={**f,'tag':'IMG','naturalWidth':500,'naturalHeight':500,'complete':True,'objectFit':'contain','objectPosition':'50% 50%','zeroImageInset':True,'elementBox':{'left':20,'top':90,'width':100,'height':80},'left':30,'right':110,'width':80,'fragmentCount':1}
  segments=[{'segment':label,'facts':image if label=='image'else{**f,'tag':'P','text':'synthetic visible product content','fragmentCount':1}}for label in a.PRODUCT_SEGMENTS]
  shell={**f,'height':626.6875,'bottom':716.6875}if oversized else f
  return {'facts':shell,'oversizedProduct':oversized,'productSegments':segments}
 def test_oversized_product_requires_every_real_content_target(self):
  row=self.product_row(True);a.assert_product_content(row)
  with self.assertRaisesRegex(AssertionError,'sticky overlay'):a.assert_focus(row['facts'])
  for index in range(6):
   for change in [{'visible':False},{'bottom':683},{'top':62},{'left':-1},{'hitTests':[True]*8+[False]},{'fragmentCount':2}]:
    broken=copy.deepcopy(row);broken['productSegments'][index]['facts'].update(change)
    with self.subTest(segment=index,change=change),self.assertRaises(AssertionError):a.assert_product_content(broken)
   broken=copy.deepcopy(row);broken['productSegments'].pop(index)
   with self.assertRaises(AssertionError):a.assert_product_content(broken)
  for change in [{'objectFit':'cover'},{'objectPosition':'left top'},{'zeroImageInset':False},{'naturalWidth':0},{'complete':False},{'width':79},{'left':29}]:
   broken=copy.deepcopy(row);broken['productSegments'][0]['facts'].update(change)
   with self.subTest(image=change),self.assertRaises(AssertionError):a.assert_product_content(broken)
  broken=copy.deepcopy(row);broken['oversizedProduct']=False
  with self.assertRaises(AssertionError):a.assert_product_content(broken)
  broken=self.product_row();broken['facts']['bottom']=683
  with self.assertRaises(AssertionError):a.assert_product_content(broken)
 def test_anchor_baseline_reset_and_http_failures_remain_fatal(self):
  origin='http://127.0.0.1:1234';link=EX['anchorFlows'][-1]
  def page(statuses):
   obj=MagicMock();obj.url=origin+link['href'];responses=iter(statuses)
   def goto(url,**kwargs):
    obj.url=url;status=next(responses);return None if status is None else type('Response',(),{'status':status})()
   obj.goto.side_effect=goto;return obj
  good=page([200,200]);flow={};runner.navigate_anchor(good,origin,link,flow)
  self.assertEqual([x.args[0]for x in good.goto.call_args_list],[origin+'/regions/',origin+link['href']])
  self.assertEqual(flow['documentHttpStatus'],200);self.assertEqual(flow['landingUrl'],origin+link['href'])
  for statuses in [[None],[404],[500],[200,None],[200,404],[200,500]]:
   with self.subTest(statuses=statuses),self.assertRaises(AssertionError):runner.navigate_anchor(page(statuses),origin,link,{})
  bad=page([200,200])
  def wrong(url,**kwargs):bad.url=origin+'/wrong/';return type('Response',(),{'status':200})()
  bad.goto.side_effect=wrong
  with self.assertRaisesRegex(AssertionError,'exact URL'):runner.navigate_anchor(bad,origin,link,{})
 def test_approved_asset_bytes_and_denominator(self):
  source=Path(os.environ.get('SOURCE_ROOT','/workspace/shared/gwanak-factory'))/a.SITE_PATH
  actual=a.verify_approved_asset_bytes(source,a.controls.manifest(source/'dist'))
  self.assertEqual(len(actual['files']),11)
  with tempfile.TemporaryDirectory()as temp:
   site=Path(temp)
   for rel in ['src/data/products.json','src/data/gwanak-copy.json','src/data/shared-banner-manifest.json']+['public/'+x['path']for x in actual['files']]+['dist/'+x['path']for x in actual['files']]:
    target=site/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source/rel,target)
   def verify():return a.verify_approved_asset_bytes(site,a.controls.manifest(site/'dist'))
   verify()
   for rel in ['public/'+actual['files'][0]['path'],'dist/'+actual['files'][0]['path'],'src/data/products.json']:
    f=site/rel;original=f.read_bytes();f.write_bytes(original+b' ')
    with self.subTest(path=rel),self.assertRaises(AssertionError):verify()
    f.write_bytes(original)
   for base in ['public/images','dist/images']:
    f=site/base/'extra.jpg';f.write_bytes(b'not approved')
    with self.assertRaises(AssertionError):verify()
    f.unlink()
   f=site/'dist'/actual['files'][-1]['path'];original=f.read_bytes();f.unlink()
   with self.assertRaises(AssertionError):verify()
   f.write_bytes(original);verify()
 def test_build_wrapper_preserves_original_first(self):
  with patch.object(a.controls,'validate_build',side_effect=AssertionError('original gate failure'))as original,patch.object(a,'verify_approved_asset_bytes')as added:
   with self.assertRaisesRegex(AssertionError,'original gate failure'):a.validate_bound_build(Path('/tmp'),{})
   original.assert_called_once();added.assert_not_called()
 def test_local_browser_run_refuses_before_any_import(self):
  with patch.object(runner.sys,'argv',['qa','--binding','missing.json','--allow-loopback-runner']),patch.dict(os.environ,{'GITHUB_ACTIONS':'false'}):
   with self.assertRaisesRegex(AssertionError,'local browser prohibited'):runner.main()
if __name__=='__main__':unittest.main(verbosity=2)
