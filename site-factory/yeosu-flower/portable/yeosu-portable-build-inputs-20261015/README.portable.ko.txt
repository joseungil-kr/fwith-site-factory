여수 private 후보의 휴대 가능한 source + exact input 묶음

목적과 범위
- 기존 후보 source 40파일을 변경 없이 보존하고, npm build/test가 실제 읽는 sibling input 26파일을 같은 상대 경로로 포함한다.
- 기존 313파일 보존 감사 전체를 재현하는 묶음이 아니다. portable original-input-baseline.json은 기존 감사에 있던 23파일과 reuse-provenance/spec에 묶인 기존 배너 원본 3파일을 검사한다. 기존 후보·원본·313파일 감사·기존 ZIP은 수정하지 않았다.
- 고객 원고, spec, review binding, 상품/배너, 렌더러, 검증 코드, package lock은 변경하지 않았다. reference/input-selection.json에 각 입력이 필요한 실제 코드 경로와 포함 이유가 있다.
- 연구 PDF·스크린샷·확장 감사·이전 로그·VCS·인증 파일·node_modules·이전 dist는 포함하지 않는다. SOURCE-MAP.ko.md는 spec sourceBindings가 exact hash로 요구하므로 포함한다. 그 문서의 과거 증거 링크는 이 묶음에 포함되지 않으며 build 입력도 아니다.

실행
1. ZIP 전체를 하나의 새 빈 위치에 풀고 디렉터리 구조를 유지한다.
2. 이 README가 있는 루트에서 python3 verify_bundle.py 로 파일 목록·크기·SHA256을 검사한다.
3. 검증된 기존 의존성 트리를 yeosu-local-implementation-20261015/candidate/node_modules 에 복사 또는 연결한다. 이 묶음은 의존성을 설치하거나 제공하지 않는다. package-lock.json의 의존성을 충족해야 한다. 검증에서는 기존 의존성을 별도 /tmp 위치로 복사했으며 설치하지 않았다.
4. cd yeosu-local-implementation-20261015/candidate
5. ASTRO_TELEMETRY_DISABLED=1 npm run build
6. ASTRO_TELEMETRY_DISABLED=1 npm test
7. 루트로 돌아와 python3 verify_bundle.py --built-output 로 생성된 실제 dist 16파일의 경로·크기·SHA256을 이전 출력과 비교한다.

build 전에 test만 실행하면 dist가 없어 실패한다. candidate/evidence/.gitkeep은 qa 결과 파일의 쓰기 위치를 보존한다. build/test는 해당 결과 파일과 page-map을 생성한다. 원고의 원래 상대 경로를 바꾸거나 candidate만 다른 곳으로 이동하지 않는다.

의존성 및 검증 환경
- 검증에 사용한 기존 환경: Node 24.19.0, npm 11.9.0, Python 3.12.14, Astro 7.3.5, @astrojs/check 0.9.10, TypeScript 5.9.3.
- 다른 운영체제, Node 22, 새 설치, 다른 의존성 트리의 재현성은 이 검증의 범위가 아니다.
- 아카이브는 source/input 자체를 포함하지만 런타임과 의존성을 포함한 완전한 실행 환경 이미지는 아니다.

과거 source의 설명과 도구
candidate/README.md와 scripts/seal_candidate.py도 기존 source identity 보존을 위해 바이트 그대로 들어 있다. 이 루트 README가 portable 실행 범위를 정의한다. 원래 README의 “원고를 candidate에 복사하지 않았다”는 기존 구현 설명이다. 이 묶음은 원고를 candidate 밖의 같은 sibling 경로에 exact copy한다.
scripts/seal_candidate.py는 과거 전체 감사·기존 로그·template 비교를 위한 도구이며 이 묶음의 실행 경로가 아니다. 생략된 과거 자료가 필요하므로 여기서 실행하지 않는다. portable 검증은 verify_bundle.py와 build/test 및 별도 readiness 보고서로 확인한다. 기존 independent review 1,008 assertions나 313파일 감사가 새 묶음에서 그대로 재실행되었다고 주장하지 않는다.

비공개 경계와 미검증 사항
이 묶음은 공개·배포·출시 승인이 아니다. 네 페이지는 noindex,follow이며 canonical/public origin/production switch가 없다. noindex는 접근 통제가 아니므로 비공개 파일로 보관한다. 목포26 미완료·여수27 독립 준비 상태를 바꾸지 않는다.
브라우저, 모바일 화면, computed visibility, 키보드/메뉴 상호작용, 실제 HTTP404, 공개 URL 응답, 현재 상품/전화/결제/배송, 신규 설치는 검사하지 않았다. 기존 browser/loopback 차단을 재시도하지 않았다.

검증 기대값
source 40파일 tree SHA256: 9bf690107d7c1523b2fed72bc53af280c822aaa78615415aceb1f7c012f200a5
dist 16파일 tree SHA256: 25e600971b1d38bb9a1036ab7825f9ae590d96069077ad4d031f25d990d31522
reference/prior-source-manifest.json 및 prior-output-manifest.json의 각 파일 기록과 대조한다.
