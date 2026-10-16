# 강진군 keyless 로컬 프리뷰

수용된 원고2991자와FAQ4, display UI는 ../inputs/author의 원본 bytes 그대로다. 역사상 원고작성 상태값을 바꾸지 않았으며 독립검수 ../inputs/review/VERDICT.json은 원고만 수용한다.

재사용: 화순 source47 17703e6e4c8a82f3271088a76b8cf7d76bf1ff08 전체 파일과 원격 Git blob을 대조하여 Astro 구조·parser·CSS·lockfile·7자산을 재사용했다. 장흥의 상품 설명 뒤 nullable-total card 배치도 읽었다. 새 외부코드/API/이미지는 없다. lock의 과거 고흥 package name은 bytes 보존을 위해 유지한다.

구조는 수용된 RENDER-STRUCTURE-PLAN과 일치한다. 마량장례식장 판매처 공지를 intro 바로 뒤/첫 hero CTA 전에 펼쳐 두며, 상품 본문 뒤의 부적합 알림 바로 다음에 일반 카드4를 렌더한다. 마량전용 상품CTA/Offer/시설상세는 없다. 상품·마량면비용 다음 budget, 리본·상담 다음 consultation을 둔다. source 명칭은 단일H2 아래 문단 링크다.

마량면 추가비용10000원만 확인돼 있으며 군 전체/다른 읍면/합계는null이다. 기본가59/79/109/149천원. 대체쌀화환SKU/가격/재고를 만들지 않는다. 시설5 HOLD.

실행: 기존 node_modules cache를 사용해 CI=1 npm_config_offline=true ASTRO_TELEMETRY_DISABLED=1 npm run build 및 npm test. 새 npm install은 하지 않는다. scripts/audit_dependencies.py는 installed versions와 lock을 대조하며 모든 dependency bytes 무결성을 보증하지 않는다.

출력11개: home/404 HTML, robots, CSS1, 승인 이미지7. 두 페이지 noindex,nofollow 및 robots Disallow:/, sitemap/canonical/OG/JSON-LD/key/proof 없음. 이 경계는 접근제어가 아니다. 패킷은 로컬에만 있으며 온라인 private site나 공개사이트가 아니다. release/credential 환경변수는 빌드를 거부한다. HTTP/화면검수 실행 여부는 패킷의 별도 보고를 따른다.
