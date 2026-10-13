#!/usr/bin/env python3
"""Exact Gwanak-only additive QA bindings. No remote write or deployment capability."""
from pathlib import Path
from unittest.mock import patch
import argparse, hashlib, json, os, re, subprocess, sys
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'upstream'))
import controls
SITE_PATH='site-factory/seoul-gwanak-flower'
SITE_URL='https://seoul-gwanak.local.invalid'
ROUTES=['/','/regions/','/regions/gwanak-funeral-wreath/','/regions/gwanak-celebration-wreath/','/404.html']
MANIFEST_SHA='49efbc6768d52b208f5d7c2bfad8faab5386d5de777d16d6134263e6df168eb7'
NATIVE_BLOB='dcd037a02423a0aa2ab51f78795a7acd34cfaba9'
GENERATED_REVISION=SITE_PATH+'/src/data/build-revision.json'
def load(p):return json.loads(Path(p).read_text())
def sha(b):return hashlib.sha256(b).hexdigest()
def write(p,x):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def saved():
 x=load(HERE/'saved-source.json')
 for k in ['sourceSha','sourceTree','repositoryTree']:assert isinstance(x.get(k),str) and re.fullmatch('[0-9a-f]{40}',x[k]) and x[k]!='0'*40,('Saved source not bound',k)
 assert x['sourceManifestSha256']==MANIFEST_SHA
 return x

def frozen_entries():
 p=HERE/'frozen-inputs/source-manifest.json';assert sha(p.read_bytes())==MANIFEST_SHA,'Frozen manifest drift'
 entries=load(p)['files'];assert len(entries)==len({e['path']for e in entries})==672
 assert all(not Path(e['path']).is_absolute()and '..'not in Path(e['path']).parts for e in entries)
 return [{**e,'path':SITE_PATH+'/'+e['path'],'gitBlobSha':e['gitBlob']}for e in entries]

def verify_upstream():
 p=load(HERE/'reuse-provenance.json')
 assert p['sourceControlSha']=='856260246fef6302f22b1b49af974e7331e6c9d0'
 for row in p['upstreamFiles']:
  f=HERE/row['localPath'];assert f.is_file()and not f.is_symlink()and sha(f.read_bytes())==row['sha256'],('Immutable upstream drift',row['localPath'])
 assert controls.NATIVE_BLOB=='41ee8a757b7a742b6125ef15b5356e0eca47c01f'
 assert controls.VIEWPORTS==[(320,740),(390,844),(1280,900)]
 return p

def verify_frozen_bytes(root,allow_generated=False):
 root=Path(root).resolve();rows=[]
 for e in frozen_entries():
  f=root/e['path'];cursor=root
  for part in Path(e['path']).parts:
   cursor=cursor/part;assert not cursor.is_symlink(),('Source symlink',e['path'])
  assert f.is_file(),('Missing frozen file',e['path']);b=f.read_bytes()
  if allow_generated and e['path']==GENERATED_REVISION:
   identity=saved();assert controls.git(root,'rev-parse','HEAD')==identity['sourceSha'],'Generated phase wrong HEAD'
   assert b==json.dumps({'revision':identity['sourceSha']},indent=2).encode(),'Post-build revision must be exact HEAD bytes'
   rows.append({'path':e['path'],'sha256':sha(b),'generatedExactHead':True});continue
  assert len(b)==e['bytes']and sha(b)==e['sha256'],('Frozen bytes changed',e['path'])
  assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==e['gitBlobSha']
  rows.append({'path':e['path'],'sha256':e['sha256']})
 return {'files':len(rows),'manifestSha256':MANIFEST_SHA,'phase':'postbuild-exact-head'if allow_generated else 'prebuild-exact-reviewed','verified':True}

def bound_verify_source(root,spec,pristine=False):
 validate_spec(spec);verify_frozen_bytes(root,allow_generated=not pristine)
 # Only the immutable native identity parameter is rebound. Every original guard
 # executes unchanged, plus the stronger full manifest and exact revision guards.
 with patch.object(controls,'NATIVE_BLOB',NATIVE_BLOB):return controls.verify_source(Path(root),spec,pristine=pristine)

