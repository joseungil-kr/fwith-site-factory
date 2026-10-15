from pathlib import Path
import json,hashlib,datetime
O=Path(__file__).resolve().parent;ROOT=O.parent
L=lambda p:json.loads(Path(p).read_text())
def sha(b):return hashlib.sha256(b).hexdigest()
def save(n,j):(O/n).write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n')
def ev(p):
 p=ROOT/p;b=p.read_bytes();return dict(path=str(p.relative_to(ROOT)),bytes=len(b),sha256=sha(b))
now=datetime.datetime.now(datetime.timezone.utc).isoformat()
reuse=[]
for name in ['astro','storefront']:
 f='yeosu-research-preparation-20261014/evidence/'+name+'-meta.tool.json';meta=json.loads(L(ROOT/f)['structuredContent']['content']);lf='yeosu-research-preparation-20261014/evidence/'+('astro-license.tool.json' if name=='astro' else 'storefront-LICENSE.tool.json');lic=L(ROOT/lf)['structuredContent']['content']
 reuse.append(dict(repository=meta['html_url'],retainedMetadata=ev(f),lastPushReported=meta['pushed_at'],archivedReported=meta['archived'],licenseEvidence=ev(lf),licenseActualTextStartsMIT=lic.startswith('MIT License'),licenseScope='MIT with retained Svelte/Rollup notices' if name=='astro' else 'MIT',statusSource='Retained2026-10-14 GitHub tool response, directly read now; no current remote check.',fit='Existing content framework; reuse original pinned Astro build and validated cards.' if name=='astro' else 'Alpha storefront, SolidJS/server actions; Stripe/Loops/Maps integrations and public mock API. Adds unnecessary service/credential scope to this static consultation landing; not adopted.'))
