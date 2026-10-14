# 독립 A04 제목 검색어 정렬 평가

## 확인된 결과

로컬 최종 문구 JSON의 HOME과 구매 글 3개를 먼저 고정한 rubric으로 평가했다. HOME·근조·결혼 글은 각각 100점으로 내부 정렬 기준을 충족했다. 행사 글은 원점수 95점이지만 필수 첫 답변 지역 기준 G4 위반으로 유효점수 89점, A04_ALIGNMENT_REVISE다. 디렉터리와 404는 역할 근거에 따라 NOT_APPLICABLE이며 점수는 null이다. 평균으로 개별 미달을 가리지 않았다.

이는 기존 문구의 직접 비교 결과다. 배포·실제 화면·주문 기능·검색 실적·전체 Production Gate 통과를 뜻하지 않는다. 기존 계획과 문구를 수정하지 않았다.

## 평가가 먼저 고정되었는지

- Rubric: A04-local-independent-v1, SHA-256 bbc7d957dc1336a555ecc5a3775b326ec0d0b1bc8d70336ac9d040314941c5fa
- Rubric freeze: 2026-10-13 10:16:02 UTC, 실제 대상 문구를 읽기 전
- Target map: SHA-256 4611ebfbf5515a22dc264e3b2b9a86a23f75caec615d0e1bcf6e5fba324b5f8e, 대상 문구를 읽기 전 metadata만 추출하여 고정
- Title 40, H1 25, 첫 답변 25, 의도 일관성 10; 필수 위반은 89점 ceiling. 이 배점과 ceiling은 공개한 검토 운영방식이며 원문이 정한 공식 배점이나 검색엔진 공식이 아니다.

## 페이지별 실제 근거

### home

- URL: /
- Primary keyword: 강남구 화환
- Title: 강남구 화환 | 근조·결혼·행사 상품과 상담 | 꽃이랑
- H1: 강남구 화환, 조의와 축하에 맞춰 준비하는 꽃
- 첫 답변 전체 107자: 강남구에 보낼 근조·축하화환을 기본가격 59,000원부터 소개합니다. 빈소에 전하는 위로, 결혼하는 두 분의 축하, 전시와 기업행사의 응원에 맞춰 꽃이랑의 여덟 상품과 리본 문구를 상담합니다.
- 직접 답변 첫 문장 완료 위치: 정규화 문자 38번째까지
- Title 조합 span: [0, 6]; 전반부 계산: {'length': 30, 'midpoint_exclusive': 15, 'first_separator': 7, 'span': [0, 6], 'front_test': True}
- 행별 점수: T1=10/10, T2=10/10, T3=10/10, T4=10/10, H1=15/15, H2=10/10, A1=15/15, A2=10/10, I1=10/10
- 원점수 100, 유효점수 100; A04_ALIGNMENT_MEETS_INTERNAL_THRESHOLD

### funeral

- URL: /regions/gangnam-funeral-wreath/
- Primary keyword: 강남구 근조화환
- Title: 강남구 근조화환 | 삼성서울·강남세브란스 상품 안내 | 꽃이랑
- H1: 강남구 근조화환, 빈소에 전하는 조용한 위로
- 첫 답변 전체 154자: 강남구 장례식장에 보낼 근조화환은 기본가격 59,000원부터 149,000원까지 네 가지로 안내합니다. 꽃이랑에서 예산과 조의를 전할 문구를 상담해 드립니다. 삼성서울병원은 빈소 안 진열과 10개 이내 제한이 있어, 받는 빈소의 수령 여건에 따라 주문 가능 여부가 달라집니다.
- 직접 답변 첫 문장 완료 위치: 정규화 문자 57번째까지
- Title 조합 span: [0, 8]; 전반부 계산: {'length': 34, 'midpoint_exclusive': 17, 'first_separator': 9, 'span': [0, 8], 'front_test': True}
- 행별 점수: T1=10/10, T2=10/10, T3=10/10, T4=10/10, H1=15/15, H2=10/10, A1=15/15, A2=10/10, I1=10/10
- 원점수 100, 유효점수 100; A04_ALIGNMENT_MEETS_INTERNAL_THRESHOLD

### wedding

- URL: /regions/gangnam-wedding-wreath/
- Primary keyword: 강남구 결혼식 축하화환
- Title: 강남구 결혼식 축하화환 | 그랜드힐 홀·상품 안내 | 꽃이랑
- H1: 강남구 결혼식 축하화환, 두 분의 시작을 축하하며
- 첫 답변 전체 136자: 결혼하는 두 분께 전할 강남구 축하화환을 기본가격 59,000원·79,000원·99,000원·149,000원의 네 상품으로 소개합니다. 꽃이랑에서 준비하신 예산과 축하 인사에 맞춰 상품을 상담하며, 그랜드힐 컨벤션의 홀 안내도 함께 담았습니다.
- 직접 답변 첫 문장 완료 위치: 정규화 문자 75번째까지
- Title 조합 span: [0, 12]; 전반부 계산: {'length': 33, 'midpoint_exclusive': 17, 'first_separator': 13, 'span': [0, 12], 'front_test': True}
- 행별 점수: T1=10/10, T2=10/10, T3=10/10, T4=10/10, H1=15/15, H2=10/10, A1=15/15, A2=10/10, I1=10/10
- 원점수 100, 유효점수 100; A04_ALIGNMENT_MEETS_INTERNAL_THRESHOLD

### event

