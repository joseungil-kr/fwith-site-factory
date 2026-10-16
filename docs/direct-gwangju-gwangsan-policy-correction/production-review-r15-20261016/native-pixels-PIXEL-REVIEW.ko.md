# 광산 R15 실제 화면 독립 검수

## 판정

ACCEPT_EXACT_ONE_PARAGRAPH_CORRECTION_PIXELS_WITH_CAPTURE_LIMITS.

source654dafd7cafa4c6a158684ac4b304ceb7a5996b5 → source0da9982f8ea294c6fb38729d17e9043d45f7ca72의 늦은 주문 1문단 수정에 한정해 실제 화면을 수용한다. 새 문단은 320·390·1280 모두 전체가 가림 없이 읽힌다. 기존 본문/CSS/자산과 이전 실제 화면 수용 증거를 독립 비교하여 상속 범위를 좁혔다. 일반 full/core-hub launch는 NOT_ASSESSED. 새 공개 배포/공개 HTTP/주문 수행 수용이 아니다.

## [직접 확인]

- 실제 artifact12048241187, run38905282539, control ed5f28d7f29241af735b3f63d7692f942701d502, source0da9982f8ea294c6fb38729d17e9043d45f7ca72. ZIP 14,307,212 bytes SHA256 c088aa1bc251ca7f4027fad7bb1afb9f3d5e53c5ae42944670daa5bc30d42b64. 패킷 인계문/manifest/binding을 먼저 읽고 ZIP95개 실제 바이트와 펼친 파일을 대조했다. browser manifest64개도 크기·SHA를 재계산했다.
- 원본36 PNG를 모두 view_image로 열었다. 긴 home/article 원본6개에는 원본 좌표에서 1000px 간격·최대1100px 높이의 무변형 crop43개를 만들어 전부 열었다. PNG 유효성이나 작성자 PASS만으로 판단하지 않았다. 각 원본 경로·SHA·직접 본 영역·가림 한계는 PIXEL-REVIEW.json screenshots에 기록했다.
- 15 DOM을 Python 표준 HTMLParser로 직접 파싱했다. 4route×3폭+unknown-path×3의 H1/title/description/robots/canonical/source revision을 실제 DOM에서 뽑아 report와 대조했다. main text는 각 built HTML과 정확히 같고 retained response hash도 각각 실제 dist bytes와 같다. 각 article DOM에서 수정 문단은 UL 직후 P로 정확히 한 번 존재하고 구 문단은 없다.
- customer-copy 두 원본의 전체 leaf를 비교해 /detail/sections/4/afterList/0만 변경됐음을 확인했다. visible-strings117개 중 다른116개는 정확히 같다. 실제 dist18개는 이전 수용 artifact12021337286/run38840834496의 보관된 dist와 비교했다. 비HTML14개는 바이트 동일, HTML4개는 source revision·copy SHA·해당1문단 치환 외 차이0이다. CSS·상품4사진·공유배너3개·favicon·robots·sitemap·proof 등이 이 범위에 포함된다.
- 이전 pixel review에 기재된36개 SHA를 이전 실제 PNG bytes에서도 다시 계산했다. 이번36개 중30개가 이전 PNG와 바이트 동일하다. 바뀐6개는 article full3개와 FAQ section3개뿐이다. 변경문단 이후 문서 높이가 늘어나 full/section 위치가 달라진 부분을 새 실제 화면으로 직접 검수했다. 이전 pixel review SHA 및 각 이전/현재 PNG SHA는 JSON에 있다.
- home의 지역 H1·공급자 중심 설명·기본가/배송비 상담·수완 상세 CTA·리본 상담·전화/출처 링크·3배너 순서를 확인했다. article의 수완장례식장 H1, 네 상품(B201 59,000원, B203 79,000원, B205 109,000원, B060 149,000원), 사진별 색·배치 설명, 배송비/최종금액 상담, 층·호실/일정/리본/주문 정보, FAQ4쌍, 출처와 최종 CTA를 full·viewport·section을 교차해 읽었다. 모바일은 한 열·desktop은 두 열 상품 카드이며 사진 내용과 가격/링크가 나타난다.
- 수정 문단 핵심 증거: article-320-full.png의 crop7(y7000–8100)·crop8(y8000–9100), article-390-full.png의 crop6(y6000–7100)·crop7(y7000–8100), article-1280-full.png의 crop4(y4000–5100). 모두 문단 전체를 함께 읽을 수 있으며 줄 겹침·가로 잘림·축약/토글은 보이지 않는다. 문단 길이 증가 자체는 보이지만 16px 본문과 충분한 행간으로 읽힌다.
- 보관된 상인 원본 B201/B203/B205/B060 상세 이미지4개를 결속 SHA에 대조하고 전체 및 상·하단을 직접 열었다. B201/B203/B205 상단의 평일19시→평일기준 익일 오전, 주말·공휴일19시→익일13시전후, 하단의19시·주말공휴일 제외, B060 하단의21시·주말공휴일 제외를 확인했다. 새 문단은 두 게시 위치를 구별하고 적용범위·예외를 확정하지 않으며 수완 실제 주문 상담으로 마친다. 원문의 적용 우선순위나 특정 주문 가능시간은 확정하지 않는다.
- support의 안내 카드/상세 이동, 404와 unknown의 제목·홈 복구 CTA·footer는 3폭에서 읽힌다. support noindex, home/article index, 404 noindex·canonical 없음은 DOM에서 확인했다. robots/sitemap은 이전 출력과 바이트 동일하다.

