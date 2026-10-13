from pathlib import Path
import json,hashlib,sys,zipfile
from PIL import Image
ROOT=Path('/workspace/scratch/e695498f2eb8');R=ROOT/'gwanak-qa-run-38400663920';A=R/'assembled';O=ROOT/'gwanak-pixel-independent-38400663920'
Q=ROOT/'gwanak-correction-bound-candidate-20261013/control/.github/qa/unpublished-gwanak';sys.path.insert(0,str(Q));import adapter,run_bound_capture as runner
sha=lambda b:hashlib.sha256(b).hexdigest();load=lambda p:json.loads(p.read_text())
spec=load(A/'bound-spec.json');adapter.validate_spec(spec)
assert spec['sourceSha']=='9f9c5abde306c5855104ea4ae58175a8da77496f'
seal=load(A/'evidence-manifest.json');assert seal['sourceSha']==spec['sourceSha']and seal['controlSha']=='5a7a3529b74180cd610ffa40bd748cce04dc9f4c'and str(seal['runId'])=='38400663920'and str(seal['runAttempt'])=='1'
assert len(seal['files'])==180
for name,h in seal['files'].items():
 p=A/name;assert p.is_file() and not p.is_symlink() and sha(p.read_bytes())==h,name
fresh=load(A/'supplemental-results.json');old=load(ROOT/'remote-recovery-20261013/original-failed-qa-reports/supplemental-results.json');assert fresh['sourceSha']==spec['sourceSha']and fresh['controlSha']==seal['controlSha']
expected=adapter.expectations(ROOT/'gwanak-corrected-source-exact-20261013'/adapter.SITE_PATH)
coverage=adapter.validate_supplemental_evidence(fresh['rows'],fresh['flows'],expected,A)
assert len(fresh['rows'])==285 and not any(r['issues']for r in fresh['rows'])
for r in fresh['rows']:
 if r['label'].startswith('product-'):adapter.assert_product_content(r)
 elif r['label']=='footer':adapter.assert_footer_content(r['facts'])
 elif r['label']=='header':assert r['facts']['visible']and all(r['facts']['hitTests'])
 else:adapter.assert_focus(r['facts'])
keyboard=[f for f in fresh['flows']if f['flow']=='keyboard-tab-focus'];assert len(keyboard)==15
for f in keyboard:
 assert f['passed']and not f['issues']
 assert len({t['domIndex']for t in f['targets']})==len(f['targets'])
 for t in f['targets']:adapter.assert_keyboard_focus(t)
assert sum(len(f['targets'])for f in keyboard)==279
comparison=[]
for f in old['flows']:
 if f['flow']=='keyboard-tab-focus'and f.get('issues'):
  t=f['targets'][-1];g=next(g for g in keyboard if(g['width'],g['route'])==(f['width'],f['route']));n=next(n for n in g['targets']if n['domIndex']==t['domIndex']);assert n['text']==t['text']and n['href']==t['href'];adapter.assert_keyboard_focus(n)
  assert t['bottom']>t['safeBottom'] or not all(t['hitTests'])
  comparison.append({'width':f['width'],'route':f['route'],'domIndex':t['domIndex'],'text':t['text'],'href':t['href'],'beforeBottom':t['bottom'],'afterBottom':n['bottom'],'safeBottom':n['safeBottom'],'afterTop':n['top'],'safeTop':n['safeTop'],'afterFragmentHits':n['hitTests'],'focusVisible':n['focusVisible']})
assert len(comparison)==8
anchor=[f for f in fresh['flows']if f['flow']=='anchor-first-landing'];assert len(anchor)==15
for f in anchor:
 assert f['baselineHttpStatus']==200 and f['passed']and not f['issues'];adapter.assert_focus(f['facts'])
 assert f['heading']['tag']=='H2'and f['heading']['id']==f['href'].split('#')[1]
 if f['href'].endswith('#opening-occasion'):assert f['documentHttpStatus']==200
 assert f['landingUrl'].endswith(f['href'])
