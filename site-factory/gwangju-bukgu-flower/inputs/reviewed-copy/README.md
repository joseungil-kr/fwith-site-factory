# 북구12300 고객 원고·구매계획·렌더계획 r1

상태: 작성자 로컬 사실·문서·사양 검사를 마친 독립검토 입력. 앱 구현·HTML·화면·배포 완료가 아니다.

## 산출물

- customer-copy.json: 기존 렌더러와 호환되는7키 고객 정본, 한국어 문자열115개
- drafts/: home, green-funeral, support,404 전문. 리뷰용 Markdown이며 실제 HTML이 아니다.
- PURCHASE-PLAN.ko.md, purchase-intent-metadata.json: 의도·질문→답변→근거→CTA, 지역 고유 맥락, 경쟁/재사용 판단
- render-plan.json:4경로,2개 미래 색인URL, noindex지원목록과 실제404, 항상 보이는FAQ3개, H1/meta/canonical/social/배너/카드/탐색/footer 계획
- SOURCE-MAP.json/.ko.md: 직접 확인·도구 보고·편집 판단·미확인 구분, 패키지 안 상대경로 원문 바인딩
- asset-manifest.json 및 assets/: 상품사진4개·승인배너3개, 모두 원본과 같은 바이트
- original-clause-review-input.json: 현재 main지침의 원문 전체 행·해시, 정책이미지 조항 및 시설 절차 원문 검토 입력
- visible-strings.json, ALL-VISIBLE-STRINGS.ko.md: 본문뿐 아니라 버튼·카드·alt·메타·출처·공통문구까지 검토
- body-count-and-overlap.json, local-verification.json, verification.log: 분모와 한계를 남긴 작성자 검사
- review-input-manifest-r1.json, SHA256SUMS: exact frozen input. 변경하면 새 revision으로 재검토한다.

## 확인한 범위

[직접 확인] 지정 연구 DELIVERABLES SHA70d46c857…를 기준으로 남아 있는 근거 파일을 재검산했다. 상품가격·사진·정책이미지·정부229행·운영자 최소발췌와 현재 main네 제작지침을 직접 읽었다. 주본문2,163자, FAQ·마무리 포함2,854자다. 제목·공통카드·출처·메뉴·footer·CTA는 제외했다. 작성자 검사1,357건의 실패는0건이다. 대부분 바이트·구조·필드 검사이며 문체 점수 또는 독립 품질 PASS가 아니다.

[도구 보고] 연구의 HTTP·검색 결과와 과거 독립 연구 판정은 기존 기록이다. 모든 원본 사이트를 이번 작성자가 새 요청한 것은 아니다. main63/230은 기록이며63곳 신규 공개 재검증이 아니다.

[추정·판단] 상품사진→리본→전체예산→그린의 빈소절차와 일정→주문→FAQ순서로 구매 결정을 돕는다. 명칭마스킹20자 shingle 중복은 실제 형제5원고 대비 약0.14~1.39%이며 독창성의 합격선으로 쓰지 않았다.

[미확인] 북구 최종배송비·총액, 현재 운영·재고·전화응답·빈소·화환 반입수령, 실제 배송 및 개별환불은 미확인이다. 원고 독립검토와 실제 앱/HTML/browser/publicHTTP도 남아 있다. namespace는 후보이며 origin/domain=null, productionEnabled=false다.

## 구현 인계

- 홈: selection → facility-guide → consultation. 홈에는4상품사진이 없다. 네 사진은 연결된 그린 상세에 있다.
- 상세: products → ribbon → budget → facility → order. 기존 남구의 배열순서를 그대로 가정하지 말고 ID와 정본 순서를 사용한다. budget배너는 facility 바로 앞이다.
- FAQ: 변경/취소 → 소재차이/불량 → 결제후 배송불가/재고없음. 세 문답을 항상 보여 준다.
- 그린은 시설주소·전화와 일반 안치후호실확인 절차만 사용한다.24시간시설이용은 꽃수령이 아니다. 구호전·일곡의 미해결 주소/전화, 주차수·실시간 빈소·납품경험은 원고에 없다.
- 모든 주문전화 CTA는 tel:18440644. 시설062-250-4455는 꽃 주문 CTA가 아니다.
- footer는 기존 sharedUI.brand/phoneLink/homeLink를 사용한다. 새 마케팅 문구·전국 링크를 추가하지 않는다.
- 이미지7개만 고객자산이다. evidence/의 정책이미지와 선택본문은 리뷰용이며 웹 public에 복사하지 않는다.
- 연구폴더 전체·경쟁사 원문·개인 부고는 공개하지 않는다. 추후 소스 저장은 필요한 최소 공개용 사실·출처·해시와 승인자산만 선별한다.

마감 main21cbba3…는 남구 제어·검토51파일만 추가했고, 읽은 main1d421424…의 네 지침은 바뀌지 않았다. 비교 결과는 evidence/closing-main-reconciliation.json에 있다. 원격쓰기·앱개발·Actions·배포·IndexNow·PC/CodexWork·클라우드 작업·contentAPI·새 이미지·설치는 수행하지 않았다.
