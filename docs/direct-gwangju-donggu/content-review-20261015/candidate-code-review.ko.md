# 광주 동구 로컬 후보 독립 코드·실제 HTML 검수

판정: PASS_EXACT_LOCAL_CODE_AND_OUTPUT_ONLY. 수정 필수사항 0건. 이 판정은 최종 소스와 실제 로컬 정적 산출물만 대상으로 하며 배포 승인이나 공개 완료 판정이 아니다.

## [직접 확인] 검수 대상과 결속

- 광주 동구, 공식코드 12210, 전국 순서 31. namespace는 gwangju-donggu. 예정 호스트는 gwangju-donggu.fwith.kr이며 provider 실체·소유권은 미확인이다.
- source 76개를 확정 manifest대로 별도 replay/source에 복사했다. private 61개와 adapter 15개가 서로 겹치지 않게 합쳐진다. 두 소스 집합과 전체 manifest, 파일 SHA256 및 Git blob SHA1, 파일 크기를 직접 재계산했다. 처음과 마지막 원본·복사본 76개가 일치했다.
- 원고 SHA256: 9f4643d1aa73945983497c953296716bbe0449ce93960a1a3427a6a6933d7687
- render-plan SHA256: 15667a76349c650f4bdc9974bb892f68ea8823a44f07b44365a1597a19a0b36c
- 독립 원고 binding SHA256: 2c7a0752f5f8817d2be19aaa8a5c8623cd3093e3414eeb73ee7e9a8ec382deeb
- 전체 source tree SHA256: cf06b23cb8d6777f82f1996f98e21079742770bc458a5bb86785a902f4253d14
- private tree SHA256: 85e324271442ec82bec2322e1c6cef86a2621e90266d3d6c0a236a79cb9fbfa1
- adapter tree SHA256: 45d3806a4ef0e35d5b6918cd671aab3b83ec36e0dd943cd60922267ec4b9c8a3
- 전체 source-manifest SHA256: ad9db2706241ad3bee6ddb9ac5776c17849da7e16346cd76fa5e611956f06ffd
- 실제 source commit은 null이다. private/adapter는 한 실제 source commit으로 저장 가능한 형태이며, 아직 존재하지 않는 predecessor를 만들거나 성공 증거로 사용하지 않는다.

