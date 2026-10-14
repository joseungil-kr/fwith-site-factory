import json,hashlib,copy
from pathlib import Path
from datetime import datetime,timezone
P=Path('/workspace/shared/seocho-plan-copy-20261013');R=Path('/workspace/shared/seocho-research-20261013');O=P/'independent-copy-review'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
load=lambda p:json.loads(Path(p).read_text())
a2=load(P/'copy/article-copy.rev2.json');a3=load(P/'copy/article-copy.rev3.json')
assert sha(P/'copy/article-copy.rev3.json')=='cd0d68f391c97d8eceb407390aebb90f6f84aeeab99fec47971c478512af28b0'
assert sha(P/'copy/common-visible-copy.rev2.json')=='22b4b6d12142767cee9dbba40c31db290675f942000a6b86338fbf29b4a3b4cb'
def diff(a,b,path=''):
 if type(a)!=type(b):return [path]
 if isinstance(a,dict):
  out=[]
  for k in sorted(set(a)|set(b)):
   out+=diff(a.get(k),b.get(k),path+'/'+k)
  return out
 if isinstance(a,list):
  if len(a)!=len(b):return [path]
  return [d for i,(x,y) in enumerate(zip(a,b)) for d in diff(x,y,path+'/'+str(i))]
 return [] if a==b else [path]
changed=diff(a2,a3)
allowed=['/revision','/priorDraft/path','/priorDraft/sha256','/articles/1/faq/0/question','/articles/1/faq/0/answer','/articles/1/faq/0/evidence','/articles/1/faqChars','/articles/1/bodyAndFaqChars']
assert sorted(changed)==sorted(allowed),(changed,allowed)
assert a2['articles'][0]==a3['articles'][0]
for k in a2['articles'][1]:
 if k not in ['faq','faqChars','bodyAndFaqChars']:assert a2['articles'][1][k]==a3['articles'][1][k]
review=load(O/'verdict.rev2.json');review['revision']=3;review['reviewedAtUTC']=datetime.now(timezone.utc).isoformat();review['verdict']='PASS_EXACT_LOCAL_COPY_TONE_AND_INTENT';review['bindings']={str(p.relative_to(P)):sha(p) for p in [P/'copy/article-copy.rev3.json',P/'copy/article-copy.rev3.txt',P/'copy/common-visible-copy.rev2.json',P/'copy/review-input-manifest.rev3.json',P/'copy/intent-completion-matrix.rev3.json',P/'copy/claim-evidence-map.rev3.json',P/'plan/fixed-plan.json',P/'plan/evidence-registry.json',P/'handoff/approved-assets.json',P/'independent-plan-review/verdict.fixed.json']}
for f in review['facets']:
 if f['facet']=='가르치는 말투·반복 지시·경고 비중':
  f['verdict']='PASS_LOCAL_COPY';f['finding']='본문은 명령형 제목 연속·고객 선택법 강요 없이 대체로 적절하다. 장소 설명 뒤 실제 필수정보가 중앙 주문문단으로 모인다. 소재·추가비용·변경취소는 필요한 위치에 있고 CTA/FAQ에 같은 경고를 반복하지 않는다. rev2의 가상 엘블레스 오주소 질문은 제거되었다.'
 if f['facet']=='검색 의도·정보 완결성':f['verdict']='PASS_LOCAL_COPY'
 if f['facet']=='FAQ':
  f['verdict']='PASS_LOCAL_COPY';f['finding']='근조의 시설전화/판매자전화 구분은 본문의 빈소 설명과 다른 실제 추가 정보다. 최종 축하 FAQ는 카드취소 처리기간을 묻고 원본 change-policy.jpg의 카드사 처리에 따라 일주일 정도 소요될 수 있다는 내용을 정확히 옮긴다. 본문에 없는 처리기간을 답하며 취소 가능성·환불을 보장하지 않는다. 한 개씩이라는 수는 합격 근거가 아니다.'