def verify_approved_asset_bytes(site,files):
 site=Path(site);entries={e['path']:e for e in frozen_entries()}
 def read_frozen(rel):
  e=entries[SITE_PATH+'/'+rel];p=site/rel;assert p.is_file()and not p.is_symlink()
  b=p.read_bytes();assert len(b)==e['bytes']and sha(b)==e['sha256'],('Asset input changed',rel)
  return json.loads(b)
 products=read_frozen('src/data/products.json');common=read_frozen('src/data/gwanak-copy.json')['common'];banner_manifest=read_frozen('src/data/shared-banner-manifest.json')
 assert len(products)==8 and len(banner_manifest)==3
 paths=[p['img'].lstrip('/')for p in products]+['images/shared-banners/'+common['banners'][v]['file']for v in ['message','budget','consultation']]
 assert len(paths)==len(set(paths))==11 and all(p.startswith(('images/products/','images/shared-banners/'))and '..'not in Path(p).parts for p in paths),'Asset scope drift'
 declared={p['img'].lstrip('/'):p['imageSha256']for p in products};declared.update({'images/shared-banners/'+b['name']+'.webp':b['sha256']for b in banner_manifest})
 assert set(declared)==set(paths),'Approved asset definition mismatch'
 actual_public=controls.manifest(site/'public/images')
 assert {'images/'+p for p in actual_public}==set(paths),'Public image denominator expanded/missing'
 assert {p for p in files if p.startswith('images/')}==set(paths),'Dist image denominator expanded/missing'
 rows=[]
 for rel in paths:
  e=entries[SITE_PATH+'/public/'+rel];assert e['sha256']==declared[rel],'Asset approval hash not frozen'
  public=site/'public'/rel;dist=site/'dist'/rel
  assert public.is_file()and dist.is_file()and not public.is_symlink()and not dist.is_symlink()
  assert sha(public.read_bytes())==sha(dist.read_bytes())==files[rel]==e['sha256'],('Actual source/dist asset bytes drift',rel)
  rows.append({'path':rel,'sha256':e['sha256'],'bytes':e['bytes'],'sourceAndDistMatched':True})
 return {'products':8,'banners':3,'files':rows,'scope':'Actual frozen approved public and built dist bytes; no browser pixel claim'}

def validate_bound_build(site,spec):
 files=controls.validate_build(site,spec)
 verify_approved_asset_bytes(site,files)
 return files

def validate_spec(spec):
 identity=saved()
 for k in ['sourceSha','sourceTree','repositoryTree']:assert spec[k]==identity[k],('Saved identity drift',k)
 assert spec['path']==SITE_PATH and spec['siteUrl']==SITE_URL
 assert spec['routes']==ROUTES and spec['sitemapRoutes']==[]
 assert spec['productionApproved'] is False and spec['indexable'] is False
 assert spec['frozenManifestSha256']==MANIFEST_SHA
 return spec

def make_binding(root,source_sha):
 verify_upstream();root=Path(root).resolve();identity=saved();assert source_sha==identity['sourceSha']
 assert controls.git(root,'rev-parse','HEAD')==source_sha
 verify_frozen_bytes(root)
 data=subprocess.check_output(['git','-C',str(root),'ls-tree','-rz',source_sha,'--',SITE_PATH]);actual={}
 for raw in data.split(b'\0'):
  if not raw:continue
  meta,path=raw.split(b'\t',1);mode,kind,blob=meta.decode().split()
  assert kind=='blob'and mode in ['100644','100755'];actual[path.decode()]=blob
 assert actual=={e['path']:e['gitBlobSha']for e in frozen_entries()},'Saved tree differs from all 672 reviewed files'
 assert GENERATED_REVISION in actual,'Reviewed revision must be tracked in saved source'
 spec={k:identity[k]for k in ['sourceSha','sourceTree','repositoryTree']}
 spec.update(path=SITE_PATH,siteUrl=SITE_URL,productionApproved=False,indexable=False,routes=ROUTES,sitemapRoutes=[],frozenManifestSha256=MANIFEST_SHA)
 bound_verify_source(root,spec,pristine=True);expectations(root/SITE_PATH);return spec

