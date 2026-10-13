#!/usr/bin/env python3
"""Additive offline source binding and future QA checks; never saves Git state.

Upstream guards remain byte-identical. Bound only to the reviewed saved Dongjak source; no publication capability. No network operations.
"""
from pathlib import Path
import argparse, hashlib, json, os, re, subprocess, sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE/'upstream'))
import controls

SITE_PATH = 'site-factory/seoul-dongjak-flower'
SITE_URL = 'https://dongjak-preview.invalid'
ROUTES = ['/', '/regions/', '/regions/dongjak-funeral-wreath/', '/404.html']
MANIFEST_SHA = 'cbff591015f8458f35ce6d20c8eb6965323d052208f7a9f6aefa2cf8fa7d7722'
SOURCE_SHA = '430dada32f3f8b53f24aec8d9fdf3724529604e1'
SOURCE_TREE = 'a032dbdad16e044af8bca7163e26ca795f3b7d6c'
REPOSITORY_TREE = '5d64d0467d6b900c549a8b26660b95b6f2b1e882'
GENERATED_REVISION = SITE_PATH+'/src/data/build-revision.json'


def load(path): return json.loads(Path(path).read_text())
def sha(data): return hashlib.sha256(data).hexdigest()
def write(path, value):
    p=Path(path); p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')


LINEAGE_SHA = 'c6e06ec86e83429f4d471cf1f3ec6c229de7f5b53c4a04a951d1e342bc6e1b1c'

def validate_source_lineage(original, current, lineage):
    assert lineage['baseSourceSha']=='1570f3866985a1434c2847604840926db92e300b'
    assert lineage['currentSourceSha']==SOURCE_SHA and lineage['publicationApproved'] is False
    assert lineage['baseManifestSha256']=='9635b41b830b811748c9fe76ca0c5e6815d3b4224eca8aaebc0d4bbe44b429bc'
    assert lineage['currentManifestSha256']==MANIFEST_SHA
    a={e['path']:{k:e[k]for k in ('bytes','sha256','gitBlobSha')}for e in original}
    b={e['path']:{k:e[k]for k in ('bytes','sha256','gitBlobSha')}for e in current}
    assert len(original)==len(current)==len(a)==len(b)==629 and a.keys()==b.keys(), 'Lineage source scope changed'
    changed=[p for p in a if a[p]!=b[p]]
    assert changed==lineage['changedPaths']==[SITE_PATH+'/src/styles/global.css'], 'Lineage is not CSS-only'
    css=b[changed[0]]
    assert css['sha256']==lineage['reviewedCssSha256']=='406699399515194fffd9a1bcaa14f8ee9bbbea6736475d4488359a23fcbfce6a'
    assert css['gitBlobSha']==lineage['actualSavedCssGitBlob']=='fd5b1d6edbf2b728b7b9f1b1861f7a0c71695a8d'
    return True

def verify_source_lineage():
    path=HERE/'source-lineage.json'
    assert sha(path.read_bytes())==LINEAGE_SHA, 'Lineage metadata drift'
    lineage=load(path);original_path=HERE/'frozen-inputs/source-file-manifest.original.json'
    assert sha(original_path.read_bytes())==lineage['baseManifestSha256'], 'Original frozen manifest drift'
    current_path=HERE/'frozen-inputs/source-file-manifest.final.json'
    assert sha(current_path.read_bytes())==lineage['currentManifestSha256'], 'Current frozen manifest drift'
    return validate_source_lineage(load(original_path),load(current_path),lineage)

def frozen_entries():
    verify_source_lineage()
    path=HERE/'frozen-inputs/source-file-manifest.final.json'
    assert sha(path.read_bytes()) == MANIFEST_SHA, 'Authoritative manifest drift'
    entries=load(path)
    assert len(entries)==629 and len({e['path'] for e in entries})==629, 'Frozen scope count'
    assert all(e['path'].startswith(SITE_PATH+'/') and '..' not in Path(e['path']).parts for e in entries), 'Unsafe manifest scope'
    return entries

