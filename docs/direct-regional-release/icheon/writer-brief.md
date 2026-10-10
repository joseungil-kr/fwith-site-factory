# 이천 직접 지역 사이트 작성 기준

고정 계획은 법정동 15개, 읍 2개, 면 8개 총 25개다. 행정동은 별도 글 분모에 더하지 않는다. 23개 이상 독립 내용 검수에 합격해야 공개 가능하다. 글 수 때문에 근거 없는 글을 만들거나 분모를 줄이지 않는다.

`../research/membership-runtime.json`과 `../research/venue-sources.json`을 읽는다. `../review/catalog-review.json`의 현재 상품명·가격·사진을 사용한다. 기존 다른 시의 고객 본문은 복사하지 않는다. `../../hourly-direct-0300/content/pages-a.json`은 JSON 필드와 renderer 계약 확인용일 뿐 문장 템플릿이 아니다.

각 글은 실제 구매할 화환을 고르는 사람을 위한 지역·시설·구매 목적의 검색어에서 시작한다. 실제 검색 결과와 공식 원문을 확인하고 query-plan 및 evidence에 남긴다. 동일 시설·의도의 동의어로 별도 글을 늘리지 않는다. 지명이 들어간 막연한 주문 체크리스트 대신 그 장소에 보내는 구매자가 실제 판단할 내용을 제공한다. 시설의 존재·주소·법정동을 공식 자료로 연결하고, 반입·영업·수령 제한은 확인한 범위만 쓴다. 과거 기사·검색 요약만으로 현재 운영이나 주소를 단정하지 않는다. 검색량·후기·납품 실적·배송 보장·판매하지 않는 상품을 발명하지 않는다.

필드: slug, title, h1, primaryKeyword, description, cardSummary, firstAnswer, contentMarkdown, sources, source, regionalPurchaseMode, regionalProductKeys, regionalProductFamilies, visualIntent, sections, faq, relatedKeys, relatedSlugs, assetSlot. 실제 필드 규칙은 재사용 renderer/schema를 읽어 맞춘다. 본문 중복 H1 금지. firstAnswer는 한국어 120~180자 직접 답변이며 본문 첫 단락과 일치한다. cardSummary는 description과 별도로 작성한다. 상품 네 종류를 설명하면 상품키도 그 네 종류다. relatedSlugs는 이번 최종 합격 문서가 확정되기 전 빈 배열로 둔다. sources는 name/url/type/verifiedAt가 필요하며 runtime은 HTTPS 출처 계약이다. HTTP만 가능한 사이트는 HTTPS 공식 대체 근거를 찾고, 없으면 이를 숨기지 말고 검토 요청한다.

근조: funeral-basic B201 59,000 / funeral-premium B203 79,000 / funeral-large B205 109,000 / funeral-xl B060 149,000.
축하: congrats-basic C200 59,000 / congrats-premium C203 79,000 / congrats-large C204 99,000 / congrats-xl C205 149,000.
공식몰 현재 검증 상품명을 그대로 사용하고 기본가격·최종 조건을 구분한다. CTA https://fwith.co.kr/ 및 tel:18440644, 꽃이랑 1844-0644, 상담 08:00~23:00. 미등록 꽃다발·난 상품카드를 만들지 않는다. 자사 상품 사진은 디자인 비교이며 특정 현장 납품 증거가 아니다.

중요 출처 메모:
- 이천병원 관고동 장례식장: 공식 안내 '조화 10개 이상 진열 제한'. '10개까지 허용'으로 바꾸지 않는다. 수령과 진열 여유를 확인한다.
- 이천아트홀: 꽃다발 객석 반입 금지 안내가 화환 판매 가능 증거는 아니다. 시설 담당자 수령 조건 확인과 상품군을 혼동하지 않는다.
- 모가면 테르메덴: 2026-10-12~22 휴장 공지. 365일 운영 또는 즉시 전달을 약속하지 않는다.

각자 할당 파일만 작성하고 원격 저장·배포·다른 작성자 파일 수정은 하지 않는다. 본문 수정은 작성자만 하고 검토자는 파일 해시로 독립 재검토한다. 글별 근거가 부족하면 holds JSON에 정확 이유를 남긴다.
