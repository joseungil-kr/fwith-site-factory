# 남구12270 고객 원고·구매계획·렌더계획 r2

상태: 작성자 로컬 원고·근거·사양 검사를 마친 독립검토 입력이다. 앱 구현·HTML·화면·배포·공개 완료가 아니다.

## 산출물

- customer-copy.json: 7키 고객용 정본. 한국어 문자열 112개
- drafts/: home, nammoon-funeral, support, 404의 전문
- PURCHASE-PLAN.ko.md 및 purchase-intent-metadata.json: 사진 중심 구매의도, 질문·답변·근거·다음 행동, 경쟁/형제 원고 비교
- render-plan.json: 4경로, 미래 sitemap 2개, noindex support와 실제404, FAQ·카드·배너·title/H1/H2/meta/OG/Twitter/canonical·탐색·footer 계약
- SOURCE-MAP.json/.ko.md: 직접 읽은 원본, 도구 보고, 편집 판단, 미확인 경계
- assets/ 및 asset-manifest.json: 상품사진4개·승인 공통배너3개. 모두 기존 정본과 동일 바이트
- visible-strings.json 및 ALL-VISIBLE-STRINGS.ko.md: 본문·UI·버튼·FAQ·출처·alt·메타 전체 문자열
- original-clause-review-input.json: 지정 main 원문 규정 전체의 행·해시와 정책이미지 영역별 검토 입력
- body-count-and-overlap.json / local-verification.json / verification.log: 작성자 검사와 분모·한계
- review-input-manifest-r2.json / SHA256SUMS: 동결 검토 입력. 변경 시 후속 revision으로 검토

## 검증 범위

[직접 확인] 정확한 가격·시설CSV행·상품사진·정책이미지·배너·지정 main 지침을 대조했다. 고유 주본문은 2,090자, FAQ·마무리 포함은 2,797자다. 제목·공통카드·출처·메뉴·footer·CTA는 제외했다. 작성자 검사 621건의 실패는 0건이며 선행연구 파일 무결성 검사도 포함한다. 이는 품질점수나 독립 어투 PASS가 아니다.

[도구 보고] 원문 HTTP와 연구 검색 관찰은 보존 수집 기록을 읽은 결과다. 새 HTTP 요청이나 검색순위 측정이 아니다.

[추정·판단] 사진과 전체예산에서 시작하는 한 시설 안내를 권고한다. 명칭을 마스킹한 20자 shingle 중복은 서구 약0.90%, 동구 약0.33%, 나주 약0.05%, 광양0%이며, 이 측정만으로 고유성 합격을 선언하지 않는다. 공통 사실·카드·UI는 의도적으로 재사용했다.

[미확인] 도메인 연속성·지번 등가성·현재 운영·반입·수령·실주문·최종비용·개별 환불은 미확인이다. 원고 독립검토와 실제 HTML/browser/public 검증도 남아 있다. origin/domain=null, productionEnabled=false이며 namespace를 예약하지 않았다.

## 구현 인계

- 홈 순서: selection → facility-guide → consultation. 시설카드는 ID로 찾는다.
- 상세 순서: products → budget → facility → ribbon → order. budget 배너는 facility 바로 앞이다.
- FAQ 순서: 결제후배송불가/재고없음 → 변경/취소 → 소재차이/불량. 세 쌍을 항상 표시한다.
- 고객 시설 사실은 정부 명부의 도로명주소·명칭·대표전화만 쓴다. nammoon.kr·지번·운구/절차 시간·삼성서울 잔존 문구·기독병원은 원고에 넣지 않는다.
- 시설전화062-675-5000은 꽃 주문 CTA가 아니다. 모든 전화 주문 링크는 tel:18440644다.
- footer는 sharedUI.brand/phoneLink/homeLink를 기존 layout에서 재사용한다.
- 계획·검증·근거 문서는 고객 본문으로 렌더하지 않는다. 이 작업에서는 원격쓰기·앱개발·Actions·배포·IndexNow·PC/CodexWork·클라우드 작업·content API·새 이미지·설치를 수행하지 않았다.

## r2 수정 이력

독립검토 F1_HOME_PHOTO_LOCATION에 따라 홈을 예산·리본 상담 및 남문 상세의 실제 사진으로 연결되는 입구로 명확히 했다. r1 폴더와 ZIP은 보존했다. 상세·상품·UI·배너·지원/404 원고와 이미지 7개는 r1과 동일하다. revisions/의 정확한 diff와 수정 기록을 함께 검토한다.
