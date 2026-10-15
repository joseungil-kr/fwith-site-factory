# 광주 서구 검수 원고 기반 정적 소스

서구12240, 전국 순서32의 독립검수 R2원고와 render-plan을 그대로 사용한다. 원고 SHA256 ecf53e7cc0ede77e9a4e85d19fb6f8a78e1f0e196813e2b7832fc20c173e4404, 독립검수 SHA256 207fcb4286080538495b282675ec9f5104d84daed6dba5f8abef97d280fe4a25, binding SHA256 e29344ad4a0f6ba94b3e38aec0b2597d80d0e67e900b4a3327d8d83c91f5f81c다. 원고 검수를 앱·브라우저·배포 검수로 취급하지 않는다.

검증된 동구 actual source a2e19b4d7e53681adf5749188bbcf6ea472319ee에서 코드·레이아웃·원본 자산만 재사용했다. 고객 문구를 지역명치환하지 않았다. 내부 renderer module 파일명은 원본바이트 보존을 위해 유지했지만 데이터와 region/hash binding은 서구다. home budget→facility-guide→consultation, detail budget→products→ribbon→facility→order를 보존한다.

private와 adapter manifest는 한 실제 source commit으로 저장할 수 있도록 분리하며 저장전 sourceRevision은 null이다. 가짜 predecessor나 다른지역 공개순서 gate가 없다. 원본 조사 전체 HTML/PDF·쿠키·개인내용·비공개대화는 source에 넣지 않는다. gwangju-seogu.fwith.kr는 별도 기술 adapter의 계획값이며 provider 소유권이나 공개를 뜻하지 않는다.
