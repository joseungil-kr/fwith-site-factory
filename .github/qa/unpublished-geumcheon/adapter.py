#!/usr/bin/env python3
"""Exact source-bound banner-successor QA. Offline preparation is not a saved source or browser pass."""
from pathlib import Path
import argparse,hashlib,json,os,re,stat,struct,subprocess,sys,zlib
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'upstream'))
import controls
REGION='geumcheon'
SITE_PATH='site-factory/seoul-'+REGION+'-flower'
CONTRACT_SHA='4e38935632be0b2a225f1794ea6efaabf3dc4bfed59ab3fcf10daa113cdfa62c'
PROVENANCE_SHA='0ec58beb8220c54ea0aac7374be4ae48582fc9a8308e65f7f387aa7be409d4b1'
def load(p):return json.loads(Path(p).read_text())
def sha(b):return hashlib.sha256(b).hexdigest()
def write(p,v):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def contract():
 p=HERE/'source-contract.json';assert sha(p.read_bytes())==CONTRACT_SHA,'Source contract drift'
 return load(p)
C=contract();SITE_URL=C['siteUrl'];ROUTES=C['routes'];MANIFEST_SHA=C['sourceManifestSha256']
GENERATED_REVISION=SITE_PATH+'/src/data/build-revision.json'
def saved():
 x=load(HERE/'bound-spec.json')
 for k in ('sourceSha','sourceTree','repositoryTree'):
  assert isinstance(x.get(k),str) and re.fullmatch('[0-9a-f]{40}',x[k]) and x[k]!='0'*40,('Saved identity pending/invalid',k)
 assert x['sourceSavedAndIndependentlyReadBack']is True,'Saved source independent readback pending'
 assert x['sourceTree']==C['sourceTree'],'Saved site tree differs from exact proposed bytes'
 return x

def frozen_entries():
 p=HERE/'frozen-inputs/source-file-manifest.banner-phone.json';assert sha(p.read_bytes())==MANIFEST_SHA,'Frozen manifest drift'
 current=load(p);p=HERE/'frozen-inputs/source-file-manifest.before-banner.json';assert sha(p.read_bytes())==C['baseManifestSha256'],'Baseline manifest drift'
 old=load(p)
 def index(rows):
  assert len(rows)==len({e['path']for e in rows})
  for e in rows:
   assert e['path'].startswith(SITE_PATH+'/')and '..'not in Path(e['path']).parts
   assert e['mode']in ('100644','100755')and isinstance(e['bytes'],int)and e['bytes']>0
   assert re.fullmatch('[0-9a-f]{64}',e['sha256'])and re.fullmatch('[0-9a-f]{40}',e['gitBlobSha'])
  return {e['path']:e for e in rows}
 a=index(old);b=index(current)
 assert len(a)==C['beforeFileCount']and len(b)==C['sourceFileCount']
 assert not set(a)-set(b),'Source deletion'
 assert sorted(set(b)-set(a))==C['addedPaths'],'Unapproved added path'
 assert sorted(p for p in a if a[p]!=b[p])==C['modifiedPaths'],'Unapproved source changes'
 return current

def verify_upstream():
 p=HERE/'reuse-provenance.json';assert sha(p.read_bytes())==PROVENANCE_SHA,'Reuse provenance drift'
 x=load(p)
 for row in x['upstreamFiles']:
  f=HERE/row['localPath'];assert f.is_file()and not f.is_symlink()and sha(f.read_bytes())==row['sha256'],('Immutable upstream drift',row['localPath'])
 assert controls.NATIVE_BLOB=='41ee8a757b7a742b6125ef15b5356e0eca47c01f'
 assert controls.VIEWPORTS==[(320,740),(390,844),(1280,900)]
 return x

def native_output_names():
 return {'home-mobile.png','report.json'}|{f'detail-{w}-{part}.png'for w in (390,1280)for part in ('top','body','faq')}

