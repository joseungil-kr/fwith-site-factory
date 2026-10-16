# 화순 원고 구현 인계

이 파일은 구조 계획이며 실제 렌더 완료가 아니다.

1. /의 H1은 display.page.h1 하나다. 공감 intro 뒤 restrictionNotice를 항상 펼쳐서 표시한다. 첫 상품·전화 CTA와 배너보다 앞에 둔다. notice 자체의 링크는 병원 공식 안내 읽기만 허용한다.
2. sections 순서 locations → products-cost → order-timing → ribbon-order → appearance → questions를 유지한다. 병원 판매 상세, 시설 카드, 시설별 주문 버튼은 만들지 않는다. 출처는 H2 하나 아래 모은다.
3. 제품 영역 #products-cost 내부에서 productEligibilityNotice를 카드 네 개 앞에 표시한다. 앵커로 바로 들어와도 확인할 수 있어야 한다. 병원명과 특정 네 SKU를 결제 용도로 묶는 추천 문구, 구조화 데이터, 미리 선택 상태를 만들지 않는다.
4. product.referenceSumKRW와 postedHwasunAdditionalDeliveryKRW는 null이다. NOT_LISTED_NOT_ZERO가 정본이다. p.sumLabel=null이면 요소를 생략한다. 0원, 무료, 기본가와 같은 합계, 보성 10,000원, 고흥 20,000원 또는 placeholder 합계를 생성하는 코드는 거부한다. 일반 상품 CTA는 각각 검증된 SKU URL이며 승인 없는 주문 제출은 하지 않는다.
5. FAQ 세 개는 질문·답변 전문을 펼쳐 실제 출력한다. sections의 questions는 faq 배열을 한 번만 렌더한다. Markdown과 배열을 함께 렌더해 중복시키지 않는다.
6. 동일한 승인 배너 세 장을 message → budget → consultation 순서로 실질 콘텐츠 사이에 분산한다. 예: locations 뒤 message, 상품·주문시간 뒤 budget, 소재·FAQ 사이 consultation. 이미지를 연속으로 쌓지 않는다. 실제 상품사진 네 장과 배너 세 장, 총 일곱 개이며 assets manifest SHA를 대조한다. 승인된 공통 캡션 삭제는 유지한다.
7. noindex,nofollow가 로컬 미승인 기본값이다. 공개 승인 이후에만 별도 release 계약으로 index,follow와 canonical·sitemap을 다룬다. 404는 noindex이고 배너가 없으며, 실제 404 HTTP는 후속 검증한다.
8. 검사 대상은 작성된 정확한 leaf strings, FAQ 전문, title/H1/meta/heading 순서, 전체 링크·fragment, 네 가격, nullable 배송비, 반입 제한의 DOM 순서, 일곱 이미지 SHA·치수, 모바일·데스크톱 픽셀이다. 병원 notice 삭제, CTA 앞뒤 역전, 화순 추가비 0원값, 병원 전용 상품 CTA 변조를 거부 사례에 넣는다.
9. 원고 SHA가 바뀌면 이전 검수 승인을 재사용하지 않는다. 실제 빌드·화면·공개 응답을 검증하기 전에는 지역 완료로 표시하지 않는다.