- URL: /regions/gangnam-event-wreath/
- Primary keyword: 강남구 행사 화환
- Title: 강남구 행사 화환 | 코엑스·SETEC 상품·반출 안내 | 꽃이랑
- H1: 강남구 행사 화환, 전시의 시작과 기업의 도약을 응원하며
- 첫 답변 전체 153자: 전시 참가와 기업행사를 축하하는 화환은 기본가격 59,000원부터 149,000원의 네 상품으로 안내합니다. 꽃이랑에서 행사에 전할 인사와 예산을 상담합니다. 코엑스·SETEC은 행사별로 화환 반입이 제한될 수 있어, 수령과 진열이 가능한 행사를 대상으로 주문을 상담합니다.
- 직접 답변 첫 문장 완료 위치: 정규화 문자 60번째까지
- Title 조합 span: [0, 9]; 전반부 계산: {'length': 36, 'midpoint_exclusive': 18, 'first_separator': 10, 'span': [0, 9], 'front_test': True}
- 행별 점수: T1=10/10, T2=10/10, T3=10/10, T4=10/10, H1=15/15, H2=10/10, A1=15/15, A2=5/10, I1=10/10
- 원점수 95, 유효점수 89; A04_ALIGNMENT_REVISE

[직접 확인] 153자 첫 답변 전체에 강남구가 없다. 코엑스·SETEC은 등장하나 H1의 강남구를 명시적으로 되받는 표현은 없다. 첫 답변의 서비스·행사 목적은 맞으므로 A2는 5/10이다.

[추정·판단] 이후 본문 주소로 두 시설이 강남구에 있음을 연결하는 것은 가능하지만, 사전에 고정한 첫 답변 지역 표현/명시적 참조 기준을 대신하지 않는다. 따라서 원점수 95를 그대로 기준 충족으로 보고하지 않고 G4 ceiling을 적용했다. 이 판단은 새로운 지리 사실이나 키워드 반복 횟수 규칙을 만든 것이 아니다.

후속 조치가 허용되면 첫 답변이 어느 지역의 화환 안내인지 명시하도록 작성자 경로에서 검토한 뒤 새 문구 버전을 다시 평가할 수 있다. 이번 보완 평가에서는 새 문구를 작성하거나 원문을 변경하지 않았다.

## 역할별 비적용

- directory /regions/: The authored intro, heading and links define navigation to the three purchase documents and facility/region relationships; no independent primary query is assigned. Eventual indexability eligibility in the plan does not itself make this a primary query document. This is a local documented-role classification, not a claim of production robots/HTTP state.
  실제 문구: 어느 자리로 전할 꽃인지에 따라 근조, 결혼, 전시·기업행사 안내를 보실 수 있습니다. 각 글에는 상품 선택과 함께 빈소·홀·행사의 조건을 설명합니다.
- notFound /404.html: The local notFound fields state an error/recovery role and link home, not a primary query landing page. Actual 404 HTTP/noindex behavior is outside local-copy verification.
  실제 문구: 페이지를 찾을 수 없습니다 | 꽃이랑

## 의도 중복과 metadata 판단

[추정·판단] 6개 페이지쌍을 비교했다. HOME의 상황 선택과 각 구매 글의 목적지·주문 결정은 구분된다. 결혼과 행사 글은 축하상품과 전화번호가 같지만 예식 회차/신랑·신부 정보와 행사/부스/반입·반출 정보가 다르다. 근조는 상품군과 수령·추모 목적이 다르다. 이 네 문서 안에서는 중복 primary intent를 발견하지 않았다. 다른 기존 URL이나 실제 검색 카니발리제이션은 조사하지 않았다.

[직접 확인] 보완 metadata의 원문 file/hash/pointer, 11개 저장 검색기록의 질의·시각·남겨진 결과 수를 대조했다. 20개 참조 파일의 hash가 일치했다. query_priority=1은 네 페이지가 같은 상업 우선 tier라는 새 편집 판단이며 예전 수치나 검색량 순위가 아니다. HOME cluster/class도 새 명시화다. 점수는 이번 보완 산출물에만 있다.

[도구 보고] 저장된 검색 결과는 조사 도구가 실행한 질의와 반환 결과다. 실제 고객의 검색 빈도, 수요, 순위 또는 노출을 측정한 자료가 아니다. Q02 원본은 query_id/response_received_at 대신 observed_at 구조여서 query-log pointer, 동일 질의, 파일명, hash와 observed_at으로 대조했다.

## 미확인과 한계

- HTML/rendered first-prose binding and visuals
- actual CTA destination functionality
- public HTTP/robots/canonical/sitemap/indexing
- external factual claims and live prices/current venue acceptance not independently rechecked in this narrow local assessment
- search demand, volume, rank, traffic or conversion
- original drafting chronology cannot be proven by an after-the-fact metadata addendum

## 검증 증거

- a04-independent-assessment.v1.json: 필드 원문, 120/180자 창, 문자 span, 9개 기준별 점수·이유, 의도 비교, query readback
- assessment-readback-log.json: 원문으로 돌아가 399개 인용 span, 4개 산술 계산, 11개 query 기록, 20개 source hash 재검증
- targets.frozen.json 및 TARGETS_SHA256.txt: 문구를 보기 전에 고정한 target
- ../rubric/: 규칙 원문 hash, 고정 rubric, 정규화/산술 구현, 합성 테스트 9개

검증 스크립트 첫 실행은 Q02에 query_id가 없다는 KeyError로 중단되었다. 실제 원본 구조를 확인하고 Q02의 observed_at/filename/hash 연결을 명시한 뒤 재실행했다. 다른 기록을 추정으로 채우지 않았다.
