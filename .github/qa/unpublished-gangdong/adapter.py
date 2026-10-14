"""Gangdong schema boundary. Safe local verification; browser entrypoint is runner-only."""
from pathlib import Path, PurePosixPath
from functools import partial
from urllib.parse import urlsplit,urljoin
import hashlib, importlib.util, json, math, os, re, stat, struct, subprocess, sys
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'upstream'))
import controls as upstream
SPEC_PATH=HERE/'bound-spec.json'
SOURCE_SHA='9c044584505eec60c71f2bc7add497f0902f5424'
ROOT_TREE='ed67c4474d713452e51b2abbc5dd7119a0d4787f'
PROJECT_TREE='a7e8ff540822dc7ee326f1503a9a2bbccf07f996'
SITE_PATH='site-factory/seoul-gangdong-flower'
REF='refs/heads/qa/gangdong-local-preview-20261014'
ORIGIN='https://seoul-gangdong.local.invalid'
ROUTES=['/','/regions/gangdong-condolence-wreath/','/regions/gangdong-wedding-wreath/','/regions/','/404.html']
VIEWPORTS=[(320,740),(390,844),(1280,900)]
DOM_CONTRACT_SHA='c84d19402deba65229c7263c461d4a1be03af7d7eb05aae697c19bd6ea9705a3'
SOURCE_CONTENT='7d483a76b13f07251b4b12baac3c8f0517d9c7735a642df9ce94c73acbae3137'
OUTPUT_CONTENT='a848243530757c43133c4b1645abc5619cb03c8fddf5039b004e679d200e1cc3'
LOCK_SHA='cb4632b121bee8506eae3b629362c4618c9e9e27b4f6e240faa27f5d253ac749'
FLAGS=['ownershipVerified','productionApproved','publicApproved','indexNowEnabled','indexable']
GENERATED={'gangdong-static-qa.json','gangdong-negative-fixtures.json','rendered-copy-extraction.json','customer-string-output-role-map.json'}
digest=upstream.digest
compact=upstream.compact
write=upstream.write_json
load=lambda p:json.loads(Path(p).read_text())

def require(condition,message):
    if not condition:raise AssertionError(message)

BOOL_FIELDS={'visible','collapsed','complete','geometryPassed','passed','fixedBar','focusVisible','sourceUnchanged','outputUnchanged','publicHttpVerified','clickOpenClose','keyboardEnterSpace','navigationBackReload','navigationForward','back','forward','reload','skipTargetVisible','blocked','blockedWebSocket','expected404','descriptionVisible','sampleLabelVisible'}
NUMBER_FIELDS={'width','height','naturalWidth','naturalHeight','viewport','scrollWidth','left','right','top','bottom','safeTop','safeBottom','viewportWidth','viewportHeight','outlineWidth','count','domIndex','status','http'}
def validate_types(value):
    if isinstance(value,list):
        for x in value:validate_types(x)
    elif isinstance(value,dict):
        for key,v in value.items():
            if key in BOOL_FIELDS:require(type(v)is bool,'Boolean field type: '+key)
            if key in NUMBER_FIELDS:require(type(v)in(int,float) and math.isfinite(v),'Numeric field type: '+key)
            if key=='hitTests':require(type(v)is list and len(v)>=9 and all(type(x)is bool for x in v),'Hit-test booleans')
            validate_types(v)

def safe_path(value):
    require(isinstance(value,str) and bool(value) and not value.startswith('/') and '\\' not in value and '\x00' not in value,'Unsafe relative path')
    require(all(x not in ('','.','..') for x in value.split('/')),'Unsafe path component')
    return value

def regular_root(root):
    root=Path(root)
    require(root.is_absolute() and root.is_dir(),'Missing absolute root')
    for part in [root,*root.parents]:require(not part.is_symlink(),'Symlink ancestor/root')
    return root

