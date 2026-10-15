# 현재 순천 공개 정책

2026-10-15 12:43:59 UTC 사용자 지시: “공개에 순서는 없다. 완료되면 바로 공개한다.”

순천 공개 여부는 순천 자체의 승인·원본/제어 commit·실제 build/QA/pixel/artifact 검수·호스트 충돌 안전성·공개HTTP/실제404·IndexNow 요구사항으로 판단한다. 다른 지역의 공개 완료 기록은 요구하지 않는다.

해시 고정 계약의 역사적 필드 중 아래 항목만 최신 지시로 대체되었다.
- bounded-contract.json의 launchOrder 전체: 지역 순번 및 선행 지역 상태는 역사적 정보이며 실행 조건이 아니다.
- requiredEvidence[]의 predecessor-public-release-verification: 현재 필수 증거가 아니다.
- productionLaunchGateStatus 문자열의 PREDECESSOR 구성요소: 현재 공개 차단 사유가 아니다.

나머지 bounded 품질·검증 요구사항은 그대로 유효하다. 이 JSON은 source69 내부 계약과 byte-exact/hash로 묶여 있어 파일 자체는 변경하지 않았다. 원본55·원고·이미지·source69에 남아 있는 기존 순서 서술도 동결된 이력이며 현재 공개 의존성을 만들지 않는다. Git 원본 predecessor commit·ancestry 검증은 지역 공개 순서와 별개인 source 무결성 요구사항으로 유지한다.

실제 publisher의 prior_launch 함수/호출, prior_launch_sha256 요청 필드, prior-launch-binding.json은 제거되었다. 그 필드를 보낸 이전 요청은 exact payload 검사에서 거부된다. 기존 순서전용 fixture4개를 제거하고, 순서 기록이 없는 정상 fixture와 own gate 우회 방지 회귀5개를 추가했다.

scripts/direct-suncheon/prior-launch-binding.json은 기존 후보 대비 제외 경로다. 부모 통합 작업자의 확인에 따르면 현재 실제 remote control에 존재한 적이 없으므로 별도 삭제가 필요하지 않다. 통합 전 fresh GET에서 예상 밖 파일이 발견되면 보고하고 자동 삭제하지 않는다. 이번 로컬 작업에서는 원격 존재를 직접 조회하거나 삭제하지 않았다. 다른 지역 evidence 디렉터리 전체 삭제는 계획에 없다.
