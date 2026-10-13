from pathlib import Path
from PIL import Image,ImageChops
import json,hashlib,shutil
ROOT=Path('/workspace/scratch/e695498f2eb8');R=ROOT/'gwanak-qa-run-38400663920';O=ROOT/'gwanak-pixel-independent-38400663920';D=ROOT/'gwanak-desktop-pixel-independent-38400663920'
sha=lambda b:hashlib.sha256(b).hexdigest();load=lambda p:json.loads(p.read_text())
sheets=load(O/'inspection-sheets.json');coverage={}
for s in sheets:
 assert s['opened'];im=Image.open(O/s['sheet']).convert('RGB');x=0
 for origin in s['originals']:
  p=R/origin['path'];source=Image.open(p).convert('RGB');assert sha(p.read_bytes())==origin['sha256']
  coverage.setdefault(origin['path'],{'path':origin['path'],'sha256':origin['sha256'],'dimensions':list(source.size),'ranges':[],'openedInLosslessNativeResolutionSheets':[]})
  for y,z in origin['ranges']:
   offset=40 if s['kind']=='fullpage-lossless-tiles' else 65
   tile=im.crop((x,offset,x+source.width,offset+z-y))
   assert ImageChops.difference(tile,source.crop((0,y,source.width,z))).getbbox()is None
   coverage[origin['path']]['ranges'].append([y,z]);coverage[origin['path']]['openedInLosslessNativeResolutionSheets'].append(s['sheet']);x+=source.width
for e in coverage.values():
 ranges=sorted(e['ranges']);last=0
 for a,b in ranges:assert a<=last;last=max(last,b)
 assert last==e['dimensions'][1]
assert len(coverage)==75
peer=load(D/'desktop-pixel-verdict.json');peerhash=sha((D/'desktop-pixel-verdict.json').read_bytes());assert peerhash=='02d02bc47951f39186faf37db179f13256cd7fbf14e32192e9a3179aa8370c05'
for e in peer['fullpage_evidence']+peer['supplemental_evidence']:
 assert sha(Path(e['path']).read_bytes())==e['sha256'];im=Image.open(e['path']);assert list(im.size)==e['dimensions'];assert e['original_opened']
 for c in e.get('native_width_crops_opened',[]):
  ci=Image.open(c['crop']).convert('RGB');assert sha(Path(c['crop']).read_bytes())==c['crop_sha256'];assert ImageChops.difference(ci,im.convert('RGB').crop(c['range_xyxy'])).getbbox()is None