def safe_file(root,rel):
    safe_path(rel);root=regular_root(root);p=root/rel
    for q in [p,*p.parents]:
        if q==root:break
        require(not q.is_symlink(),'Symlink file/ancestor')
    require(p.is_file() and stat.S_ISREG(p.stat().st_mode),'Missing regular file')
    require(p.resolve().is_relative_to(root),'Escaped root')
    return p

def validate_spec(spec):
    # Binding is intentionally rigid, rather than accepting a caller-selected source.
    require(spec==load(SPEC_PATH),'Changed binding')
    require(spec['repository']=='joseungil-kr/fwith-site-factory' and spec['sourceContentSha256']==SOURCE_CONTENT and spec['outputContentSha256']==OUTPUT_CONTENT and spec['lockSha256']==LOCK_SHA,'Source/output/lock pin')
    require(spec['sourceSha']==SOURCE_SHA and spec['repositoryTree']==ROOT_TREE and spec['sourceTree']==PROJECT_TREE,'Wrong immutable source binding')
    require(spec['path']==SITE_PATH and spec['controlRef']==REF and spec['siteUrl']==ORIGIN and spec['mode']=='LOCAL_PREVIEW','Unsafe binding scope')
    require(spec['routes']==ROUTES and spec['viewports']==[list(x) for x in VIEWPORTS],'Wrong routes/viewports')
    require(all(spec[x] is False for x in FLAGS),'Public flag enabled')
    return spec

def validate_environment(spec,env=None):
    env=os.environ if env is None else env
    expected={'GITHUB_ACTIONS':'true','GITHUB_EVENT_NAME':'push','GITHUB_RUN_ATTEMPT':'1','GITHUB_ACTOR':'joseungil-kr','GITHUB_TRIGGERING_ACTOR':'joseungil-kr','GITHUB_REPOSITORY':spec['repository'],'GITHUB_REF':REF,'SITE_FACTORY_REVISION':SOURCE_SHA,'SITE_URL':ORIGIN,'SITE_ORIGIN':ORIGIN,'SITE_INDEXABLE':'false','PRODUCTION_APPROVED':'false','OWNERSHIP_VERIFIED':'false','INDEXNOW_ENABLED':'false','PUBLIC_APPROVED':'false','PYTHONDONTWRITEBYTECODE':'1'}
    for key,value in expected.items():require(env.get(key)==value,'Environment mismatch: '+key)
    require(bool(re.fullmatch('[0-9a-f]{40}',env.get('GITHUB_SHA',''))),'Invalid control SHA')
    for k in ('GITHUB_RUN_ID','GITHUB_RUN_ATTEMPT'):require(bool(re.fullmatch('[1-9][0-9]*',env.get(k,''))),'Invalid run identity')
    root=regular_root(Path(env.get('GITHUB_WORKSPACE','')))
    source=regular_root(Path(env.get('SOURCE_ROOT','')))
    evidence=Path(env.get('EVIDENCE_ROOT',''))
    require(source==root/'source' and evidence==root/'evidence/gangdong','Wrong source/evidence root')
    require(HERE==root/'control/.github/qa/unpublished-gangdong','Wrong control path')
    for ancestor in [evidence,*evidence.parents]:require(not ancestor.is_symlink(),'Symlink evidence root/ancestor')
    require(upstream.git(root/'control','rev-parse','HEAD')==env['GITHUB_SHA'],'Wrong control checkout')
    require(not upstream.git(root/'control','status','--porcelain','--untracked-files=all'),'Dirty control checkout')
    return source,evidence

def verify_reuse():
    p=load(HERE/'reuse-provenance.json')
    for row in p['files']:
        require(digest(safe_file(HERE,row['candidatePath']).read_bytes())==row['sha256'],'Upstream bytes changed')
    return p

