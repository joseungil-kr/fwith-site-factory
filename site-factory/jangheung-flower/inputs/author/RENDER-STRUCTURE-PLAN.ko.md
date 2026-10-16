# 장흥군 원고 구현 인계

이 문서는 구현 계획이며 실제 빌드·화면·공개 완료가 아니다.

1. 홈 / 하나의 실질 고객 페이지로 구현한다. H1은 display.page.h1 하나다. intro 뒤 heroActions를 제공한다. 시설 상세5개와 빈 지역목록을 생성하거나 링크하지 않는다. 양주시 장흥면은 이 페이지 대상이 아니다.
2. sections는 products-cost → delivery-cost → locations → order-timing → ribbon-order → questions 순서다. #products-cost에 네 상품카드와 productEligibilityNotice/productNotice/amountNotice를 표시한다. 시설명에 상품구매 버튼을 결합하지 않으며 현재 영업·반입 허용을 암시하지 않는다.
3. 상품 기본가격은 59,000/79,000/109,000/149,000원이다. 배송비는 장흥군10,000원·관산읍대덕읍20,000원이라는 공식 두 행을 그대로 표시한다. referenceSumKRW와 sumLabel은 null이며 요소를 생략한다. 실제 주문 최종액, 무료, 일괄10,000원, 두 행을 합친30,000원, 인접지역 금액을 생성하지 않는다.
4. 상품 CTA는 해당 SKU의 공식 상세 URL이다. 전화 버튼은 tel:18440644. 링크 점검은 승인 없는 주문 제출·통화를 포함하지 않는다. 노출 텍스트와 aria-label까지 display-copy.json을 정본으로 쓴다.
5. FAQ4개 질문·답변 전문은 항상 펼친 상태로 표시한다. sections.questions를 faq 배열에서 한 번만 렌더한다. 변경/취소/입금 이름 답변을 숨기거나 중복 출력하지 않는다.
6. 승인 배너 message → budget → consultation을 실질 콘텐츠 사이에 분산한다. 예: 상품 뒤 message, 시설·시간 뒤 budget, 리본 뒤 consultation. 연속으로 쌓지 않는다. 동일 정본3개와 판매사진4개, 총7개의 SHA·치수·설명적 alt를 유지한다. 배너 alt에는 전화번호1번, 삭제된 공통 캡션을 다시 넣지 않는다.
7. 단일 H2 출처 및 확인 정보 아래 원문 링크와2026-04-01 시설기준일/2026-10-17 KST 자료확인일을 표시한다. 군청 실패·잘못 연결된 병원도메인 같은 조사 사정은 고객문구에 넣지 않고 출처로도 오인시키지 않는다.
8. 미승인 private 기본값은 noindex,nofollow다. 향후 승인된 공개 계약에서만 plannedOrigin·canonical·robots·sitemap을 확정한다. 404는 noindex·배너 없음이며 실제 HTTP404를 별도 검사한다. 현재 host 생성/소유권/공개는 검증하지 않았다.
9. 후속 검사에서는 원고 leaf strings/순서/FAQ/가격·배송비각행/SKU CTA/내부앵커/이미지7/heading/meta/mobile320·390/desktop1280을 실제 출력에서 확인한다. 20,000원 누락·10,000원 일괄치환·sumLabel0원·배송 보장·시설 전용 CTA·배너번호 변경·FAQ 누락을 부정검사에 넣는다.
10. 원고가 바뀌면 이전 digest의 검수 승인을 승계하지 않는다. 작성자 구조검사와 별도 독립 품질검수를 모두 실제 산출물에 결속한다.
