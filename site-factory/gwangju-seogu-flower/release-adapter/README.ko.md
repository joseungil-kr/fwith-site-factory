# 광주 서구 별도 기술 어댑터

동구 실제 source a2e19b4d7e53681adf5749188bbcf6ea472319ee의 검증된 별도 어댑터를 재사용했다. 서구 최종 검수 원고와 기존 private renderer, 네 HTML body 및 아홉 정적 자산을 보존한다. candidate의 내부 donggu 파일명은 renderer byte 재사용을 위해 유지한다.

private와 adapter manifest는 하나의 후속 실제 source commit으로 저장하도록 분리한다. sourceRevision=null, local-inspection은 로컬 검사만 의미한다. 예정 호스트 gwangju-seogu.fwith.kr의 provider 소유권과 실제 공개 여부는 미확인이다. 이 모듈은 provider API를 호출하지 않는다. 기존 공개 proof bytes만 재사용하며 새 credential 생성이나 IndexNow 제출을 하지 않는다.

실제 remote source/control/runner binding, main owner, browser pixels, provider 및 public HTTP 검증은 별도 gate다. 테스트의 승인 fixture는 합성 local fixture이며 실제 배포 승인이 아니다.
