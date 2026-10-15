# 광양 로컬 candidate 독립 코드·출력 검수

판정: **PASS_LOCAL_CODE_AND_OUTPUT_ONLY**. 검수한 freeze에 대한 필수 수정은 발견하지 않았다. 이 판정은 원격 저장·Actions·브라우저·배포 완료 판정이 아니다.

## [직접 확인] 검수 대상과 원본 결속

- 저장소 대상: `joseungil-kr/fwith-site-factory`, 광양시 공식코드 `12190`, 전국 순서 `30`.
- 실제 검수 대상은 `gwangyang-local-implementation-20261015/source`의 71개 파일이며, 별도 `replay/source` 복사본도 전부 동일하다.
- 71파일 tree SHA256: `6d5436097aeebb5acf242c042635d293f5c19a72779815d0bd5e5ddbb84ee753`.
- private 56파일 tree SHA256: `b751a75d19f313433682ab131849edb3d725ece4dedfce2cc0013ef99a6a01a3`.
- adapter 15파일 tree SHA256: `bced0975298eaabb71384e9835d24789f3ffc8eab39abca8b23d39ed1fb65916`.
- 정본 customer-copy SHA256: `45a635ec0fff5c94a990814dfdd52b7a844687d558e5e7fcba29f8eba26b10cf`.
- render-plan SHA256: `b97eb621fced61c67596a6ba9c8e1f765dc7e0e0e3189da66d0821bdb3bf8c6d`.
- 독립 원고 binding SHA256: `dd0224d247acb8a7861736950d51d14b07806f6700697f2044a1f98038cbbb76`.
- 나주 템플릿 원본 69파일의 실제 로컬 내용을 읽어 Git blob SHA1을 재계산하고 보관된 GitHub recursive-tree 원본의 `21ebc3cffc12df8977e8209bc4fc3139e084fa8b` 항목과 일치시켰다. 이번 검수에서 새 원격 조회를 수행한 것은 아니다.
- package-lock의 프로젝트명 차이를 제외한 dependency graph가 나주 원본과 같다. 설치 없이 이미 존재하는 node_modules만 재사용했다.

## [직접 확인] 실행과 생성 결과

- 별도 복사본에서 실제 Astro typecheck/build를 다시 실행했다. 13개 Astro 파일 진단은 오류 0, 경고 0, hint 0이다.
- private 실제 출력 16개, 오프라인 production형 검사 출력 18개가 생성됐다. 원래 구현자의 최종 출력과 모든 파일의 SHA256이 일치한다.
- 회귀 236개를 재실행했다: private Node 51, private Python 63, adapter Node 36, adapter Python 30, output Python 55, Node/Python 변환 parity 1. 모두 exit 0이며 생략·실패가 없다.
- 구현 QA 모듈을 가져오지 않는 별도 lxml/Pillow 검사를 작성했다. 정본 inventory의 117개 문자열을 JSON pointer로 다시 읽고 두 출력 모드의 실제 HTML 본문·접근성 이름·alt·head와 결속했다.
- detail FAQ 3쌍은 h3 질문과 바로 이어지는 답변으로 각 1회 존재한다. SKU 4개, 각각의 기본가·별도 10,000원 배송비·정확한 SKU 링크·사진 alt를 확인했다. 상품 안내 문장은 1회다.
- 승인된 세 배너는 home/detail에 각각 3개, support/404에는 0개다. 7개 원본 이미지의 byte 일치, SHA, JPEG/WebP 디코딩, 500×500/1774×887 치수, lazy/async 속성을 확인했다. 새 이미지 생성이나 변형은 없다.
- support의 비자기 inbound는 detail breadcrumb에서 오는 1개이며, detail은 home/support에서 연결된다. breadcrumb 본문·순서·aria-current·label·자기링크 금지, 모든 로컬 fragment, H1 각 1개, H2/H3 계층을 확인했다.
- preview는 모든 HTML에 `noindex,nofollow,noarchive`, robots `Disallow: /`, empty sitemap, global noindex header가 정확하다. canonical/절대 social URL은 없다.
- production형 오프라인 출력은 home/detail `index,follow`, support/404 `noindex,follow`다. home/detail/support에는 자기 canonical과 OG/Twitter 14개가 정확히 있다. 승인 B201 사진·500×500·summary card를 사용한다. 404는 canonical·OG·Twitter·제품·배너가 없다.
- production형 robots는 두 indexable 경로를 허용한다. sitemap-index가 참조한 sitemap-0의 실제 URL은 home/detail 2개뿐이다. `_headers`는 정확히 `/*\n`이다.
- private/production형 출력에서 4 HTML body와 정적 자산 9개가 byte-identical이다. head·robots·sitemap·headers·기존 proof만 계획된 방식으로 달라진다.
- 별도 negative 8개도 실제 출력 복사본에 적용해 거부를 확인했다: support inbound 손상, FAQ 숨김, H3 계층 변경, Twitter 누락, header 삽입, 원고 변경, 제3자 raw 원본 추가, orphan XML 추가.
- 공개 산출물 파일 집합을 정확히 제한하고 `/workspace`, `/tmp`, file URL, loopback 주소, raw.githubusercontent.com, node_modules, source-map 경로 누출이 없는지 검사했다. 71 source 파일에도 제3자 HTML/PDF/CSV 원문은 포함되지 않는다. 고객용 출처 링크는 의도된 내용이다.