save('research-reuse-review.json',dict(reviewedUTC=now,scope='Read existing Yeosu research evidence; no new development direction or remote research.',github=reuse,existingImplementation=dict(package=ev('yeosu-research-preparation-20261014/evidence/fwith-site-factory-package-json.tool.json'),cards=ev('yeosu-research-preparation-20261014/evidence/fwith-site-factory-ProductCards-astro.tool.json'),decision='Reuse original static Astro, exact SKU card actions, shared assets and validators. No commerce integration or new region text copied.'),market=dict(evidence=['a04-targets-and-scores.json#/queryEvidence/Q3','a04-targets-and-scores.json#/queryEvidence/Q4'],finding='Retained full competitor text shows venue-specific and regional commercial offers. This supports buyer-question selection, not traffic, demand, market share or efficacy claims.',noCompetitorPromiseImported=True),freshness='Historical retained evidence only. Metadata recency does not prove maintenance quality.'))
save('verification-method-notes.json',dict(scope='Reviewer-local recovery notes; no product source was modified.',events=[dict(issue='Unavailable cloud skill package',exactError='skill package is not available',resolution='Continued authorized read-only local content/contract inspection; no setup or unsupported access workaround.'),dict(issue='Wrong assumed prior verification filename',exactError="FileNotFoundError: yeosu-local-implementation-20261015/verification.json",resolution='Located actual evidence/source-manifest.json and original-input-baseline.json. No claim derived from missing file.'),dict(issue='First independent Markdown extractor handled comments incorrectly',effect='B201 heading omitted from expected list; trailing PRODUCT_CARDS_END comment remained in expected text.',resolution='Fixed reviewer-only parser to remove comments before splitting. Exact original44 detail blocks now equal44 compiled blocks. Original source unchanged.'),dict(issue='Initial sibling-input scope selected historical313-file workspace baseline',resolution='Corrected to portable26-file original-input-baseline actually consumed by frozen candidate; all26 match. Broad historical baseline was not used as release denominator.'),dict(issue='Manifest refresh overlapped parent metadata fixes',resolution='Intermediate expected digests were stale during authorized parent edits. Final source85/control23 manifests independently reread after parent freeze; all match.'),dict(issue='Fast status message first paragraph length off by one',resolution='NFC/whitespace/codepoint method gives home122/article177. Report and exact first120/180 extraction corrected; message to parent explicitly corrected.'),dict(issue='Policy-image URL was initially transcribed incorrectly in reviewer draft ledger',resolution='Checked retained-source-provenance.json; authoritative order-top2 URL is https://fwith.co.kr/shop/img/order-top2.jpg. Corrected only reviewer ledger.'),dict(issue='Twitter metadata missing in initial production fixture',resolution='Recorded initial actual heads. Parent corrected production adapter only; current exact12 social fields per3non404 pages and unchanged body4/static9 directly verified.'),dict(issue='Metadata-only validator ambiguity reported by technical reviewer',resolution='Parent strengthened source validators/tests without output changes. This content review binds final refreshed source/control hashes; technical behavior remains that reviewer’s separate result.')]))
review=L(O/'review.json');review.pop('publicationAuthorized',None);review['publicationAuthorizationVerified']=False
review['directlyVerified']=[
 'Read original full customer copy, contracts and retained primary sources, with source hashes.',
 'Independently matched all 85 source files and 23 control files to the final manifests.',
 'Confirmed all 75 frozen portable files, original 40 source files and 26 sibling inputs remain unchanged.',
 'Compared all 4 full customer bodies and 9 static assets against the frozen preview: exact bytes preserved.',
 'Extracted exact title, H1, first 120/180 codepoints, all 3 FAQ answers, 4 SKU cards and destination links.',
 'Verified planned-origin local canonical/robots/sitemap and 12 exact OG/Twitter fields on each of 3 non-404 pages.',
 str(review['staticChecks']['total'])+' independent local static checks passed. This is not runner, browser or public HTTP evidence.'
]
review['toolReportedOnly']=[
 'Parent reports build/adapter/output/control test success; this worker did not rerun those suites.',
 'Historical HTTP acquisition and GitHub readbacks are retained tool reports, not current network verification.',
 'Prior cross-region overlap metrics were read but not rerun; no market-demand measurement was performed.'
]
review['notVerified']=[
 'Actual remote successor commit/tree and saved content-review binding.',
 'Actual clean runner install/build/run/artifact and all-route 320/390/1280 browser captures.',
 'Independent browser pixel review and computed FAQ/CTA visibility or interaction.',
 'Current product prices, stock, telephone connection, destination responses and venue conditions.',
 'Actual approved hostname/provider ownership/collision/attachment, public HTTP200/404 and asset MIME.',
 'Actual Mokpo26 predecessor public completion and authorization/receipt bindings.',
 'IndexNow receipt, crawling, indexing, impressions, CTR and ranking.'
]
review['requiredNextEvidence']=[
 'Bind this exact review/rubric/A04 supplement to the actual runner artifact and source/control commits, preserving frozen content.',
 'Review all four routes at 320/390/1280 and computed FAQ/CTA visibility; leave S10 and AEO-A06 pending until that evidence exists.',
 'Verify public bytes, HTTP200, real unknown-path404, resource MIME and exact product destinations; leave S09 pending until verified.',
 'Reconcile scope-matched release/origin authorization and prior Mokpo26 public evidence.',
 'Track submission, crawl, index and ranking as separate states.'
]
review['resolvedStaticDefects'][0].update(finding='Initial local production head omitted required Twitter metadata.',fixedBy='Parent technical adapter; this content reviewer made no source edits.',verified='Independently read 12 exact OG/Twitter fields on all three non-404 pages, exact B201 image/alt, final source/control hashes and unchanged four bodies/nine assets.',scope='Local fixture only.')
review['files']={p.name:sha(p.read_bytes()) for p in sorted(O.iterdir()) if p.is_file() and p.name not in ['review.json','SHA256SUMS','self-verification.json']};save('review.json',review)
# Cross-check the saved deliverable rather than trusting its creator's return status.
b=L(O/'input-binding.json');s=L(O/'static-observations.json');r=L(O/'rubric.json');a=L(O/'a04-targets-and-scores.json');scores=L(O/'scores.json');pres=L(O/'original-preservation.json');c=L(O/'contract-applicability.json')
checks=[]
def ck(n,v):checks.append(dict(check=n,pass_=bool(v)))
ck('source final exact',b['sourceManifest']['matches'] and b['sourceManifest']['treeSHA256']=='4df5f0dc1d7803d23fca19df1ff91622fe8b5417bb7b6cede7ad5aa83bad7c7c')
ck('control final exact',b['controlManifest']['matches'] and b['controlManifest']['treeSHA256']=='07720aef23bb2d9b097c4b7ce6e8401fb751c0ce61e705a26d1dbbc32be20109')
ck('all static checks directly reread',s['counts']['failCount']==0 and len(s['checks'])==s['counts']['total'])
ck('all24 original clauses',len(c['items'])==24 and {x['id'] for x in c['items']}=={f'C{i:02d}' for i in range(1,15)}|{f'A{i:02d}' for i in range(1,11)})
ck('original75/40/26 complete',len(pres['frozen75'])==75 and len(pres['original40']['files'])==40 and len(pres['original26'])==26 and all(x['matches'] for x in pres['frozen75']+pres['original26']))
ck('body4/static9 immutable',pres['customerBodyCount']==4 and pres['staticAssetCount']==9 and all(x['same'] for x in pres['customerBodies']) and all(x['unchanged'] for x in pres['staticAssets']))
ck('A04 exact two100 scores',len(a['pages'])==2 and all(p['title_alignment_score']==sum(x['verifiedPoints'] for x in p['criteria'])==100 for p in a['pages']))
for p in scores['pages']:
 for group,expected in [('SEO',80),('GEO',100),('AEO',90)]:
  v=p['scores'][group];ck(p['id']+' '+group+' fixed100 and evidence sum',sum(x['weight'] for x in v['criteria'])==100 and v['verifiedPoints']==sum(x['verifiedPoints'] for x in v['criteria'])==expected)
 ck(p['id']+' required pending scores remain zero',all(x['verifiedPoints']==0 and x['status']=='PENDING' for x in p['scores']['SEO']['criteria'] if x['id'] in ['S09','S10']) and next(x for x in p['scores']['AEO']['criteria'] if x['id']=='A06')['verifiedPoints']==0)
