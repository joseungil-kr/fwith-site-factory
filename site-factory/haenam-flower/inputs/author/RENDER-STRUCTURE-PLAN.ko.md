# 해남 한 홈의 구현 인계

이 파일은 구현 계획이다. 실제 HTML·화면·빌드는 아직 만들거나 검증하지 않았다.

H1 하나와 intro 뒤에 상품·상담 CTA를 둔다. 본문 순서는 products-cost, delivery-cost, locations, order-timing, ribbon-order, questions다. 상품 설명 다음에 네 ProductCards를 배치한다. 배송비 10,000원 공통 행과 문내면·송지면 15,000원 행을 보존하고 referenceSumKRW와 sumLabel은 null로 유지한다. 본문과 카드의 기본가격을 최종금액으로 바꾸지 않는다.

message 배너는 hero 이후, products-cost 시작 전에 놓는다. budget 배너는 상품·배송비 본문 뒤, locations 전에 놓는다. consultation 배너는 locations·order-timing·ribbon-order를 지난 뒤 FAQ 앞에 놓는다. 세 배너 사이에 펼쳐진 실질 본문을 두며 이미지를 연속으로 쌓지 않는다. 정본 배너 3개와 상품사진 4개는 수정하거나 생성하지 않는다. 이미지의 전화번호 alt·치수·설명은 유지하고 삭제된 AI figcaption은 재삽입하지 않는다. 상품상세 CTA는 각각의 SKU 직접 URL이다.

FAQ 4개는 question과 answer 모두 열린 텍스트로 렌더한다. contentMarkdown 유무로 숨기지 않고 faq 배열에서 한 번만 렌더한다. 061-533-4444는 운영자 출처 문맥의 시설 문의번호이고 꽃이랑 CTA는 tel:18440644다. 시설 상세 6개는 HOLD, 역사 후보 1개도 별도 HOLD로 유지하며 목록·가짜 상세·빈 링크는 생성하지 않는다. 판매처 공지의 해남 미언급을 반입 허용으로 구현하지 않는다.

출처 H2 하나, 고유 title·meta, 자기 canonical 계획, home과404의 실제 robots 상태, 한 홈 sitemap과 진짜404를 구현 후 검증해야 한다. preview는 noindex,nofollow이며 별도로 승인된 공개 과정까지 index 상태나 hostname 소유권을 주장하지 않는다. 공개 URL 응답·키·IndexNow 검증은 이번 원고 산출물 범위에 없다.