def validate_environment(spec):
 validate_spec(spec);controls.validate_branch(os.environ.get('GITHUB_REF'))
 assert os.environ.get('GITHUB_REPOSITORY')=='joseungil-kr/fwith-site-factory'
 assert re.fullmatch('[0-9a-f]{40}',os.environ.get('GITHUB_SHA',''))
 assert os.environ.get('SITE_FACTORY_REVISION')==spec['sourceSha']
 assert os.environ.get('SITE_URL')==SITE_URL and os.environ.get('SITE_ORIGIN')==SITE_URL and os.environ.get('SITE_INDEXABLE')=='false'

def not_found_contract(common,ui):
 nav=common['navigation'];f=common['footer'];n=common['notFound']
 anchors=[{'href':'#main-content','text':ui['accessibility']['skip']},{'href':'/','text':'✿'+common['brand']}]
 anchors += [{'href':h,'text':nav[k]}for h,k in [('/','home'),(ROUTES[2],'funeral'),(ROUTES[3],'celebration'),('/regions/','regions')]]
 anchors += [{'href':f['phoneHref'],'text':nav['phone']},{'href':n['homeHref'],'text':n['homeLabel']},{'href':f['phoneHref'],'text':f['phoneLabel']},{'href':f['shopHref'],'text':f['shopLabel']},{'href':'/','text':f['homeLinkLabel']},{'href':f['phoneHref'],'text':nav['phone']},{'href':'/regions/','text':nav['regions']}]
 assert len(anchors)==13 and f['shopHref']=='https://fwith.co.kr/'and f['phoneHref']=='tel:1844-0644'
 return {'h1':[n['h1']],'title':n['title'],'description':n['text'],'anchors':anchors}

def expectations(site):
 site=Path(site);pages=load(site/'src/data/pages.json');cov=load(site/'src/data/region-coverage.json');products=load(site/'src/data/products.json')
 cp=load(site/'src/data/gwanak-copy.json');c=cp['common'];ui=load(site/'src/data/gwanak-ui-copy.json');config=load(site/'src/data/site-config.json');plan=load(site/'src/data/gwanak-plan-binding.json')
 assert config['productionApproved']is False and config['hostnameOwnershipVerified']is False and config['previewUrl']==SITE_URL
 assert controls.source_routes(site)==ROUTES and len(pages)==2
 assert [len(p['facilityAnchors'])for p in pages]==[1,3]and [len(p.get('buyerOccasionAnchors',[]))for p in pages]==[0,1]
 assert [len(p['faq'])for p in pages]==[2,2]and len(products)==8
 assert len(cov['units'])==3 and len(cov['administrativeCrosswalk'])==21 and sum(len(a['relations'])for a in cov['administrativeCrosswalk'])==21
 assert [plan[k]for k in ['originalPlanN','originalCandidateN','activePhysicalFacilityN','activeBuyerOccasionN','heldCandidateN']]==[2,15,4,1,10]
 def product(p):return {'key':p['key'],'sku':p['officialSku'],'href':p['orderUrl'],'priceLabel':p['priceLabel'],'name':p['name'],'description':p['desc'],'image':p['img'],'alt':p['imageAlt'],'caption':p['photoCaption'],'cta':p['ctaLabel']}
 exp={'routes':ROUTES,'viewports':[list(x)for x in controls.VIEWPORTS],'captureCount':15,'notFoundContract':not_found_contract(c,ui),'phoneHref':c['footer']['phoneHref'],'common':c,'ui':ui,'homeProducts':[product(p)for p in products],'pages':{},'legalUnits':[x['unitKey']for x in cov['units']]}
 for page in pages:
  article=next(x for x in cp['articles']if x['slug']==page['slug'])
  exp['pages'][page['url']]={'h1':page['h1'],'title':page['title'],'description':page['description'],'firstAnswer':page['firstAnswer'],'faq':[{k:f[k]for k in ['question','answer']}for f in page['faq']],'facilities':page['facilityAnchors'],'occasions':page.get('buyerOccasionAnchors',[]),'products':[product(next(p for p in products if p['officialSku']==sku))for sku in article['productSkus']],'sections':[{k:s[k]for k in ['id','heading','paragraphs']}for s in article['sections']],'sources':article['sourceLinks'],'sourceNote':article['sourceNote'],'relatedLink':article['relatedLink']}
 exp['banners']=[{'variant':v,'src':'/images/shared-banners/'+c['banners'][v]['file'],'alt':c['banners'][v]['alt'],'caption':c['banners']['caption']}for v in ['message','budget','consultation']]
 allfac=[f for p in pages for f in p['facilityAnchors']]
 exp['legalLinks']=[{k:f[k]for k in ['unitKey','href','candidateId']}for f in allfac if f['unitKey']]
 exp['unassignedLinks']=[{k:f[k]for k in ['href','candidateId']}for f in allfac if f['unitKey']is None]
 exp['adminRows']=[{'key':a['aliasKey'],'code':a['administrativeCode'],'name':a['name'],'unitKey':u['unitKey']}for u in cov['units']for a in cov['administrativeCrosswalk']if any(r['unitKey']==u['unitKey']for r in a['relations'])]
 exp['anchorFlows']=[{'kind':'facility','href':f['href'],'candidateId':f['candidateId'],'anchor':f['anchor'],'selector':('[data-facility-legal-unit]'if f['unitKey']else '[data-district-unassigned]')+' a[data-candidate-id="'+f['candidateId']+'"]'}for f in allfac]
 exp['anchorFlows'] += [{'kind':'occasion','href':f['href'],'candidateId':f['candidateId'],'anchor':f['anchor']}for p in pages for f in p.get('buyerOccasionAnchors',[])]
 assert len(exp['legalLinks'])==3 and len(exp['unassignedLinks'])==1 and len(exp['anchorFlows'])==5
 assert exp['unassignedLinks'][0]['candidateId']=='snu-faculty'
 return exp

