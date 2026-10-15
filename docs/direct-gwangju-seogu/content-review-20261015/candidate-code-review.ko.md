# 광주 서구 동결 로컬 후보 독립 검수

[직접 확인] PASS_FROZEN_LOCAL_SOURCE_AND_OUTPUT_ONLY. 필수 수정 0개. 검수 범위는 동결된 79개 소스의 별도 복사본과 실제 로컬 빌드·정적 산출물이다.

## 확인된 결과

- 코드 12240 / 전국 순서 32 / namespace gwangju-seogu. 예정 주소 https://gwangju-seogu.fwith.kr. 실제 공개 주소로 확인한 것은 아니다.
- source79 / private64 / adapter15 파일과 3 manifest를 전체 재해시했다. 빌드 전후 원본·복사본 모두 동일하다.
- 최종 원고·render-plan·review·binding은 원래 스키마와 verdict 그대로 검증했다. 정정 closure r2를 기준으로 확인했고 이전 closure는 중간 이력이다.
- Astro check 13파일, error/warning/hint 0. 전체 회귀 266개 및 별도 독립 negative 80개 통과.
- 두 모드 각각 114문자열, 모든 버튼·제약 문구·alt·aria, 4상품·3FAQ·승인 배너3종을 실제 HTML에서 대조했다. 이미지7개를 실제 열어 보고 SHA/MIME/규격도 검사했다.
- budget→facility-guide 흐름, H1/H2/H3, breadcrumb 및 support inbound1 일치. facility-guide는 ID로 찾으며 0개/복수/잘못된 ID·카드 형태를 거부한다.
- 국빈 공식 출처 HTTP 정확 URL 1개만 허용한다. 호스트/경로/쿼리/대소문자/포트/fragment/userinfo/encoding 12개 변형은 실제 LINK_SAFETY gate에서 거부됐다. 보안 설정·브라우저 경고 우회 없음.
- private 원점·canonical null 및 noindex. 별도 offline production-like 원점의 14개 OG/Twitter tag, B201 500×500 summary, 404 canonical/social 예외, 정확 headers/robots/sitemap2 일치.
- 4개 body·9개 정적 자산 byte parity, production-like18파일 inventory 일치. 공개 산출물의 전체 문구·파일 범위가 검수 원본과 일치하며 연구 원본·부고 기록·쿠키·내부 절대 경로 없음.

## 검증 증거

- source tree: 0e7c01bb8a7d296580758f7bd4c8eea4d4d88f6aae3a8d83be19d429c5fb97a0
- private tree: bdb1d5457de356432b988b7e125cb2b7c8d504c854719d7483be78952623e27d
- adapter tree: 53598bce7a6c18fbf1b940cc994896a2479e3ea87dc2824e264be5a6e61da189
- source manifest SHA256: ddf26ac1408f615515c91a286dccb19d53be83bd0a298cebeeaf7df5b5ff814e
- independent-code-review.json, implementation-code-review-binding.json 및 evidence의 원본/산출물/negative/회귀 로그에 파일별 증거가 있다.

## 실패와 복구

검수 실행 래퍼가 첫 비동기 세션 ID를 표시하지 않아 중복 검사에서 기존 inspection 디렉터리 충돌이 있었다. 첫 산출물을 보존한 뒤 추적 가능한 세션에서 전체 명령을 재실행했다. 두 산출물 모두 같은 바이트임을 확인했다. 후보 소스 수정은 없었다.

## 미확인 및 경계

실제 commit·Actions·브라우저/화면·클릭/키보드·공개 HTTP·실제404·provider 소유권·managed robots prefix·IndexNow는 이 검수에서 확인하지 않았다. 원본 이미지 확인과 정적 문구 가시성 검사를 실제 화면 검증으로 간주하지 않는다. separate capture-control projection은 source79 범위 밖이다. 배포 승인 또는 production PASS가 아니다. sourceCommit=null, publicationEligible=false이다.

## 재현

기존 설치 캐시만 사용하며 추가 설치·네트워크·원격 쓰기는 없다. 깨끗한 새 형제 디렉터리의 evidence 디렉터리를 만들고 이 검수의 replay_tests.py, verify_source.py, verify_independent.py, verify_boundary.mjs, verify_specific_negatives.py를 복사한다. 다음을 순서대로 실행한다.

1. PYTHONDONTWRITEBYTECODE=1 python <새 검수 디렉터리>/replay_tests.py
2. PYTHONDONTWRITEBYTECODE=1 python <새 검수 디렉터리>/verify_source.py
3. PYTHONDONTWRITEBYTECODE=1 python <새 검수 디렉터리>/verify_independent.py
4. node <새 검수 디렉터리>/verify_boundary.mjs
5. PYTHONDONTWRITEBYTECODE=1 python <새 검수 디렉터리>/verify_specific_negatives.py
6. PYTHONDONTWRITEBYTECODE=1 python <새 검수 디렉터리>/verify_source.py

replay_tests.py는 pin된 source manifest의 79개 파일만 복사하고 설치 캐시를 연결한다. 기존 inspection 디렉터리를 덮어쓰지 않으므로 반드시 새로운 검수 디렉터리에서 시작한다. manifest·원고·검수 원본이 바뀌면 실패한다.
