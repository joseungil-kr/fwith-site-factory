# 광주 동구 검수 원고 기반 정적 소스

동구 12210, 전국 순서31의 독립 검수된 원고와 render-plan을 그대로 사용한다. 고객 원고 SHA256 9f4643d1aa73945983497c953296716bbe0449ce93960a1a3427a6a6933d7687, 독립 R2 검수 SHA256 d3b1c7742263f6d373f4a89082247a1763666f90bd223bc67ea9e148297bc803이다. 원고 검수를 코드·브라우저·배포 검수로 취급하지 않는다.

광양 source 78382db9e684e61ff40d3e6720c7c68e1995168b의 실제 Git blob을 대조해 코드·레이아웃·승인 자산을 재사용했다. 다른 지역의 고객 문구를 치환하지 않았다. 동명 동구의 혼동을 막기 위한 namespace는 gwangju-donggu이며 후보 호스트는 외부 어댑터에만 기록한다. 원고의 domain과 origin은 null 그대로다.

private manifest와 adapter manifest를 분리하여 한 실제 source commit으로 저장할 수 있다. sourceRevision은 저장 전 null이며 가짜 predecessor는 없다. 로컬 원문과 제3자 전체 HTML/PDF, 비공개 대화는 소스에 넣지 않는다. provider 생성·연결·소유권·공개 HTTP·실제 브라우저는 별도 gate다.
