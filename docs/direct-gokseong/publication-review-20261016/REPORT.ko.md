# 곡성 실제 공개 독립 검수

판정: PUBLIC_HTTP_VERIFIED_INDEXNOW_REJECTED_RELEASE_INCOMPLETE

## 직접 확인
- 공개 주소: https://gokseong.fwith.kr/
- source 7e6573e2eb97ac5473622d37478729ee43b565f1, activation main 8379c174156518f2435481cc767c14b64f50b3ef. 원격 53개 바이트·Git blob·SHA256 일치, 추가 10/수정 2/삭제 0 및 나머지 원격 blob 불변을 확인했다.
- 실제 publish run 38928433446, attempt 1의 원본 로그·API 및 결과 artifact 12058026462를 검사했다. ZIP 9,578 bytes, SHA256 f37ee7c35336138262b8d6fd18ed28e2234428227fd0ac59e8e6089b2b30f633, 안전한 16파일이다. release manifest는 검수한 실제 build 38923430470의 원문과 같다.
- 2026-10-16 16:03:58–16:04 UTC에 독립 HTTPS GET을 수행했다. 총 15경로: 정상 14 HTTP 200와 실제 없는 경로 1 HTTP 404. 원문 12파일은 byte exact, HTML 2개는 허용된 Cloudflare beacon 정확히 1개 제거 후 byte exact, robots는 고정 managed prefix와 원본 suffix를 검증했다. raw 응답은 바꾸지 않았다.
- canonical·revision·robots·sitemap의 홈 URL 하나·전용 proof와 자산 SHA를 검증했다. 홈 29개/404 17개 anchor, 홈 이미지 7개, 두 문서의 main text와 metadata를 다시 비교했다. 공개 HTML의 원본 102문구를 exact selector로 재검사해 논리 occurrence 119개, 페이지 확장 occurrence 143개 및 SKU 4개가 모두 일치했다. 이는 정적 DOM 검증이며 공개 브라우저 조작 검증은 아니다.
- 새로 읽은 공개 영수증 #399의 bot 댓글 두 개는 attempt 1의 started → rejected다. endpoint https://searchadvisor.naver.com/indexnow, 홈 URL 하나, run·source·fingerprint 1210c3960ef5fd7e8059ffc6eebe685ceb7147718189b858f6fcb7e4a1209b8b가 재계산과 일치한다. 이 run의 기록된 POST는 1회, 응답은 HTTP 422다.

## 도구 보고와 원문 검사의 구분
- provider 초기 Worker/hostname 부재, attach 및 정확 binding readback은 실제 runner가 남긴 API 결과를 원문 검사했다. 검수자가 provider API에 새로 로그인하거나 변경하지 않았다.
- deploy/attach/binding/public HTTP는 성공했지만 최종 run은 failure다. IndexNow step의 API success는 continue-on-error가 반영된 결론이다. 원본 INDEXNOW=failure, 422 rejected와 최종 실패 gate를 우선한다.
- publish runner의 회귀 요약은 Ran 165 tests; OK (skipped=17)이다. 앞서 독립 activation 환경에서 확인한 174개/skip 0 결과와 섞지 않는다.

## 판단과 남은 실패
공개 주소에서 검수한 한 페이지 산출물을 확인했다. IndexNow 접수는 거절됐으므로 전체 배포 절차의 완료 판정은 내리지 않는다. 기존 source/control/actual-artifact/activation 문서는 변경하지 않았다.

422 응답 본문과 실제 outgoing request wire bytes는 artifact에 없다. 응답 SHA만 있으므로 구체적인 거절 사유를 단정할 수 없다. 검색 색인·순위, 공개 브라우저 픽셀·상호작용, 실제 주문·전화·배송·최종 견적은 미확인이다. 별도 실제 build 브라우저 증거는 그대로 결속했다.

검수자는 새 키 생성, 재배포, 재POST, provider 변경 또는 브라우저 실행을 하지 않았다. 이 보고서는 그러한 후속 변경을 승인하지 않는다.

## 증거
- run: https://github.com/joseungil-kr/fwith-site-factory/actions/runs/38928433446
- started: https://github.com/joseungil-kr/fwith-site-factory/issues/399#issuecomment-6219442529
- rejected: https://github.com/joseungil-kr/fwith-site-factory/issues/399#issuecomment-6219443018
- 함께 제공하는 review.json, public-get-evidence.json, live-content-evidence.json, live-occurrences.json, publication-evidence.json, indexnow-evidence.json, activation-remote-readback.json 및 MANIFEST.json이 공개 가능한 원문이다. raw GET headers, 원본 API 계정 객체, runner 로그와 로컬 경로는 공개 projection에 포함하지 않는다.
