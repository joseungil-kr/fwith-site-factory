# 여수 반입불가·오브제 안내 교정: 별도 읽기 전용 QA

이 경로는 기존 scripts/direct-yeosu 및 여수 게시 workflow를 수정하지 않는다. 현재 source97382615bf24f164f097f323295f495b84561f8d, project treeec6333c44b9f8b94f7dc271b9c9096b917a0f665만 수용한다. 원472c source85에 대해 builder1수정+correction3추가, private75 및84기존파일 보존을 검사한다.

기대값은 원 실제 build38742707182의 검증된 원본 HTML과 검수한 r3 patch-spec43c3295fc63b3e4ab81019c086bf07eb1c74629f37cfb8a525d5948e4e074fc5에서 고정했다. 후보 DOM이나 실행 결과에서 합격 기대값을 만들지 않는다. r2 검수 입력과 r3 source-save 검수 입력을 별개로 보존한다.

production-binding.json의 승인 필드는 변경하지 않은 역사 생산자 스키마를 위한 기술적 빌드 호환 입력이다. 과거 authorizationEvidence는 새 교정 내용, 새 실행, provider update 또는 IndexNow의 승인이 아니다. qa-scope.json과 모든 산출물은 배포권한 없음 및 IndexNow 미실행을 명시한다. 현재 namespace에 게시 기능·provider API·IndexNow 호출은 없다.

실행 순서:
1. 정확한 owner/main/first-attempt/issue JSON, source branch와 commit 고정
2. source88, 원source85, 전체저장소 diff4 및 private75 검증
3. 원 private build→원 private tests
4. 실제 baseline production transform→원 production QA·mutation tests
5. 저장된 전체 producer 실행: private build·baseline QA 이후 필수 교정
6. 별도 corrected18 gate·mutation tests, 산출물 재읽기 및 포장
7. 진짜 Astro preview, 4경로×320/390/1280, 실제 미존재 경로404, 원본HTTP bytes, 이미지·모바일메뉴·키보드·뒤로/앞으로·넘침 검사
8. 실패를 포함한 DOM·screenshots·network·console·source/output/control binding 봉인, 독립 픽셀검수 대기

카드0·SKU주문링크0·FAQ4·판매처 원문 및 시설운영자 확인 한계·새 OG와 전화CTA를 검사한다. 홈3+상세3 공통배너와 상품사진 파일4개는 그대로 유지한다.404는 revision meta 외 보존하므로 그 페이지의 역사 메뉴 문구도 보존한다.

실제 Actions/브라우저/독립 픽셀검수 성공은 로컬 정적 테스트 통과와 별도다. 로컬 Chromium 시작 권한 문제를 우회하지 않는다. main 반영과 owner issue 작성은 별도 root 검수·lease 이후에만 수행한다. 공개 update는 fresh provider baseline·별도 update controls·한 번의 시도권·공개HTTP 검증이 추가로 필요하며 본 QA가 이를 허용하지 않는다.
