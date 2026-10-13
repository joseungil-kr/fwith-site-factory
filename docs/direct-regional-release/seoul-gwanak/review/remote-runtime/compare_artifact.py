from pathlib import Path
import json,hashlib,re,subprocess
from lxml import html
O=Path('/workspace/shared/gwanak-remote-runtime-independent-20261013');L=Path('/workspace/shared/gwanak-runtime-copy-independent-20261013');OLD=Path('/workspace/shared/gwanak-factory/site-factory/seoul-gwanak-flower/dist');R=Path('/workspace/shared/gwanak-source-exact');P=R/'site-factory/seoul-gwanak-flower';NEW=P/'dist';S='4f982994513cb7913f869b0114b3427be50b1362'
sha=lambda b:hashlib.sha256(b).hexdigest();m=json.loads((L/'dist-manifest.json').read_text())['files'];rows=[]
assert {str(p.relative_to(NEW)) for p in NEW.rglob('*') if p.is_file()}=={e['path'] for e in m}
pattern=re.compile(rb'(<meta name="site-factory-revision" content=")([^"]*)(")')
for e in m:
 old=(OLD/e['path']).read_bytes();new=(NEW/e['path']).read_bytes();assert sha(old)==e['sha256'];isHtml=e['path'].endswith('.html');changed=old!=new
 if isHtml:
  prior=pattern.findall(old);current=pattern.findall(new);assert len(prior)==len(current)==1;assert prior[0][1]==b'local-gwanak-unpublished';assert current[0][1]==S.encode();assert pattern.sub(lambda x:x[1]+b'COMMIT_REVISION'+x[3],old)==pattern.sub(lambda x:x[1]+b'COMMIT_REVISION'+x[3],new)
  t=html.fromstring(new);assert len(t.xpath('//h1'))==1;assert t.xpath('//meta[@name="robots"]/@content')==['noindex,nofollow,noarchive']
 else:assert old==new
 rows.append({'path':e['path'],'oldSha256':e['sha256'],'sha256':sha(new),'bytes':len(new),'changed':changed,'onlyChange':'site-factory-revision content' if changed else None})
assert sum(x['changed'] for x in rows)==5
manifest={'scope':'Exact source-SHA local build; independently rehashed20 files. Browser/publication unverified.','sourceCommit':S,'files':[{k:x[k] for k in ['path','bytes','sha256']} for x in rows]};(O/'actual-sha-dist-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
restore=[]
for e in json.loads((L/'source-manifest.json').read_text())['files']:
 if sha((P/e['path']).read_bytes())!=e['sha256']:restore.append(e['path'])
assert restore==[];assert subprocess.check_output(['git','status','--porcelain'],cwd=R,text=True)==''
bindings=json.loads((P/'src/data/copy-review-bindings.json').read_text());checkpoint=json.loads((P/'src/data/direct-checkpoint.json').read_text());site=json.loads((P/'src/data/site-config.json').read_text())
assert bindings['renderedReview']=='PENDING' and bindings['screenQa']=='UNVERIFIED' and bindings['productionApproval']==False
assert site['productionApproved']==False and site['hostnameOwnershipVerified']==False
report={'sourceCommit':S,'status':'EXACT_SHA_LOCAL_ARTIFACT_EQUIVALENCE_PASS','previousDistManifestSha256':sha((L/'dist-manifest.json').read_bytes()),'actualDistManifestSha256':sha((O/'actual-sha-dist-manifest.json').read_bytes()),'artifactFileCount':len(rows),'changedFiles':5,'allowedChange':'Exactly one site-factory-revision meta content per HTML, local-gwanak-unpublished -> exact source commit. Every other byte is unchanged.','source672RestoredToCommittedBytes':True,'gitWorkingTreeClean':True,'privateHistoricalProvenanceUnmodified':{'copyRenderedReview':bindings['renderedReview'],'copyScreenQa':bindings['screenQa'],'copyVerdict':bindings['verdict'],'directCheckpointStatus':checkpoint['status']},'productionApproved':False,'hostnameOwnershipVerified':False,'files':rows}
(O/'actual-sha-artifact-equivalence.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='files'},ensure_ascii=False,indent=2))