def verify_manifest(root,manifest,with_modes=False,exact=False):
    regular_root(root); rows=manifest['files']; require(len(rows)==manifest['fileCount'],'Manifest count')
    require([r['path']for r in rows]==sorted({r['path']for r in rows}),'Manifest duplicate/order')
    actual=[]
    for row in rows:
        p=safe_file(root,row['path']);data=p.read_bytes()
        fact={'path':row['path'],'bytes':len(data),'sha256':digest(data)}
        if with_modes:fact['mode']=f'{stat.S_IMODE(p.stat().st_mode):04o}'
        require(fact==row,'Frozen bytes/mode mismatch: '+row['path']);actual.append(fact)
    if exact:
        paths=[]
        for p in root.rglob('*'):
            require(not p.is_symlink(),'Unexpected symlink')
            if p.is_file():paths.append(p.relative_to(root).as_posix())
        require(sorted(paths)==[r['path']for r in rows],'Unexpected artifact path set')
    field='sourceContentSha256' if with_modes else 'outputContentSha256'
    require(digest(compact(actual))==manifest[field],'Manifest content digest mismatch')
    return actual

def verify_source_files(site):
    spec=validate_spec(load(SPEC_PATH));m=load(HERE/'source-manifest.json')
    require(m['fileCount']==69 and m['sourceContentSha256']==spec['sourceContentSha256'],'Source seal')
    rows=verify_manifest(site,m,with_modes=True)
    runtime=load(safe_file(site,'src/data/gangdong-runtime.json'))
    require(runtime['mode']['mode']=='LOCAL_PREVIEW' and runtime['origin']==ORIGIN,'Runtime mode/origin')
    require(all(runtime[f] is False for f in FLAGS),'Runtime public flag')
    require([p['path']for p in runtime['pages']]==ROUTES and runtime['sitemap']==[],'Runtime route/sitemap')
    inventory=load(safe_file(site,'src/data/frozen/all-strings-inventory.json'))
    require(inventory['customerTextCount']==249,'Frozen customer text count')
    require(digest(safe_file(site,'package-lock.json').read_bytes())==spec['lockSha256'],'Dependency lock changed')
    return rows

def verify_source(source,pristine=False):
    source=regular_root(source);spec=validate_spec(load(SPEC_PATH))
    for expression,expected in [('HEAD',SOURCE_SHA),('HEAD^',spec['sourceParent']),('HEAD^{tree}',ROOT_TREE),('HEAD:'+SITE_PATH,PROJECT_TREE)]:
        require(upstream.git(source,'rev-parse',expression)==expected,'Source git identity: '+expression)
    require(not upstream.git(source,'diff','--name-only','HEAD'),'Source tracked mutation')
    require(not upstream.git(source,'diff','--cached','--name-only'),'Source staged mutation')
    tracked=upstream.git(source,'ls-files','--',SITE_PATH).splitlines()
    expected=[SITE_PATH+'/'+r['path']for r in load(HERE/'source-manifest.json')['files']]
    require(sorted(tracked)==sorted(expected),'Source tracked file set')
    site=source/SITE_PATH;verify_source_files(site)
    allowed_dirs=set() if pristine else {'node_modules','dist','.astro'}
    tracked_rel={x.removeprefix(SITE_PATH+'/')for x in tracked}
    for directory,dirs,files in os.walk(site,followlinks=False):
        rel=Path(directory).relative_to(site)
        for name in list(dirs):
            item=Path(directory)/name;require(not item.is_symlink(),'Source directory symlink')
            if rel==Path('.') and name in allowed_dirs:dirs.remove(name)
        for name in files:
            item=Path(directory)/name;require(not item.is_symlink(),'Source symlink')
            r=item.relative_to(site).as_posix()
            require(r in tracked_rel or (not pristine and r in GENERATED),'Unexpected project file: '+r)
    return site

def validate_build(site):
    spec=validate_spec(load(SPEC_PATH));m=load(HERE/'output-manifest.json')
    require(m['fileCount']==21 and m['outputContentSha256']==spec['outputContentSha256'],'Output seal')
    return verify_manifest(site/'dist',m,exact=True)