def verify_native_output(site,native_evidence):
 generated=Path(site)/'browser-rendering-qa';evidence=Path(native_evidence)
 assert generated.resolve()!=evidence.resolve(),'Native evidence must be separate copy'
 expected=native_output_names();assert len(expected)==8
 for root in (generated,evidence):
  assert root.is_dir()and all(not p.is_symlink()for p in [root,*root.parents]),'Unsafe native output root/parent'
  nodes=list(root.iterdir());assert {p.name for p in nodes}==expected,'Native output exact file set'
  for p in nodes:assert not p.is_symlink()and stat.S_ISREG(p.lstat().st_mode),'Native output link/special/directory'
 for name in expected:
  raw=(generated/name).read_bytes();assert raw==(evidence/name).read_bytes(),'Native output differs from evidence copy'
  if name.endswith('.png'):
   assert raw.startswith(b'\x89PNG\r\n\x1a\n'),'Native output is not PNG'
   pos=8;first=True;ended=False
   while pos<len(raw):
    assert pos+12<=len(raw),'Truncated PNG chunk'
    n=struct.unpack('>I',raw[pos:pos+4])[0];kind=raw[pos+4:pos+8];end=pos+12+n
    assert end<=len(raw),'Truncated PNG data'
    assert zlib.crc32(raw[pos+4:pos+8+n])&0xffffffff==struct.unpack('>I',raw[pos+8+n:end])[0],'PNG CRC'
    if first:
     assert kind==b'IHDR'and n==13,'PNG header'
     width,height=struct.unpack('>II',raw[pos+8:pos+16]);assert 0<width<=1280 and 0<height<=100000,'PNG dimensions'
     first=False
    pos=end
    if kind==b'IEND':assert n==0 and pos==len(raw),'PNG trailing data';ended=True;break
   assert ended,'PNG missing end'
 report=load(generated/'report.json')
 assert set(report)=={'localOrigin','scope','checks','errors'}and report['errors']==[],'Native report errors/schema'
 m=re.fullmatch(r'http://127[.]0[.]0[.]1:([0-9]+)',report['localOrigin']);assert m and 0<int(m.group(1))<65536
 assert report['scope']=='Local static artifact only; not public HTTP verification'
 assert [(r['route'],r['width'],r['height'])for r in report['checks']]==[(r,w,h)for w,h in controls.VIEWPORTS for r in ROUTES],'Native exact route grid'
 assert all(r['http']==200 and r['issues']==[]for r in report['checks']),'Native failed route'
 return {'files':8,'checks':len(ROUTES)*3,'sameEvidenceBytes':True}

def verify_scoped_source_tree(root,allow_generated=False,*,native_evidence=None):
 root=Path(root);site=root/SITE_PATH
 assert root.is_dir()and site.is_dir()and all(not p.is_symlink()for p in [site,*site.parents]),'Source root/parent symlink'
 expected={e['path'].removeprefix(SITE_PATH+'/')for e in frozen_entries()}
 if allow_generated:expected.add('src/data/build-revision.json')
 expected_top={p.split('/')[0]for p in expected}
 dirs={'node_modules','dist','.astro'}if allow_generated else set()
 reports=set(C['nativeGeneratedReports'])if allow_generated else set()
 if native_evidence is not None:
  assert allow_generated,'Native output forbidden in prebuild'
  verify_native_output(site,native_evidence);dirs.add('browser-rendering-qa')
 for p in site.iterdir():
  mode=p.lstat().st_mode
  assert not p.is_symlink()and(stat.S_ISREG(mode)or stat.S_ISDIR(mode)),'Unsafe source root entry'
  assert p.name in expected_top|dirs|reports,('Unreviewed source root entry',p.name)
  if p.name in dirs:assert p.is_dir(),'Generated directory type changed'
  if p.name in reports:assert p.is_file()and isinstance(load(p),dict),'Generated report type/schema'
 actual=set()
 for name in expected_top:
  top=site/name;assert top.exists(),('Missing source root entry',name)
  for p in ([top,*top.rglob('*')]if top.is_dir()else[top]):
   mode=p.lstat().st_mode;rel=p.relative_to(site).as_posix()
   assert not p.is_symlink()and(stat.S_ISREG(mode)or stat.S_ISDIR(mode)),'Source tree link/special file'
   assert '__pycache__'not in p.relative_to(site).parts,'Source Python cache forbidden'
   if stat.S_ISREG(mode):actual.add(rel)
 assert actual==expected,'Unreviewed/missing source file'
 return True