## [미확인] 이 결과에서 승격할 수 없는 항목

- 광양의 실제 원격 source commit/branch, trusted Git pre/post 검증, 실제 GitHub Actions run/artifact는 없다.
- `local-inspection` 및 합성 `aaaa…` revision은 로컬 검사용 값이며 실제 commit/승인 증거가 아니다. production 승인 URL 형식·binding 계약 테스트가 실제 승인 검증을 대신하지 않는다.
- 브라우저를 실행하지 않았다. computed CSS, 화면·mobile/desktop overflow, 메뉴 열기·닫기, 실제 keyboard/tap/전화/구매 동작은 별도 검증이 필요하다. HTML·CSS에서 숨김 여부를 검사한 사실을 실제 시각적 검증으로 표현하지 않는다.
- `https://gwangyang.fwith.kr`은 코드에 제안된 origin이다. 도메인 소유·충돌·provider 연결·공개 응답은 이번 작업에서 확인하지 않았다.
- 404.html 파일의 내용과 메타데이터는 확인했으나 실제 missing route의 HTTP 404는 미검증이다. 서버가 404를 제공한다는 보장은 없다.
- public MIME/status/hash, 실제 상품 endpoint 최신 응답, IndexNow 제출·영수증·색인/검색노출도 확인하지 않았다.

## 재현 및 증거

- `python3 verify_independent.py`: 독립 117문자열/DOM/자산/metadata/graph/negative 검사.
- `replay/source/release-adapter/scripts/gwangyang_adapter.py inspect`: frozen private source 검증과 실제 typecheck/build/private 114회귀, 오프라인 변환 검증. 이미 존재하는 destination은 덮어쓰지 않으므로 새 destination을 지정해야 한다.
- `evidence/independent-source-audit.json`: 71파일 및 나주69 원본 Git blob 재계산.
- `evidence/independent-output-audit.json`: 두 실제 출력 전수 검사, string pointer별 binding, 전체 output SHA, 추가 negative 8개.
- `evidence/regression-results.json`, `evidence/*-python.log`, `evidence/adapter-node.log`, `evidence/node-python-parity.log`: adapter/output 회귀 122개 명령·exit·로그.
- `replay/evidence/typecheck.log`, `private-build.log`, `private-qa.log`, `private-node-tests.log`, `private-python-tests.log`: 직접 재빌드와 private 114회귀 증거.
- `evidence/final-postcheck.json`: 마지막 source/출력 재검사와 총 검증 수.

최종 범위: **로컬 구현 수행·산출물 검증됨. 원격·브라우저·배포 단계는 미수행/미검증**.
