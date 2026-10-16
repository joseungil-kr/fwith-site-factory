# 담양 단일 구매 홈 별도 릴리스 어댑터

기존 광산 릴리스 어댑터의 원본 파일을 변경하지 않고 후속 복사본을 최소 수정했다. 담양 자체 원고와 실제 private 빌드가 고정된 뒤에만 검증을 통과한다. 기존 지역의 출력 fixture나 작성자 완료 보고를 성공 근거로 사용하지 않는다.

## 고정 계약

- HTML: index.html, 404.html만 허용
- indexable 및 sitemap URL: 홈 `/` 하나
- 구매 본문: 홈 한 개. 시설 상세 및 support 페이지 0개
- private 출력 14개, dedicated-proof successor production 형식 출력 17개 및 예상 공개 HTTP 검사 16개. 원본 공개 release16/HTTP15는 변경하지 않는 과거 기록이다. 실제 inventory와 고정 baseline을 대조하며 예상 수만으로 성공을 선언하지 않음
- 본문 2개와 static asset 9개의 bytes 보존. robots/canonical/social/revision 등 허용된 head 변경만 허용
- 기존 공개 IndexNow proof bytes와 상품사진·배너 보존
- source path/symlink, 명시적인 외부 binding, provider credential 금지, source revision 형식, 개인 preview 차단 경계 보존

## 로컬 검증

candidate에서 private 빌드 및 qa_damyang.py를 먼저 실행한 뒤, 소스 manifest와 preview-equivalence를 실제 산출물로 고정한다. 이후 이 폴더에서 다음 명령을 실행한다.

- node --test release-tests/damyang-release.test.mjs
- python3 scripts/test_damyang_adapter.py
- python3 scripts/test_damyang_release_output.py
- python3 scripts/test_damyang_node_python_parity.py
- python3 scripts/test_damyang_runner_output.py

출력 변이 테스트는 candidate/dist를 검증한 후 새 임시 fixture를 만든다. Node/Python parity와 runner 변이는 같은 담양 소스를 임시 경로로 복사하고 가짜 a×40 revision과 합성 승인 envelope를 사용한다. 기존 proof를 보존하고 새 proof를 추가한 실제 inventory 17개 파일을 재검사하며 실제 승인·원격 저장·runner·공개·IndexNow 제출을 의미하지 않는다. IndexNow payload 테스트는 홈 하나를 통과시키고 empty, duplicate, extra, foreign, 404 목록을 거부하며 네트워크 전송은 하지 않는다.

## 미확인 경계

sourceRevision=null 또는 local-inspection은 이번 successor의 로컬 준비 상태다. 원본 source89c92dff3dca6456c1b0a3f7ee0587efe0361bed는 damyang.fwith.kr / damyang-flower-guide에 공개됐지만 현재 provider deployment/version/settings baseline과 successor 상태는 별도로 확인해야 한다. 기존 고정 host의 assets-only 업데이트만 대상이며 최초 publication 재실행·새 Worker 생성·hostname attach를 허용하지 않는다. 실제 successor source/control 결속, runner, 브라우저·모바일 화면, 최신 기존-target baseline, 공개 HTTP·real404, IndexNow receipt는 별도 후속 검증이다. 이 어댑터의 로컬 inspect 명령은 게시하지 않으며 production 명령은 차단한다.

## Historical manuscript r2 timing correction (before this proof successor)

This separate source revision consumes the exact r2 manuscript review (copy 3bc9a15e452efbc3afac06f366f711ac45008b136d3597a6a15d997ddfb741d0). Only one customer paragraph changes. Both upper/lower timing notices, unresolved applicability and separate B06021 condition remain together. Original165/24/16/3 and null scores are retained; supplemental6+1 are separately validated. Exact r1 review identities remain historical, with timing scope superseded. Rebuild fixtures from source; never copy r1 outputs or claim public verification. Source inventory is derived from the frozen manifests, not the historical74.

## Dedicated public proof successor (2026-10-16)
The original legacy proof is retained byte-for-byte. Only the new dedicated proof is eligible for the one bounded recovery request. The original receipt377 and its first rejected attempt remain in the explicit recovery-chain binding; changing the key/source never resets the attempt budget. Original customer-source65 files and all author/reviewer historical evidence are unchanged. Remote successor SHA, actual QA, existing-host update, public GETs and accepted receipt are still pending. This source cannot authorize a first-publication rerun or any provider/security change.
