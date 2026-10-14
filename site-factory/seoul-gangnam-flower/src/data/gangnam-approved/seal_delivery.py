from pathlib import Path
import json,hashlib,datetime,zipfile
O=Path(__file__).parent
read=lambda p:json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
a=read(O/'copy/article-copy.final.json');c=read(O/'copy/common-visible-copy.final.json');ed=read(O/'independent-copy-review/editorial-verdict.json');fa=read(O/'independent-copy-review/facts-verdict.json')
# Do not guess verdict schema: acceptance requires an explicitly allowed final state and actual exact input hash binding.
print('Editorial verdict',ed.get('verdict'));print('Facts verdict',fa.get('verdict'))
assert 'PASS' in str(ed.get('verdict','')) or str(ed.get('verdict','')).startswith('ACCEPT'), 'Editorial final review not accepted'
assert 'PASS' in str(fa.get('verdict','')) or str(fa.get('verdict','')).startswith('ACCEPT'), 'Facts final review not accepted'
for verdict in [ed,fa]:
 t=json.dumps(verdict)
 assert sha(O/'copy/article-copy.final.json') in t, 'Verdict does not bind final article hash'
 assert sha(O/'copy/common-visible-copy.final.json') in t, 'Verdict does not bind final common hash'
assert read(O/'validation/copy-validation.json')['status']=='PASS'
assert read(O/'handoff/projection-validation.json')['status']=='PASS'
assert a['createdAt']>read(O/'plan/fixed-plan.json')['frozenAt']
files=['plan/fixed-plan.json','plan/candidate-plan.json','plan/candidate-ledger.json','plan/candidate-inventory.json','plan/candidate-hold-rationale.json','plan/purchase-candidate-history.json','plan/membership.json','plan/catalog-policy-evidence.json','plan/evidence-registry.json','plan/fact-clarifications.json','copy/article-copy.final.json','copy/article-copy.final.txt','copy/common-visible-copy.final.json','copy/common-visible-copy.final.txt','copy/claim-evidence-map.json','copy/faq-evidence-map.json','copy/intent-completion-matrix.json','validation/counts.json','validation/duplicate-comparison.json','validation/copy-validation.json','validation/data-guard-selftests.json','independent-plan-review/final-verdict.json','independent-plan-review/frozen-projection-verdict.json','independent-copy-review/editorial-verdict.json','independent-copy-review/facts-verdict.json','handoff/approved-assets.json','handoff/directory-input.json','handoff/input-bindings.json','handoff/runtime-input.json','handoff/visible-copy-inventory.json','handoff/projection-validation.json','handoff/root-readback.json','handoff/IMPLEMENTATION-HANDOFF.txt']
for optional in ['independent-copy-review/handoff-projection-verdict.rev3.json','independent-copy-review/common-text-projection-verdict.json']:
 if (O/optional).exists():files.append(optional)