def validate_not_found_facts(facts,expected):
 c=expected['notFoundContract'];assert facts['h1']==c['h1']and facts['anchors']==c['anchors'],'404 exact heading/anchor contract'
 assert facts['robots']=='noindex,nofollow,noarchive'and facts['canonical']is None
 assert facts['banners']==0 and facts['faq']==[]and facts['images']==[]
 assert facts['extra']['title']==c['title']and facts['extra']['description']==c['description']
 assert facts['extra']['schema']==[],'404 must not inherit Florist schema'

def validate_extra_facts(f,ex,route):
 common=ex['common'];page=ex['pages'].get(route)
 variants=[]if route in ['/regions/','/404.html']else ['message','budget','consultation']
 assert [b['variant']for b in f['banners']]==variants,'Banner order/count'
 for b in f['banners']:
  e=next(x for x in ex['banners']if x['variant']==b['variant'])
  assert all(b[k]==e[k]for k in ['variant','src','alt','caption']),'Banner exact approved copy/asset'
  assert b['naturalWidth']==1774 and b['naturalHeight']==887 and b['width']>0 and abs(b['width']/b['height']-2)<.02,'Banner dimensions/crop'
 expected_products=page['products']if page else ex['homeProducts']if route=='/'else []
 assert f['products']==expected_products,'Exact SKU/name/price/photo/caption/CTA contract'
 expected_images=([ex['homeProducts'][0],ex['homeProducts'][4]]if route=='/'else [page['products'][0]]if page else [])+expected_products
 assert f['productImages']==[{'src':p['image'],'alt':p['alt'],'width':500,'height':500}for p in expected_images],'All product image dimensions/identity/alt'
 assert all(x['valid']for x in f['priceRuns']),'Amount/currency must be on one visual line'
 assert len(f['priceRuns'])==len(expected_images),'All price labels inspected'
 assert f['duplicateIds']==[], 'Duplicate rendered ID'
 if route!='/404.html':
  assert f['schema']==[{'@context':'https://schema.org','@type':'Florist','name':common['brand'],'url':SITE_URL,'telephone':'1844-0644','areaServed':'서울특별시 관악구'}], 'Seller schema exact scope'
  hero=page['products'][0]if page else ex['homeProducts'][0]
  assert f['social']=={'ogTitle':f['title'],'ogDescription':f['description'],'twitterTitle':f['title'],'twitterDescription':f['description'],'ogImage':SITE_URL+hero['image'],'twitterImage':SITE_URL+hero['image'],'ogAlt':hero['alt'],'twitterAlt':hero['alt'],'ogWidth':'500','ogHeight':'500'}, 'Social metadata exact product contract'
 assert f['footer']=={'brand':common['footer']['brandLine'],'anchors':[{'href':common['footer']['phoneHref'],'text':common['footer']['phoneLabel']},{'href':common['footer']['shopHref'],'text':common['footer']['shopLabel']},{'href':'/','text':common['footer']['homeLinkLabel']}]},'Footer exact copy/CTA'
 if page:
  assert f['title']==page['title']and f['description']==page['description']and f['h1']==[page['h1']],'Detail head/H1'
  assert f['firstAnswer']==page['firstAnswer']and f['sections']==page['sections'],'Exact section order/paragraphs/headings'
  assert f['faq']==page['faq'],'Visible exact FAQ'
  assert f['facilities']==[{'id':x['anchor'],'heading':x['heading'],'tag':'H2','count':1}for x in page['facilities']],'Facility H2 single anchors'
  assert f['occasions']==[{'id':x['anchor'],'heading':x['heading'],'tag':'H2','count':1}for x in page['occasions']],'Opening occasion single H2'
  assert f['sources']==page['sources']and f['sourceNote']==page['sourceNote'],'Full source attribution including FAQ page 2'
  assert f['relatedLink']==page['relatedLink'],'Related article CTA'
 else:
  assert f['faq']==[]and f['sections']==[]and f['facilities']==[]and f['occasions']==[],'Unexpected article content'
  c=common['home']if route=='/'else common['directory']if route=='/regions/'else common['notFound']
  assert f['title']==c['title']and f['h1']==[c['h1']]
  assert f['description']==c.get('metaDescription',c.get('intro',c.get('text')))
 if route in ['/','/regions/']:
  assert f['guideCards']==[{k:c[k]for k in ['href','title','summary','ctaLabel']}for c in common['articleCards']],'Exactly two real purchase cards'
 if route=='/regions/':
  assert f['legalUnits']==ex['legalUnits']and f['adminRows']==ex['adminRows'],'3 legal / 21 administrative / 21 relations'
  assert sorted(f['legalLinks'],key=lambda x:x['candidateId'])==sorted(ex['legalLinks'],key=lambda x:x['candidateId'])
  assert f['unassignedLinks']==ex['unassignedLinks'],'Faculty club remains district-only'
  assert f['adminFacilityLinks']==[],'No implied administrative facility assignment'

