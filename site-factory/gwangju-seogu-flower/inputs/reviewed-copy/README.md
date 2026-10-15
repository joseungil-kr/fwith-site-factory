# 서구 12240 고객 원고·구매계획·렌더계획

상태: 작성자 로컬 문서·원본·사양 검사 완료, 독립 내용·어투 검토 대기. 실제 앱·배포 완료가 아니다.

## 산출물

- customer-copy.json: 고객용 정본. 최상위 키 7개, 한국어 문자열 114개
- drafts/: home, gukbin-funeral, support, 404 검토문서 4개
- PURCHASE-PLAN.ko.md와 purchase-intent-metadata.json: 독립 구매 의도, 경쟁 페이지의 정보 공백, 형제 원고 중복, 다음 행동
- render-plan.json: 4개 경로, 사이트맵 2개, noindex support, 404 예외, FAQ·카드·배너·소셜·탐색 계획
- SOURCE-MAP.json/.ko.md: 원본 사실·도구 관찰·편집 판단·기술 계획·미확인 항목 분리
- assets/와 asset-manifest.json: 기존 상품사진 4개·승인 공통배너 3개, 모두 동일 바이트
- ALL-VISIBLE-STRINGS.ko.md와 visible-strings.json: 메타·접근성·UI·본문을 포함한 전문
- body-count-and-overlap.json, local-verification.json, verification.log: 검사 범위를 명시한 작성자 검증
- evidence/: 지정 main 지침 11개와 Git blob 대조, 선행 연구 218개 SHA 대조. 원본 연구 전체를 복제한 것이 아님

## 검증 범위

[직접 확인] 고객 문구의 공식 사실·상품 원문·사진·정책·배너와 지정 main 지침을 대조했다. 본문 2,218자, FAQ·마무리 포함 2,940자다. 공통 카드·출처·메뉴 등은 제외했다. 검사 387개에는 선행 연구 218개 파일의 무결성 검사가 포함되며, 품질점수나 배포 PASS가 아니다.

[도구 보고] 검색 관찰·HTTP 상태·기록상 62/230 및 168개 미완료는 보존된 연구·저장소의 보고다. 62개 사이트를 동시에 새로 검증하지 않았다.

[추정·판단] 예산 우선 흐름과 리본 문구 예시, 한 시설의 동의어를 묶는 구성이 구매 결정에 도움이 된다는 편집안이다. 문체와 정보 완결성은 별도 검토가 필요하다.

[미확인] 실주문·재고·전화·반입·수령·최종비용·도착·개별 환불과 앱·HTML·화면·공개응답·색인은 검증하지 않았다. 도메인과 origin은 null이며 productionEnabled=false다.

## 후속 담당자 주의

- 홈의 시설 카드는 id=facility-guide로 찾는다. 이 원고에서는 sections[1]이며 index 0은 budget이다.
- 상세 순서는 budget → products → ribbon → facility → order다. 동구 문장이나 다른 지역 배송조건을 치환하지 않는다.
- JSON의 고객 문구만 렌더한다. 이 README나 계획·검증 문서를 고객 본문에 넣지 않는다.
- 원격쓰기·앱개발·issue·Actions·배포·IndexNow·PC/CodexWork·새이미지·설치는 수행하지 않았다.
- 독립 검수에 넘긴 동결 revision을 임의 수정하지 않는다. 수정이 필요하면 새 해시로 재검수한다.
