# r4 H2 줄바꿈 QA successor: 별도 읽기 전용 검수

기존 run38986793903/control7186/source973의 source·내용·바이트·기능 검수는 역사로 보존한다.320px H2 글자 범위 넘침은 HOLD이며 새 r4 화면 수용으로 이전하지 않는다.

현재 source7260f8d0c77b05cde16ed5b7de1b775313bfc1dd, project tree da696730d6dcedb4dd1262c179af4430307cb9bf, 단일 parent97382615bf24f164f097f323295f495b84561f8d를 고정한다. 기존973은 r3 역사이며 r4로 간주하지 않는다. 저장된 r4 source의 독립검수 JSON26b9ce71…와 검수 입력 f866bd62…를 별도 고정한다. source·로컬 producer 수용만 결속하며 새 native/pixel/public 승인은 없다. 이 controls 자체의 독립검수는 여전히 필요하다.

범위는 source의 corrector+spec2개뿐이다. 원85/private75, 기존 정책 operations52, 이미지7을 보존한다. 원 CSS16876B에 정확한41B `.copy-section h2{overflow-wrap:anywhere}\n`만 추가한16917B 새 CSS를 만들고4HTML stylesheet href만 새 이름으로 바꾼다.18개 산출물 중 nonHTML13은 동일하고404는 revision+stylesheet href 외 보존한다. 원본HTML·원본CSS와 고정spec에서 기대값을 독립 생성하며 관찰한 후보DOM을 기대값으로 사용하지 않는다.

기존 owner/main/firstattempt/exactissue/body/sourcebranch, credential-free, original baseline/private/native gates, genuine Astro preview,4routes×320/390/1280, real404, 이미지·전화href·메뉴·Back/Forward·keyboard·overflow 검사는 유지한다. title만 r4 request로 별도 구분한다. source의 원472→r3→r4 계보와 r3대비 exact2 delta를 추가 결속한다.

추가 검사는 모든 `.copy-section h2`의 각 문자 Range를 카드 내부 padding·viewport·clipancestor 경계와 비교한다. 실제 글리프 잉크는 Range와 동일하지 않을 수 있으므로 독립 픽셀검수가 여전히 필요하다. 실제 header/하단 stickyCTA를 그대로 두고 자연 스크롤만으로 제목·FAQ의 모든 텍스트라인이 가림 없이 보이는 보충 viewport를 기록한다. 모바일4routes×2폭의 실제 메뉴 열린 screenshot도 남긴다. DOM변경·CSS주입·UI숨김·sandbox우회는 없다.

production-binding.json의 승인 필드는 변경하지 않은 역사 생산자 스키마를 위한 기술적 빌드 호환 입력이다. 과거 authorizationEvidence는 새 교정 내용, 새 실행, provider update 또는 IndexNow의 승인이 아니다. qa-scope.json과 모든 산출물은 배포권한 없음 및 IndexNow 미실행을 명시한다. 현재 namespace에 게시 기능·provider API·IndexNow 호출은 없다.

이 준비는 main저장·issue·Actions·provider·공개 update·IndexNow 승인이 아니다. main 반영과 owner issue 작성은 별도 root 검수·lease 이후에만 수행한다. 실제 Actions/브라우저/독립 픽셀검수 성공은 로컬 정적 테스트 통과와 별도다. 로컬 Chromium 시작 권한 문제를 우회하지 않는다.