# Reused geometry, footer and risk-based screenshot selection retain their exact logic.
def assert_focus(facts):
    assert facts['visible'] and facts['width']>0 and facts['height']>0, 'Invisible focus target'
    assert facts['left']>=-.5 and facts['right']<=facts['viewportWidth']+.5, 'Focus horizontal clipping'
    assert facts['top']>=facts['safeTop']-.5 and facts['bottom']<=facts['safeBottom']+.5, 'Target clipped by viewport/sticky overlay'
    assert facts['hitTests'] and all(facts['hitTests']), 'Focus target occluded'


def assert_keyboard_focus(f):
 assert f['tag']!='BODY'and f['visible']and f['width']>0 and f['height']>0,'Missing/hidden keyboard target'
 assert f['left']>=-.5 and f['right']<=f['viewportWidth']+.5 and f['top']>=-.5 and f['bottom']<=f['viewportHeight']+.5,'Keyboard target clipped by viewport'
 assert f['region']in ['content','header','mobile-bar','skip'],'Unexpected focus region'
 assert f['top']>=f['safeTop']-.5 and f['bottom']<=f['safeBottom']+.5,'Keyboard target partly covered by sticky UI'
 assert f['fragmentCount']>0 and len(f['hitTests'])==f['fragmentCount']*9 and all(f['hitTests']),'Keyboard target fragment occluded'
 assert f['focusVisible']and f['outlineWidth']>=1 and f['outlineStyle']!='none','Focus ring missing'

