# 보성군 r2 keyless 로컬 프리뷰

정본: ../inputs/author/customer-copy.json 및 display-copy.json. 모든 입력 bytes는 수용된 r2 원본 그대로이며 기존 author의 역사 상태값을 고치지 않는다. 독립 원고 수용은 ../inputs/review/REVIEW-DECISION.json의 copy-only 판정이다. 구현 검수는 별도다.

고흥 private46 commit 1131fe3623c9f04a38343ae51ecd24be46818abd의 Astro 컴포넌트, plain parser, HTML parser, CSS, lockfile, 7개 이미지 재사용. 보성의 별도 display schema와 FAQ ID 부재를 기술적으로 처리했고 products-cost → locations → order-timing → ribbon-order → appearance → FAQ 3개의 검수된 순서로 렌더한다. 원고를 지역명 치환하거나 다시 쓰지 않았다.

실행: 이 candidate에서 npm run build, npm test. 재사용 가능한 dependency cache를 node_modules로 연결하면 별도 설치 없이 재현한다. scripts/audit_dependencies.py는 package-lock의 설치된 버전만 대조하며 전체 패키지 bytes 무결성 검사는 아니다. 잠긴 dependency tree와 lockfile은 변경하지 않았다.

정적 산출물은 index.html, 404.html, robots.txt, CSS 1개, 이미지 7개 총 11개. noindex,nofollow와 Disallow:/를 사용한다. canonical/social/sitemap/키/production adapter가 없고 release·credential 환경변수가 존재하면 빌드를 거부한다. 시설 상세 7개는 HOLD다.

browser_check.py는 후속 승인된 읽기 전용 loopback QA용이다. 여기서는 실행하지 않았으며 과거 Chromium socket 제한을 우회하지 않는다. 실제 모바일/데스크톱 pixels, computed visibility, keyboard·Back/Forward, local missing-path HTTP, public HTTP는 미검증이다. 본 패킷에 Git 원격 쓰기·배포·키 생성·IndexNow·콘텐츠 API 호출은 없다.
