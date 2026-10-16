# 고흥 실제 공개 독립 검수

## 판정
ACCEPTED_GOHEUNG_ACTUAL_PUBLICATION_AND_FRESH_HTTP14. accepted=true, blockingFindings=0.
고흥 구매홈의 실제 공개 결과와 새 공개 응답14개를 수용한다. 접수·검색색인·시설 상세 또는 전체 서비스 완료를 의미하지 않는다.

## [직접 확인] 공개 응답
- https://goheung.fwith.kr/ 및 고정 CSS1·상품사진4·배너3·동일 승인 proof1·robots1·sitemap2·고유 unknown404를 별도 curl GET으로 읽었다. redirect를 따라가지 않았고 13개200/1개404/redirect0이었다. raw body/header/요청 시각/transport 결과를 모두 보존했다.
- 홈20,917bytes,404 2,420bytes가 수용 artifact 원문 SHA와 바로 일치했다. 새 응답에는 정규화할 beacon이 없었다. 이미지7·CSS·proof·sitemap2도 원문 bytes와 정확히 일치한다. 응답 Content-Type14개가 기대한 형식이다.
- robots는 원본을 수정하지 않고 검사했다. raw2,751bytes=고정 관리 prefix2,676+고흥 suffix75이며 기존 strict 검사와 일치했다. 정책 변경은 없다. _headers는 서버 설정 파일이므로 공개 GET했다고 주장하지 않는다. 공개 응답14와 고정 로컬 _headers1을 결합한15 계약을 검사했다.
- 실제 공개 원문을 기존 output 및 HTTP 검사기로 오프라인 재생했다. 홈 canonical/index,follow/social14/CTA·내부링크,404 noindex,nofollow·canonical/social 없음, 실제 unknown404 응답을 확인했다. body2/static8·전체원고87+14·상품4·FAQ2·답변4문단·사진4·배너3·ALT·배송20,000원 및 합계가 앞선 수용본과 같다. 숫자만으로 원고 품질을 새 판정한 것이 아니라 전체 bytes를 결속했다.
- root가 별도로 받은 홈 원문과도 일치했다. raw 응답을 변경하지 않고 정규화/검사용 산출은 별도 보존했다.

## [직접 확인] 실행과 원본 산출물 결속
- fresh GitHub API에서 run38948785580/job117134584476/issue409, main66c79024084b510c2c14520529a96072084afaaa, owner/triggering actor joseungil-kr, attempt1, 정확 publish workflow 및 success를 직접 읽었다. job의 모든 단계가 성공이며 제출 단계가 없다.
- fresh control commit의 직접 parent가 승인 기록 commit cf9996c42c68d05eb4644562bd188c017d641259인 것을 확인했다. fresh source branch도 d6f43be6bd5ee0239ef6485c50a59a0492b9ee3e로 고정돼 있다. activation3 저장 readback은 이전 독립 수용본과 같으며 실제 issue payload를 기존 gate로 검사했다.
- 실제 runner checkout·trusted gate·회귀74 실행 로그를 새로 읽고, selected-source/control/review 결과와 결속했다. 실제 main HEAD/승인 ancestry 통과는 runner 실행 기록과 fresh commit 관계로 확인한 범위다. 로컬 Git을 꾸며서 통과시키지 않았다.
- retained artifact12067765095의 실제 ZIP6,801bytes를 fresh API digest88b8f25b…와 직접 대조했다. 중복/경로탈출/암호화/심볼릭링크 없이12개 멤버를 CRC 검사 후 별도 안전추출했다. 이 검수에서 ZIP을 새 다운로드했다고 주장하지 않는다. 전달된 원본 ZIP을 새 API identity/digest로 독립 검증했다.
- release13은 기존 actual build38943104776/artifact12064247223/control a8725623…의 원문과 동일하다. source50/output15, prior native actual verdict81f62a37…, bounded descriptor a148e98d…가 유지된다.

## [도구 보고] 실행 중 provider 및 edge 처리
- 실제 artifact의 before는 고정 Worker/hostname 부재, attach는1회 요청 수락, after는 같은 account digest·Worker·hostname 연결 확인이다. fresh job은 단일 deploy/attach/readback 단계 성공을 보고했다. reviewer가 provider를 추가 호출하지 않았다. DNS 소유권 상태는 관찰되지 않았으며 바꿨다고 주장하지 않는다.
- runner public-http는 attempts2,14경로·404 및 beacon2 정규화를 보고한다. runner의 원시 HTML 응답2개는 artifact에 없으므로 그 bytes를 별도로 재정규화했다고 주장하지 않는다. 수용 코드가 정규화 후 정확 artifact SHA를 요구하는 것과 실제 성공 기록을 확인했고, 별도 fresh GET에서는 HTML 원문 SHA가 곧바로 일치했다. runner raw robots는 저장돼 있고 fresh 응답과 동일하다.

## [추정·판단] 품질과 수용 범위
공개 응답이 앞서 독립 시각 수용한 입력과 정확히 일치하므로 그 화면 품질 판정을 같은 본문·스타일·사진에 결속할 수 있다. 새 공개 화면 캡처는0개다. 이전 실제 PNG38개/24개 전체 viewport 비교를 다시 촬영하거나 공개 브라우저에서 보았다고 표현하지 않는다. 320px 첫 화면 CTA가 아래쪽에 있다는 비차단 한계, 긴 정책문구의 스크롤 부담은 그대로다. 실제 공개 Safari/모바일 기기, 외부 구매 링크 클릭·전화 연결·주문 이행은 확인하지 않았다.

이번 bounded 공개 범위에서 must-fix는 없다. 후속 IndexNow 접수는 별도 검수·실행·영수증이 필요하다. 코드/워크플로우에 IndexNow 기능·submit step·receipt 의존이 없고 검토한 실행의 제출은0이다. 검색색인 여부는 미확인이다. 시설6 HOLD, core/full NOT_ASSESSED 유지. SEO93/GEO90/AEO93은 앞선 한 구매홈의 편집·기술 준비평가이며 실제 검색·AI 성과가 아니다.

## 실패와 재현 기록
초기 reviewer harness는 activation readback wrapper가 request 하위라고 가정해 KeyError('request')가 났다. 실제 path/ref/response 형식에 맞춰 harness1곳만 수정했다. 초기 오류 로그를 보존했다. 출하 코드나 입력 봉인은 변경하지 않았다. 최종 독립검사308개가 통과했다.

새 GET은 fetch_public.py, 보존 응답의 오프라인 재검증은 verify_publication.py로 재현할 수 있다. fresh fetch를 반복할 때는 새 폴더를 사용해 기존 응답을 덮어쓰지 않는다. 제공 public/4파일과 PUBLIC-PACKAGE.json은 원격 저장 후보이며 이 검수에서 저장하지 않았다.
