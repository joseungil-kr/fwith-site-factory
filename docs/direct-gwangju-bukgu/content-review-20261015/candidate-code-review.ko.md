# 북구 독립 구현 코드 검토

[직접 확인] source 83개(private 68 + adapter 15)를 새 사본에서 재빌드하여 10명령·268 tests를 통과했습니다. 추가 출력 부정시험111건과 runtime38건도 통과했습니다. 268과111·38은 서로 다른 검사 분모입니다.

- 독립 HTML parser로115문구·4 SKU·FAQ3·홈/상세 배너3·내부링크·heading·메타·support noindex·sitemap2·404 예외를 검사했습니다.
- 상세 순서 products → ribbon → budget → facility → order를 확인했습니다. stable ID renderer와 CSS·레이아웃·7자산·의존성은 기존 원본을 재사용합니다.
- private16/offline18파일은 원작성자 산출물과 모두 같은 bytes입니다. 모드 간 HTML body4·static assets9도 같습니다. 상품4사진과 배너3개의 실제 픽셀을 열었습니다.
- HTTP 출처 두 개는 그린 운영자 /page/page3와/page/sub006 정본만 source영역에서 사용합니다. 추가48 URL변형과4개의 다른용도·문맥 변형을 모두 거부했습니다. 보안경고를 우회하지 않았습니다.
- 원고51·닫힌 검수77·projection26·정식참조14를 재해시했습니다. 원래154 지침행·15 정책조건·1 시설항목 및 manuscript-only 판정은 그대로 보존했습니다.
- Namgu82 source와 저장 readback을 Git tree에 대조했고 전체18806행·noncopy1210행 diff를 재생성했습니다.29파일이 byte-identical입니다.
- source tree SHA256: 757ec67969fea73236773222f97aad9e37f29fad5ebf5851ee96af27c12d1c08

[도구 보고] fresh main GET은4fb255a…이며 해당 commit의 Namgu·Seogu workflow본문2개를 다시 열어 Git blob을 검산했습니다. Namgu82파일의 commit 연결은 보존된 GitHub tree응답이고 실제 로컬 bytes를 독립 재검산했습니다.

[추정·판단] 검토 범위 내 필수 수정은 없습니다. 정확한 source83 및 이번 검토 원본을 결속해 다음 source저장 단계로 진행할 수 있습니다.

[미확인] 북구 실제 source commit/readback·trusted controls·Actions·브라우저/모바일 화면·provider·공개HTTP/real404·IndexNow는 별도 gate입니다. 이번 판정은 로컬 source저장 준비이며 공개 완료가 아닙니다.

공개용 검토 파일은 PUBLICATION-MANIFEST.json의 정확한 목록만 사용합니다. raw logs·스크립트·복사한 source·연구 원문은 이 공개용 검토 목록에 포함하지 않습니다. 원본 독립검토와 binding은 동결 후 덮어쓰지 않습니다.
