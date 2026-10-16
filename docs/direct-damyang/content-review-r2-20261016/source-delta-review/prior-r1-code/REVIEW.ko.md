# 담양 단일 구매 홈: 독립 소스 검토

## [직접 확인]

고정 ZIP의 74개 파일을 새 경로로 추출해 파일별 SHA256·크기를 대조했다. 작성자 산출물·fixture·evidence를 복사하지 않고 10개 명령을 다시 실행했다. 7개 시험군의 332개 케이스가 통과했고, 실제로 생성된 private 14파일과 production-like 16파일 모두 작성자 산출물과 byte-identical이었다.

- 본문은 home + 404 두 개뿐이다. 홈의 상품 4개·FAQ 4쌍·배너 3개·이미지 7개와 작성 문구 100개를 실제 HTML에서 확인했다. 시설 상세·support·regions 페이지는 없다.
- 네 사진과 세 승인 배너를 직접 열어 보았다. 상품사진 파일은 각 500×500, 배너는 1774×887이며 고정 원본과 bytes가 같다. 이는 브라우저 화면 검증과 구별한다.
- 참고예산은 59/79/109/149천원 + 배송비 10천원 = 69/89/119/159천원이다. referenceTotalLabel이 카드마다 있고 finalPriceKRW는 null이다. 날짜 있는 시설 식별 3개, 주문 afterList 3문단, FAQ 마지막 문항, 출처 8개와 제한 문맥이 보존된다.
- production-like 홈 canonical·social과 404 noindex/무 canonical·무 social을 확인했다. sitemap은 홈 URL 하나다. 본문 2개와 자산 9개의 bytes가 private와 같다. 기본 HTTP 계획은 실제 inventory에서 14개 파일 GET + missing-route probe 1개로 도출했으며 아직 요청하지 않았다.
- 독립 양성 확인 46개, 독립 변이 49개가 성립했다. 추가/누락 경로, sitemap 중복·빈값·외부·404, 네 참고가격, 숨김·누락 FAQ, 주문/시설/출처 제한, URL 변경, metadata, 404 indexability, 자산 변조, symlink, 원본 검토 판정·점수·분모 변조, 원본 입력 추가, 미결속 production/provider 환경을 거부했다.
- 원본 공개안전 원고검토 32개 항목과 manifest·SHA 파일을 전부 재검사했다. 원고 projection 26개가 원본 bytes와 같다. 165/24/16/3 분모, 원고검토 전용 verdict, null 점수 및 당시 미구현 상태를 변경하지 않았다.
- 기존 광산 로컬 기준에서 전체 1,190,326-byte diff를 재생성해 정확히 일치시켰다. 변경 28·동일 20·추가 26·삭제 26이며 데이터 이름만 바꾼 구현이 아니다. CopyPage의 home 본문, ProductCards의 참고합계, BaseLayout의 홈 앵커, 2-route runtime과 검증기가 실제로 변경되었다.
- 67개 텍스트 소스와 원본 공개안전 검토를 검사해 실제 사적 절대경로·인증값·raw 연구원문 유입을 찾지 못했다. 합성 테스트 경로와 공개 IndexNow proof는 실제 개인 경로나 비밀키가 아니다.

## [추정·판단]

검토한 정적 소스 범위에서 저장 전 필수 수정은 없다. 기존 Astro·잠금파일·CSS·사진·배너·입력경계를 재사용한 구현이 원고 계약을 충족한다. 후속 릴리스 통제 검토로 넘길 수 있지만 공개 완료 판정은 아니다.

## [도구 보고]

이 검토의 신규 외부 자료 조회는 없다. 상위 원고검토의 상품·정부자료 조사와 기존 원격 기준 commit 조회는 원본 보고로 유지한다. 테스트 통과 외에도 새 산출물의 원문·파일·본문·자산을 별도로 검사했다.

## [미확인]

실제 source commit, GitHub readback, 별도 release controls/Actions, 브라우저 계산스타일·모바일·키보드·hash/back/forward, hostname 소유권, 공개 HTTP·MIME·real404, IndexNow 영수증은 확인하지 않았다. native details 메뉴에 별도 Escape 동작은 약속하지 않는다. 시설 현재 운영·납품·최종금액·색인·순위도 확인하지 않았다. coreHub/fullLaunch는 NOT_ASSESSED이다.

## 검증 증거 및 정확한 범위

- code-review.json / code-review-binding.json: 고유 담양 검토 상태 및 정확한 소스·원본 결속
- source-manifest.json / private-manifest.json / adapter-manifest.json: 74 = 59 + 15 파일별 bytes/hash
- reproduction.json: 독립 10명령, 각 원본 로그 hash, 332케이스와 재현 조건
- independent-observations.json: 독립 양성 46·변이 49, 실제 출력 inventory와 hash
- diff-check.json: 전체 diff 재생성 결과
- public-safe-allowlist.json / REVIEW-MANIFEST.json / SHA256SUMS: 이번 검토 공개안전 파일 경계

고정 소스 tree: 0b3812116c10af12fdf15dca9d2c8b0a3f7f97b9987a277138ad8f330931493c
고정 ZIP SHA256: 98fca5210ab62b4b2703537370eb88c09abda94ee91fa5854d41c186e8af8a6a

기존 원고 판정을 PASS로 바꾸지 않으며, 이 검토 자체가 원격 쓰기·배포 승인을 만들지 않는다.