def verify_frozen_bytes(root,allow_generated=False,*,native_evidence=None):
 verify_scoped_source_tree(root,allow_generated,native_evidence=native_evidence)
 root=Path(root);rows=frozen_entries()
 if allow_generated:
  x=saved();assert controls.git(root,'rev-parse','HEAD')==x['sourceSha'],'Generated revision needs exact saved HEAD'
  p=root/GENERATED_REVISION;assert p.is_file()and not p.is_symlink()and stat.S_IMODE(p.stat().st_mode)==0o644,'Generated revision type/mode'
  assert p.read_bytes()==json.dumps({'revision':x['sourceSha']},indent=2).encode(),'Generated revision must equal saved HEAD bytes'
 for e in rows:
  f=root/e['path'];b=f.read_bytes();assert stat.S_IMODE(f.stat().st_mode)==(int(e['mode'],8)&0o777),('Frozen mode changed',e['path'])
  if allow_generated and e['path']==GENERATED_REVISION:
   x=saved();assert controls.git(root,'rev-parse','HEAD')==x['sourceSha'],'Generated revision needs exact saved HEAD'
   assert b==json.dumps({'revision':x['sourceSha']},indent=2).encode(),'Generated revision must equal saved HEAD bytes'
   continue
  assert len(b)==e['bytes']and sha(b)==e['sha256'],('Frozen source changed',e['path'])
  assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==e['gitBlobSha']
 return {'files':len(rows),'manifestSha256':MANIFEST_SHA,'verified':True,'phase':'postbuild'if allow_generated else 'prebuild'}

def expectations(site):
 site=Path(site);pages=load(site/'src/data/pages.json');coverage=load(site/'src/data/region-coverage.json');products=load(site/'src/data/products.json')
 common=load(site/f'src/data/{REGION}-copy.json')['common'];config=load(site/'src/data/site-config.json');banner=load(site/'src/data/shared-banner-manifest.json')
 assert config['productionApproved']is True and config['hostnameOwnershipVerified']is False and config['previewUrl']==SITE_URL
 assert controls.source_routes(site)==ROUTES
 historical=common['sharedBanners']['assets']if REGION=='geumcheon'else common['bannerPolicy']['banners']
 historical={b.get('variant',b.get('key')):b for b in historical}
 def chosen(p):
  return [x for key in p['productCardKeys']for x in products if x['key']==key]
 result={'routes':ROUTES,'customerRoutes':ROUTES[:-1],'viewports':[list(x)for x in controls.VIEWPORTS],'captureCount':len(ROUTES)*3,'customerCaptureCount':(len(ROUTES)-1)*3,'productionApproved':True,'qaPublicationApproved':False,'indexable':False,'sitemapRoutes':[],
 'homeProducts':[{k:p[k]for k in ('key','priceLabel')}|{'href':p['orderUrl']}for p in products],
 'pages':{p['url']:{'faq':p['faq'],'facilities':p['facilityAnchors'],'products':[{'key':x['key'],'sku':x['officialSku'],'href':x['orderUrl'],'priceLabel':x['priceLabel']}for x in chosen(p)]}for p in pages},
 'banners':[{'variant':x['name'].removeprefix('flower-'),'src':'/images/shared-banners/'+x['name']+'.webp','sha256':x['sha256'],'width':1774,'height':887,'alt':historical[x['name'].removeprefix('flower-')]['alt']+' 전화 1844-0644.'}for x in banner],
 'legalUnits':[u['unitKey']for u in coverage['units']],
 'legalLinks':[{k:f[k]for k in ('unitKey','href','candidateId')}for p in pages for f in p['facilityAnchors']],
 'adminFacilityLinks':[f['href']for a in coverage['administrativeCrosswalk']for rel in a['relations']for p in pages for f in p['facilityAnchors']if f['unitKey']==rel['unitKey']]if REGION=='geumcheon'else [],
 'adminRows':[{'key':a['aliasKey'],'relations':[next(u['name']for u in coverage['units']if u['unitKey']==rel['unitKey'])+(' 일부'if rel['scope']=='partial'else '')for rel in a['relations']]}for a in coverage['administrativeCrosswalk']]}
 assert sha(controls.compact(result))==C['expectationsSha256'],'Frozen regional rendering contract drift'
 return result

