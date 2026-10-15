# 나주 검수 원고 기반 정적 소스

고객 원고 ae92f1762be8bdf0ef7e4193c8c03094e9484d2d31eaae6f1e27f545a94c2698을 단일 입력으로 사용한다. 원고 검수 PASS는 코드·브라우저·배포 검수 PASS가 아니다. sourceCommit은 원격 저장 후 실제 값으로 결속한다. 문구 수정 시 원고 검수를 다시 받는다.

서로 독립적인 private source와 release adapter manifests를 동결한다. 실제 원격 source commit 한 개에 묶되 가짜 predecessor SHA를 만들지 않는다. 원고 원본의 초안 status는 bytes 보존을 위해 유지하고 별도 독립 검수 결속을 검증한다. 전체 원 HTML은 제외하고 최소화된 사실·출처만 저장한다.