review['blockingDefects']=[];review['resolvedDefects']=[{'id':'COPY-001','oldRevision':2,'status':'RESOLVED_IN_EXACT_REVISION_3','change':'Unsupported wrong-address FAQ replaced by verified card-cancellation processing-time FAQ.','exactNewFAQ':a3['articles'][1]['faq'][0],'source':{'file':str(R/'raw/change-policy.jpg'),'sha256':sha(R/'raw/change-policy.jpg')},'scope':'Only response timing is described; eligibility and order status remain conditional.'}]
review['revisionVerification']={'changedJSONPaths':changed,'matchesNarrowExpectedChange':True,'unchangedFuneralArticle':True,'unchangedCelebrationOutsideFAQAndCounts':True,'unchangedCommonRev2':True,'method':'Read rev2 full text and all intended common strings, independently compared full parsed rev3 objects and source diff, reread the exact final FAQ against the already visually read original policy image. No old verdict used as a substitute for changed-text review.'}
review['copyScopeGates']={'factualClaims':'PASS','productCardsAndEightPhotos':'PASS','threeApprovedBannersAndAlt':'PASS','providerVoice':'PASS','empathyAndNaturalSmallTalk':'PASS','respectfulNonPatronizingTone':'PASS','warningsVersusHelpBalance':'PASS','searchIntentAndInformationCompleteness':'PASS','localPurchaseValueAndNoNameSwapBody':'PASS','titlesMetaH1CardsFirstAnswers':'PASS','FAQQualityNotQuota':'PASS','intendedButtonsNotices404AccessibilityText':'PASS','runtimeHTMLAndActualFAQVisibility':'NOT_IMPLEMENTED_NOT_VERIFIED','sourceCommitRemoteBuildAndRelease':'OUT_OF_SCOPE_NOT_VERIFIED'}
review['evidence']='recomputed-checks.rev3.json';review['completionBoundary']='The exact local customer-copy review is complete and approved only for article rev3 plus unchanged common rev2 and bound assets. This is not source, build, runtime, browser, deployment, fulfillment or indexing approval. Any customer-copy edit invalidates the affected exact-text verdict and requires renewed review.'
review['followOnRequirements']=['Bind the exact approved article/common files to the eventual source commit and inspect all actual rendered customer strings; do not expose metadata/renderRule.','Verify one H1, proper H2/H3 hierarchy, source heading, title/meta/canonical/robots/sitemap/404 in actual generated HTML.','Verify visible FAQ text despite contentMarkdown, all eight SKU-specific CTA destinations, planned facility anchors and related links.','Retain five planned routes and two purchase articles; list noindex/follow/no sitemap/no banners; do not activate held facilities.','Verify public image HTTP/MIME/SHA and banner placement; maintain honest separate unverified status for actual browser/viewport QA and delivery fulfillment.']
(O/'verdict.rev3.json').write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n')
inspected=[R/'raw/order-policy.jpg',R/'raw/change-policy.jpg']+[R/'raw'/f'{sku}-photo.jpg' for sku in ['B201','B203','B205','B060','C200','C203','C204','C205']]+[R/'reuse/banners'/f for f in ['flower-message.webp','flower-budget.webp','flower-consultation.webp']]+[R/'facilities/raw'/f for f in ['funeral-floor1.jpg','funeral-floor2.png','funeral-floor3.jpg']]
(O/'visual-original-inspection.json').write_text(json.dumps({'classification':'직접 확인','method':'Opened actual image pixels with view_image, not only OCR, metadata or another agent description.','files':[{'path':str(p),'sha256':sha(p)} for p in inspected],'notPerformed':'No website/browser screenshot or runtime UI inspection.'},ensure_ascii=False,indent=2)+'\n')
summary='''[직접 확인]\narticle-copy.rev3.json 전문과 변경 없는 common-visible-copy.rev2.json의 고객노출 예정 문구를 독립 검토했습니다. 정책 이미지 2장, 상품 원본사진 8장, 공통 배너 3장, 서울성모 층별 도면 3장 및 공식 시설/상품 HTML을 대조했습니다. 독립 결속·데이터 재계산 132검사 중 실패 0건입니다.\n\n[추정·판단]\n최종 판정: PASS_EXACT_LOCAL_COPY_TONE_AND_INTENT. 사실/상품, 판매자 화자, 공감·자연스러운 짧은 스몰토크, 고객 존중, 검색 의도·정보 완결성, 지역 고유 구매정보를 각각 검토했습니다. rev2의 가상 오주소 FAQ 1건은 카드취소 처리기간 FAQ로 수정되어 해소되었습니다. 본문은 2546자/2672자이며 분량으로 합격시키지 않았습니다.\n\n[미확인]\n실제 HTML·FAQ 노출·버튼 동작·모바일/접근성 화면·source commit·배포·공개 HTTP·색인·실주문/반입/배송은 이번 로컬 문구 검토 범위 밖입니다. 이 PASS를 공개 완료로 사용하면 안 됩니다.\n\n검증 증거: verdict.rev3.json, recomputed-checks.rev3.json, visual-original-inspection.json.\n'''
(O/'README.txt').write_text(summary)
print(json.dumps({'verdictFile':str(O/'verdict.rev3.json'),'verdictSha256':sha(O/'verdict.rev3.json'),'independentChecks':132,'failures':0,'articleSHA':sha(P/'copy/article-copy.rev3.json'),'commonSHA':sha(P/'copy/common-visible-copy.rev2.json'),'changedPaths':changed},ensure_ascii=False,indent=2))