class GangdongHandler(upstream.SafeHandler):
    """Reuse strict resolver; return frozen custom body with real 404 for absent paths."""
    def send_head(self):
        status=200
        try:p=upstream.resolve_request(Path(self.directory),self.path)
        except FileNotFoundError:p=safe_file(Path(self.directory),'404.html');status=404
        except (ValueError,AssertionError,UnicodeError):self.send_error(403);return None
        stream=p.open('rb');self.send_response(status)
        self.send_header('Content-Type',self.guess_type(str(p)))
        self.send_header('Content-Length',str(p.stat().st_size));self.send_header('Cache-Control','no-store')
        self.send_header('X-Robots-Tag','noindex, nofollow, noarchive');self.end_headers();return stream

SafeServer=upstream.SafeServer
allowed_request=upstream.allowed_request

def expected_for(runtime,route):
    page=next(p for p in runtime['pages'] if p['path']==route)
    skus=[]
    for section in page.get('sections',[]):
        skus+=section.get('productSKUs',[])
        for group in section.get('productGroups',[]):skus+=group['skus']
    return page,[next(p for p in runtime['products'] if p['sku']==sku) for sku in skus]

def dom_contract():
    path=HERE/'dom-contract.json';require(digest(path.read_bytes())==DOM_CONTRACT_SHA,'Frozen DOM contract changed')
    value=load(path);require(value['schema']=='gangdong-frozen-dom-contract-v1' and value['sourceSha']==SOURCE_SHA and value['outputContentSha256']==OUTPUT_CONTENT,'DOM binding')
    require(list(value['routes'])==ROUTES,'DOM route binding')
    return value['routes']


def assert_facts(f,runtime,route,width):
    p,products=expected_for(runtime,route);validate_types(f)
    require(f['links']==dom_contract()[route]['links'],'Frozen DOM anchor set/order')
    require(f['h1']==[p['h1']] and f['title']==p['title'] and f['description']==p['metaDescription'],'Metadata/H1')
    require(f['firstAnswer']==p['firstAnswer'],'First answer')
    require(f['viewport']==width and f['scrollWidth']<=width+1 and not f['overflow'],'Horizontal overflow')
    require(f['robots']=='noindex,nofollow,noarchive' and f['canonical']==(None if route=='/404.html' else ORIGIN+route),'Preview metadata')
    require(f['pageId']==p['id'] and f['copySha']==runtime['inputSHA256'],'Rendered input identity')
    require(not f['duplicateIds'] and f['fontStatus']=='loaded','IDs/fonts')
    require([{k:x[k]for k in ('question','answer')}for x in f['faq']]==p.get('faqs',[]),'Exact FAQ text/count')
    require(all(x['visible'] and not x['collapsed'] for x in f['faq']),'Hidden FAQ')
    expected_images=[('/images/shared-banners/'+next(b['assetName']for b in runtime['common']['banners']if b['id']==x['banner']),next(b['alt']for b in runtime['common']['banners']if b['id']==x['banner']),1774,887)for x in p['bannerPlacement']]+[(x['img'],x['alt'],500,500)for x in products]
    require(sorted((i['src'],i['alt'],i['naturalWidth'],i['naturalHeight'])for i in f['images'])==sorted(expected_images),'Rendered image set')
    require(all(i['complete'] and i['naturalWidth']>0 and i['naturalHeight']>0 and i['width']>0 and i['height']>0 and i['alt'].strip() for i in f['images']),'Image decode/alt')
    require([b['variant']for b in f['banners']]==[b['banner']for b in p['bannerPlacement']],'Banner count/order')
    for banner in f['banners']:
        b=next(b for b in runtime['common']['banners']if b['id']==banner['variant'])
        require(banner['src']=='/images/shared-banners/'+b['assetName'] and banner['alt']==b['alt'],'Banner identity')
        require(banner['complete'] is True,'Banner not loaded')
        require(banner['naturalWidth']==1774 and banner['naturalHeight']==887 and abs(banner['width']/banner['height']-2)<.01 and banner['objectFit']=='contain','Banner intrinsic/CSS aspect/crop')
    require(len(f['products'])==len(products),'Product count')
    for a,e in zip(f['products'],products):
        require(a['sku']==e['sku'] and a['family']==e['family'] and a['href']==e['cta']['href'] and a['src']==e['img'] and a['alt']==e['alt'] and a['name']==e['name'] and a['price']==e['priceText'],'Product SKU/link/image/copy')
        require(a['complete'] is True,'Product not loaded')
        require(a['naturalWidth']==500 and a['naturalHeight']==500 and a['width']>0 and a['height']>0 and abs(a['width']/a['height']-1)<.01 and a['objectFit']=='contain','Product intrinsic/CSS crop/aspect')
        require(a['description']==e['description'] and a['sampleLabel']==runtime['common']['productLabels']['samplePhoto'] and a['descriptionVisible'] and a['sampleLabelVisible'],'Product description/sample visible')
    require(f['sources']==p.get('officialSources',[]),'Actual source-card links')
    require(f['sourceSectionCount']==(1 if p.get('officialSources') else 0),'Source-card section count')
    require(f['sourceNote']==p.get('sourceNote',''),'Source observation note')
    require(all(a in f['ids'] for a in runtime['presentation']['requiredAnchors'].get(route,[])),'Required anchor missing')
    require(f['phones'] and set(f['phones'])=={runtime['common']['phone']['href']},'Exact phone anchor')
    require(f['fixedBar']==(width<=860),'Native mobile bar breakpoint')