def validate_spec(spec):
 x=saved();assert spec==x,'Exact source spec drift'
 assert spec['path']==SITE_PATH and spec['siteUrl']==SITE_URL
 assert spec['productionApproved']is True and spec['qaPublicationApproved']is False and spec['hostnameOwnershipVerified']is False and spec['indexable']is False
 assert spec['routes']==ROUTES and spec['sitemapRoutes']==[]and spec['frozenManifestSha256']==MANIFEST_SHA
 return spec

def verify_global_checkout(root):
 # The reviewed revision file is untracked in both sources; no tracked exception.
 assert not controls.git(root,'diff','--name-only','HEAD','--'),'Global tracked checkout drift'
 assert not controls.git(root,'diff','--cached','--name-only','HEAD','--'),'Global staged checkout drift'
 for options in [('only',),('ignored',)]:
  flags=['--others','--exclude-standard'] if options==('only',) else ['--others','--ignored','--exclude-standard']
  raw=subprocess.check_output(['git','-C',str(root),'ls-files','-z',*flags])
  for item in raw.split(b'\0'):
   if item:assert item.decode().startswith(SITE_PATH+'/'),'Unreviewed file outside source subtree'
 return True

def make_binding(root,source_sha):
 verify_upstream();spec=saved();assert source_sha==spec['sourceSha'];validate_spec(spec)
 verify_global_checkout(root);verify_frozen_bytes(root);assert controls.git(root,'rev-parse','HEAD')==source_sha
 assert controls.git(root,'rev-list','--parents','-n','1',source_sha).split()==[source_sha,C['baseSourceSha']], 'Saved successor must have the exact independently reviewed live baseline parent'
 actual={}
 for raw in subprocess.check_output(['git','-C',str(root),'ls-tree','-rz',source_sha,'--',SITE_PATH]).split(b'\0'):
  if not raw:continue
  meta,p=raw.split(b'\t',1);mode,kind,blob=meta.decode().split();assert kind=='blob'and mode in ('100644','100755')
  actual[p.decode()]={'mode':mode,'gitBlobSha':blob}
 assert actual=={e['path']:{k:e[k]for k in ('mode','gitBlobSha')}for e in frozen_entries()},'Exact committed site tree mismatch'
 controls.verify_source(Path(root),spec,pristine=True);expectations(Path(root)/SITE_PATH);return spec

def validate_environment(spec):
 validate_spec(spec);controls.validate_branch(os.environ.get('GITHUB_REF'))
 assert os.environ.get('GITHUB_ACTIONS')=='true','Only actual authorized GitHub Actions runner'
 assert os.environ.get('GITHUB_REPOSITORY')=='joseungil-kr/fwith-site-factory'
 assert re.fullmatch('[0-9a-f]{40}',os.environ.get('GITHUB_SHA',''))
 assert os.environ.get('SITE_FACTORY_REVISION')==spec['sourceSha']
 assert os.environ.get('SITE_URL')==SITE_URL and os.environ.get('SITE_ORIGIN')==SITE_URL and os.environ.get('SITE_INDEXABLE')=='false'

def bound_verify_source(root,spec,pristine=False):
 verify_global_checkout(root)
 native=None
 if not pristine and (Path(root)/SITE_PATH/'browser-rendering-qa').exists():native=Path(os.environ['EVIDENCE_ROOT'])/'native'
 verify_frozen_bytes(root,allow_generated=not pristine,native_evidence=native)
 return controls.verify_source(Path(root),spec,pristine=pristine)

def validate_bound_build(site,spec):
 files=controls.validate_build(site,spec)
 for b in expectations(site)['banners']:
  rel=b['src'].lstrip('/');assert sha((Path(site)/'public'/rel).read_bytes())==sha((Path(site)/'dist'/rel).read_bytes())==files[rel]==b['sha256'],'Frozen banner bytes differ in actual build'
 return files