def verify_upstream():
    provenance=load(HERE/'reuse-provenance.json')
    for f in provenance['upstreamFiles']:
        path=HERE/f['localPath']
        assert path.is_file() and not path.is_symlink(), 'Unsafe upstream file'
        assert sha(path.read_bytes())==f['sha256'], ('Upstream guard changed',f['localPath'])
    assert controls.NATIVE_BLOB=='41ee8a757b7a742b6125ef15b5356e0eca47c01f'
    assert controls.VIEWPORTS==[(320,740),(390,844),(1280,900)]
    return provenance

def verify_frozen_bytes(root, allow_generated=False):
    root=Path(root).resolve(); rows=[]
    for e in frozen_entries():
        file=root/e['path']; cursor=root
        for part in Path(e['path']).parts:
            cursor=cursor/part
            assert not cursor.is_symlink(), ('Symlink in source path',e['path'])
        assert file.is_file(), ('Missing frozen source',e['path'])
        data=file.read_bytes()
        if allow_generated and e['path']==GENERATED_REVISION and sha(data)!=e['sha256']:
            assert controls.git(root,'rev-parse','HEAD')==SOURCE_SHA, 'Generated revision needs exact saved HEAD'
            expected=json.dumps({'revision':SOURCE_SHA},indent=2).encode()
            assert data==expected, 'Generated revision bytes differ from exact saved SHA'
            rows.append({'path':e['path'],'sha256':sha(data),'generatedRevisionOnly':True})
            continue
        assert len(data)==e['bytes'] and sha(data)==e['sha256'], ('Frozen source changed',e['path'])
        blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
        assert blob==e['gitBlobSha'], ('Frozen blob mismatch',e['path'])
        rows.append({'path':e['path'],'sha256':e['sha256'],'gitBlobSha':blob})
    return {'files':len(rows),'bytes':sum(e['bytes'] for e in frozen_entries()),'manifestSha256':MANIFEST_SHA,'verified':True}


def not_found_contract(site):
    common=load(Path(site)/'src/data/dongjak-common-copy.json')
    ui=load(Path(site)/'src/data/dongjak-ui-copy.json')
    nf=common['notFound'];footer=common['footer']
    anchors=[{'href':'#main-content','text':ui['accessibility']['skip']},
             {'href':'/','text':'✿'+common['brandName']}]
    anchors += [{'href':x['href'],'text':x['label']}for x in common['navigation']]
    anchors += [{'href':'/regions/','text':ui['directory']['navLabel']},
                {'href':common['phoneHref'],'text':common['phoneLabel']},
                {'href':nf['href'],'text':nf['linkText']},
                {'href':common['phoneHref'],'text':footer['phoneLinkText']},
                {'href':footer['homeHref'],'text':footer['homeLinkText']},
                {'href':common['phoneHref'],'text':footer['phoneLinkText']},
                {'href':'/regions/','text':ui['directory']['navLabel']}]
    assert len(anchors)==11 and all(x['href'].startswith(('/','#','tel:'))for x in anchors)
    return {'h1':[nf['title']],'anchors':anchors}

def validate_not_found_facts(facts, expected):
    contract=expected['notFoundContract']
    assert facts['h1']==contract['h1'], '404 heading differs from approved source'
    assert facts['anchors']==contract['anchors'], '404 link href/text/order differs from approved source'
    assert facts['robots']=='noindex,nofollow,noarchive' and facts['canonical'] is None, '404 indexability/canonical drift'
    assert facts['banners']==0 and facts['faq']==[] and facts['images']==[], '404 content scope drift'

