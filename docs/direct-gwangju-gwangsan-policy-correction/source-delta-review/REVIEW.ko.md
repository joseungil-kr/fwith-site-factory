# 광산 정책 한 문단 소스 변경 독립 검수

## 판정
이 정확한 amendment 소스와 로컬 재생성물은 별도 기존 호스트 수정 배포 제어 검수로 넘길 수 있다. 소스 범위의 차단 결함은 발견하지 않았다. sourceRevision은 null, publicationEligible과 pendingFindingResolved는 false다. 이전 독립 코드 검토자가 이번 소스를 재검수했다고 주장하지 않는다.

## [직접 확인]
- 보존된 GitHub 원격 응답74개에서 원래 commit654dafd7의 URL·Gitblob·base64와 소스 바이트를 다시 대조했다. 새 원격 요청은 하지 않았다.
- 승인 원고 native17파일, 원고→소스11개 정확한 projection, 원래 코드 검토5파일+allowlist를 확인했다. 원래 inputs와159지침/24정책/2시설/117문구 분모·null 점수는 그대로다. 별도 상단6조항+미확정 관계1만 추가 맥락이다.
- 고객 JSON 변경은 /detail/sections/4/afterList/0 하나다. 다른116표시문구는 같다. visible117/context117의44번 행, timing질문, 정책요약과 copySHA 결속만 바뀐다. 원래 검토물은 덮어쓰지 않았다.
- ZIP05c81e34…ce92c를 빈 검토 디렉터리에만 추출했다. 원저자 dist·evidence·fixture를 복사하지 않고10명령을 새로 실행했다. 283테스트(73+88+36+30+55+1), 독립80확인과32거부 검사가 통과했다. 원저자/검토자 소스92바이트는 전후 동일하다.
- 실제 소스92=private77+adapter15. 기준 소스 대비11수정/18추가/0제거이며 실행 코드·테스트8파일이 바뀐다. 템플릿·레이아웃·CSS·패키지/lock·7이미지는 바이트 동일하다.
- 새 private16과production-like18 전체34파일이 원저자 결과와 바이트 동일하다. 기준654dafd7의 보존된 출력과도 비교했으며 수완 상세의 완전한 승인 문단1개와 HTML4개의 data-copy-sha만 다르다. 나머지 모든 바이트는 같다.
- private→production-like body4·static assets9가 동일하며 허용 head4만 변경된다. HTML4, sitemap2 URL, FAQ4·상품4·이미지7·배너3 구조가 유지된다. 새 문단은 상세에1번 표시되고 다른3HTML에는 없다. 광산 배송비 상담/최종가 미정도 그대로다.

## 코드 변경 위치와 검증
1. candidate/src/lib/donggu-runtime.mjs:8–16,27–63,94: 별도 amendment와 한 leaf invariant, original/native review bytes,117문구/context,6+1/null/미실행 flags 및 전체 timing 문단을 검사한다.
2. candidate/scripts/qa_donggu.py:14–16,31,82–95: 별도 resolved copy와 pinned manifest를 읽으며 기존 DOM projection 검사는 유지한다.
3. candidate/tests/donggu-runtime.test.mjs:32–42, candidate/scripts/test_donggu.py:99–104: timing 누락/변조6개씩 추가했다.
4. release-adapter/scripts/gwangsan_adapter.py, gwangsan_release.mjs, gwangsan_release_output.py: 기존 코드와 비교해 정확한 hash/count 재결속만 바뀐다.
5. release-adapter/scripts/test_gwangsan_adapter.py:6: 실제77개 소스 개수 assertion만 바뀐다.

독립 부정검사는 native review 점수·scope·가짜build/public/publication/finding해결, 원본검토 변조, second customer leaf, context/manifest 누락·중복·경로 이탈·재해시 공격을 거부했다. 실제 생성HTML timing7변형과 production canonical/robots/body/proof4변형도 거부했다. 보안·호스트/계정 변경이나 provider 호출은 없다.

## [도구 보고] 내용 근거
원고 검토자는 상품 이미지 상·하단 고지를 함께 보존하고 B06021시 조건을 구분했다고 보고했다. 이번 소스 검토는 원고의 정확한 bytes와 출력 연결을 직접 확인했다. 원문 정책 이미지 픽셀이나 현재 상품 페이지를 새로 봤다고 주장하지 않는다. 두 고지의 적용범위/우선순위나 실제 도착시간을 추론하지 않으며 새 정책변경도 주장하지 않는다.

## [추정·판단]
검사한 정확한 소스에 추가 필수 수정을 요구하지 않는다. 긴 문단의 실제 모바일 가독성과 전체 노출은 후속 화면 검토가 필요하다. inherited Node test 제목에59가 남지만 실행 guard와 manifest는77을 강제한다. 과거 원본 문서의 표현은 현재 amendment 기록과 구분해 읽어야 한다.

## [미확인] 남은 필수 단계
- 새 source commit/tree와 정확한 readback, 새 소스에 결속된 별도 제어/승인.
- 기존 호스트 content-successor 경로의 current-main 해시 검증 및 독립 제어 검토. 최초 게시 target-absent guard를 완화하거나 그대로 수정 배포에 재사용하면 안 된다.
- 실제 Actions run/artifact/receipt,320/390/1280 화면의 문단·버튼·키보드·404 검토.
- 같은 provider account/hostname/소유권 및 기존 배포 identity 보존, 공개 후 body/asset/HTTP/real404와 update영수증 검증.

기존 게시/완료기록은 그대로 보존한다. 이 검토는 신규 게시 승인이나 이미 운영 중인 사이트 수정의 완료를 뜻하지 않는다. 사용한 dependency cache의 최상위4패키지는 lock과 일치하지만 전이 의존성 설치 바이트 전체를 새로 감사하지는 않았다. 검토 count parser의 Node 출력prefix 불일치는 검토 스크립트만 고친 뒤 전체80/32검사를 다시 실행해 해결했다. 원본 코드 수정·우회·테스트생략은 없었다.

## 검증 증거
source-delta-binding.json과source-delta-review.json이 native binding과판정이다. source/private/adapter-manifest.json에 정확한92/77/15가 있다. reproduction.json과logs/는 새10명령283테스트, independent-observations.json은80/32검사와34출력 비교다. complete-source.diff와source-delta.json이 모든 변경, manuscript-binding.json이 한 leaf와파생물 변경, saved-base-readback.json이 보존된74원격응답 대조다. native-amendment/와prior-code/의 원본 바이트/저자 귀속은 그대로다.
