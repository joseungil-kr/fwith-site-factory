# 광양 별도 기술 어댑터

나주 navigation successor 21ebc3cffc12df8977e8209bc4fc3139e084fa8b의 검증된 분리 어댑터를 재사용했다. 광양의 검수된 B201 500×500 OG/Twitter, Core7 private robots, 네 실제 경로에 맞춘 metadata 변환만 달라진다. 원본 JSON과 HTML body·정적 자산은 byte-identical이어야 한다.

private manifest와 adapter manifest를 분리해 한 실제 source commit에 저장할 수 있다. 가짜 predecessor를 요구하지 않는다. sourceRevision=null / local-inspection은 오프라인 검사 전용이고 실제 production SHA·승인으로 인정되지 않는다. 외부 승인/control binding과 trusted 실제 Git pre/post·main owner·실제 QA artifact/pixel·provider·공개 HTTP는 별도 미완 게이트다. 기존 proof bytes의 로컬 재사용은 새 자격증명 생성이나 IndexNow 제출이 아니다.

실제 원격 쓰기·배포는 이 코드 작성 또는 오프라인 검사로 승인되지 않는다. 모든 테스트 fixture는 synthetic local이라고 명시한다.
