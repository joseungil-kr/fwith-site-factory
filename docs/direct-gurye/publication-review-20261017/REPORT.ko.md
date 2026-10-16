# 구례 공개 검증 결과

[직접 확인] https://gurye.fwith.kr/ 공개 홈200, 알려지지 않은 경로404와 총14경로를 별도 GET했습니다. 리디렉션은 없었습니다. 이번 독립 조회의 홈·404 원문은 기존 수용 HTML과 그대로 같았고, CSS·상품사진4·공통배너3·사이트맵·동일 공개 확인 파일도 일치했습니다. robots는 검수된 Cloudflare 관리 접두부와 원본 접미부 조합입니다.

[직접 확인] 활성화 commit e0b875fc7960b1f3323e7eeb19e47789f609e573의 정확12파일, 기존3259 leaf 및192개 비-main ref 보존, 원격35파일 readback과99시험을 확인했습니다. source de6147, 기존 실제 생산15와 release.json은 그대로입니다.

[도구 보고 및 산출물 대조] owner issue405의 run38939914274에서 업로드·hostname 연결·binding readback·공개 HTTP 단계는 통과했습니다. provider API를 별도 인증 조회하지는 않았으며, 실제 공개 응답을 독립 대조했습니다. 기존 실제 production38 화면 검수는 같은 소스·출력에 결속되지만 이번 공개 호스트의 새 브라우저 촬영은 하지 않았습니다.

[실패·미확인] Naver IndexNow 요청1회는 HTTP422로 거절돼 전체 run은 failure입니다. 요청187바이트 원문은 확인했습니다. 응답은 완전12바이트 UTF-8 및 해시로 기록됐지만 원문이 안전 허용목록 밖이라 보존되지 않았습니다. 구체적인 거절 사유는 알 수 없고 응답 해시를 원문에서 다시 계산할 수 없습니다. receipt404의 started→rejected 댓글2개를 대조했습니다. 접수 성공·검색 반영·순위 향상을 주장하지 않습니다.

같은 실행에서는422 뒤 재시도하지 않았습니다. standalone finalize의 새 호출은 rejected를 허용하지만, 전체 publisher에는 기존 Worker/hostname을 거부하는 최초발행 preflight가 별도로 있습니다. 추가 POST·재배포·복구 실행은 하지 않았습니다. 시설별 페이지3 HOLD와 core/full NOT_ASSESSED는 유지됩니다.

공개 성공과 검색 접수 실패를 분리해 기록합니다.

- 공개: https://gurye.fwith.kr/
- 실행: https://github.com/joseungil-kr/fwith-site-factory/actions/runs/38939914274
- 영수증: https://github.com/joseungil-kr/fwith-site-factory/issues/404
