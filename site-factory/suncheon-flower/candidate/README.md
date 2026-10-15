순천 로컬 비공개 후보: 소스·필수 입력·정적 산출물

이 묶음은 공개되거나 호스팅된 사이트가 아닙니다. origin/domain/canonical은 null이고 HTML 네 개는 noindex,follow입니다. 비공개 후보라는 작업 범위를 뜻하며 noindex가 인증이나 접근 제어를 제공한다는 뜻은 아닙니다. 목포 26 → 여수 27 → 순천 28 공개 순서는 그대로이며 앞 지역을 완료 처리하지 않습니다.

대상 정적 경로
- / : 순천 홈
- /regions/suncheon-stcarollo-funeral-wreath/ : 성가롤로병원 상세 한 편
- /regions/ : 한 상세로 이동하는 지원 탐색
- /404.html : 정적 404 문서. 실제 HTTP 404 응답은 검사하지 않았습니다.

입력과 렌더링
inputs/reviewed-copy의 원래 JSON이 유일한 홈/상세 런타임 원본입니다. Markdown은 원문 대조용으로만 들어 있으며 렌더하지 않습니다. FAQ 3쌍과 상품 4카드는 상세에 한 번만 출력됩니다. 순천 원문을 지역명 교체로 생성하지 않았습니다. 입력의 원래 절대경로와 과거 보고서의 참고 경로는 출처 문맥이며 재빌드에서 따라 읽는 경로가 아닙니다.

required-originals.json에는 실제 필요한 원본 사본 18개만 결속했습니다. 검토된 7개 파일, 해당 최종 독립 검토/결속 자료, 출처 대응표와 재사용 이미지 7개가 포함됩니다. 새 탐색/404 문구의 별도 검토는 inputs/ui-copy-review.json에 있습니다. 역사적 전체 감사 327개나 원래 작업공간은 빌드 조건이 아닙니다. reference의 연구·라이선스 자료는 선택 근거이며 추가 런타임 입력이 아닙니다.

재검사
1. 묶음 루트에서 python3 verify_bundle.py --built-output을 실행해 포함된 파일의 경로·바이트·해시를 검사합니다.
2. candidate로 이동합니다. package-lock.json의 의존성이 준비된 환경이어야 합니다. 이 묶음에는 node_modules가 없습니다. 이번 검증은 기존 설치 의존성으로만 수행했으며 새 설치나 다른 OS/Node 버전을 검증한 것이 아닙니다.
3. ASTRO_TELEMETRY_DISABLED=1 npm run build
4. ASTRO_TELEMETRY_DISABLED=1 npm test
5. 묶음 루트에서 python3 verify_bundle.py --built-output

build는 입력 결속 검사, Astro typecheck, 정적 빌드, 실제 생성 HTML에 대한 별도 JSON 투영 검사를 수행합니다. test는 Node 회귀와 생성 HTML 복사본의 변조 검사를 실행합니다. 시험용 변조는 임시 복사본에만 적용합니다. dist를 새로 생성해도 source/output manifest와 일치해야 합니다. 기존 버전과의 의존성 차이는 프로젝트 이름만이며 버전·integrity는 바꾸지 않았습니다.

검증 한계
정적 HTML, CSS의 직접적인 숨김 규칙, 원본 이미지 바이트, CTA 목적지와 내부 링크를 검사했습니다. 실제 브라우저 화면·모바일 레이아웃·computed style·메뉴/키보드 상호작용·공개 HTTP·전화 연결·상품 재고/주문/배송·배포·IndexNow·검색 색인/순위는 검사하지 않았습니다. 기존 browser/loopback 소켓 차단을 재시도하지 않았습니다. 이미지 7개는 기존 바이트를 그대로 사용했으며 새 이미지 생성은 없습니다.

검증 증거
reference/source-manifest.json, reference/output-manifest.json
candidate/evidence/static-qa.json
reference/independent-static-review.json
MANIFEST.json, SHA256SUMS