acceptance={'schemaVersion':1,'acceptedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'LOCAL_PLAN_AND_CUSTOMER_COPY_REVIEWED_ONLY','classification':{'directlyChecked':'Local originals, final exact text, assets, schemas, counts, links as data, hashes and projection readbacks','toolReported':'Independent review conclusions and prior source HTTP/Git observations; review artifacts bound by hashes','judgment':'N3 purchase-intent plan and editorial originality/provider tone','unverified':'No site implementation/sourceCommit/build/render/browser/publicHTTP/IndexNow, actual venue receipt/stock/total/delivery.'},'originalPlanN':3,'routeDenominator':6,'urls':[x['url'] for x in a['articles']],'finalArticleRevision':a['revision'],'finalCommonRevision':c['revision'],'files':[{'path':p,'bytes':(O/p).stat().st_size,'sha256':sha(O/p)} for p in files],'criticalPoliciesPreserved':['Samsung room-only and maximum 10 placement/capacity, not artificial-material rule','Same Yonsei Gangnam / Gangnam Severance facility, road address 211, no conflicting lot number','Coex meeting-room guide disposal cost with posted-date/edition distinction','SETEC user/organizer duties, no blanket courier paperwork','Mixed material/no seller collection/one-day and production/delivery change limits source-attributed','12 candidate groups, 8 initial purchase candidates, 14 legal units / 22 administrative units / 31 relationships; all facility administrative assignments null, Samsung/SETEC legal units null'],'remoteActionsPerformed':[],'sourceCommit':None,'publicUrl':None,'ownershipStatus':'Not asserted or changed','separateProgress':'Gwanak unfinished first; Seocho local static unpublished; no national completion numerator changed.'}
write(O/'handoff/acceptance.json',acceptance)
readme=f'''강남구 로컬 계획·고객 원고 인계

[직접 확인]
- 최초 originalPlanN=3과 구매 URL 3개를 독립 계획검토 후 원고 작성 전에 동결했습니다. 예상 HTML 경로는 홈·목록·404 포함 6개이며 아직 생성하지 않았습니다.
- 최종 고유본문은 근조 {a['articles'][0]['uniqueBodyCharsIncludingFirstAnswer']:,}자, 결혼 {a['articles'][1]['uniqueBodyCharsIncludingFirstAnswer']:,}자, 전시·기업행사 {a['articles'][2]['uniqueBodyCharsIncludingFirstAnswer']:,}자입니다. 첫 답변과 문단 구분 개행 포함, 공통 UI·상품카드·FAQ·제목 제외입니다. 문자수는 합격 최소선이 아닙니다.
- 홈·카드·FAQ·UI·버튼·고지·404 전체 문구를 별도 JSON으로 작성했고, 실제 상품사진 8개와 승인된 동일 배너 3개의 바이트·SHA·크기를 검사했습니다.
- 연구 입력 manifest c6dd49cd8ef6f70e4cab38f49aaf4df4d839545528d5ffc10bff6b51c671863a 및 331파일 재해시 불일치 0건. 법정동 14개·행정동 22개·관계 31행과 12후보군·보류를 유지했습니다.
- 원본 정책 이미지와 공식 시설 자료를 읽었습니다. 초기 검수에서 환불 시간 제한 누락, 검토자 말투, 반복 FAQ, 코엑스 자료 목록 게시일/판본 날짜 구분을 보완했습니다. diff와 초기 실패 판정도 보존했습니다.

[도구 보고]
- 독립 계획·최종 원고 사실·문체/구매의도 검토의 판정은 acceptance.json에 정확한 입력 hash와 함께 결속했습니다. 그 판정은 실제 배포나 배송 성공을 뜻하지 않습니다.
- 이전 연구의 HTTP·검색·원격 Git 관측은 저장된 스냅샷입니다. 이 작성 단계에서 원격 서비스 요청을 새로 하지 않았습니다.

[추정·판단]
- 근조는 삼성의 빈소 진열 제한과 연세 강남/강남세브란스 식별을 통합합니다. 결혼은 예식 홀·회차와 축하 인사를, 행사는 수령·반출·폐기 책임을 별도로 답합니다. 3개는 할당량이나 시설 수가 아닙니다.
- 서초와의 문단/30자 ngram 비교와 독립 전문 대조에서 지역명 치환 복제로 판단되는 본문은 없었습니다. 상품·가격·판매자 정책과 승인 배너는 의도적으로 공유하는 사실·자산입니다.

[미확인 및 실패]
- 사이트 소스·Git SHA·빌드·실제 HTML·화면·공개 URL/HTTP·IndexNow는 없습니다. 수행하지 않은 단계는 검토 PASS로 대체하지 않습니다.
- 실제 시설 수령·재고·개별 총액·전달 시각·설치·완료사진은 검증하지 않았습니다. 꽃이랑의 별도 수거는 제공하지 않는다고 원문에 명시되어 있습니다.
- 관악 미완료 우선순위, 서초 로컬 정적 미공개 상태, 서비스 승인대기, source/hostname 소유권과 전국 진행 분자를 변경하지 않았습니다.

인계 파일
- plan/fixed-plan.json: 동결 계획·URL·분모·보류
- copy/article-copy.final.json 및 .txt: 최종 고객 원고
- copy/common-visible-copy.final.json: 모든 공통 노출 문구
- copy/claim-evidence-map.json, faq-evidence-map.json, intent-completion-matrix.json: 답변과 근거
- validation/: 길이·중복·정확한 데이터 검사
- independent-plan-review/, independent-copy-review/: 별도 검토와 수정 이력
- handoff/IMPLEMENTATION-HANDOFF.txt: 후속 구현 기준
- handoff/acceptance.json: 검토한 정확한 파일 결속
- handoff/runtime-input.json: 로컬 데이터 투영이며 실행된 사이트가 아님
- handoff/approved-assets.json 및 assets/: 실제 상품 8개·정본 배너 3개
- delivery-manifest.json: 최종 인계 파일 목록과 SHA

SHA-256은 파일 지문이며 Git commit이나 전자서명이 아닙니다. 연구 원본은 ../gangnam-research-20261013의 고정 입력을 참조합니다. 고객 사이트에는 경쟁 원문·검수 파일·내부 메타데이터를 배포하지 않습니다.
'''
(O/'README.txt').write_text(readme)
exclude={'delivery-manifest.json','handoff/package-manifest.json','handoff/package-verification.json'}
allfiles=[p for p in O.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.zip' and str(p.relative_to(O)) not in exclude]
entries=[{'path':str(p.relative_to(O)),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(allfiles)]
write(O/'handoff/package-manifest.json',{'createdAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'All local package files except self, verification wrapper, final delivery manifest, ZIP and __pycache__. Not a Git SHA.','fileCount':len(entries),'files':entries})
errors=[e['path'] for e in entries if sha(O/e['path'])!=e['sha256'] or (O/e['path']).stat().st_size!=e['bytes']]
assert not errors
write(O/'handoff/package-verification.json',{'classification':'직접 확인','manifestSha256':sha(O/'handoff/package-manifest.json'),'filesReadAndRehashed':len(entries),'mismatches':errors,'acceptanceHash':sha(O/'handoff/acceptance.json'),'scope':'Local final file byte/hash readback; no rendered or public verification.'})
allfiles=[p for p in O.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.zip' and p.name!='delivery-manifest.json']
entries=[{'path':str(p.relative_to(O)),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(allfiles)]
write(O/'delivery-manifest.json',{'createdAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Final delivery wrapper includes all persisted local files except self, ZIP and __pycache__. Review hashes bind specific final content, not remote execution.','fileCount':len(entries),'files':entries})
# Read back every sealed file before compression.
assert all(sha(O/e['path'])==e['sha256'] and (O/e['path']).stat().st_size==e['bytes'] for e in entries)
z=O/'gangnam-local-plan-copy-handoff-20261013.zip'
with zipfile.ZipFile(z,'w',zipfile.ZIP_DEFLATED) as out:
 for p in sorted(allfiles+[O/'delivery-manifest.json']):out.write(p,p.relative_to(O))
with zipfile.ZipFile(z) as zipf:
 assert zipf.testzip() is None
 for e in entries:assert hashlib.sha256(zipf.read(e['path'])).hexdigest()==e['sha256']
print(json.dumps({'files':len(entries),'deliveryManifestSha256':sha(O/'delivery-manifest.json'),'acceptanceSha256':sha(O/'handoff/acceptance.json'),'zip':str(z),'zipSha256':sha(z),'zipBytes':z.stat().st_size,'zipEntries':len(entries)+1},ensure_ascii=False,indent=2))