def assert_geometry(f,focus=False):
    validate_types(f)
    require(0<=f['safeTop']<f['safeBottom']<=f['viewportHeight'],'Impossible safe band')
    require(abs(f['right']-f['left']-f['width'])<=.5 and abs(f['bottom']-f['top']-f['height'])<=.5,'Inconsistent target rectangle')
    require(f['visible'] and f['width']>0 and f['height']>0,'Target hidden/empty')
    require(f['left']>=-.5 and f['right']<=f['viewportWidth']+.5,'Target horizontal clipping')
    require(f['top']>=f['safeTop']-.5 and f['bottom']<=f['safeBottom']+.5,'Target fixed-chrome/offscreen obstruction')
    require(len(f['hitTests'])>=9 and all(f['hitTests']),'Target obstructed')
    if focus:require(f['focusVisible'] and f['outlineWidth']>0 and f['outlineStyle']not in ('none','hidden'),'Invisible keyboard focus')

def validate_screen(row,output,full=False):
    validate_types(row)
    rel=safe_path(row['screenshot']);require(rel.startswith('screenshots/'),'Screenshot path prefix')
    p=safe_file(output,rel);data=p.read_bytes();require(data.endswith(b'\xff\xd9'),'Truncated JPEG');dims=upstream.jpeg_dimensions(data)
    require(digest(data)==row['sha256'] and dims==row['dimensions'],'Screenshot SHA/dimensions')
    require(dims['width']==row['width'] and (dims['height']>=row['height'] if full else dims['height']==row['height']),'Screenshot viewport')
    require(row['kind']==('full-page' if full else 'risk-viewport'),'Screenshot kind')
    require(row['route']in ROUTES and (row['width'],row['height'])in VIEWPORTS,'Screenshot route/viewport')
    require(row['issues']==[],'Capture issue')
    return rel

