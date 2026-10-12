# 공통 배너와 HTML 구조 기준

적용 범위: fwith.kr의 지역별 고객용 홈페이지·목록·상세 페이지와 이후 신규 페이지. 관련 없는 서비스와 blog.fwith.kr은 이번 배너 배포 대상이 아니다. 기존 본문, 상품, 출처, URL, 전체 글 수와 보류 상태를 보존한다.

## 승인된 이미지 정본

세 이미지는 지역에 관계없이 같은 파일을 사용한다. 지역명·시설명·검색어를 이미지나 파일명·alt에 억지로 추가하지 않는다. 원본은 AI 생성 분위기 이미지이며 실제 판매상품 사진이나 현장 납품사진이 아니다. 디자인·문구·비율을 바꾸지 않는다.

| 파일 | 크기 | SHA-256 |
|---|---|---|
| flower-message.webp | 1774 × 887 | b8d973861fe81839ec7765d9dd506deb9d1055614c200479aa72a632cf0c5253 |
| flower-budget.webp | 1774 × 887 | bc782e91dadd7d07840ea9cbe6154fb21941dd7f9bf32c53bb2991bc301439df |
| flower-consultation.webp | 1774 × 887 | 4cae6c69e4c6549ed277fd3b2acc32c9a797a570de194bc48a6045b50f28283b |

WebP quality 90 포맷 압축만 적용했다. 합계 379,610바이트이며 원본 크기와 구도·문구를 유지한다. 각 소스의 src/data/shared-banner-manifest.json에서 PNG 원본 SHA와 비교한다.

## 공통 컴포넌트와 배치

SharedFlowerBanner.astro와 public/images/shared-banners의 정본을 재사용한다. 이미지마다 구체적인 alt를 쓰고 width=1774, height=887, 반응형 width:100% / height:auto, loading=lazy, decoding=async를 포함한다. 첫 화면의 주요 이미지에는 무조건 지연 로딩을 적용하지 않는다. 이 공통 배너는 기존 hero 이후의 본문 흐름에 놓인다.

홈·목록·상세의 내용 흐름 사이에 message → budget → consultation을 분산한다. 본문·상품·목록·출처와 같은 실질 콘텐츠를 사이에 두고 세 장을 연속으로 쌓지 않는다. 본문과 상품 정보는 텍스트로 남기고 이미지를 제목이나 설명의 대체재로 사용하지 않는다. 404와 검색 제외된 빈 목록에는 마케팅 배너를 넣지 않는다.

## 제목·검색 기본 구조

- 고객 HTML에 H1은 정확히 하나. 내용의 H2와 하위 H3의 순서를 지킨다.
- 배너는 figure/img/figcaption으로 작성하고 장식 이미지에 별도 H1/H2를 추가하지 않는다.
- 출처 영역은 H2 ‘출처 및 확인 정보’ 하나로 묶고 출처명은 H3 또는 문단으로 둔다. 원래 출처 URL·이름·확인일은 보존한다.
- 고유 title, meta description, 자기 URL canonical, robots, sitemap 일치, 내부 링크, 모든 이미지 alt를 실제 생성 HTML에서 검사한다.
- 이미지 요청의 HTTP 200, image/webp MIME, 승인된 SHA를 공개 주소에서 재확인한다.
- 기술 검사 통과를 검색 순위나 실제 색인 성공으로 표현하지 않는다.

## 검증과 배포

코드 작성만으로 완료 처리하지 않는다. source test, 실제 static build, qa_shared_banners.py, 잘못된 src/variant·canonical·자산·heading·alt를 거부하는 negative test를 실행한다. 실제 고객 HTML 경로 전체를 분모로 유지하고 noindex/404 제외 사유를 남긴다.

소규모 canary부터 공개 배포하고 원격 source SHA, Actions run, 공개 HTTP/자산 SHA, heading·메타·배너, 기존 본문 보존을 검증한 다음 동일 패치를 전파한다. 현재 공개 branch와 미배포 문체교정 branch를 혼동하지 않는다.

기존 사이트 업데이트는 정확한 계정/Worker/hostname/이전 공개 revision을 GET으로 확인한 뒤 기존 static assets만 업데이트한다. 초기 생성 guard는 보존한다. 업데이트를 위해 새 Worker 생성, hostname attach, DNS 소유권 변경, secret/권한 변경을 하지 않는다. source 코드가 provider credentials와 함께 실행되지 않도록 기존 분리 빌드·정적 산출물 경계를 유지한다.

IndexNow는 검증된 실제 sitemap URL 집합을 제출하고 접수 영수증을 남긴다. 접수를 실제 검색 색인이나 순위 성과라고 주장하지 않는다. 접근 실패·실행 취소·화면 검증 누락은 수행됨·미검증 또는 확인 불가로 구분한다.

### 과거 검수 증거와 현재 변경 검증

과거 전체 파일 hash에 결속된 검수 증거는 덮어쓰거나 통과시키기 위해 완화하지 않는다. 정당한 배너 변경은 원본 bytes·기존 SHA를 별도 보존하고, 승인된 추가 변환을 원본에 적용한 결과가 현재 파일 전체와 정확히 같음을 검사한다. 과거 검사의 통과는 기존 승인 내용 보존을 뜻하며, 현재 코드의 동작 검증을 대신하지 않는다. 현재 source의 원문 검사와 잘못된 변경을 거부하는 테스트, 실제 build HTML 검사, 고정 publisher의 package/artifact 검사를 함께 통과해야 한다.

trusted targets manifest에 결속된 배너 revision은 기존 사이트 업데이트 모드로만 공개한다. 같은 revision을 일반 초기 발행 모드로 보내면 거부하고, 검증 전 배포 재실행이나 이슈 중복 생성을 하지 않는다. 기존 noindex 고객 페이지와 404는 전체 경로 분모에 남기되 배너 제외 이유와 경로를 따로 기록한다.

### 지역 목록의 실질 콘텐츠 분산

지역 목록에서는 구역 수가 아니라 펼쳐진 실제 페이지 카드 수를 기준으로 budget 배너를 중간에 놓는다. 접힌 details/summary 한 줄만으로 두 배너 사이 콘텐츠를 확보했다고 판단하지 않는다. 기존 카드 순서·본문·H2·링크와 InlineOrderBanner의 상대 위치를 보존한다. 페이지의 원래 배너 적용/noindex 조건을 바꾸지 않는다.

검수된 기본 구현은 안양 source dd0b91d58dff3c267cf2216c9a9d4bdf328e29c8의 src/components/RegionDirectory.astro 및 src/lib/directory-banner-split.mjs이다. helper SHA-256은 04ed49395e2a3458c9b01c74eff57f425ed693e9f713b59bfe7343a4c433a19c이다. 적용 요청이 true인 실제 카드 2개는 1/1로 나누고, 0/1개는 명시적으로 실패시킨다. 원래 적용 요청이 false이면 배너 0개를 유지한다. 실제 페이지의 기존 items.length >= 3 조건을 helper의 경계 조건으로 바꾸지 않는다.

새 페이지 제작 시 helper 단위시험과 scripts/qa_directory_spacing.py, scripts/test_directory_spacing.py를 build/qa에 연결한다. 실제 HTML에서 순서가 유지된 카드가 message–budget과 budget–consultation 사이에 각각 최소 1개 있는지 확인한다. 기존 공개31곳의 이전 revision은 별도 후속 배포 전까지 그대로이며, 새 구현의 로컬/소스 검수 결과를 그 공개 페이지에 적용됐다고 표현하지 않는다.

