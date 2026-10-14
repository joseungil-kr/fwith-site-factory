import json,hashlib
from pathlib import Path
from datetime import datetime,timezone
P=Path('/workspace/shared/seocho-plan-copy-20261013');O=P/'independent-copy-review';load=lambda p:json.loads(Path(p).read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
r=load(P/'handoff/runtime-input.json');d=load(P/'handoff/directory-input.json');b=load(P/'handoff/input-bindings.json');a=load(P/'copy/article-copy.rev4.json');c=load(P/'copy/common-visible-copy.rev2.json');m=load(P/'plan/membership.json');f=load(P/'plan/fixed-plan.json');tests=[]
def check(n,v):tests.append({'check':n,'pass':bool(v)})
submitted={'handoff/runtime-input.json':'4c745c0e299f22c7f978ff14d364b881fafdb53bdfbb36521f50aaa1fea79383','handoff/directory-input.json':'6ad12465e97664aa1ddb79a701bfb0344d8fdae3905fb7b2cbc09fe1b0c73904','handoff/input-bindings.json':'a67cbb85772831d4f141661e1a735db4b9d271f67bc437cd82da27cc3fbe125d','handoff/IMPLEMENTATION-HANDOFF.txt':'d7e000f434ee8f2adeb157ff3045cff9775d58d84eb8bc40c8b2778215468682'}
for n,s in submitted.items():check('submitted exact hash '+n,sha(P/n)==s)
check('runtime articles full exact object equality to approved rev4',r['articles']==a['articles']);check('runtime common full exact object equality to approved rev2',r['common']==c['common']);check('runtime sourceImplementation false',r['sourceImplementation'] is False)
for name in ['legalUnits','administrativeUnits','relations']:check('directory '+name+' exact equality',d[name]==m[name])
check('directory cards exact common articleCards',d['directoryArticleCards']==c['common']['articleCards']);check('only 3 physical anchors',len(d['physicalAnchors'])==3)
check('only 1 nonfacility occasion',len(d['occasions'])==1 and d['occasions'][0]['notFacility'] and d['occasions'][0]['id']=='opening-relocation' and d['occasions'][0]['legalCode'] is None)
byid={x['id']:x for x in a['articles']}
for anchor in d['physicalAnchors']+d['occasions']:
 article=byid[anchor['article']];check('existing anchor '+anchor['id'],anchor['id'] in [s['id'] for s in article['sections']]);check('exact anchor path '+anchor['id'],anchor['href']==article['url']+'#'+anchor['id']);check('no administrative inference '+anchor['id'],anchor['administrativeDong'] is None)
for anchor in d['physicalAnchors']:
 cand=next(x for x in f['candidateLedger'] if x['id']==anchor['id']);check('legalDong binding '+anchor['id'],anchor['legalCode']==cand['legalCode'] and anchor['legalDong']==cand['legalDong']);check('admission remains unverified '+anchor['id'],anchor['admissionVerified'] is False)
check('route denominator exact',b['expectedRoutes']==f['routeDenominator']['expectedRoutes']);check('no final remote source SHA',b['remoteBinding']['sourceSHA'] is None and b['remoteBinding']['directRemoteReadThisTask'] is False)
for file in b['files']:
 path=P/file['file'];check('binding '+file['file'],sha(path)==file['sha256'] and path.stat().st_size==file['bytes'])
check('runtime binding exact article final hash',r['bindings']['articlesSha256']==sha(P/'copy/article-copy.rev4.json'));check('runtime binding exact common hash',r['bindings']['commonSha256']==sha(P/'copy/common-visible-copy.rev2.json'))
check('directory unchanged against prior reviewed artifact',sha(P/'handoff/directory-input.json')==load(O/'handoff-projection-verdict.json')['files']['handoff/directory-input.json'])
check('three old instructions absent in projected bodies',all(x['old'] not in '\n'.join(z['contentMarkdown'] for z in r['articles']) for x in load(O/'exact-delta-checks.rev4.json')['expectedSentenceReplacements']))
result={'checkedAtUTC':datetime.now(timezone.utc).isoformat(),'revision':4,'verdict':'PASS_LOCAL_HANDOFF_EXACT_PROJECTION' if all(t['pass'] for t in tests) else 'REVISE','classification':'직접 확인: full parsed JSON equality, all handoff bytes and independently recomputed bindings.','files':{n:sha(P/n) for n in submitted},'tests':tests,'checkCount':len(tests),'failureCount':sum(not t['pass'] for t in tests),'copyVerdict':{'path':'independent-copy-review/verdict.rev4.json','sha256':sha(O/'verdict.rev4.json')},'manualHandoffReading':'Compared complete handoff text with preserved rev3. The only prose change clarifies aT wedding order guidance withheld, no customer checking task or promised seller confirmation service, and no revival of the 2017 planned rule as a current blanket prohibition. Other boundaries and implementation verification duties remain intact.','statusInterpretation':'Carrier runtime status remains conservatively pending. This verdict verifies exact projection only; final acceptance sealing is separate and cannot authorize source/publication.','notVerified':['Source implementation, final source commit and remote refs','Actual HTML, FAQ visibility, keyboard navigation and browser/viewport QA','Build/deployment/public HTTP/indexing','Actual facility admission, stock, order or fulfillment']}
assert result['failureCount']==0
(O/'handoff-projection-verdict.rev4.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
readback=load(O/'handoff-projection-verdict.rev4.json');assert readback==result
print(json.dumps({'verdict':result['verdict'],'checks':len(tests),'failures':result['failureCount'],'verdictSHA':sha(O/'handoff-projection-verdict.rev4.json')},ensure_ascii=False,indent=2))
readme=(O/'README.txt').read_text();readme=readme.replace('rev4 인계 데이터는 재생성 후 별도 검토가 필요합니다. 기존 handoff-projection-verdict.json은 rev3 인계 파일에만 적용됩니다.','rev4 인계 데이터의 exact projection을 43검사 실패 0건으로 확인했습니다. 현재 인계 검토서는 handoff-projection-verdict.rev4.json입니다. 기존 handoff-projection-verdict.json은 rev3 인계 파일에만 적용됩니다.');readme+='handoff-projection-verdict.rev4.json\n';(O/'README.txt').write_text(readme)