def validate_report(report,output,runtime):
    validate_types(report)
    require(type(report['routes'])is list and type(report['console'])is list and type(report['pageErrors'])is list and type(report['network'])is list,'Report collection type')
    origin=report['loopbackOrigin'];require(bool(re.fullmatch(r'http://127\.0\.0\.1:[1-9][0-9]{0,4}',origin)) and allowed_request(origin,'GET',origin),'Report loopback origin')
    require(report['schema']=='gangdong-browser-observations-v1','Wrong report schema')
    require(bool(re.fullmatch('[0-9a-f]{40}',report['controlSha'])) and bool(re.fullmatch('[1-9][0-9]*',report['runId'])) and report['runAttempt']=='1' and report['actor']=='joseungil-kr','Report run binding')
    for key,env in [('controlSha','GITHUB_SHA'),('runId','GITHUB_RUN_ID'),('runAttempt','GITHUB_RUN_ATTEMPT')]:
        if os.environ.get('GITHUB_ACTIONS')=='true':require(report[key]==os.environ[env],'Report/current runner mismatch')
    require(report['sourceSha']==SOURCE_SHA and report['sourceContentSha256']==load(SPEC_PATH)['sourceContentSha256'] and report['outputContentSha256']==load(SPEC_PATH)['outputContentSha256'],'Report source/output binding')
    require(report['pixelReview']=='pending' and report['publicHttpVerified'] is False,'False evidence escalation')
    require(report['playwrightVersion']=='1.63.0' and type(report['browserVersion'])is str and bool(re.fullmatch(r'[0-9]+(?:\.[0-9]+){1,3}',report['browserVersion'])),'Browser receipt missing')
    rows=report['routes'];grid=[(r,w,h)for w,h in VIEWPORTS for r in ROUTES]
    require([(r['route'],r['width'],r['height'])for r in rows]==grid,'Incomplete/duplicate/reordered grid')
    seen=[]
    for row in rows:
        require(row['issues']==[],'Route assertion failed')
        require(row['http']==200 and row['safeNavigation']=={'back':True,'forward':True,'reload':True},'Route/navigation result')
        assert_facts(row['facts'],runtime,row['route'],row['width'])
        require((row['fullPage']['route'],row['fullPage']['width'],row['fullPage']['height'])==(row['route'],row['width'],row['height']),'Full-page metadata binding')
        seen.append(validate_screen(row['fullPage'],output,True))
        require(len(row['targets'])==len(targets_for(runtime,row['route'])),'Duplicate/extra risk target')
        require(row['targets'] and {x['label']for x in row['targets']}==set(targets_for(runtime,row['route'])),'Risk screenshot coverage')
        for target in row['targets']:
            require((target['selector'],target['index'])==targets_for(runtime,row['route'])[target['label']],'Risk selector/index binding')
            require((target['route'],target['width'],target['height'])==(row['route'],row['width'],row['height']),'Risk metadata binding')
            require((target['geometry']['viewportWidth'],target['geometry']['viewportHeight'])==(row['width'],row['height']),'Risk geometry viewport')
            require(target['geometryPassed'] is True,'Risk geometry failed');assert_geometry(target['geometry']);seen.append(validate_screen(target,output))
        expected_keyboard=dom_contract()[row['route']]['keyboard'][str(row['width'])]
        require([{k:f[k]for k in ('domIndex','tag','href')}for f in row['keyboard']['targets']]==expected_keyboard,'Frozen full keyboard sequence')
        require(row['keyboard']['passed'] is True and row['keyboard']['count']==len(row['keyboard']['targets']) and row['keyboard']['count']>1,'Keyboard missing/failed')
        for fact in row['keyboard']['targets']:
            require((fact['viewportWidth'],fact['viewportHeight'])==(row['width'],row['height']),'Keyboard geometry viewport');assert_geometry(fact,True)
        require((row['keyboard']['screenshot']['route'],row['keyboard']['screenshot']['width'],row['keyboard']['screenshot']['height'])==(row['route'],row['width'],row['height']),'Keyboard screenshot metadata')
        seen.append(validate_screen(row['keyboard']['screenshot'],output))
        require(len({t['domIndex']for t in row['keyboard']['targets']})==row['keyboard']['count'],'Keyboard repeated target')
        if row['width']<=860:
            m=row['menu'];require(m['clickOpenClose'] and m['keyboardEnterSpace'] and m['navigationBackReload'] and m['navigationForward'],'Native menu flow incomplete')
            require((m['screenshot']['route'],m['screenshot']['width'],m['screenshot']['height'])==(row['route'],row['width'],row['height']),'Menu screenshot metadata')
            seen.append(validate_screen(m['screenshot'],output))
        require(row['menu']['passed'] is True and row['menu']['mode']==('native-details'if row['width']<=860 else 'desktop-navigation'),'Native menu coverage')
        expected_links=sorted(set(x for x in row['facts']['links']if x.startswith(('/','#'))))
        require([a['href']for a in row['internalAnchors']]==expected_links,'Dropped internal link checks')
        require(row['internalAnchors'] and all(x['passed'] for x in row['internalAnchors']),'Internal anchors incomplete/failed')
        for flow in row['internalAnchors']:
            resolved=urlsplit(urljoin(origin+row['route'],flow['href']))
            require(resolved.netloc==urlsplit(origin).netloc and resolved.scheme=='http' and resolved.path in ROUTES and not resolved.query,'Anchor resolved outside route scope')
            require(flow['resolvedPath']==resolved.path and flow['fragment']==resolved.fragment,'Forged anchor resolution')
            if resolved.fragment and resolved.fragment!='main-content':assert_geometry(flow['geometry'])
            if resolved.fragment=='main-content':require(flow['skipTargetVisible'] is True,'Missing visible skip target')
            require(flow['screenshot']['width']==row['width'] and flow['screenshot']['height']==row['height'],'Anchor screenshot viewport')
            require(flow['screenshot']['route']==flow['resolvedPath'],'Anchor screenshot route')
            if flow.get('geometry'):
                require((flow['geometry']['viewportWidth'],flow['geometry']['viewportHeight'])==(row['width'],row['height']),'Anchor geometry viewport');assert_geometry(flow['geometry'])
            seen.append(validate_screen(flow['screenshot'],output))
    require(len(seen)==len(set(seen)),'Duplicate evidence path')
    require(report['true404']['path']=='/__gangdong_missing_route__/','Unexpected missing-route proof')
    require(report['true404']['browserStatus']==404 and report['true404']['browserBodySha256']==report['true404']['bodySha256'],'Browser true404 readback')
    require(report['true404']['status']==404 and report['true404']['bodySha256']==next(r['sha256']for r in load(HERE/'output-manifest.json')['files']if r['path']=='404.html'),'Real 404 body/status')
    for c in report['expected404Console']:
        require(c['type']=='error' and c['location']['url']==origin+'/__gangdong_missing_route__/' and 'Failed to load resource' in c['text'] and '404' in c['text'],'Unapproved expected console exception')
    console_types={'log','debug','info','error','warning','dir','dirxml','table','trace','clear','startGroup','startGroupCollapsed','endGroup','assert','profile','profileEnd','count','timeEnd'}
    require(all(c['type']in console_types for c in report['console']),'Unknown console type')
    require(not report['pageErrors'] and not any(c['type']in ('error','assert')for c in report['console']),'Browser error')
    require(bool(report['network']),'Missing network observations')
    for n in report['network']:
        require(not any(n.get(k)for k in ('blocked','blockedWebSocket','failure')),'Network request failed/blocked')
        require(set(n)=={'url','status','expected404'} and type(n['status'])is int,'Unknown network record')
        require(allowed_request(n['url'],'GET',origin),'Non-loopback network observation')
        expected=n['url']==origin+'/__gangdong_missing_route__/' and n['status']==404
        require(n['expected404'] is expected,'Incorrect expected404 exception')
        require(200<=n['status']<400 or expected,'Unexpected HTTP failure')
    observed={(n['url'],n['status'])for n in report['network']}
    require(all((origin+r,200)in observed for r in ROUTES) and (origin+'/__gangdong_missing_route__/',404)in observed,'Missing route network evidence')
    require(report['fatalError'] is None,'Fatal browser error')
    require(report['sourceUnchanged'] is True and report['outputUnchanged'] is True and not report.get('fatalError'),'Mutation/fatal error')
    return {'fullPageCount':15,'riskViewportCount':len(seen)-15,'screenshots':len(seen),'pixelReview':'pending'}

