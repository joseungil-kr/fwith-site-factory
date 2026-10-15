# 동구 고객 원고·구매계획·렌더계획

지역: 전남광주통합특별시 동구 / 12210 / order31. 고객 검색명은 광주 동구이며 경기도 광주시 또는 다른 광역시 동구와 구분한다.

상태: 원고·명세 로컬 산출물 생성 및 작성자 검사 수행. 독립 원고/문체/구매완결성 검수 대기. 실제 HTML·앱·화면·공개 검증 미수행. 운영 미확인 시설의 활성 배송을 확정하는 자료가 아니다.

## 산출물

- customer-copy.json: 홈·상세·지원·404·공통 메뉴·카드·배너 alt의 단일 문구 정본
- drafts/: 위 JSON에서 재현한 검토용 Markdown 4종. 앱 소스가 아니다.
- visible-strings.json / ALL-VISIBLE-STRINGS.ko.md: 한국어 노출/접근성/메타 문자열 전문 114개. 숫자 맞추기를 위해 문구를 늘리지 않았다.
- PURCHASE-PLAN.ko.md: 구매 질문→답→근거→다음 행동, 경쟁/형제 의미중복 검토, 미확인 범위
- SOURCE-MAP.json / SOURCE-MAP.ko.md: 원문과 각 사실의 사용 범위, 연구 독립감사 결속
- render-plan.json: 실제 HTML에서 검증해야 할 경로/메타/제목/배너/FAQ/카드/내부링크 계획
- purchase-intent-metadata.json: 페이지별 검색어·역할·의도·CTA, 점수는 독립 검수 전 null
- asset-manifest.json / assets/: 승인 배너3개와 실제 상품사진4개. bytes 변경·새이미지 없음
- body-count-and-overlap.json: 본문 2,322자, FAQ·마무리 포함 3,015자. 목차·카드·출처·CTA 제외. 형제5문서와의 비교 결과
- local-verification.json: 작성자 검사199개와 미검증 항목. 기계 결과는 독립 편집 검수/HTML 검수를 대신하지 않음
- verify_manuscript.py: 원문/문구/자산/명세 검사와 Markdown·문자열·metrics 재생성. 설치 없이 기존 Python/lxml/PIL 사용
- prepare_specs.py: 기계 schema에서 동구 명세·메타데이터를 준비. 고객문장을 생성 API로 만들거나 앱 코드를 만드는 스크립트가 아님
- review-input-manifest-r2.json / SHA256SUMS: 독립검수 입력 freeze

## 직접 확인과 중요한 한계

공식 명부·대학지도는 시설 식별에 사용했다. 2026 회의자료와 학생안내 보존 페이지를 실제 보았으나 현재 운영·반입을 확정하지 않는다. 병원 웹502는 오류이며 폐쇄 증거가 아니다. 공식 중단문구가 있는 전남대병원은 별개로 제외했다.

공식 4SKU 기본가는59/79/109/149천원이다. 동구 추가배송비 행이 없다는 관찰만 확보했으므로 무료/0원/타지역10,000원으로 해석하지 않았다. 제작 완료/상품 출고 후 취소 조항의 개별 적용은 미확정이며 상담 조건을 남겼다.

공통 배너 alt만 승인된 공통 문구를 유지했고 지역별 판매 본문·FAQ·카드 설명은 별도로 작성했다. 기존 machine schema와 승인7이미지만 재사용했다. 원격쓰기·커밋·푸시·이슈·실행·배포·IndexNow·새설치·새이미지·PC/Codex Work·API 콘텐츠 생성·외부 연락은 하지 않았다.
