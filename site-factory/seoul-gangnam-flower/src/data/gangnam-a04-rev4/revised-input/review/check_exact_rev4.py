from pathlib import Path
import hashlib,json,datetime
P=Path('/workspace/shared/gangnam-a04-addendum-20261013');B=Path('/workspace/shared/gangnam-plan-copy-20261013');N=P/'revised-input';O=N/'review';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();checks=[]
def ck(name,a,b):checks.append({'check':name,'actual':a,'expected':b,'pass':a==b})
def diff(a,b,p=''):
 if type(a)!=type(b):return [{'path':p,'old':a,'new':b}]
 if isinstance(a,dict):
  out=[]
  for k in sorted(a.keys()|b.keys()):
   if k not in a:out.append({'path':p+'/'+k,'added':b[k]})
   elif k not in b:out.append({'path':p+'/'+k,'removed':a[k]})
   else:out+=diff(a[k],b[k],p+'/'+k)
  return out
 if isinstance(a,list):
  if len(a)!=len(b):return [{'path':p,'old':a,'new':b}]
  return sum((diff(x,y,p+'/'+str(i)) for i,(x,y) in enumerate(zip(a,b))),[])
 return [] if a==b else [{'path':p,'old':a,'new':b}]
manifest=json.loads((N/'review-input-manifest.rev4.json').read_text());ck('review manifest expected SHA',sha(N/'review-input-manifest.rev4.json'),'7d41236677517aaa85b9d23cf75fe7cf492d231cce013bee1381477f9a752319')
for x in manifest['inputs']+[manifest['frozenRubric'],manifest['frozenTargets'],manifest['originalAlignmentResult'],manifest['originalReproduction']]:
 f=Path(x['path']);ck('review input bytes/SHA '+str(f),[f.stat().st_size,sha(f)],[x['bytes'],x['sha256']])
old=json.loads((B/'copy/article-copy.final.json').read_text());new=json.loads((N/'copy/article-copy.rev4.json').read_text());orun=json.loads((B/'handoff/runtime-input.json').read_text());nrun=json.loads((N/'handoff/runtime-input.rev4.json').read_text());change=json.loads((N/'exact-change.json').read_text());oldfirst=old['articles'][2]['firstAnswer'];newfirst=new['articles'][2]['firstAnswer'];bodydiff=diff(old['articles'],new['articles'])
ck('exact article field change set',[x['path'] for x in bodydiff],['/2/bodyAndFaqChars','/2/firstAnswer','/2/uniqueBodyCharsIncludingFirstAnswer'])
ck('one allowed prefix substitution',newfirst,oldfirst.replace('전시 참가와 기업행사를','강남구 전시와 기업행사를',1));ck('declared exact old/new',[change['customerChange']['old'],change['customerChange']['new']],[oldfirst,newfirst]);ck('prefix count',[oldfirst.count('전시 참가와 기업행사를'),newfirst.count('강남구 전시와 기업행사를')],[1,1]);ck('remaining prices/policies exact',oldfirst.split('화환은',1)[1],newfirst.split('화환은',1)[1]);ck('new opening length',len(newfirst),154)
ck('runtime exact new article projection',nrun['articles'],new['articles'])
for k in ['common','directory','assets','expectedPaths','publication','originalPlanN','region','visibilityContract','schemaVersion']:ck('runtime unchanged '+k,nrun[k],orun[k])
ck('original article N',len(new['articles']),3);ck('expected routes',len(nrun['expectedPaths']),6)
for f,x in nrun['inputBindings'].items():p=Path(f);ck('new runtime input binding '+f,[p.stat().st_size,sha(p)],[x['bytes'],x['sha256']])
for x in new['articles']:
 parts=[x['firstAnswer']]+[p for s in x['sections'] for p in s['paragraphs']];bodylen=len('\n'.join(parts));faqlen=sum(len(f['question'])+len(f['answer']) for f in x['faq']);ck('derived counts '+x['id'],[x['uniqueBodyCharsIncludingFirstAnswer'],x['faqChars'],x['bodyAndFaqChars']],[bodylen,faqlen,bodylen+faqlen])
ck('TXT projection only changed phrase',(N/'copy/article-copy.rev4.txt').read_text(),(B/'copy/article-copy.final.txt').read_text().replace(oldfirst,newfirst))
allowed=['/revision','/status','/bindings/fixedPlanPath','/bindings/planReviewPath','/articles/2/firstAnswer','/articles/2/uniqueBodyCharsIncludingFirstAnswer','/articles/2/bodyAndFaqChars','/boundary','/editedAt','/priorDraft/path','/priorDraft/sha256','/revisionReason'];adiff=diff(old,new);ck('no unexpected article change',[x['path'] for x in adiff if x['path'] not in allowed],[])
rdiff=diff(orun,nrun);allowedruntime=['/articles/2/firstAnswer','/articles/2/uniqueBodyCharsIncludingFirstAnswer','/articles/2/bodyAndFaqChars','/inputBindings','/status','/revision','/supersedesRuntime'];ck('no unexpected runtime change',[x['path'] for x in rdiff if not any(x['path']==a or x['path'].startswith(a+'/') for a in allowedruntime)],[])
result={'reviewedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'verdict':'REV4_LOCAL_DRAFT_EXACT_CHANGE_AND_PROJECTION_VERIFIED','articleSha256':sha(N/'copy/article-copy.rev4.json'),'runtimeSha256':sha(N/'handoff/runtime-input.rev4.json'),'manifestSha256':sha(N/'review-input-manifest.rev4.json'),'directChecks':{'count':len(checks),'passed':sum(x['pass'] for x in checks),'failed':[x for x in checks if not x['pass']],'checks':checks},'exactArticleDiff':adiff,'exactRuntimeDiff':rdiff,'editorialJudgment':{'classification':'추정·판단 based on direct comparison of the complete old/new first answer and unchanged approved body','naturalness':'강남구 전시와 기업행사를 축하하는 화환은… is a concise, understandable geographic qualifier attached to the already intended exhibition/corporate-event purchase context. It does not read as a checklist or internal SEO instruction. No further rewrite is necessary for this limited correction.','providerVoice':'꽃이랑에서 … 상담합니다 remains intact. The seller consultation voice, stated basic-price range and venue-dependent receipt/placement restriction are unchanged.','intent':'Replacing 전시 참가와 with 강남구 전시와 states the existing regional target; no new SKU, article, facility, business service or guarantee is introduced. Exhibition participation remains covered in the unchanged body.','scopePreservation':'N3, six routes, title/H1/meta/cards/body/FAQ/CTAs/source links/assets and all pricing/material/refund/collection policies are identical.'},'renderBoundary':'This is replacement-input review. The current actual event HTML still uses rev3 firstAnswer. Neither revised static build nor revised screen/public delivery was verified here.','previousResultPreserved':'Original A04 raw95/effective89/G4 REVISE records remain unchanged; rev4 removes the verified text absence under the same frozen rubric/targets.','noSourceEdits':True}
(O/'second-exact-copy-review.rev4.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'checks':len(checks),'passed':result['directChecks']['passed'],'failed':result['directChecks']['failed'],'reportSha256':sha(O/'second-exact-copy-review.rev4.json')},ensure_ascii=False,indent=2))