원고 원본 18개 파일, 독립 리뷰·binding 2개, 승인 원본 이미지 7개로 구성한 required-originals 27개를 실제 bytes로 대조했다. source에는 제3자 HTML/PDF 원문이나 사용자 대화·내부 절대경로를 포함하지 않는다. 정확한 source 목록과 명시적 경로 패턴을 검사했으며 모든 가능한 비밀값을 판별했다는 의미는 아니다. 테스트의 /tmp/binding은 합성 경로, package-lock의 tests/projects/workspace/packages/*는 의존 패키지 메타데이터다.

## [직접 확인] 재사용과 실제 재빌드

광양 원본 78382db9e684e61ff40d3e6720c7c68e1995168b의 로컬 71파일을 실제 열어 Git blob SHA1을 계산하고 보관된 GitHub recursive-tree 원본의 blob ID와 크기에 대조했다. 이번 검수에서 GitHub를 새로 조회한 것은 아니다. 원격 tree 응답의 현재성은 이 검수로 갱신하지 않았다.

기존 설치된 node_modules cache를 별도 복사본에 연결했으며 새 설치 없이 수행했다. package.json의 dependencies/devDependencies와 package-lock 전체 의존 그래프는 광양과 같고 최상위 패키지 이름만 동구에 맞게 다르다.

- verify-inputs: 통과
- Astro check: 13파일, 오류 0·경고 0·힌트 0
- Astro 실제 정적 build: 4 HTML 생성
- private Python QA: 실제 생성물을 읽어 통과
- private Node tests: 51
- private Python mutations: 67
- adapter Node tests: 36
- adapter Python tests: 30
- production-shaped output Python mutations: 55
- Node/Python synthetic head writer parity: 1
- 합계 240개 재현 검사 통과. 마지막 parity는 로컬 합성 계약이며 실제 승인·source commit·runner가 아니다.

별도 검사기는 구현의 QA 모듈을 import하지 않고 lxml/Pillow로 원고와 실제 HTML·이미지를 직접 읽었다. 29개 추가 산출물 변조를 모두 거부했다. 별도 계약 검사도 synthetic 정상 fixture 1개와 negative 3개를 실행했다. negative는 누락 경로의 200 상태를 주장하는 binding, 미확인 publicHTTPVerified=true, 가짜 predecessor 필드를 거부한다. 이것은 실제 HTTP 404 응답 검사가 아니다.

## [직접 확인] 실제 정적 HTML과 자산

home /, detail /regions/chosun-hospital-funeral-wreath/, support /regions/, technical 404 /404.html의 네 HTML을 모두 검사했다. 114개 원고·접근성·metadata 문자열을 원본 JSON pointer에 결속했고, 본문 block의 태그·문구·순서 및 모든 body/chrome 텍스트를 별도 기대 투영과 비교했다. 누락·추가·변경을 발견하지 않았다.

- 네 title/description은 각각 유일하며 H1은 각 1개다. home 카드 H3, detail의 상품 H3·FAQ H3는 올바른 H2 아래에 있고 source H2는 primary당 1개다.
- SKU B201/B203/B205/B060 카드가 detail에 각각 1개다. 기본가 59,000/79,000/109,000/149,000원, 배송 포함 최종금액 별도 상담 문구, 상품별 공식 CTA URL이 원고와 같다. 판매 전화 링크는 tel:18440644로 동일하다.
- FAQ 3쌍은 원고와 동일하고 정적 DOM에 각각 1회 존재한다. main·FAQ·breadcrumb·필수 CTA의 간단한 hidden/inert/aria-hidden/inline style 회귀를 검사했다. 실제 computed visibility는 아래 미확인 항목이다.
- detail breadcrumb의 홈→support→현재 페이지, support breadcrumb의 홈→현재 페이지를 확인했다. 실제 href 그래프의 support inbound는 detail 1개, detail inbound는 home/support 2개다. 내부 링크 및 #sources가 존재하며 support는 주 메뉴에서 제외된다.
- home/detail은 message→budget→consultation 배너 각 3개, support/404는 0개다. 원본 WEBP 1774×887, figure/img, 정확한 alt(전화 1회), lazy/async, width/height를 확인했다. CSS는 width:100%, height:auto, aspect-ratio:2/1, object-fit:contain이다.
- 제품 원본 JPEG는 각각 500×500, 이미지 alt·width·height·lazy·async가 일치한다. 승인 이미지 7개를 Pillow로 decode하고 원본 bytes/SHA256을 확인했다. 이는 실제 브라우저 스크린샷 검수가 아니다.
- _astro CSS와 favicon을 포함한 정적 자산 9개, 네 HTML의 body는 private와 production-like 사이 byte-identical이다. 전체 16개 private 및 18개 production-like 산출물도 작성자 freeze 산출물과 각각 byte-identical이다.

## [직접 확인] private 경계와 오프라인 metadata 변환

private의 origin/domain/canonical=null, 모든 네 페이지 noindex,nofollow,noarchive, robots Disallow: /, 빈 sitemap, 정확한 _headers를 유지한다. private에는 canonical·og:url·og:image가 없고 404에는 OG/Twitter가 없다. 허가되지 않은 provider/release 환경을 거부한다.

별도 오프라인 adapter 결과에서만 예정 host를 사용한다. home/detail은 index,follow + own canonical, support는 noindex,follow + own canonical, 404는 noindex,follow + canonical/social 없음이다. home/detail/support 각각 OG/Twitter 14태그가 원본 title/description과 동일하며 B201 500×500, 정확한 alt, twitter:card=summary이다. sitemap은 home/detail 정확히 2 URL이고 support/404는 제외된다. production-like _headers는 정확히 /*\n이며 추가 redirect/global-noindex 헤더가 없다.

이 출력의 revision은 local-inspection이고 실제 sourceRevision은 null이다. IndexNow 기존 공개 proof bytes만 로컬 출력에 복사했으며 제출하지 않았다. 산출물 내 local path/raw-source URL/source map/node_modules 누출을 검사했고 발견하지 않았다.

## [도구 보고]

구현자가 보고한 통과 숫자를 그대로 받아 완료 처리하지 않았다. 주요 source/build/test/HTML/assets 결과는 위처럼 별도 복사본에서 다시 실행·열람했다. 최신 main의 90 workflow 무트리거 보고, provider/registry 현재 상태, 원격 저장 계획 실행은 이번 독립 검수로 새로 확인한 사실이 아니다.

## [추정·판단]

동구 최종 원고와 local source/output 결속 범위는 통과했다. 소스 저장·현재 main owner·trusted controls·runner·실제 브라우저·provider·공개 HTTP gate를 별도로 충족해야 다음 공개 단계로 진행할 수 있다. 원고의 조건부 상담 표현을 현재 운영·반입 허용·당일 도착·무료배송 보장으로 확장하면 재검수가 필요하다.

## [미확인 및 실패]

후보 코드나 산출물의 미해결 검수 실패는 0개다. 검수 스크립트 준비 중 이전 지역 inventory의 field 키를 사용해 KeyError가 났고, 현재 동구 원본의 pointer 스키마로 수정해 전량 재실행했다. source manifest 비교에서 Git blob 필드를 빠뜨린 검수 스크립트 assertion도 전체 레코드 비교로 수정해 재실행했다. 후보 source를 수정한 것은 아니다.

아래는 수행하지 않았으며 통과로 인정하지 않는다.
- 실제 source commit/원격 readback, actual Actions run/artifact, trusted control 실행
- 실제 브라우저 모바일·데스크톱 pixels, 메뉴/키보드/focus/overflow/버튼 hit target
- provider 생성·연결·소유권·DNS/host 검증
- 공개 URL HTTP/MIME/raw byte 검사, 실제 새로운 누락 URL의 HTTP 404
- SKU/출처 외부 링크의 현재 HTTP 재확인, 실제 주문·전화·결제·재고·배송 가능 여부
- IndexNow 제출·영수증 및 실제 크롤·색인·유입

## 검증 증거와 재현

- evidence/independent-source-audit.json: 76 source·27 originals·71 template 원본 결속
- evidence/independent-output-audit.json: 두 모드의 114문구·페이지별 heading/robots/canonical·전체 파일 해시·29 negative
- evidence/independent-boundary-audit.json: 합성 계약의 false200/public-claim/predecessor 거부
- evidence/regression-results.json 및 각 .log: 직접 실행한 명령과 종료코드
- evidence/final-postcheck.json: frozen source 불변과 16/18 산출물 전체 byte parity
- replay/source/candidate/dist 및 replay/evidence/inspection-dist: 직접 생성·열람한 결과물
- verify_independent.py, verify_source.py, verify_boundary.mjs: 독립 검사기

현재 보관된 복사본은 다음 세 독립 검사기를 다시 실행해 검증할 수 있다.

python3 donggu-candidate-code-independent-20261015/verify_source.py
python3 donggu-candidate-code-independent-20261015/verify_independent.py
node donggu-candidate-code-independent-20261015/verify_boundary.mjs

전체 재빌드는 replay_tests.py의 manifest 기반 복사 및 명령 목록을 따르되 새 빈 replay 작업 폴더를 사용해야 한다. 기존 inspection-dist를 덮어쓰지 않는 것이 의도된 안전 경계다. 별도 복사본 source/candidate에서 verify-inputs, astro check/build, qa_donggu.py, private Node/Python, adapter Node tests 순으로 실행한 뒤, source 밖 evidence/inspection-dist를 생성하고 adapter/output/parity Python tests를 실행한다. test_donggu_runner_output.py는 실제 production revision을 요구하므로 이번 로컬 검사에서 실행하지 않았다.