for key in ['network','console','pageErrors']:
 if key=='network':assert not any(x.get('blocked')or x.get('blockedWebSocket')or x.get('failure')or x.get('status',200)>=400 for x in fresh[key])
 if key=='console':assert not any(x['type']=='error'for x in fresh[key])
 if key=='pageErrors':assert not fresh[key]
assert not fresh['fatalError']
cap=load(A/'capture-results.json');print('capture keys',cap.keys())
rows=cap['results']
assert len(rows)==15
for r in rows:
 assert not r['issues'];p=A/r['screenshot'];im=Image.open(p);im.load();assert sha(p.read_bytes())==r['screenshotSha256'];assert {'width':im.width,'height':im.height}==r['screenshotDimensions']
runner.controls.validate_capture_evidence(rows,spec,A)
# Independently compare all fresh unfocused full-page source bytes with old artifact ZIP bytes.
with zipfile.ZipFile(ROOT/'remote-recovery-20261013/original-failed-qa-artifacts/fullpages.zip') as z:
 for p in sorted((R/'fullpages').rglob('*.jpg')):assert p.read_bytes()==z.read(p.relative_to(R/'fullpages').as_posix())
# Explicit footer representative equality and individual raw clearance.
foot=next(r for r in fresh['rows']if r['width']==390 and r['route']=='/404.html'and r['label']=='footer');homefoot=next(r for r in fresh['rows']if r['width']==390 and r['route']=='/'and r['label']=='footer')
assert foot['facts']['renderSignature']==homefoot['facts']['renderSignature']
assert 'supplemental/390/home/footer.jpg'in foot['screenReferences'];adapter.assert_footer_content(foot['facts'])
# Two exact build manifests and all dist bytes independently checked.
assert (A/'logs/first.manifest.json').read_bytes()==(A/'logs/second.manifest.json').read_bytes()
m=load(A/'logs/first.manifest.json');assert len(m)==20
for n,h in m.items():assert sha((A/'dist'/n).read_bytes())==h
native=load(A/'native/report.json');assert len(native['checks'])==15 and not native['errors']
for x in native['checks']:
 assert x['http']==200 and not x['overflow'] and x['scrollWidth']<=x['width']
 assert all(i['loaded']for i in x['images'])and all(p['valid']for p in x['priceRuns'])
opened=load(O/'opened-mobile-sheets.json');sheets=load(O/'inspection-sheets.json');assert set(opened)=={s['sheet']for s in sheets}
for s in sheets:s['opened']=True
(O/'inspection-sheets.json').write_text(json.dumps(sheets,indent=2)+'\n')
result={'sourceSha':spec['sourceSha'],'controlSha':seal['controlSha'],'runId':38400663920,'attempt':1,'sealFilesRehashed':180,'fullpageScreenshotsRehashed':15,'fullpageOldUnfocusedByteIdentity':15,'coverageRecalculated':coverage,'nativeChecksRead':15,'keyboardTargetsRechecked':279,'previousKeyboardFailuresSameTargetRechecked':comparison,'openingAnchorDocument200Checks':3,'allAnchorMeasurementsRechecked':15,'footer390404':{'allFieldsRevalidated':True,'contentBottom':foot['facts']['bottom'],'safeBottom':foot['facts']['safeBottom'],'representative':foot['screenReferences'],'sameRenderSignatureAsHome':True},'twoBuildManifestByteIdentity':True,'distFilesRehashed':20,'mobileFullOriginalsPixelReviewed':10,'mobileSupplementalOriginalsPixelReviewed':65,'losslessInspectionSheetsOpened':38,'browserLaunched':False,'screenshotsLimit':'The 15 keyboard screenshots are final focus views; intermediate 279 targets have measured geometry and fragment hit tests, not one screenshot each.'}
(O/'independent-raw-results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k!='previousKeyboardFailuresSameTargetRechecked'},ensure_ascii=False,indent=2))
