# 강진군 원고 구현 인계

정본은 draft-home.ko.md와display-copy.json이며customer-copy.json은두정본의정확한구조화projection이다. 원고본문·전체UI문구를 바꾸면 새digest/검수가 필요하다. 이번은 실제구현 없음.

1. header/본문건너뛰기/main(H1한개)
2. intro 후 restrictionNotice를 펼쳐 표시. 마량시설 예외가 hero action·배너·사진link·상품가격보다 먼저. 해당알림은판매처공지읽기link만;3단상품CTA 없음.
3. heroActions
4. message배너
5. products-cost H2/본문 + productEligibilityNotice + 실제4card. card H3/actual500px사진/개별SKUCTA. 마량시설전용상품또는Offer처럼연결금지.
6. delivery-cost H2/본문. 표기마량면10000원과나머지미기재(null)를구분. 군전체10000/기타0/무료/마량시설에3단가능으로표시금지. referenceSum/sumLabel모두null은의도적임.
7. budget배너
8. locations H2/본문. 주소·전화는정보용.시설별판매상세5 HOLD,목록·가짜카드·내부상세링크0. 마량제약을나머지시설전체로확대하지않음.
9. order-timing H2/본문.19/21시상품별조건과주말상하단차이보존.
10. ribbon-order H2/본문·입력4줄,inlineOrderUI
11. consultation배너
12. questions H2/FAQ4(H3질문+답변전문) 항상펼쳐보임.배열question/answer에서렌더하고본문중복렌더하지않음.
13. sources H2‘출처 및 확인 정보’/소스이름문단 또는H3/checkedLabel와exactURL
14. closingAction/footer

배너3은message→budget→consultation사이에실질텍스트/상품이있다.공통캡션없고전화1844-0644는각alt한번. width1774/height887/반응형/lazy/async.본래hero이미지로승격하지않음.사진4와배너3 총7자산.

예정URL https://gangjin.fwith.kr/ 는계획필드일뿐소유/연결/공개검증아님.기본private noindex,nofollow.공개승인후별도adapter에서만index,follow/canonical/sitemap구성.홈1개+404,facility5 HOLD 유지.404에마케팅배너없음.

실제후속검사:규정알림이첫매출CTA보다앞/상시노출,마량전용3단CTA0,FAQ4전문,본문/카드/alt/meta문자열정확성,SKU별URL,배송비null,19/21,양환불조항,단일H1/연속H2H3,sourceheading1개,모바일320/390/desktop1280읽기/버튼,URL/fragment대상,real404/robots/canonical/sitemap,정본7hash.스크립트PASS만으로실제픽셀검수완료라고하지않음.