def assert_footer_content(facts):
    """Check readable footer content, never the intentional padded footer shell."""
    assert_focus(facts)
    footer=facts.get('footerContent')
    assert isinstance(footer,dict) and footer.get('selector')=='footer > div', 'Footer content wrapper required'
    assert footer['contentBottom']==facts['bottom'], 'Footer content geometry mismatch'
    assert footer['barTop']==facts['safeBottom'], 'Footer overlay boundary mismatch'
    # shellBottom is retained as evidence but may extend below barTop because the
    # original CSS reserves fixed-CTA/safe-area padding inside the footer shell.
    assert footer['contentBottom']<=footer['barTop']+.5, 'Footer content overlaps fixed CTA'
    assert footer['items'], 'Footer readable content missing'
    for item in footer['items']:
        assert item['visible'] and item['text'].strip(), 'Footer text/link is hidden or empty'
        assert item['top']>=facts['safeTop']-.5 and item['bottom']<=footer['barTop']+.5, 'Footer text/link overlaps sticky UI'
        assert item['left']>=-.5 and item['right']<=facts['viewportWidth']+.5, 'Footer text/link horizontal clipping'
        assert item['hitTests'] and all(item['hitTests']), 'Footer text/link occluded'


def focus_labels(expected,route):
 labels=['header','footer']
 if route not in ['/regions/','/404.html']:labels += ['banner-'+b['variant']for b in expected['banners']]
 if route=='/':labels += ['product-'+x['key']for x in expected['homeProducts']]
 if route in expected['pages']:
  p=expected['pages'][route]
  labels += ['faq-'+str(i)for i in range(len(p['faq']))]
  labels += ['facility-'+x['anchor']for x in p['facilities']]
  labels += ['occasion-'+x['anchor']for x in p['occasions']]
  labels += ['product-'+x['key']for x in p['products']]
  labels += ['source-'+str(i)for i in range(len(p['sources']))]
  labels += ['heading-'+x['id']for x in p['sections']]
 if route=='/regions/':labels += ['legal-'+str(i)for i in range(3)]+['admin-'+str(i)for i in range(21)]+['district-unassigned']
 return labels

def screenshot_selection(rows):
    """Keep every geometry check, deduplicate only redundant visible-pixel evidence."""
    selected={};seen={}
    def key(row):return (row['width'],row['route'],row['label'])
    def choose(row,reason):selected.setdefault(key(row),[]).append(reason)
    for row in rows:
        label=row['label']; facts=row.get('facts',{})
        if row.get('issues'):choose(row,'failed-geometry-or-occlusion')
        if label.startswith('faq-'):choose(row,'every-unique-FAQ-at-every-width')
        if label.startswith('banner-') or label=='footer':
            signature=(row['width'],label,facts.get('renderSignature'),round(facts.get('width',0),2),round(facts.get('height',0),2))
            if signature not in seen:
                choose(row,'first-distinct-shared-component-rendering');seen[signature]=key(row)
    for width,height in controls.VIEWPORTS:
        legal=[r for r in rows if r['width']==width and r['route']=='/regions/' and r['label'].startswith('legal-')]
        admin=[r for r in rows if r['width']==width and r['route']=='/regions/' and r['label'].startswith('admin-')]
        for group,prefix in ((legal,'legal'),(admin,'admin')):
            if not group:continue
            choose(max(group,key=lambda r:r.get('facts',{}).get('height',0)),prefix+'-tallest-wrapped-row')
            choose(group[-1],prefix+'-last-boundary-row')
            if prefix=='admin':choose(group[0],'administrative-first-partial-relation-row')
    return selected