def validate_extra_facts(facts, expected, route):
    variants=[] if route in ('/regions/','/404.html') else ['message','budget','consultation']
    assert [b['variant'] for b in facts['banners']]==variants, 'Banner order/count'
    for b in facts['banners']:
        source=next(x for x in expected['banners'] if x['variant']==b['variant'])
        assert b['src']==source['src'] and b['naturalWidth']==1774 and b['naturalHeight']==887, 'Banner asset mismatch'
        assert b['width']>0 and abs(b['width']/b['height']-2)<.02, 'Banner geometry/cropping'
        assert b['alt'].strip() and b['alt']==source['alt'], 'Exact phone-inclusive banner alternative text'
        assert b['caption']=='' and b['figcaptionCount']==0, 'Shared banner caption must be absent from DOM'
    page=expected['pages'].get(route)
    if page:
        assert facts['faq']==page['faq'], 'Visible FAQ copy differs'
        assert facts['products']==[{k:x[k] for k in ('key','href','priceLabel')}for x in page['products']], 'Product card/price/order mismatch'
        assert facts['facilities']==[{'id':f['anchor'],'heading':f['heading'],'tag':'H3' if REGION=='yeongdeungpo' and 'funeral' in route else 'H2'} for f in page['facilities']], 'Facility heading/anchor mismatch'
    else: assert facts['faq']==[], 'Unexpected FAQ'
    if route=='/':
        assert facts['products']==expected['homeProducts'], 'Home product card/price/order mismatch'
    if route=='/regions/':
        assert facts['guideLinks']==ROUTES[2:-1], 'Directory guide card count/scope'
        assert facts['legalUnits']==expected['legalUnits'], 'Legal geography differs'
        assert sorted(facts['legalLinks'],key=lambda x:x['candidateId'])==sorted(expected['legalLinks'],key=lambda x:x['candidateId']), 'Legal facility links differ'
        assert facts['adminRows']==expected['adminRows'], 'Administrative relation mismatch'
        assert facts['adminFacilityLinks']==expected['adminFacilityLinks'], 'Administrative destination links differ from exact region source'

def assert_focus(facts):
    assert facts['visible'] and facts['width']>0 and facts['height']>0, 'Invisible focus target'
    assert facts['left']>=-.5 and facts['right']<=facts['viewportWidth']+.5, 'Focus horizontal clipping'
    assert facts['top']>=facts['safeTop']-.5 and facts['bottom']<=facts['safeBottom']+.5, 'Target clipped by viewport/sticky overlay'
    assert facts['hitTests'] and all(facts['hitTests']), 'Focus target occluded'


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


def focus_labels(expected, route):
    labels=['header','footer']
    if route not in ('/regions/','/404.html'):
        labels += ['banner-'+x['variant'] for x in expected['banners']]
    if route=='/':
        labels += ['product-'+x['key']for x in expected['homeProducts']]
    if route in expected['pages']:
        page=expected['pages'][route]
        labels += ['faq-'+str(i) for i in range(len(page['faq']))]
        labels += ['facility-'+x['anchor'] for x in page['facilities']]
        labels += ['product-'+x['key'] for x in page['products']]
    if route=='/regions/':
        labels += ['legal-'+str(i) for i in range(len(expected['legalUnits']))]+['admin-'+str(i) for i in range(len(expected['adminRows']))]
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