def targets_for(runtime,route):
    p,products=expected_for(runtime,route)
    targets={'header':('.site-header',0),'footer':('footer > div',0),'opening':('#opening > h1',0),'first-answer':('[data-first-answer]',0)}
    targets.update({'banner-'+x['banner']:('[data-shared-flower-banner="'+x['banner']+'"]',0)for x in p['bannerPlacement']})
    targets.update({'product-image-'+x['sku']:('[data-product-sku="'+x['sku']+'"] img',0)for x in products})
    targets.update({'product-description-'+x['sku']:('[data-product-sku="'+x['sku']+'"] p:not(.product-sku):not(.product-notice)',0)for x in products})
    targets.update({'product-sample-'+x['sku']:('[data-product-sku="'+x['sku']+'"] .product-notice',0)for x in products})
    targets.update({'product-link-'+x['sku']:('[data-order-product-sku="'+x['sku']+'"]',0)for x in products})
    targets.update({'faq-'+str(i):('[data-faq-entry]',i)for i in range(len(p.get('faqs',[])))})
    targets.update({'section-'+x['id']:('#'+x['id']+' > h2',0)for x in p.get('sections',[])})
    targets.update({'source-'+str(i):('[data-source-references] .copy-links a',i)for i in range(len(p.get('officialSources',[])))})
    targets.update({'card-'+str(i):('[data-purchase-cards] .page-card',i)for i in range(len(p.get('cards',[])))})
    if route==ROUTES[1]:targets.update({a:('#'+a,0)for a in ['bohun','kyunghee','sacred-heart']})
    return targets

