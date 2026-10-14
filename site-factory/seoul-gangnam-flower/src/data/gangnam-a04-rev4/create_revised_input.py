from pathlib import Path
import json,hashlib,datetime,difflib,copy
O=Path(__file__).parent; B=Path('/workspace/shared/gangnam-plan-copy-20261013'); R=O/'revised-input'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text())
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def bind(p):return {'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)}
now=datetime.datetime.now(datetime.timezone.utc).isoformat()
a=read(B/'copy/article-copy.final.json'); old=a['articles'][2]['firstAnswer'];old_prefix='전시 참가와 기업행사를 축하하는 화환은';new_prefix='강남구 전시와 기업행사를 축하하는 화환은'
assert old.startswith(old_prefix)
new=new_prefix+old[len(old_prefix):]
a['articles'][2]['firstAnswer']=new
for k in ['uniqueBodyCharsIncludingFirstAnswer','bodyAndFaqChars']: a['articles'][2][k]+=len(new)-len(old)
a['revision']=4;a['editedAt']=now;a['priorDraft']={'path':str(B/'copy/article-copy.final.json'),'sha256':sha(B/'copy/article-copy.final.json')}
a['revisionReason']='Root-directed minimal event opening-region clarification after preserved A04 v1 REVISE; only customer first-answer prefix changes. Existing N, URLs, primary target, prices, policies, body, FAQ, CTA and assets preserved.'
a['bindings']['fixedPlanPath']=str(B/'plan/fixed-plan.json');a['bindings']['planReviewPath']=str(B/'independent-plan-review/final-verdict.json')
a['status']='REV4_DRAFT_FOR_EXACT_COPY_AND_FROZEN_A04_REVIEW'
a['boundary']='Separate local replacement input. Original sealed bundle and implementation source remain unchanged. Revised copy has not been rendered or deployed; apply only after supplementary acceptance.'
ap=R/'copy/article-copy.rev4.json';write(ap,a)
txt=(B/'copy/article-copy.final.txt').read_text();assert txt.count(old)==1;(R/'copy/article-copy.rev4.txt').write_text(txt.replace(old,new))
r=read(B/'handoff/runtime-input.json');r['articles']=copy.deepcopy(a['articles'])
oldbindings=r['inputBindings'];r['inputBindings']={str(B/k):v for k,v in oldbindings.items() if k!='copy/article-copy.final.json'};r['inputBindings'][str(ap)]={'sha256':sha(ap),'bytes':ap.stat().st_size}
r['status']='LOCAL_REV4_REPLACEMENT_INPUT_NOT_IMPLEMENTED';r['revision']=4;r['supersedesRuntime'] = bind(B/'handoff/runtime-input.json')
rp=R/'handoff/runtime-input.rev4.json';write(rp,r)
for oldf,newf,name in [(B/'copy/article-copy.final.json',ap,'article-copy.rev3-to-rev4.diff'),(B/'handoff/runtime-input.json',rp,'runtime-input.rev3-to-rev4.diff')]:
 (R/name).write_text(''.join(difflib.unified_diff(oldf.read_text().splitlines(True),newf.read_text().splitlines(True),fromfile=str(oldf),tofile=str(newf))))
change={'recordedAt':now,'classification':'직접 확인: exact local input diff; instruction authority from root task','scope':'Only one customer-visible string changes; metadata and derived counts are separately enumerated. No source edits.', 'customerChange':{'sourcePointer':'/articles/2/firstAnswer','old':old,'new':new,'oldCharacters':len(old),'newCharacters':len(new),'oldPrefix':old_prefix,'newPrefix':new_prefix},'derivedChanges':['/articles/2/uniqueBodyCharsIncludingFirstAnswer','/articles/2/bodyAndFaqChars'],'nonCustomerMetadataChanged':{'article':['revision','editedAt','priorDraft','revisionReason','bindings.fixedPlanPath','bindings.planReviewPath','status','boundary'],'runtime':['inputBindings','status','revision','supersedesRuntime']},'originalInputs':[bind(B/'copy/article-copy.final.json'),bind(B/'handoff/runtime-input.json'),bind(B/'copy/common-visible-copy.final.json'),bind(B/'plan/fixed-plan.json')],'newInputs':[bind(ap),bind(R/'copy/article-copy.rev4.txt'),bind(rp)],'rootSelectedOption':'강남구 전시와 기업행사를 축하하는 화환은…','noNewFacts':'The region is the existing page target and venue geography. Prices and all conditions are byte-identical after the changed prefix. No added delivery/availability guarantee.'}
write(R/'exact-change.json',change)
write(R/'review-input-manifest.rev4.json',{'createdAt':now,'status':'REVIEW_INPUT_ONLY_NOT_ACCEPTANCE','articleRevision':4,'commonRevision':2,'originalArticleN':3,'expectedRouteCount':6,'frozenRubric':bind(O/'rubric/A04_RUBRIC_v1.md'),'frozenTargets':bind(O/'assessment/targets.frozen.json'),'inputs':[bind(ap),bind(R/'copy/article-copy.rev4.txt'),bind(rp),bind(B/'copy/common-visible-copy.final.json'),bind(B/'plan/fixed-plan.json'),bind(R/'exact-change.json')],'originalAlignmentResult':bind(O/'assessment/a04-independent-assessment.v1.json'),'originalReproduction':bind(O/'independent-review/independent-assessment.json'),'evaluationBoundary':'New draft-input assessment. Current local HTML remains old revision and is not evidence of revised visible copy. No source modification allowed by this task.'})
print(json.dumps({'newFirstAnswer':new,'chars':len(new),'article':bind(ap),'runtime':bind(rp),'reviewManifest':bind(R/'review-input-manifest.rev4.json')},ensure_ascii=False,indent=2))
