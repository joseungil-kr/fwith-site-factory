# 광양 검수 원고 기반 정적 소스

고객 원고 45a635ec0fff5c94a990814dfdd52b7a844687d558e5e7fcba29f8eba26b10cf와 독립 R2 결속을 단일 입력으로 사용한다. 원고 검수 결과는 HTML·코드·브라우저·배포 검수 결과가 아니다. 실제 원격 source commit은 저장 후 외부 통제에서 결속한다. 가짜 predecessor를 만들지 않는다.

private source와 release adapter 해시를 분리하여 하나의 실제 source commit에 저장할 수 있도록 한다. 초안 status를 포함한 검수 입력 bytes는 보존한다. 전체 제3자 HTML/PDF 원문은 제외하고 필요한 source-map만 포함한다. 광양시 12190, 순서30, namespace gwangyang이며 경기도 광주와 다르다.
