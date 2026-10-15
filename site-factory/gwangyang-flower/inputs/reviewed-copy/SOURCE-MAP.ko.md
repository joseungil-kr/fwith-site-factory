# 광양 원고 출처 결속

고객 원고 정본 SHA256: `45a635ec0fff5c94a990814dfdd52b7a844687d558e5e7fcba29f8eba26b10cf`.
렌더 계획 SHA256: `b97eb621fced61c67596a6ba9c8e1f765dc7e0e0e3189da66d0821bdb3bf8c6d`.

## 직접 읽은 원본과 사용 범위

1. 보건복지부 장례식장 현황: [원문 안내](https://www.data.go.kr/data/15143467/fileData.do), [원본 CSV](https://www.data.go.kr/cmm/cmm/fileDownload.do?atchFileId=FILE_000000003623209&fileDetailSn=1&insertDataPrcus=N). 보존 CSV를 cp949로 파싱하여 physical 730행을 직접 읽었다. 2026-04-01 기준, 포털 수정일 2026-04-09. 최초 GET은 2026-10-15 13:57 UTC, 이번 원고 작업에서는 재다운로드하지 않았다. `evidence/originals/mohw-funeral-official.csv`, SHA256 `fcf4911ed271cfbc364d2005c3ad02a5e821d3946fdf80b5119e36dfaadccd4b`.
2. 광양시 [2023 자연재난 표준행동매뉴얼](https://gwangyang.go.kr/boardDownload.es?bid=0207&list_no=160020&seq=1). 16:03 UTC GET 보존 PDF와 PDF 107쪽(인쇄 99쪽) 전체 표 이미지를 이번 작업에서 직접 열었다. `city-disaster-plan.body`, SHA256 `911f239f9b76483fb5892c2302b1c3dbac35a87732c5654260f3ac2fc1a5bd1b`. 시설명·해광로 897·061-761-5500만 사용한다. 2023 자료를 현재 반입 보증으로 쓰지 않는다.
3. 광양시 [문화관광 구내식당 등록 원문](https://gwangyang.go.kr/tour/gallery.es?act=view&b_list=12&bid=0015&keyField=&list_no=11803&mid=a31204020000&nPage=194&orderby=&vlist_no_npage=0). 16:05 UTC GET 보존 HTML 전체 본문을 다시 추출해 읽었다. 표기 최종수정일 2026-02-03, SHA256 `0436ba00bc8ffc7666a6bea9488f6333228e32a3cb14326d1a081ef56e7a5e1f`. 주소·전화만 교차 대조하며 식당 운영·층·출입구로 확장하지 않는다.
4. 꽃이랑 4개 [B201](https://fwith.co.kr/shop/item.php?it_id=B201) · [B203](https://fwith.co.kr/shop/item.php?it_id=B203) · [B205](https://fwith.co.kr/shop/item.php?it_id=B205) · [B060](https://fwith.co.kr/shop/item.php?it_id=B060). 2026-10-15 13:49:49~13:49:55 UTC 직접 GET의 보존 원문을 이번에 다시 읽고 영수증 SHA와 일치시켰다. 이번 원고 작업의 새 GET이 아니다. 판매가격 `<tr>`와 광양시·10,000원이 함께 있는 배송비 `<tr>`, 사진 URL·상담 번호를 확인했다. 실제 결제·재고·통화·배송은 확인하지 않았다.
5. [공통 소재·수거 안내](https://fwith.co.kr/shop/img/order-top2.jpg)와 [교환·환불 안내](https://fwith.co.kr/data/common/flower379/de_change_content.jpg) 보존 이미지 전체 픽셀을 직접 열었다. SHA256 각각 `24c11e1cc413d3f64ad05145fdc0fb4171c8f3e618d4351609777f8e2ff43bc3`, `02701dd33c2a09258a882873df005dbe616842c2add159a08d618b68a934944c`. 생화·조화 혼합, 별도 수거 없음, 계절·지역 소재 차이만을 이유로 취소/환불 불가를 사용한다. 제작 완료 제한·출고 후 취소 문구의 적용 관계는 미해결로 남기고 일률 환불액을 쓰지 않는다.
6. 네 상품사진과 승인 공통 배너 세 장의 전체 픽셀을 직접 재열람했다. 이미지별 URL·SHA·크기·검사 범위는 `asset-manifest.json`에 있다. 사진상의 색·장식·리본만 설명하며 꽃의 종·수량·높이·우월성은 추정하지 않는다. 승인 배너는 지역명 치환·재생성·crop 없이 동일 bytes다.

공식 명칭은 ‘(주)광양장례식장’이다. 이것을 별도 운영법인 정보나 제휴·자사 운영 주장으로 확장하지 않는다. 주소 본문은 도시 이하를 그대로 썼으며 2026 CSV의 ‘전라남도’를 새 행정명으로 바꾸어 인용하지 않았다. CSV 빈소 4실/시청 PDF 5실, CSV 식당 미설치/문화관광 식당 등재의 충돌은 고객 설명에서 제외했다. 관련 명칭은 실제 출처 링크 제목에만 남는다.

## 원고 필드별 근거

- `home.lead`, `home.sections[budget]`, `detail.lead`, `detail.sections[products]`, `productCards`: 공식 SKU 이름·가격·사진·10,000원 배송 행. 상품 기본가와 추가배송비는 별도 표기한다.
- `detail.sections[budget]`: 같은 원본 수치의 산술. 10만 원 범위 예시는 편집 판단이며 최종 견적이 아니다.
- `detail.sections[facility]`: 정부 CSV 730행·시청 PDF 107쪽·문화관광 주소/전화의 일치 범위. 별도 상담 번호는 꽃이랑 공식 HTML.
- `detail.sections[ribbon]`, `home.sections[consultation]`: 문구·발송인 예시는 편집 제안이다. 특정 고객의 감정·종교·관계나 실제 주문을 가정하지 않는다. 상품·리본 상담은 기존 승인 사업 범위 안에서 쓴다.
- `detail.sections[order]`: 실제 주문에 필요한 수령·일정·문구 정보 정리 및 조건부 상담. 반입 가능·시간·설치 실적의 사실 주장으로 읽지 않는다.
- `detail.faq[0]`: 제작 완료 꽃 상품은 공식 교환·환불 불가 대상임을 명시하고 제작·배송 진행 상태별 상담으로 마무리한다. 변경 수수료·무조건 취소 가능·처리기간을 만들지 않는다.
- `detail.faq[1]`: 공식 소재 차이에 대한 취소/환불 제한. 파손·다른 상품 문제는 개별 상담으로 한정하며 무조건 환불 약속이 아니다.
- `detail.faq[2]`: 공식 별도 수거 없음.
- `support`, `notFound`, 버튼·breadcrumb·공통 메뉴: 이 로컬 계획 안에 존재하는 경로만 대상으로 한다. 원격 페이지가 이미 존재한다는 주장은 없다.
- `title/description`, OG/Twitter: 같은 정본 값 사용. 필수 metadata와 실제 header/HTML 검증은 계획 단계다.

## 경쟁 비교와 재사용 근거

보존된 [hallflower 상세](https://www.hallflower.com/%EA%B4%91%EC%96%91%EC%9E%A5%EB%A1%80%EC%8B%9D%EC%9E%A5/index.html), [Tistory 491](https://2332kk.tistory.com/491), [talktalkflower](https://talktalkflower.co.kr/fhs/%EA%B4%91%EC%96%91%EC%9E%A5%EB%A1%80%EC%8B%9D%EC%9E%A5-814/) HTML 원문을 열고 스크립트·스타일 제외 전체 본문을 읽었다. 원문 bytes와 최초 GET 일시·상태는 `evidence/research/SOURCE-MAP.json`의 sources에 결속되어 있다. 원문 재독이지 새 GET이나 경쟁사의 실제 배송 검증이 아니다. 경쟁 사진·checkout은 검사하지 않았다.

자사 코드/외부 오픈소스 검토는 `evidence/research/`에 보존한 도구 원문과 `PURCHASE-PLAN.ko.md`의 재사용 판단을 함께 읽는다. 여수 최종 release HTML의 실제 breadcrumb·OG/Twitter tag를 `evidence/verified-reference-navigation.json`에 남겼다. 광양에 이 기능이 구현됐다는 뜻은 아니다.

## 도구 보고와 미확인 경계

[도구 보고] 원본 최초 HTTP 응답·서버 시각, upstream repository 메타, 기존 다른 지역의 공개 성공은 보존 영수증과 기록의 보고다. 이번 작성자는 원본 bytes·정확한 필드·사진 픽셀·기준 문서·정본 문구를 직접 읽었다. 새 네트워크 응답으로 표현하지 않는다.

[미확인] 현장 운영·통화·반입 조건·빈소 배정, 실제 주문과 최종 결제, 제작·배송, 환불 적용 관계, 공개 호스트·runner·HTML·화면·HTTP·검색 색인은 이번 검증 범위 밖이다. 반입이나 법인 정보가 없다는 이유로 무근거 내용을 채우지 않았다. 원고의 독립 문체·완결성 판정도 아직 대기 중이다.

첫 본문 추출 시도에서 `ModuleNotFoundError: No module named 'bs4'`가 발생했다. 외부 설치 없이 Python 표준 도구로 원본을 추출·파싱하여 이어갔으며 원본 bytes는 바꾸지 않았다. 접근 거절 우회, 사용자 PC, Codex/Work, 인증·보안 변경, 취소된 출처 재요청, CAPTCHA 조작은 없었다.