## 캡처 결함과 실제 레이아웃 판단

1. 원본 section PNG6개에는 sticky header가 제품사진 또는 FAQ 제목/첫 답변에 겹친다. 모바일 section에는 fixed bottom bar도 제품설명/FAQ 셋째 답변에 겹친다. 이는 현재 보관된 이미지의 분명한 가림이다. 다만 같은 폭의 full 원본에는 그 상품4개·FAQ4쌍이 가림 없이 모두 있어 직접 읽어 보완했다. 영구적으로 본문이 겹치는 결함이라는 증거는 없다.
2. 모바일 full은 최초 viewport의 fixed bottom bar를 문서 y842–900에 남긴다. home320/390 가격문단 앞부분, article320 도입 둘째 문단 일부, article390 첫 배너 일부가 가려진다. 원본 viewport도 같은 부분에 bar가 있으므로 home가격과 article320 도입의 해당 폭 무가림 픽셀은 이번 retained evidence만으로 입증할 수 없다. DOM 존재, 다른 폭의 표시, 이전 수용 PNG와의 바이트 동일성으로 한정 상속하며 '현재 모든 글자가 모든 위치에서 가림 없이 보임'이라고 주장하지 않는다.
3. 실제 CSS에 header position:sticky/top:0, mobile fixed bar, footer58px+safe-area 추가 여백, scroll-padding/scroll-margin이 있다. 원본 화면의 가림 위치와 일치한다. 동일 본문이 full의 다른 위치에서 읽히고 현재30PNG·CSS가 이전과 동일한 점을 합쳐 캡처 당시 고정요소 합성 한계로 판단한다. 실제 모든 scroll 위치의 가독성은 새로 재생하지 않았으므로 단정하지 않는다. 기존 수용에서도 같은 한계가 명시돼 있다.
4. 수정된 늦은 주문 문단은 이 가림 영역 밖이며 세 폭 모두 전문이 직접 읽힌다. 이번 한 문단 correction의 수용을 위해 변경되지 않은 영역에 새 전면 재검수 게이트를 만들지는 않는다.

## [도구 보고]

- retained actual runner report는 12화면200, unknown404 3개, navigation/keyboard flow3개, pageerror0/외부요청0을 기록한다. HTTP상태와 실제 클릭·Space/Enter·back/forward를 이 검수에서 새로 실행한 것은 아니다. 다만 실제 DOM/응답 SHA/이미지를 직접 대조해 보고서와 일치함을 확인했다. /404.html 직접요청200과 unknown경로404는 구분한다.
- 3flow 원문에서 home→article, support 직접/인바운드→article, breadcrumb, 브랜드 홈, skip-link focus 및 모바일 메뉴 click/Space/Enter 결과를 읽었다. unknown3개는 recoveryUrl이 홈이며 응답SHA가 실제404.html과 같다. 현재의 네트워크 상태나 공개 도메인 성공을 뜻하지 않는다.

## [추정·판단]

이전 수용된 출력의 비HTML14개가 정확히 같고 HTML차이가 provenance+정정1문단으로만 설명되며, 새 문단과 영향을 받는 아래 FAQ의 실제 픽셀을 세 폭에서 확인했다. 따라서 현재 보관된 build/browser 증거 범위의 한정 정정 수용에 새 blocking pixel regression은 관찰되지 않았다. '무결한 전체 스크롤 화면'이나 새 전체 사이트 출시 수용으로 확대하지 않는다.

## [미확인 및 실패]

새 공개 HTTP/실제 배포, 물리 iOS·Android, 보조기술, 외부 상품 checkout/전화/재고·최종 배송비/실제 배송, 원문 상하단 적용 우선순위는 미확인이다. 이 검수는 remote write/provider/IndexNow0, 신규 browser render0, 원본변경0이다. 최초 bs4 파싱은 ModuleNotFoundError로 실패했고 표준 HTMLParser로 대체하여15DOM을 완결했다. 원본 report의 pixelReview:pending/publicHTTPVerified:false는 그대로 보존했다.

## 증거 파일

- PIXEL-REVIEW.json: 판단·36PNG별 SHA/이전SHA/직접범위/캡처한계
- DIRECT-PIXEL-SCOPE-VERIFICATION.json, verify_pixels_scope.py, verification.log: 독립 비교 결과와 재실행 가능한 검증
- crops/article-320-full-7.png, crops/article-320-full-8.png, crops/article-390-full-6.png, crops/article-390-full-7.png, crops/article-1280-full-4.png: 새 문단 핵심 crop
- crops/article-320-full-8.png~10.png, crops/article-390-full-7.png~9.png, crops/article-1280-full-5.png: FAQ 전체 대조
- policy-originals/*-upper.png, *-lower.png: 결속된 상인 원문 상하단 직접 열람용 crop
