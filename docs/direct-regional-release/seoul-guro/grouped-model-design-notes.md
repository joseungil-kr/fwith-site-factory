# 구로 묶음 구매 안내의 제한적 설계 요구

상태: 계획 독립검토 대기. 구현/본문 작성/계획 N 동결은 하지 않았다.
기준 소스: Gangseo 9692b2cf29a90a4eb3f50e27788293284cffc1b3. 구로 코드에만 추가하며 원본의 단일시설 계약을 약화하지 않는다.

## 명시적 모드와 기존 회귀
- 새 모드는 구로 siteKey/scopeKey/assignment 값의 일치가 있어야 활성화한다. 빠진 값, 다른 지역으로의 opt-in, unknown field 및 기존 모델과 섞인 레코드는 실패한다.
- 기존 regions.mjs 구현은 원본을 보존한 legacy 어댑터에 위임할 수 있다. 기존 단일시설 테스트와 코드 checksum으로 소실/완화가 없음을 확인한다.
- N3 채택 시 근조 장소별 안내 1, 예식장별 안내 1, 사무실 개업/이전 안내 1. 원래 후보 8개와 사전 보류 4개의 이력은 그대로 둔다. 원래 후보 중 제이오스티엘 1개는 최초 동결 전에 HTTPS 고객 출처 미해결로 보류하며, 활성 7맥락은 6개 시설과 1개 지역맥락이다.
- 후보수, 페이지수, 시설수, 지역맥락수를 각각 세며 8개 후보를 3개 시설로 잘못 기록하지 않는다.

## 시설 및 지역 맥락
- 실제 시설은 facilityKey/name/address/unitKey/source identity와 근거 sourceIds를 유지한다.
- 구로디지털단지는 area-context 유형으로 구분한다. 대표 건물·가짜 도로명 주소·가짜 현장 수령처를 만들지 않는다.
- candidate-to-article 매핑은 정확히 한번씩, article-to-candidate 역참조도 정확히 일치해야 한다. 같은 후보가 두 canonical URL에 배정되면 실패한다.
- 각 시설 section은 검토된 anchor, facilityKey, heading, sourceIds 및 시설 고유 사실과 결속한다. 존재하지 않는 anchor로의 링크는 실패한다.
- HTTP 원문은 원문 그대로 보존한다. HTTPS 성공 증거나 별도 승인된 원문 표현 계약 없이 scheme을 바꾸거나 기존 source validator를 느슨하게 하지 않는다. 라마다는 실제 HTTPS 서울다누림의 이름·도로명·법정동과 Wyndham의 홀명 원문을 따로 결속한다. 제이오스티엘의 고객 HTTPS 출처는 미해결 상태로 최초 동결 전 보류한다.

## 경로 및 렌더링
- 페이지 URL은 각각 고유 canonical 경로 하나. 시설 앵커는 새 색인 페이지가 아니며 sitemap/IndexNow에 넣지 않는다.
- 근조 제목/설명에 두 시설명, 두 H2와 시설명 링크를 제공한다. 시설 선택 비교라고 부르지 않는다.
- 예식 안내에는 4개 활성 시설의 이름별 실제 anchor와 직접 접근 링크를 둔다. 동일한 그랜드볼룸 명칭을 호텔/건물 이름과 함께 쓴다.
- legal/admin 디렉터리는 시설이 속한 정확한 법정동에 시설명+article#anchor를 모두 연결한다. Map의 마지막 항목만 남거나 URL 중복제거 때문에 같은 문서의 다른 시설이 소실되는 버그를 방지한다.
- 행정동의 부분 관할은 특정 시설의 실제 행정동 귀속으로 추정하지 않는다. 기존 official crosswalk의 relation 범위와 '일부'를 보존한다.
- 링크와 타깃 렌더링을 실제 HTML로 검사한다. H1 하나, H2 본문, H3 하위, 출처 제목 하나, FAQ 실제 노출, 배너 세 장의 hash/alt/치수/lazy 확인을 유지한다.

## 음성/수익표현 관련 정적 및 독립 검수
- 상품 8 SKU 및 실제 가격, 이미지와 orderUrl은 fresh catalog와 일치해야 한다.
- 라마다 홀 층수는 확정된 원문이 없으므로 사용하지 않는다. 이미지파일명 14f는 층수 증거로 승격하지 않는다.
- 제작 이후 제한만 보편규칙으로 표시하지 않는다. 공식 이미지의 불량·파손·오배송 예외 및 문구의 적용 불명확성을 함께 정확히 처리한다.
- 2,500~3,000자 목표는 본문을 채우기 위한 시설연혁/경고 반복 허가가 아니다. contentMarkdown와 첫답변+고유본문+FAQ 길이를 각각 보고한다.
- 미확인 외부화환 조건을 반입허용/수령/설치/회수/당일도착 약속으로 바꾸지 않는다.

## 테스트 목록
1. 정상 구로 N3, 원래 8후보 이력을 보존하고 활성 7맥락(6시설+1지역맥락)의 정확한 coverage 통과. 보류 제이오스티엘은 연구 trace에만 남고 고객 앵커·링크·메타에는 나타나지 않아야 한다.
2. 누락/추가/중복 후보, intent family mismatch, 가짜 단일 주소, source identity scheme drift, wrong legal dong 실패.
3. 모든 활성 anchor 유일성, heading text와 facility name, sourceIds 결속, 누락/임의 anchor 실패.
4. 구로동 다중시설과 신도림동 2시설의 링크 모두 노출. 같은 article URL의 여러 anchor 보존.
5. 기존 Gangseo 단일시설 및 legacy unit-assignment 모델의 기존 실패/통과 회귀.
6. page-map/architecture/manifest/snapshot의 페이지 및 후보 배열·순서·본문해시·review bindings 정확한 일치.
7. source cards HTTPS 엄격검증 기존 테스트 무변경. 새 HTTP provenance 처리 존재 시 별도 승인된 계약에 대한 엄격 테스트.
8. productionApproved=false, noindex인 로컬 산출물. 출판 승인 없이 공개 배포 트리거·issue·IndexNow를 실행하지 않음.