def expectations(site):
    site=Path(site); pages=load(site/'src/data/pages.json'); coverage=load(site/'src/data/region-coverage.json')
    products=load(site/'src/data/products.json'); banner=load(site/'src/data/shared-banner-manifest.json')
    config=load(site/'src/data/site-config.json'); plan=load(site/'src/data/dongjak-plan-binding.json')
    assert config['productionApproved'] is False and config['previewUrl']==SITE_URL and config['hostnameOwnershipVerified'] is False
    assert controls.source_routes(site)==ROUTES
    assert len(pages)==1 and [len(p['facilityAnchors']) for p in pages]==[2]
    assert [len(p['faq']) for p in pages]==[2]
    assert len(coverage['units'])==9 and len(coverage['administrativeCrosswalk'])==15
    assert sum(len(a['relations']) for a in coverage['administrativeCrosswalk'])==18
    assert (plan['originalPlanN'],plan['originalCandidateN'],plan['activeCandidateN'],plan['heldCandidateN'])==(1,12,2,10)
    def chosen(p):
        return [{'key':x['key'],'sku':x['officialSku'],'href':x['orderUrl'],'priceLabel':x['priceLabel']} for sku in p['productCardSkus'] for x in products if x['officialSku']==sku]
    return {'notFoundContract':not_found_contract(site),'routes':ROUTES,'customerRoutes':ROUTES[:-1], 'viewports':[list(x) for x in controls.VIEWPORTS],
        'captureCount':12,'customerCaptureCount':9,'productionApproved':False,'indexable':False,'sitemapRoutes':[],
        'homeProducts':[{'key':p['key'],'href':p['orderUrl'],'priceLabel':p['priceLabel']}for p in products],
        'pages':{p['url']:{'faq':p['faq'],'facilities':p['facilityAnchors'],'products':chosen(p)} for p in pages},
        'banners':[{'variant':x['name'].removeprefix('flower-'),'src':'/images/shared-banners/'+x['name']+'.webp','sha256':x['sha256'],'width':1774,'height':887}for x in banner],
        'legalUnits':[u['unitKey'] for u in coverage['units']],
        'legalLinks':[{k:f[k] for k in ('unitKey','href','candidateId')} for p in pages for f in p['facilityAnchors']],
        'adminRows':[{'key':a['aliasKey'],'relations':[next(u['name'] for u in coverage['units'] if u['unitKey']==rel['unitKey'])+(' 일부' if rel['scope']=='partial' else '')for rel in a['relations']]} for a in coverage['administrativeCrosswalk']]}

def validate_spec(spec):
    assert spec.get('path')==SITE_PATH and spec.get('siteUrl')==SITE_URL, 'Scope drift'
    for key in ('sourceSha','sourceTree','repositoryTree'):
        assert isinstance(spec.get(key),str) and re.fullmatch(r'[0-9a-f]{40}',spec[key]) and spec[key]!='0'*40, ('Unbound or invalid Git identity',key)
    assert (spec['sourceSha'],spec['sourceTree'],spec['repositoryTree'])==(SOURCE_SHA,SOURCE_TREE,REPOSITORY_TREE), 'Exact saved source identities differ'
    assert spec.get('productionApproved') is False and spec.get('indexable') is False, 'Publication prohibited'
    assert spec.get('routes')==ROUTES and spec.get('sitemapRoutes')==[], 'Native route/sitemap scope drift'
    assert spec.get('frozenManifestSha256')==MANIFEST_SHA, 'Source review binding drift'
    return spec

