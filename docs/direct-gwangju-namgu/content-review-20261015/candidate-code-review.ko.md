# 남구 독립 구현 코드 검토

[직접 확인] 로컬 소스·정적 산출물 범위에서 source 저장 준비 판정입니다. 원격 저장·공개 완료 판정은 아닙니다.

- 최종 source 82개(private 67 + adapter 15)를 별도 사본에 복사해 10명령·266 tests를 재실행했습니다. 모두 exit 0입니다.
- 추가 독립검사: 실제 bytes를 변경한 출력 부정시험 55건을 모두 거부했고 runtime 검사 37건이 통과했습니다. 별도 capture 비교 fixture 19건도 통과했습니다. 서로 다른 분모입니다.
- 네 HTML을 별도 표준 라이브러리 parser로 검사했습니다. 112문구·4 SKU·FAQ 3개·홈/상세 배너3·내부링크·heading·메타·support noindex·sitemap2·404 예외를 확인했습니다.
- private16/offline18 산출물은 작성자의 출력과 전부 같은 bytes입니다. 모드 사이 body4·static asset9도 같습니다. 4상품사진과 3배너의 실제 픽셀을 열었습니다.
- 고객 원본43·닫힌 검수39·projection25·핵심 참조11을 재해시했습니다. 원검수 verdict와149조항/13정책 평가를 변경하지 않았습니다. 공개용 successor의 차이는 manifest 경로 한 값뿐입니다.
- source tree SHA256: ee961f55693294866d2e3ac607d517d74bf41072590c02f3fa11e47f95e19d9c
- customer-copy SHA256: 052f89035bce44c5e4f403e7e42b9306dc0f49588e10d7aa89a8f088a8cadf08

[도구 보고] Seogu d9aee870… 및 main04e0a0d2…의 commit/tree 관계는 준비 단계에 보존된 GitHub 응답입니다. 이 검토자는 해당 tree에 대해 원본79파일과 main42파일의 실제 bytes/Git blob을 독립 재계산했습니다. 새 원격 조회를 했다고 주장하지 않습니다.

[추정·판단] 범위 내 필수 코드 수정 사항은 없습니다. 홈 배너 삽입은 facility-guide stable ID만 사용하며 남구에서 Seogu HTTP 예외를 제거했습니다. 이후 저장은 정확한82파일과 최종 검토 bytes를 결속해야 합니다.

[미확인] 실제 source commit/readback, trusted controls 전체, Actions, 실제 브라우저 화면·모바일 동작, provider/hostname, 공개 HTTP·real404·IndexNow는 별도 검증입니다. 비교 control-projection은 실제 저장/실행할 control이 아닙니다. 원본 검수의 원고/사실 판단을 새 구현 PASS로 고쳐 쓰지 않았습니다.

검증 증거: independent-code-review.json, implementation-code-review-binding.json 및 evidence의 구조화된 검사 결과와 로그. 공개용 파일은 PUBLICATION-MANIFEST.json의 정확한 목록만 사용합니다. 전체 검토 폴더나 raw logs를 Git에 올리지 않습니다.