def validate_supplemental_evidence(rows, flows, expected, output):
    grid=[(w,h,route,label)for w,h in controls.VIEWPORTS for route in ROUTES for label in focus_labels(expected,route)]
    assert [(r['width'],r['height'],r['route'],r['label'])for r in rows]==grid, 'Supplemental coverage incomplete/duplicate/reordered'
    expected_flows=[]
    for width,height in controls.VIEWPORTS:
        expected_flows.append((width,'admin-open-close-reopen',None))
        expected_flows += [(width,'legal-facility-anchor-first-landing',x['href'])for x in expected['legalLinks']]
    assert [(f['width'],f['flow'],f.get('href'))for f in flows]==expected_flows, 'Interaction coverage incomplete'
    selected=screenshot_selection(rows)
    assert {(r['width'],r['route'],r['label'])for r in rows if 'screenshot' in r}==set(selected),'Required representative/failed screenshots missing or duplicate scope'
    for r in rows:
        key=(r['width'],r['route'],r['label'])
        assert r.get('screenshotReasons',[])==selected.get(key,[]),'Screenshot selection reason differs'
    banner_grid={(w,'banner-'+b['variant'])for w,h in controls.VIEWPORTS for b in expected['banners']}
    assert {(r['width'],r['label'])for r in rows if 'screenshot' in r and r['label'].startswith('banner-')}==banner_grid, 'Missing phone-banner viewport evidence'
    assert len([r for r in rows if r['route']=='/' and 'screenshot' in r and r['label'].startswith('banner-')])==9, 'Nine exact primary phone views required'
    assert all('screenshot' in f for f in flows if f['flow']=='legal-facility-anchor-first-landing'),'Missing initial anchor screenshot'
    assert all(f.get('passed') is True for f in flows if f['flow']=='admin-open-close-reopen'),'Missing details interaction proof'
    shots=[r for r in rows if 'screenshot' in r]+[f for f in flows if 'screenshot' in f]
    assert len({r['screenshot']for r in shots})==len(shots),'Duplicate supplemental screenshot'
    for r in shots:
        assert r.get('imageReadiness')=='decode-completed-and-two-paint-frames-awaited', 'Screenshot image readiness missing'
        rel=r['screenshot'];assert rel.startswith('supplemental/') and '..' not in Path(rel).parts
        file=Path(output)/rel;assert file.is_file() and not file.is_symlink(),'Missing supplemental screenshot'
        assert sha(file.read_bytes())==r['screenshotSha256'],'Supplemental screenshot hash mismatch'
        dims=controls.jpeg_dimensions(file.read_bytes())
        assert dims==r['dimensions'] and dims['width']==r['width'],'Supplemental screenshot dimensions'
        assert dims['height']==dict(controls.VIEWPORTS)[r['width']],'Viewport screenshot must not be full-page'
    return {'geometryChecks':len(rows),'focusScreenshots':len(selected),'anchorFirstLandingScreenshots':len(shots)-len(selected),'interactions':len(flows)}



def main():
 p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
 q=sub.add_parser('check-local');q.add_argument('--root',type=Path,required=True);q.add_argument('--output',type=Path,required=True)
 q=sub.add_parser('bind');q.add_argument('--root',type=Path,required=True);q.add_argument('--sha',required=True);q.add_argument('--output',type=Path,required=True)
 for name in ('source','manifest'):
  q=sub.add_parser(name);q.add_argument('--root',type=Path,required=True);q.add_argument('--binding',type=Path,required=True);q.add_argument('--output',type=Path,required=True)
 q=sub.add_parser('seal');q.add_argument('--binding',type=Path,required=True);q.add_argument('--evidence',type=Path,required=True)
 a=p.parse_args();verify_upstream()
 if a.command=='check-local':write(a.output,{'status':'LOCAL_SOURCE_PREPARATION_ONLY','source':verify_frozen_bytes(a.root),'expectations':expectations(a.root/SITE_PATH),'sourceIdentity':'pending-independent-GitHub-readback','browserExecuted':False})
 elif a.command=='bind':write(a.output,make_binding(a.root,a.sha))
 elif a.command=='seal':
  spec=validate_spec(load(a.binding));validate_environment(spec);files=controls.manifest(a.evidence);files.pop('evidence-manifest.json',None)
  write(a.evidence/'evidence-manifest.json',{'sourceSha':spec['sourceSha'],'sourceTree':spec['sourceTree'],'repositoryTree':spec['repositoryTree'],'controlSha':os.environ['GITHUB_SHA'],'runId':os.environ['GITHUB_RUN_ID'],'runAttempt':os.environ['GITHUB_RUN_ATTEMPT'],'files':files,'pixelReview':'pending','publicationAuthorization':'not-issued'})
 else:
  spec=validate_spec(load(a.binding));validate_environment(spec);site=bound_verify_source(a.root,spec,pristine=a.command=='source');expectations(site)
  if a.command=='source':write(a.output,{'spec':spec,'actualHead':controls.git(a.root,'rev-parse','HEAD'),'frozenBytesVerified':True})
  else:a.output.write_bytes(controls.compact(validate_bound_build(site,spec)))
if __name__=='__main__':main()
