# 광주 북구 별도 기술 어댑터

남구 실제 source 22e4e03de9177eb624d6fb0a0651109da4881ac5의 검증된 adapter를 재사용했다. 북구 최종 독립검수 원고와 private renderer, 네 HTML body 및 아홉 static assets를 정확히 보존한다. candidate의 내부 donggu 파일명은 기존 renderer import 재사용을 위해 유지한다.

private와 adapter manifest는 하나의 후속 실제 source commit으로 저장하도록 분리한다. sourceRevision=null과 local-inspection은 로컬 검사만 의미한다. 예정 호스트 gwangju-bukgu.fwith.kr의 provider 소유권과 실제 공개는 미확인이다. provider 호출이나 신규 인증정보 생성, IndexNow 제출을 하지 않는다. 실제 remote source/control/runner binding, 독립 code/DOM/pixels, provider 및 public HTTP는 별도 gate다. 테스트 fixture는 합성 local fixture이며 실제 배포 승인이 아니다.
