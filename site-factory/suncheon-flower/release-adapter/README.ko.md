# 순천 외부 production 준비 adapter

기존 GitHub 저장본 55파일과 후보 애플리케이션40파일을 수정하지 않습니다. candidate와 inputs의 상대 경로, package.json, 원본 JSON 및 모든 기존 테스트도 그대로 둡니다. 이 디렉터리는 별도 추가 파일입니다.

로컬 준비 검사:

    python release-adapter/scripts/suncheon_adapter.py verify-source
    python release-adapter/scripts/suncheon_adapter.py inspect --destination <source 밖의 새 출력 경로> --evidence <검사 로그 경로>

inspect는 기존 npm build와 npm test를 실제 실행한 다음 외부 폴더에 metadata inspection 출력만 만듭니다. private dist는 계속 네 페이지 모두 noindex입니다. inspection 출력의 source revision은 실제 저장 확인한 private predecessor 커밋이며 production successor 커밋으로 주장하지 않습니다. release.json, 승인 binding, provider 실행, IndexNow 접수는 만들지 않습니다.

허용된 출력 변화는 robots/revision/canonical/og:url, 검토된 제목·설명·기존 message 배너를 재사용하는 OG image 및 Twitter card/title/description/image, 404의 social 제거, robots.txt와 sitemap 재구성, 전역 noindex 응답헤더 제거, 기존 공개 proof 바이트 복사입니다. 고객 본문4개 전체 바이트, 원본 title/description 및 그 밖의 head 내용, 이미지7개·CSS·favicon 등 static9개는 고정됩니다. home와 성가롤로 상세만 index 및 sitemap 대상입니다. /regions/는 noindex support navigation이며 /404.html은 noindex·canonical/social/schema 없음입니다.

production 명령은 현재 차단됩니다. 실제 source/control successor, 부모의 순천 차례 통지, 목포26→여수27의 공개 검증, 실제 runner/독립검수/최초 호스트 preflight가 연결되기 전 이 준비물을 배포 완료나 deployable release로 취급하면 안 됩니다. control/integration-plan.json에 후속 기존 controller 통합 범위가 있습니다.

검사는 정적 파일 범위입니다. 실제 모바일 화면, 브라우저 CSS 계산, HTTP404, 공개 URL, 주문·통화·현재 재고, 색인·순위는 검사하지 않았습니다.