def artifact_file_fact(p,root):
    data=p.read_bytes();row={'path':p.relative_to(root).as_posix(),'bytes':len(data),'sha256':digest(data)}
    if p.suffix.lower() in ('.jpg','.jpeg'):
        require(data.endswith(b'\xff\xd9'),'Truncated JPEG');row.update({'format':'jpeg','dimensions':upstream.jpeg_dimensions(data)})
    elif p.suffix.lower()=='.png':
        require(data[:8]==b'\x89PNG\r\n\x1a\n' and data[12:16]==b'IHDR','Invalid PNG')
        width,height=struct.unpack('>II',data[16:24]);row.update({'format':'png','dimensions':{'width':width,'height':height}})
    return row


def main():
    command=sys.argv[1];spec=validate_spec(load(SPEC_PATH));verify_reuse()
    source,evidence=validate_environment(spec);evidence.mkdir(parents=True,exist_ok=True);(evidence/'logs').mkdir(exist_ok=True)
    if command=='source':
        site=verify_source(source,pristine=True)
        write(evidence/'source-readback.json',{'sourceSha':SOURCE_SHA,'sourceTree':PROJECT_TREE,'repositoryTree':ROOT_TREE,'files':69,'sourceContentSha256':spec['sourceContentSha256'],'mode':'LOCAL_PREVIEW','productionApproved':False})
    elif command=='manifest':
        site=verify_source(source);rows=validate_build(site);Path(sys.argv[2]).write_bytes(compact(rows))
    elif command=='seal':
        rows=[]
        for p in sorted(evidence.rglob('*')):
            require(not p.is_symlink(),'Evidence symlink')
            if p.is_file() and p.name!='evidence-manifest.json':rows.append(artifact_file_fact(p,evidence))
        capture=load(evidence/'capture-results.json') if (evidence/'capture-results.json').is_file() else None
        state='incomplete-no-capture-report' if capture is None else capture.get('state','incomplete-unknown-capture-state')
        write(evidence/'evidence-manifest.json',{'evidenceState':state,'completeBrowserEvidence':state=='machine-checks-only-awaiting-independent-pixel-review','sourceSha':SOURCE_SHA,'controlSha':os.environ['GITHUB_SHA'],'runId':os.environ['GITHUB_RUN_ID'],'runAttempt':os.environ['GITHUB_RUN_ATTEMPT'],'files':rows,'pixelReview':'pending','publicHttpVerified':False})
    else:raise ValueError('Unknown command')
if __name__=='__main__':main()
