# 화순군 r2 keyless 로컬 프리뷰

정본: ../inputs/author/customer-copy.json, display-copy.json, draft-home.ko.md와 FULL-CUSTOMER-COPY.ko.md. 원고 bytes는 수용된 화순 r2 그대로다. 원저자의 역사 상태값을 고치지 않았다. 독립 원고 수용은 ../inputs/review/RESULT.json의 ACCEPTED_LOCAL_COPY_R2_ONLY이며 구현 수용과 다르다.

보성 private46 e4fea02b97a46aa4e3853ed8d63a242a20b1dee3의 전체 46파일을 pinned remote Git tree와 대조한 뒤 Astro 구조·plain parser·HTML parser·CSS·lockfile·7개 이미지를 재사용했다. 그 이전 고흥 source46 1131fe3623c9f04a38343ae51ecd24be46818abd의 이미지 Git blob 및 lock도 동일하다. lock의 과거 고흥 패키지 이름은 bytes 보존을 위해 남겼으며 의존성은 변경하지 않았다. 새 외부 코드를 가져오지 않았다.

순서: 공감 도입 → 병원 제한 → hero CTA → locations → message 배너 → products-cost → order-timing → budget 배너 → ribbon-order → appearance → consultation 배너 → FAQ3 → 상담 → 출처 → 마무리 CTA. 상품 앵커 안에서 제목 바로 다음에 승인된 병원 부적합 문구와 카드4개를 연이어 두고, 원문 상품설명은 카드 뒤에 그대로 펼친다. 병원 전용 판매페이지·상품 선택 상태·구조화 추천은 없다. 상품사진과 텍스트 CTA 모두 해당 일반 SKU 상세로 연결한다.

금액은 기본가 59,000/79,000/109,000/149,000원이다. 배송비·합계는 null이며 sumLabel=null인 요소는 생성하지 않는다. 화순 추가비를 0원 또는 이웃 지역 요금으로 계산하지 않는다. 시설 상세4 HOLD다.

실행: candidate에서 npm run build 및 npm test. 기존 dependency cache를 node_modules로 연결할 수 있다. scripts/audit_dependencies.py는 lock의 설치 버전 대조이며 패키지 전체 bytes 검사는 아니다. 별도 fresh ZIP 재현은 상위 패킷 reproduce_packet.py를 사용한다. 네트워크 설치 없이 기존 캐시로 검사했다.

정적 출력은 index.html, 404.html, robots.txt, CSS1 및 이미지7, 총11파일이다. 홈/404 모두 noindex,nofollow, robots는 Disallow:/다. canonical·social·sitemap·key·proof·production adapter가 없다. release/credential 환경변수가 있으면 빌드를 거부한다.

browser_check.py는 후속 승인된 loopback QA 참고용이며 이번에는 실행하지 않았다. 실제 화면, computed visibility·overflow·touch targets, 키보드와 Back/Forward, 실제 missing-path HTTP는 미검증이다. 부모는 보성의 성공한 읽기 전용 Actions 제어와 fixture/actual 분리 r2를 참고할 수 있으나 이를 화순 실행으로 대신할 수 없다.
