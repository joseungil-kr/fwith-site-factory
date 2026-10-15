# 나주 별도 기술 어댑터

순천 b5e8d623의 최종 소셜 메타 어댑터를 재사용한다. 고객 본문·정적 자산은 private 결과와 바이트가 같아야 한다. 나주 원고는 독립 검수 SHA로 고정돼 있다.

의도적인 계약 차이: 나주 private source와 adapter를 한 실제 source commit에 저장하므로, 과거 지역의 previewSourceRevision 또는 가짜 predecessor를 요구하거나 복제하지 않는다. 대신 private-source-manifest 전체 파일 집합·bytes·SHA와 외부 source-contract의 실제 source commit을 결속한다. 추가·삭제·symlink·숨김 파일을 fail-closed 검사한다. 별도 source/adapter manifest는 로컬 최종 evidence에 보존하며 원격 이후 external controls에서 정확히 pin한다.

현 단계 `naju_adapter.py inspect`는 sourceRevision=null, 메타 revision=local-inspection인 오프라인 검사다. production 검증은 그 marker를 거절한다. 실제 source SHA·외부 승인/control binding 없이는 production 명령이 실패한다. 공개·모바일·runner·provider·HTTP·IndexNow 증거는 생성하지 않는다.
