# 해남군 keyless 로컬 프리뷰

수용 원고2874자(끝 LF 포함), FAQ4, display UI를 inputs/author의 원본 bytes 그대로 렌더한다. 원고 독립검수의2873자는 끝 공백을 strip한 방법 차이다. 원고 상태값은 역사 그대로이며 독립검수는 원고만 수용한다.

강진 source48의 local-source.zip을 원본 source683487ff의 Git tree와 파일별 대조해 Astro 구조·CSS·parser·lock·7자산을 재사용했다. 원본 강진 commit683487ff86f8505076e8f595a6b8e54b2aa9a6e6. 외부 코드/API/이미지는 추가하지 않는다. lock의 과거 package name은 bytes 보존을 위해 유지한다.

본문 뒤 카드4, message→상품/배송비→budget→시설/시각/리본→consultation→열린FAQ4→출처 구성이다. 해남군10000원과 문내면·송지면15000원은 구분하고 합계는null. 두 병원의 읍면·주소 및 병원전화와꽃이랑1844-0644를 구분한다. 현재시설6 HOLD와역사후보1 별도HOLD, facility route 없음.

nav 폭·높이44px 최소 CSS 및 flex-wrap을 추가하되 실제320/390/1280px 검사는 별도 미검증이다. capture의 모든 링크44×44 및 overflow기준을 그대로 유지한다. 기존 socket denial을 회피하거나 브라우저를 재실행하지 않는다.

기존 node_modules cache만 사용해 CI=1 npm_config_offline=true ASTRO_TELEMETRY_DISABLED=1 npm run build 및 npm test를 실행한다. 새 install없음. audit_dependencies.py는 cache 버전만 lock과 대조하며 dependency bytes전체 무결성을 뜻하지 않는다.

출력11개: home/404 HTML, robots, CSS1, 승인 이미지7. 양쪽 noindex,nofollow와 robots Disallow:/, canonical/sitemap/OG/JSON-LD/key/proof없음. 로컬 전용 패킷이며 온라인 비공개 사이트를 의미하지 않는다. 무색인은 접근제어가 아니다. release/credential 환경변수는 build가 거부한다. 원격Git/issue/Actions/배포/IndexNow/키생성/콘텐츠API/새Work/PC는 부모의 별도 조정 없이는 수행하지 않는다.
