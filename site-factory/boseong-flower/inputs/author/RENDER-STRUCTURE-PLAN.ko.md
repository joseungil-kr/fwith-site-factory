# 보성 home 렌더 인계

구현하지 않은 계획이다. `/` home과 실제404만 후보 범위이며, 빈 regions 허브나 시설상세를 만들지 않는다. 본문/FAQ와 모든추가노출문구의 정본은 draft-home.ko.md, display-copy.json, 그 둘에서 파생한 customer-copy.json이다. 이번 파일의 지시로 source·배포·키·외부행동이 승인되는 것은 아니다.

1. H1 하나 → intro와 실제 전화/상품 CTA → message 배너.
2. H2 products-cost 본문과 네 실제상품카드 → budget 배너. 각카드 H3·500×500 사진·상품가/추가비/참고액·해당 SKU 직결. 카드 숫자4와 근거표 숫자4 일치.
3. locations → order-timing → ribbon-order → appearance 본문. 문단 순서·제한·주소의 출처날짜를 보존한다.
4. questions H2 아래 FAQ3개 H3와 답변을 실제 HTML에 펼쳐 렌더. 본문과 FAQ를 이중출력하지 않는다. customer-copy faq 배열을 사용하고 sections.questions는 참조만 한다.
5. 실제 FAQ/본문 뒤 consultation 배너와 주문상담 CTA, H2 출처 및 확인 정보. 같은 source 링크를 유지한다. 세 배너를 연속 배치하지 않는다.
6. 404는noindex,nofollow·배너0, home 복귀 링크만. 알 수 없는 실제경로가HTTP404인지 후속검사한다.

공통배너3종 파일·1774×887·정본 SHA 고정. alt의1844-0644는정확히한번. 삭제된 공통 AI 설명캡션을 본문·alt로 되살리지 않는다. 제품사진은 별도의 판매사진 안내를 유지한다. 공유 CSS·반응형·키보드·CTA·출처·메타·canonical·robots·sitemap·FAQ 가시성은 실제 build/DOM/pixel로 검증해야 한다.

plannedOrigin은https://boseong.fwith.kr이며 hostname 소유권·DNS·공개상태는 확인하지 않은 계획값이다. 서명/키/provider·IndexNow·전국집계 상태를 인접지역에서 복사하지 않는다. source와 실제render 수정 후 모든정본 digest와 검수 binding을 다시 만든다.