def make_binding(root, source_sha):
    verify_upstream(); root=Path(root).resolve()
    assert re.fullmatch(r'[0-9a-f]{40}',source_sha or '') and source_sha!='0'*40, 'A real saved Git SHA is required'
    assert controls.git(root,'rev-parse','HEAD')==source_sha, 'Source HEAD differs'
    verify_frozen_bytes(root)
    # Every and only the reviewed 629 files must occur in the committed site tree.
    data=subprocess.check_output(['git','-C',str(root),'ls-tree','-rz',source_sha,'--',SITE_PATH])
    actual={}
    for entry in data.split(b'\0'):
        if not entry: continue
        meta,path=entry.split(b'\t',1); mode,kind,blob=meta.decode().split()
        assert kind=='blob' and mode in ('100644','100755'), 'Symlink or submodule in saved source'
        actual[path.decode()]=blob
    expected={e['path']:e['gitBlobSha'] for e in frozen_entries()}
    assert actual==expected, 'Saved Git source does not exactly match 629 reviewed files'
    spec={'sourceSha':source_sha,'sourceTree':controls.git(root,'rev-parse',source_sha+':'+SITE_PATH),
          'repositoryTree':controls.git(root,'rev-parse',source_sha+'^{tree}'),'path':SITE_PATH,'siteUrl':SITE_URL,
          'productionApproved':False,'indexable':False,'routes':ROUTES,'sitemapRoutes':[],'frozenManifestSha256':MANIFEST_SHA}
    validate_spec(spec); controls.verify_source(root,spec,pristine=True)
    expectations(root/SITE_PATH)
    return spec

def validate_environment(spec):
    validate_spec(spec); controls.validate_branch(os.environ.get('GITHUB_REF'))
    assert os.environ.get('GITHUB_REPOSITORY')=='joseungil-kr/fwith-site-factory', 'Wrong repository'
    for key in ('GITHUB_SHA',):
        assert re.fullmatch(r'[0-9a-f]{40}',os.environ.get(key,'')), 'Missing real control SHA'
    assert os.environ.get('SITE_FACTORY_REVISION')==spec['sourceSha']
    assert os.environ.get('SITE_URL')==SITE_URL and os.environ.get('SITE_ORIGIN')==SITE_URL
    assert os.environ.get('SITE_INDEXABLE')=='false'

def validate_extra_facts(facts, expected, route):
    variants=[] if route in ('/regions/','/404.html') else ['message','budget','consultation']
    assert [b['variant'] for b in facts['banners']]==variants, 'Banner order/count'
    for b in facts['banners']:
        source=next(x for x in expected['banners'] if x['variant']==b['variant'])
        assert b['src']==source['src'] and b['naturalWidth']==1774 and b['naturalHeight']==887, 'Banner asset mismatch'
        assert b['width']>0 and abs(b['width']/b['height']-2)<.02, 'Banner geometry/cropping'
        assert b['alt'].strip() and 'AI' in b['caption'], 'Banner alternative/provenance text'
    page=expected['pages'].get(route)
    if page:
        assert facts['faq']==page['faq'], 'Visible FAQ copy differs'
        assert facts['products']==[{k:x[k] for k in ('key','href','priceLabel')}for x in page['products']], 'Product card/price/order mismatch'
        assert facts['facilities']==[{'id':f['anchor'],'heading':f['heading'],'tag':'H3' if 'funeral' in route else 'H2'} for f in page['facilities']], 'Facility heading/anchor mismatch'
    else: assert facts['faq']==[], 'Unexpected FAQ'
    if route=='/':
        assert facts['products']==expected['homeProducts'], 'Home product card/price/order mismatch'
    if route=='/regions/':
        assert facts['guideLinks']==ROUTES[2:-1], 'Directory guide card count/scope'
        assert facts['legalUnits']==expected['legalUnits'], 'Legal geography differs'
        assert sorted(facts['legalLinks'],key=lambda x:x['candidateId'])==sorted(expected['legalLinks'],key=lambda x:x['candidateId']), 'Legal facility links differ'
        assert facts['adminRows']==expected['adminRows'], 'Administrative relation mismatch'
        assert facts['adminFacilityLinks']==[], 'Administrative rows imply facility assignment'

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
        labels += ['legal-'+str(i) for i in range(9)]+['admin-'+str(i) for i in range(15)]
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
    assert all('screenshot' in f for f in flows if f['flow']=='legal-facility-anchor-first-landing'),'Missing initial anchor screenshot'
    assert all(f.get('passed') is True for f in flows if f['flow']=='admin-open-close-reopen'),'Missing details interaction proof'
    shots=[r for r in rows if 'screenshot' in r]+[f for f in flows if 'screenshot' in f]
    assert len({r['screenshot']for r in shots})==len(shots),'Duplicate supplemental screenshot'
    for r in shots:
        rel=r['screenshot'];assert rel.startswith('supplemental/') and '..' not in Path(rel).parts
        file=Path(output)/rel;assert file.is_file() and not file.is_symlink(),'Missing supplemental screenshot'
        assert sha(file.read_bytes())==r['screenshotSha256'],'Supplemental screenshot hash mismatch'
        dims=controls.jpeg_dimensions(file.read_bytes())
        assert dims==r['dimensions'] and dims['width']==r['width'],'Supplemental screenshot dimensions'
        assert dims['height']==dict(controls.VIEWPORTS)[r['width']],'Viewport screenshot must not be full-page'
    return {'geometryChecks':len(rows),'focusScreenshots':len(selected),'anchorFirstLandingScreenshots':len(shots)-len(selected),'interactions':len(flows)}


