# 담양 r1→r2 소스 변경 독립 검토

판정: R2_EXACT_SOURCE_AND_REBUILT_OUTPUTS_VERIFIED_FOR_SEPARATE_RELEASE_CONTROLS_REVIEW

이번 문서는 별도 r2 변경 검토다. 기존 r1 독립 코드검토와 잠정 제어검토를 수정하지 않았다. 원래 검토자가 r2를 재실행했다고 주장하지 않는다. 최종 출시 승인 또는 공개 성공 증거가 아니다.

## [직접 확인] 확인된 결과

- 정확한 r2 ZIP을 빈 검토 디렉터리에 추출했다. 소스 80 = private65 + adapter15이며 모두 바이트·크기·manifest와 대조하고 테스트 후 다시 확인했다. 작성자 dist·evidence·생성된 출력 fixture를 복사하지 않았다.
- 기존 lock 일치 dependency cache만 연결하여 10명령을 새로 실행했다. 실제 로그의 테스트 수는 private Node73, private Python81, adapter Node36, adapter Python30, output Python63, Node/Python parity1, runner-output60으로 총344개다. 전부 exit0이며 건너뛴 단계는 없다. dependency 설치나 업그레이드는 하지 않았다. cache 전체 전이 package 바이트를 독립 감사한 것은 아니다.
- 별도 독립 검사95개와 거부변이65개를 확인했다. immutable native r2 정책자료, 기존 r1 이력, supplementary6+1, 원고의 완전한 시각문단, B060 구분, 공개검증·점수 승격 금지, 실제 HTML상의 누락·확정 도착 주장 변이를 포함한다.
- r1→r2 소스는31 수정·9 추가·3 제거다. 삭제된 r1 소스 projection 항목을 원본 검토 삭제로 보지 않는다. 원본 r1 코드검토12파일과 native r2 원고검토73파일 안의 prior/r1 원고34파일을 그대로 보존했다.
- 고객 JSON 변경은 /home/sections/4/afterList/1 한 곳이며 나머지99문구는 동일하다. 원래165/24/16/3 분모와 null 점수를 유지하고 상단6조항·적용범위 미확정1개를 별도 분모로 결속한다.
- renderer·components·layout·pages·CSS·7개 이미지자산·dependency 파일은 r1과 바이트 동일하다. 실행/검증 코드가 모두 그대로인 것은 아니다. 아래7개 executable/test 파일의 차이를 별도로 읽고 검사했다.
- private14와 production-like16을 새로 생성하고 작성자 결과와 전부 바이트 비교했다. r1의 대응 출력30파일과도 비교했다. 허용 차이는 홈의 승인 문단1개와 HTML2개의 data-copy-sha 표시값뿐이며 다른 모든 바이트는 같다.
- r2 내부 private→production-like 전환은 HTML body2·정적 자산9가 바이트 동일하고 허용된 head 변경만 있다. HTML은 home+404 두 개, indexable/sitemap URL은 홈1개, XML은2개다. 홈 상품4·사진4·배너3·이미지7·FAQ4, 배송비+10,000원과 참고69/89/119/159천원, 최종가null을 확인했다.
- 공개 HTTP15경로는 생성물에서 도출한 계획이다. 실제 요청하지 않았다. 실제 브라우저·모바일 픽셀도 검사하지 않았다.

## 실행 코드 변경과 검사 위치

1. candidate/src/lib/damyang-runtime.mjs:8–9,25–55,77–78: r2 copy/manifest/review pins, required originals33와 projection32, native supplementary6+1/원점수null/미실행 플래그, r1 원본 및 한정 supersession, 완전한 timing paragraph 검사 추가. 기존 price/route/CTA/private boundary 검사는 유지했다.
2. candidate/scripts/qa_damyang.py:25,68–77: r2 copy/manifest pins와 완전한 timing paragraph invariant 추가. JSON→실제 HTML projection 검사 유지.
3. candidate/tests/damyang-runtime.test.mjs: 기존67개에 timing6개 추가, 실제73개 실행.
4. candidate/scripts/test_damyang.py:95–100: 기존75개에 실제 HTML timing6개 추가, 실제81개 실행.
5. release-adapter/scripts/damyang_adapter.py:14–17: private count65 및 manifest/tree/contract pin만 변경.
6. release-adapter/scripts/damyang_release.mjs:7,16–17: required-input pin과 private count/tree pin만 변경.
7. release-adapter/scripts/damyang_release_output.py:11: rebuilt equivalence pin만 변경.

3개 adapter 실행 파일은 SHA256값과 private-file count를 정규화한 뒤 r1과 전부 동일함을 추가 확인했다. 전체 실제 diff는 r1-r2-complete-source.diff에 있다. 검토된 원본 자체는 수정하지 않았다.

## [도구 보고] 보존한 내용 판단

native r2 원고 검토자는 같은 상품 이미지의 상단과 하단 시간 안내, B060의 별도21시 조건, 적용범위 미확정성을 함께 보존했음을 보고했다. 이번 소스 검토는 그 원본 package bytes와 소스·생성 HTML의 정확한 연결을 확인했다. 정책 이미지의 픽셀이나 현재 merchant page를 새로 열람했다고 주장하지 않는다. 두 안내의 우선순위 또는 실제 도착일은 여전히 확정할 수 없으며 새 정책변경도 주장하지 않는다.

## [추정·판단]

이 정확한 소스 변경 범위에서 남은 필수 소스 수정은 발견하지 않았다. r2는 기존 구조·사진·금액·기술 경계를 유지하면서 승인된 문단 및 native 보충 검토를 결속한다. 문단이 길어진 만큼 실제 모바일 가독성·전체 문단 노출은 별도 browser/pixel 검토 대상이다.

## [미확인] 다음 필수 단계

- 실제 source commit/tree 원격 readback 및 별도 authorization/control binding
- 정확한 r2 control snapshot의 최종 독립 재검토와 전체 재실행
- 실제 Actions build/capture run 및 retained artifact ID/digest
- 320/390/1280 실제 화면·버튼·키보드·완전한 정책문단 가독성/노출 검토
- provider 대상/소유권, 공개 HTTP·실제404·managed robots·proof, IndexNow 영수증

sourceRevision/sourceTree의 실제 Git 식별자는 이 검토에 null로 남긴다. 원격 성공을 synthetic local 값으로 채우지 않는다. 원격 쓰기0·provider0·browser0이며 출시 승인은 별도다.

## 검증 증거

- source-delta-binding.json / source-delta-review.json: 이 검토의 native binding과 판정
- source/private/adapter-manifest.json: source80/private65/adapter15 정확한 파일 명세
- reproduction.json 및 logs/: 새 ZIP-only10명령344테스트. 공개 로그에서 환경 로컬 경로만 치환했다.
- independent-observations.json / delta-semantics.json: 독립95확인·65거부, 실제 output30 비교
- source-delta.json / r1-r2-complete-source.diff:31수정9추가3제거와 executable7 변경
- manuscript-delta.json / manuscript-r2/: 한 문구 변경 및 native73파일, 원본r1 보존
- prior-r1-code/: 원래 독립 코드검토12파일의 변경 없는 바이트