for name,digest in review['files'].items():ck('review file binding '+name,sha((O/name).read_bytes())==digest)
for section in ['sourceManifest','controlManifest']:
 base=ROOT/'yeosu-production-preparation-20261015'/('source' if section=='sourceManifest' else 'control')
 ck(section+' unchanged at final readback',all(sha((base/x['path']).read_bytes())==x['sha256'] for x in b[section]['files']))
ck('never claims complete production',review['productionGateStatus']=='PENDING' and not review['publicationExecuted'] and not review['publicHTTPVerified'] and not review['browserPixelsVerified'] and not review['actualRunnerArtifactVerified'])
save('self-verification.json',dict(reviewedUTC=now,status='PASS_REVIEW_ARTIFACT_READBACK' if all(x['pass_'] for x in checks) else 'FAIL',checks=checks,failures=[x for x in checks if not x['pass_']],notAProductReleasePass=True))
manifest=''.join(sha(p.read_bytes())+'  '+p.name+'\n' for p in sorted(O.iterdir()) if p.is_file() and p.name!='SHA256SUMS');(O/'SHA256SUMS').write_text(manifest)
print(json.dumps(dict(reviewSHA256=sha((O/'review.json').read_bytes()),reportSHA256=sha((O/'REPORT.ko.txt').read_bytes()),artifactFiles=len(list(O.iterdir())),selfChecks=len(checks),failed=[x for x in checks if not x['pass_']]),indent=2))
assert all(x['pass_'] for x in checks)