def main():
    p=argparse.ArgumentParser(description=__doc__); sub=p.add_subparsers(dest='command',required=True)
    q=sub.add_parser('check-local');q.add_argument('--root',type=Path,required=True);q.add_argument('--output',type=Path,required=True)
    q=sub.add_parser('bind');q.add_argument('--root',type=Path,required=True);q.add_argument('--sha',required=True);q.add_argument('--output',type=Path,required=True)
    q=sub.add_parser('source');q.add_argument('--root',type=Path,required=True);q.add_argument('--binding',type=Path,required=True);q.add_argument('--output',type=Path,required=True)
    q=sub.add_parser('manifest');q.add_argument('--root',type=Path,required=True);q.add_argument('--binding',type=Path,required=True);q.add_argument('--output',type=Path,required=True)
    q=sub.add_parser('seal');q.add_argument('--binding',type=Path,required=True);q.add_argument('--evidence',type=Path,required=True)
    args=p.parse_args(); verify_upstream()
    if args.command=='check-local':
        report={'status':'LOCAL_PREPARATION_VERIFIED_NOT_BROWSER_QA','frozenSource':verify_frozen_bytes(args.root),'expectations':expectations(args.root/SITE_PATH),'sourceCommit':None,'browserExecuted':False,'remoteActions':False}
        write(args.output,report)
    elif args.command=='bind':
        write(args.output,make_binding(args.root,args.sha))
    elif args.command=='seal':
        spec=validate_spec(load(args.binding));validate_environment(spec)
        files=controls.manifest(args.evidence);files.pop('evidence-manifest.json',None)
        write(args.evidence/'evidence-manifest.json',{'sourceSha':spec['sourceSha'],'sourceTree':spec['sourceTree'],'repositoryTree':spec['repositoryTree'],'controlSha':os.environ['GITHUB_SHA'],'runId':os.environ['GITHUB_RUN_ID'],'runAttempt':os.environ['GITHUB_RUN_ATTEMPT'],'files':files,'pixelReview':'pending','publicationAuthorization':'not-issued'})
    else:
        spec=validate_spec(load(args.binding));validate_environment(spec)
        site=controls.verify_source(args.root,spec,pristine=args.command=='source')
        verify_frozen_bytes(args.root,allow_generated=args.command=='manifest');expectations(site)
        if args.command=='source':write(args.output,{'spec':spec,'actualHead':controls.git(args.root,'rev-parse','HEAD'),'frozenBytesVerified':True})
        else:args.output.write_bytes(controls.compact(controls.validate_build(site,spec)))
    print(json.dumps({'command':args.command,'status':'verified','browserExecuted':False}))

if __name__=='__main__':main()