shutil.copyfile(D/'desktop-pixel-verdict.json',O/'peer-desktop-pixel-verdict.json')
raw=load(O/'independent-raw-results.json');cross=load(O/'opened-desktop-crosscheck.json')
verdict={
 'status':'BOUNDED_UNPUBLISHED_CHROMIUM_QA_VERIFIED_NO_BLOCKING_PIXEL_DEFECT_OBSERVED',
 'runId':38400663920,'runAttempt':1,'sourceSha':raw['sourceSha'],'controlSha':raw['controlSha'],
 'runUrl':'https://github.com/joseungil-kr/fwith-site-factory/actions/runs/38400663920',
 'checkedResults':[
  'Read and independently rehashed all 180 sealed files, all 20 built dist files, all 15 full-page screenshot hashes/dimensions, and the byte-identical first/second build manifests. Source/control/run/attempt identity matches the reviewed corrected source and QA control.',
  'Directly opened the decoded pixels of all ten mobile full-page images over their entire vertical extents and all 65 mobile supplemental viewports at original resolution through 38 lossless PNG inspection sheets. Every sheet tile was subsequently checked pixel-for-pixel against the decoded original JPEG, without source mutation or scaling.',
  'All three oversized 320px cards retained their original shell height. I personally opened all six actual-content views for each card, eighteen segment images total. Product image, name, complete amount/currency, description, order link and caption were visible when targeted. No clipped photo content or hidden target text was found. A card shell extending behind the fixed order bar is not being counted as proof of inaccessible content.',
  'I personally opened all ten mobile initial-anchor views, all three opening-occasion widths, the desktop funeral anchor, all mobile final keyboard views, both mobile footer representative views and desktop footer/FAQ samples. Intended anchor headings are clear of the sticky header. Mobile final focus is on the fixed bar with visible outline; footer links are readable above it.',
  'Independently reran the actual saved-data validators over 285 geometry rows, 288 product content targets, 15 anchor flows and 279 keyboard targets. Every target satisfies the original unrelaxed visibility, boundary, fragment occlusion and focus-ring rules, with no recorded row/flow/network/page-console error.',
  'Matched each of the eight previously failing keyboard arrivals by route, width, DOM index, exact text and href between the original failed report and the corrected raw report. All eight now satisfy their safe-area bounds and all hit tests. 320px home bottom changes from 740.140625 to 670.140625 with bar top 682; 390px 404 return link changes from 790.59375 to 773.59375 with bar top 786.',
  'All three corrected opening-occasion flows record directory baseline HTTP200 and a distinct occasion document HTTP200, exact first-landing URL and expected H2 text/ID, with unobstructed target measurements. All three corresponding images were personally opened.',
  'The apparent footer overlap in the 390px 404 full-page capture is the initial fixed-bar position in a full-page snapshot. The actual 404 final-focus image shows the links above the bar. Independently checked footer row has content bottom751.59375 versus bar786, every item/hit check succeeds, and its rendering signature exactly matches the explicitly referenced supplemental/390/home/footer.jpg, which was personally inspected.',
  'All 15 fresh unfocused full-page JPEG files are byte-identical to the original unfocused-layout artifact ZIP entries. This is consistent with the isolated scroll-padding change and is not used as proof of corrected focused states; those require the new native-arrival measurements and viewport evidence.'
 ],
 'peerReview':{
  'category':'Tool/agent report, artifact independently read and hashes/crop pixels cross-checked',
  'scope':'Independent desktop reviewer opened all five 1280px full-page originals plus 25 native-width vertical crop ranges, and all22 desktop supplemental originals. No blocking defect observed.',
  'report':'peer-desktop-pixel-verdict.json','sha256':peerhash,
  'myCrossCheck':'I additionally opened all five desktop full-page overviews and four full-resolution supplemental views (opening anchor, funeral anchor, footer and funeral FAQ). Detailed all-height desktop legibility observations beyond those samples remain the peer reviewer’s direct observations.'
 },
 'judgment':[
  'Within the supplied Chromium loopback run at320x740,390x844 and1280x900, the corrected-source QA has produced verifiable artifacts and no blocking visual defect remains in the reviewed coverage. This is sufficient to close the requested unpublished visual-QA correction stage.',
  'The mobile layout is long and the 320px two-column home navigation cards are narrow, but text remains readable and untruncated in the reviewed pixels. Original copy/images have not been shortened or replaced to pass geometry. No new design change is proposed by this review.'
 ],
 'unverifiedAndLimits':[
  'The 15 keyboard screenshots show each flow’s final focus target. The intermediate279 targets, including the eight historical failures, are supported by recorded native-arrival DOM geometry and nine-per-fragment hit tests; they do not each have a dedicated screenshot. Do not describe this as279 separate pixel captures.',
  'Image review covers102 actual screenshots across independent reviewers:15 full-page and87 supplemental. I personally performed native-resolution full-extent review of75 mobile originals, plus desktop overview/sample cross-checks; the detailed full desktop review is separately attributed above.',
  'No browser was launched and no new screenshot was produced during this independent review. It examines the saved artifacts of the exact-source run, not live production.',
  'Public deployment, domain ownership/DNS, production HTTP, external order/telephone/source link activation, IndexNow/search submission and real purchases are not verified or authorized by this QA verdict.',
  'Safari/Firefox, other widths/heights, zoom levels, touch interaction, real safe-area devices, virtual on-screen keyboard behavior, screen readers, contrast ratios and a comprehensive accessibility audit are outside this run.',
  'Current seller stock/prices, source factual accuracy, venue acceptance, arrival promises and live service availability are not re-researched in this visual review.'
 ],
 'pixelCoverage':{'fullpageImagesAcrossIndependentReviewers':15,'supplementalImagesAcrossIndependentReviewers':87,'myNativeResolutionMobileOriginals':75,'myDesktopFullpageOverviews':5,'myDesktopSupplementalSamples':4,'peerDesktopOriginals':27,'myMobileFiles':list(coverage.values()),'myDesktopCrosscheck':cross},
 'evidence':{'rawReverification':'independent-raw-results.json','rawReverificationSha256':sha((O/'independent-raw-results.json').read_bytes()),'pixelRanges':'inspection-sheets.json','pixelRangesSha256':sha((O/'inspection-sheets.json').read_bytes()),'verificationScript':'verify_raw_results.py','pixelReadbackScript':'write_final_review.py'},
 'unpublishedVisualQaStageVerified':True,'productionDeploymentVerified':False,'publicationAuthorization':'not-issued','browserLaunchedByReviewer':False,'remoteWritesByReviewer':False
}
(O/'VERDICT.json').write_text(json.dumps(verdict,ensure_ascii=False,indent=2)+'\n')
assert load(O/'VERDICT.json')==verdict
files=[{'path':p.name,'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())}for p in sorted(O.iterdir())if p.is_file()and p.name!='review-evidence-manifest.json']
(O/'review-evidence-manifest.json').write_text(json.dumps({'files':files},indent=2)+'\n')
print('VERDICT.json SHA256',sha((O/'VERDICT.json').read_bytes()))
print('Verified inspection sheets pixel-equal to source:38; mobile originals covered75; peer original hashes27; stored evidence files',len(files))
