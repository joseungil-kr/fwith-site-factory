# 고흥 원고 출력 구조 계획

이 문서는 구현 전 구조 계약이다. HTML·브라우저·공개 URL 검사가 수행됐다는 뜻이 아니다. 이 단계에는 새 사이트 코드, 빌드 또는 배포가 없다.

## 경로와 범위
- 구매 판단에 필요한 정보를 한 흐름으로 읽는 `/` 한 페이지를 작성했다. 같은 의도의 가격/리본/야간 상세 URL은 추가하지 않는다. 근거가 부족한 여섯 시설의 독립 페이지는 모두 HOLD다.
- `https://goheung.fwith.kr/`는 계획 canonical일 뿐 확인된 서비스 URL이나 소유권 주장이 아니다. 개발/미승인 미리보기는 noindex,nofollow. 승인된 별도 공개 단계에서만 canonical·robots·sitemap을 실제 hostname과 결속한다.
- 404는 별도 상태 페이지이며 실제 HTTP404와 noindex,nofollow를 요구한다. 마케팅 배너나 상품카드는 넣지 않는다. 루트의 별도 detail 사본을 만들지 않는다.

## 단일 원문과 유효 구조
- 집필 정본은 draft-home.ko.md와 display-copy.json. customer-copy.json은 두 정본에서 본문·FAQ·UI를 손실 없이 묶은 데이터 산출물이다. sourceSHA256이 둘을 결속한다.
- H1은 page.h1 한 번만 출력한다. draft-home의 H1을 추가로 출력하지 않는다. 본문은 main id=main-content 아래에 놓는다. hero 소개는 각각 p로, CTA들은 별도 링크 그룹으로 출력한다.
- 각각의 section은 H2와 p/ul 등 형제 block을 가진다. `p` 안에 section, figure, div, ul 또는 또 다른 p를 넣지 않는다. Markdown 전체를 p로 감싸는 구현은 거부한다. ul은 실제 li이며 줄바꿈만으로 목록을 흉내내지 않는다.
- budget에는 H2 아래 본문 세 문단과 상품카드 네 개를 실제로 출력한다. 각 카드는 H3, 확인된500×500 상품사진, 이름, 상품가·추가비·참고금액, 시각적 묘사, SKU 상세 CTA를 가진다. 카드 제목 외 중복 H2는 넣지 않는다. 카드의 합산 참고금액을 확정 결제액으로 보이게 만들지 않는다.
- questions는 H2 아래 customer-copy.faq의 질문 두 개를 H3, 답변을 p들로 한 번씩 펼쳐 출력한다. draft Markdown의 FAQ와 faq 배열을 동시에 출력하지 않는다. `contentMarkdown`의 유무에 따라 FAQ를 통째로 숨기거나 이중 출력하는 조건문을 사용하지 않는다.
- 출처 영역 H2 ‘출처 및 확인 정보’는 한 번. 출처명은 p 또는 목록링크로 출력한다. 사용자용 본문에 연구·충돌·검수 사정을 삽입하지 않는다.

## 읽는 순서
1. 공통 헤더·내비게이션 → 단일 H1·소개·두 CTA
2. 승인된 message 배너
3. budget 본문과 실제 상품카드4, 사진·금액 안내
4. message-order 본문과 한 번의 주문정보 목록·리본 예시·상담
5. 승인된 budget 배너
6. appearance → timing → location 본문
7. questions의 펼친 FAQ2
8. 승인된 consultation 배너 → inlineOrder 문구·전화 CTA
9. 출처·최종 상담 링크·푸터

배너 사이에 충분한 펼쳐진 본문과 상품 콘텐츠가 있으며, 연속 세 장·접힌 summary 한 줄로 간격을 대체하지 않는다. 본문과 배너의 순서를 수정한다면 이 구조와 문구 전문을 다시 검사한다.

## 이미지·버튼·접근성
- 승인 배너3종은 현행 정본과 동일 bytes. 파일명·SHA·1774×887·alt는 display-copy.json에 있다. 전화번호는 alt에 정확히 한 번이며 이미지 내 전화번호도 그대로 유지한다. 캡션 없음. 삭제된 AI 생성 안내문을 본문·alt로 옮기지 않는다. 새이미지/재생성/블롭 없음.
- 배너는 figure/img, width=1774·height=887·width:100%·height:auto·loading=lazy·decoding=async. 첫 화면의 중요 이미지는 무조건 lazy 처리하지 않는다. 배너로 텍스트 정보나 H1을 대체하지 않는다.
- 상품사진은 실제 조사에서 확인한 원본 SHA에 결속한다. 임의 크롭·새로운 상품 합성·배송현장 사진처럼 표시하지 않는다. CSS object-fit:contain으로 전체 상품이 보이도록 한다.
- 카드 링크는 각 SKU의 `https://fwith.co.kr/shop/item.php?it_id=...`로 간다. 공식몰 홈 링크와 전화 CTA는 별도 역할이다. 상담전화는 tel:18440644. 시설 전화버튼은 만들지 않는다.
- 앵커 budget/message-order/appearance/timing/location/questions/sources/main-content는 각각 유일해야 한다. 키보드 포커스·명확한 링크명·모바일 터치 영역과 가로넘침을 실제 출력에서 검사한다. 네 카드나 FAQ를 화면 크기별로 감추지 않는다.

## 후속 구현에서 필요한 실제 검증
- HTML parser로 H1=1, H2→H3 순서, p 중첩 금지, 실제 펼친 FAQ2의 질문·답변 일치, 정확한 카드4·사진4·CTA4 확인
- sourceArea/본문/메타의 모든 고객 문자열이 최종 원고와 일치하는지, HTML escape/줄바꿈/링크 변환으로 누락되지 않는지 검사
- 독립된 title/meta/canonical/robots, sitemap 집합, 실제404, 모든 내부 앵커·외부 상품링크, 이미지 HTTP/MIME/SHA 확인
- 390px 등 모바일과 데스크톱의 실제 픽셀·키보드·버튼을 검토. 문구계획 자체를 화면 PASS로 간주하지 않기
- 잘못된 SKU링크·누락FAQ·중복H1·배너SHA변경·전화오번호/중복·삭제캡션재삽입을 거부하는 음성 테스트
- 비밀키·provider·공개·IndexNow와 무관한 원고검수 상태를 분리하며, 실제 검색 색인·순위·배송성과를 주장하지 않기