def validate_supplemental_evidence(rows,flows,expected,output):
 grid=[(w,h,r,l)for w,h in controls.VIEWPORTS for r in ROUTES for l in focus_labels(expected,r)]
 assert [(r['width'],r['height'],r['route'],r['label'])for r in rows]==grid,'Supplemental geometry coverage missing/duplicate/reordered'
 needed=[(w,'anchor-first-landing',f['href'])for w,h in controls.VIEWPORTS for f in expected['anchorFlows']]
 actual=[(f['width'],f['flow'],f.get('href'))for f in flows if f['flow']=='anchor-first-landing']
 assert actual==needed,'All 4 facility + 1 occasion anchors at all widths required'
 keyboard=[(f['width'],f['route'])for f in flows if f['flow']=='keyboard-tab-focus']
 assert keyboard==[(w,r)for w,h in controls.VIEWPORTS for r in ROUTES],'Keyboard route/width coverage'
 assert all(f.get('passed')for f in flows),'Interaction failed'
 assert all(all(k in f for k in ['screenshot','screenshotSha256','dimensions'])for f in flows),'Every anchor and keyboard flow requires screenshot/hash/dimensions'
 assert len(flows)==30,'Unexpected interaction scope'
 selected=screenshot_selection(rows)
 assert {(r['width'],r['route'],r['label'])for r in rows if 'screenshot'in r}==set(selected),'Risk-based screenshot coverage'
 for r in rows:assert r.get('screenshotReasons',[])==selected.get((r['width'],r['route'],r['label']),[])
 shots=[r for r in rows if 'screenshot'in r]+[f for f in flows if 'screenshot'in f]
 assert len({r['screenshot']for r in shots})==len(shots),'Duplicate screenshot path'
 for r in shots:
  rel=r['screenshot'];assert rel.startswith('supplemental/')and '..'not in Path(rel).parts
  f=Path(output)/rel;assert f.is_file()and not f.is_symlink()and sha(f.read_bytes())==r['screenshotSha256']
  dims=controls.jpeg_dimensions(f.read_bytes());assert dims==r['dimensions']and dims=={'width':r['width'],'height':dict(controls.VIEWPORTS)[r['width']]}
 return {'geometryChecks':len(rows),'riskBasedScreenshots':len(selected),'anchorScreenshots':sum(f['flow']=='anchor-first-landing'and 'screenshot'in f for f in flows),'keyboardScreenshots':sum(f['flow']=='keyboard-tab-focus'and 'screenshot'in f for f in flows),'keyboardFlows':len(keyboard),'interactionChecks':len(flows)}

def main():
 p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
 q=sub.add_parser('check-local');q.add_argument('--root',type=Path,required=True);q.add_argument('--output',type=Path,required=True)
 q=sub.add_parser('bind');q.add_argument('--root',type=Path,required=True);q.add_argument('--sha',required=True);q.add_argument('--output',type=Path,required=True)
 for name in ['source','manifest']:
  q=sub.add_parser(name);q.add_argument('--root',type=Path,required=True);q.add_argument('--binding',type=Path,required=True);q.add_argument('--output',type=Path,required=True)
 q=sub.add_parser('seal');q.add_argument('--binding',type=Path,required=True);q.add_argument('--evidence',type=Path,required=True)
 a=p.parse_args();verify_upstream()
 if a.command=='check-local':write(a.output,{'status':'LOCAL_PREPARATION_ONLY','frozenSource':verify_frozen_bytes(a.root),'expectations':expectations(a.root/SITE_PATH),'browserExecuted':False,'remoteWrites':False})
 elif a.command=='bind':write(a.output,make_binding(a.root,a.sha))
 elif a.command=='seal':
  spec=validate_spec(load(a.binding));validate_environment(spec);files=controls.manifest(a.evidence);files.pop('evidence-manifest.json',None)
  write(a.evidence/'evidence-manifest.json',{'sourceSha':spec['sourceSha'],'sourceTree':spec['sourceTree'],'repositoryTree':spec['repositoryTree'],'controlSha':os.environ['GITHUB_SHA'],'runId':os.environ['GITHUB_RUN_ID'],'runAttempt':os.environ['GITHUB_RUN_ATTEMPT'],'files':files,'pixelReview':'pending','publicationAuthorization':'not-issued'})
 else:
  spec=validate_spec(load(a.binding));validate_environment(spec);site=bound_verify_source(a.root,spec,pristine=a.command=='source');expectations(site)
  if a.command=='source':write(a.output,{'spec':spec,'actualHead':controls.git(a.root,'rev-parse','HEAD'),'frozenBytesVerified':True,'files':672,'revisionTracked':True})
  else:
   files=validate_bound_build(site,spec);a.output.write_bytes(controls.compact(files))
   write(a.output.with_suffix('.assets.json'),{'sourceSha':spec['sourceSha'],**verify_approved_asset_bytes(site,files)})
 print(json.dumps({'command':a.command,'status':'verified','browserExecuted':False}))
if __name__=='__main__':main()
