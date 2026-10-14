# 서초 현재 공식 사실 독립 검수

판정: **REVISE_ONE_UNSUPPORTED_FLOOR_CLAIM**

현재 고객 원고의 빈소층 문장 한 가지를 증거 범위로 좁혀야 합니다. 아래 나머지 확인 사실에서는 충돌을 찾지 못했습니다. 이 판정은 사실 검수에 한정하며 소스 저장, QA, 배포, 도메인 또는 공개 승인 완료를 뜻하지 않습니다.

검수 기준 시각: 2026-10-13 18:17:38 UTC. 이 보고서와 verdict.json은 수정 전 원고의 동결 검수 기록입니다. 후속 수정 검수는 새 파일·새 원고 해시로 분리하며 이 기록을 덮어쓰지 않습니다. 검수자는 소스·main·QA·외부 제공자 작업을 수행하지 않았습니다.

## 직접 확인한 수정 필요 사항

- 원고 위치: funeral → sections.seoul-st-mary-funeral 첫 문단과 중복 contentMarkdown, 총 2회
- 현재 문장: “공식 시설 안내에는 지상 1층부터 3층까지의 빈소가 나뉘어 있습니다.”
- 권장 최소 수정: “공식 시설 안내에서는 지상 1층부터 3층까지의 층별 정보를 안내합니다.”

공식 facilities HTML 592–619행에는 제단·접객실·예식실·휴게공간 이미지 항목, 지상1층·지상2층·지상3층 탭, 각 층 지도 이미지 링크가 있습니다. 각 층에 빈소가 있음을 설명하는 본문·호실표는 없습니다. 따라서 층별 안내의 존재는 직접 확인했지만 실제 빈소 분포를 확인했다고 할 수 없습니다. 이는 사실이 거짓임을 입증한 판정이 아니라 현재 근거가 문장을 충분히 뒷받침하지 못한다는 판정입니다.

[공식 시설 안내](http://kfh.catholicfuneral.co.kr/phgrp/cnts/CntsFrntView.do?cntsId=CFV_2030000&menuNo=2030000)

## 미확인 및 실패한 지도 확보

raw/funeral-floor-1.jpg, raw/funeral-floor-2.png, raw/funeral-floor-3.jpg는 모두 실제 이미지가 아닌 175바이트 HTML입니다. 실제 바이트를 cp949로 읽으면 “[웹방화벽] 비정상적인 접근으로 인해 차단되었습니다. (Web Application Firewall page block)”라는 문구가 있습니다. file 검사도 텍스트로 식별했고 view_image는 unsupported image data로 실패했습니다. HTTP 200만으로 이미지 확보 성공을 인정하지 않습니다.

세 파일 공통 SHA256: 96f9fe3fd96dda5c2f4f3664e014f8bdb64cb3aa05533e0c0ab465945933f743

실제 지도, 빈소 배치, 각 층 빈소 유무는 미검증입니다. 별도 공식 자료 검색에서도 보강 근거를 확보하지 못했으며 차단 우회는 하지 않았습니다.

## 직접 확인한 상품 사실

각 상품의 실제 저장 HTML에서 상품명, 판매가격, 배송비결제 문구, 추가 배송비 안내, 판매자 연락처를 읽어 원고와 대조했습니다. 모든 상품은 배송비 “주문시 결제”, 배송지에 따라 추가 배송비 발생 가능, 전화 1844-0644를 게시합니다.

- [B201 근조 3단 화환](https://fwith.co.kr/shop/item.php?it_id=B201): 59,000원
- [B203 근조 고급 3단 화환](https://fwith.co.kr/shop/item.php?it_id=B203): 79,000원
- [B205 근조 특대 3단 화환](https://fwith.co.kr/shop/item.php?it_id=B205): 109,000원
- [B060 근조 특특대 3단 화환](https://fwith.co.kr/shop/item.php?it_id=B060): 149,000원
- [C200 축하 3단 화환](https://fwith.co.kr/shop/item.php?it_id=C200): 59,000원
- [C203 축하 고급 3단 화환](https://fwith.co.kr/shop/item.php?it_id=C203): 79,000원
- [C204 축하 특대 3단 화환](https://fwith.co.kr/shop/item.php?it_id=C204): 99,000원
- [C205 축하 특특대 3단 화환](https://fwith.co.kr/shop/item.php?it_id=C205): 149,000원

상품사진 8개의 실제 픽셀을 열어 보았고 SHA256을 고객 원고와 보존 registry에 독립 대조했습니다. 8개 모두 동일하며 원고의 색상 묘사를 뒷받침합니다. 상품 실재고, 배송 실적, 현재 주문 가능 일정, 특정 시설 수령 가능성, 주문별 최종금액까지 확인한 것은 아닙니다.

## 직접 확인한 소재와 변경 안내

[구매 안내 이미지](https://fwith.co.kr/shop/img/order-top2.jpg)와 [교환·환불 이미지](https://fwith.co.kr/data/common/flower379/de_change_content.jpg)를 실제로 열어 읽었습니다. 생화·조화 혼합, 지역별 후다지 차이, 별도 수거 없음, 계절·지역별 소재 차이, 제작완료·배송 하루 경과·배송지 오류·수취거부의 교환·환불 제한, 불량·파손·전혀 다른 상품의 환불, 배송 불가·재고 없음의 전액 환불, 출고 뒤 취소 시 배송비 제외, 카드사 취소 처리 약 일주일 안내가 원고와 일치합니다. 판매자 게시 안내를 대조한 것이며 개별 주문의 법적 권리를 판정하지 않았습니다.

## 직접 확인한 시설 사실

### 서울성모장례식장

[공식 오시는 길](http://kfh.catholicfuneral.co.kr/phgrp/cnts/CntsFrntView.do?cntsId=CFV_1040000&menuNo=1040000)의 반포대로 222·반포동 505·02-2258-5940은 원고와 같습니다. 병원 전화 안내도 장례식장 안내 02-2258-5940을 게시합니다. 층별 빈소 주장은 앞서 설명한 증거 한계가 있습니다.

### 엘타워

[오시는 길](https://www.eltower.com/brand/route/)의 강남대로 213·양재동 24, [웨딩 안내](https://www.eltower.com/wedding/info/)의 그랜드홀 7층·그레이스홀 6층·오르체홀 5층·엘하우스홀 8층을 확인했습니다. [FAQ](https://www.eltower.com/concierge/faq/)는 담당자와 사전 협의한 행사물품 보관, 행사정보 표기, 미협의 또는 미표기 물품의 분실·파손 및 큰 물품 보관 한계를 안내합니다. 원고는 이를 화환 무조건 반입 허용으로 확대하지 않고 별도 수령 조건 상담으로 구분했습니다.

### aT센터

[제1전시장](https://www.at.or.kr/contents/acko321111/view.action)은 1층, [제2전시장](https://www.at.or.kr/contents/acko321121/view.action)은 3층이며 주소 강남대로 27·양재동 232도 일치합니다. [2026 전시장 운영지침](https://www.at.or.kr/file/center/conv04_260107.pdf)에서는 2026-01-02 시행과 전시장 층, 전시품 반출입 절차를 확인했습니다. PDF를 새로 pdftotext로 추출해 기존 추출문과 바이트 단위 동일함을 확인했으며 제공된 page1/page3/page6 렌더 이미지를 열어 관련 내용도 보았습니다. 전체 PDF 페이지를 시각 검수한 것은 아닙니다.

[2017-07-20 공지](https://www.at.or.kr/article/apko341b10/view.action?articleId=29423)는 웨딩홀에서 조화 사용 3단 화환 반입을 금지할 예정이라고 설명합니다. 이 과거 문구는 현재 전시장 전체 금지나 혼합화환 허용의 근거가 아닙니다. 현행 편의시설 페이지가 예식장 용도를 안내하지만 현재 화환 반입 허용까지 입증하지는 않습니다. 원고의 전시장 주최 측 조건 확인과 예식장 현재 반입 여부 미확인·주문 미안내 구분은 근거 범위에 맞습니다.

### 예술의전당

[현재 공식 대관규약](https://www.sac.or.kr/site/main/content/museumRentalAgreement)에서 2026·2027 규약 모두 전시장 내 화환 반입 금지를 읽었습니다. 전시장은 전시실과 로비 등 대여 가능한 부속 실내공간을 포함합니다.

- 2026 규약: 전시장 사용일 2026-04-01부터 2027-03-31
- 2027 규약: 2027-01-01 시행 예정, 사용일 2027-01-01부터 2028-03-31
- 경과조치: 2026 규약으로 체결했고 사용기간이 2027-03-31까지인 계약에는 2026 규약 적용. 2027-04-01 이후 사용 부분에는 2027 규약 적용

원고 sourceNote는 참조한 2026 규약 기간을 정확하게 적었습니다. 이를 모든 2027 계약의 유일한 적용 규칙으로 일반화해서는 안 됩니다. 본 검수는 개별 계약의 적용 규약을 판정하지 않습니다.

## 직접 확인과 도구 취득보고 구분

[직접 확인] 아래 23개 재취득 파일의 실제 바이트·SHA256을 다시 계산하고 보존 registry의 과거 지문과 대조했습니다. 보존 registry에 적힌 원본 경로는 모두 현재 존재하지 않습니다. HTML/PDF 21개 중 9개는 과거 지문과 정확히 같고 12개는 다릅니다. 별도 구매·환불 이미지 2개는 과거 지문과 같습니다. 제품사진 8개도 원고·registry와 각각 같습니다. 따라서 “원본 전부 복구”가 아니라 “현재 공식 자료 재취득, 그중 일부 과거 지문 일치”입니다.

[도구 보고] HTTP 상태, 최종 URL과 취득시각은 기존 fetch 도구의 보고입니다. 이 검수는 저장된 실제 파일 내용과 해시를 독립 확인했습니다. web 도구에서도 엘타워 웨딩·FAQ 및 예술의전당 규약을 다시 열어 관련 내용을 확인했습니다. 별도 funeral web 요청은 502, 일부 aT 요청은 internal error로 실패했으므로 그 경로의 성공을 주장하지 않습니다.

[추정·판단] 빈소층 문장은 층별 시설 안내 문장으로 최소 수정해야 합니다. 나머지 열거한 확인 범위에서는 실질적인 충돌을 찾지 못했습니다. 역사적 aT 공지를 현행 허용 또는 전시설 금지로 넓히지 않는 현재 원고 방식이 적절합니다.

[미확인] 실제 빈소 지도·배치, aT 예식장의 현재 혼합화환 반입, 재고·실제 배송·수령·최종금액, 개별 주문의 환불권리, 개별 대관계약 적용, 배포·QA·도메인 및 공개 승인 상태는 이 검수로 확인되지 않았습니다.

## 검수 대상 동결 해시

- seocho-banner-successor-local-20261013/source/src/data/seocho-copy.json
  - SHA256: 969ba9a80160dd808f9652a0e2ca66e920228f7532dbe44cdd726ec1a3139cf4
- seocho-banner-successor-local-20261013/source/src/data/seocho-ui-copy.json
  - SHA256: a7699c9a3a28665a606ee07951f083dd6571bd84405ba95dcba171dc9c1f6e92
- seocho-banner-successor-local-20261013/source/src/data/seocho-approved/plan/evidence-registry.json
  - SHA256: 710a20c75e9f4541e85d64160bc33703f64cdc2fd64d55b0191bc455b0bd7ce2
- seocho-current-facts-recheck-20261013/fetch-results.json
  - SHA256: f946bdc9f26645858f7ce096bb40b3dcb90796e69f348051b7fa6078bc535513
- seocho-current-facts-recheck-20261013/current-product-photo-readback.json
  - SHA256: 0bafaa3a6051a8453280a24f1839ac0f1130c3ebd3450f77fd1ac30eb8348179
- seocho-current-facts-recheck-20261013/current-floor-image-readback.json
  - SHA256: b345f42e16251021abf29467dba312f9efd7c2b8acc7fba7957dcb296a43ca87

전달된 945개는 소스 manifest 대상 개수입니다. 폴더의 단순 find 개수 977은 dist/cache 등 실행 산출물을 포함할 수 있어 소스 변경으로 판정하지 않습니다. 전체 트리 동일성은 이 검수 범위 밖이며 위 원고 2개와 근거 파일 해시에 판단을 고정했습니다.

## 재취득 원문 증거 목록

각 HTTP 상태와 취득시각은 verdict.json에서 도구 보고 필드로 보존했습니다. 아래 현재 SHA256 및 과거 지문 대조는 직접 재계산한 결과입니다.

- [funeral-route](http://kfh.catholicfuneral.co.kr/phgrp/cnts/CntsFrntView.do?cntsId=CFV_1040000&menuNo=1040000)
  - 파일: seocho-current-facts-recheck-20261013/raw/funeral-route.html
  - 현재 SHA256: d40ca7a34a6559604139badf4b1a806de717951391e44c3944e9d4c1f7fee378
  - 과거 SHA256: d40ca7a34a6559604139badf4b1a806de717951391e44c3944e9d4c1f7fee378
  - 과거 지문 일치: 예
- [funeral-facilities](http://kfh.catholicfuneral.co.kr/phgrp/cnts/CntsFrntView.do?cntsId=CFV_2030000&menuNo=2030000)
  - 파일: seocho-current-facts-recheck-20261013/raw/funeral-facilities.html
  - 현재 SHA256: 541a1e4e801de407558be6a35bd109ca857e245f36aa82424648c41da68fd7b5
  - 과거 SHA256: 541a1e4e801de407558be6a35bd109ca857e245f36aa82424648c41da68fd7b5
  - 과거 지문 일치: 예
- [hospital-phone](https://www.cmcseoul.or.kr/hospitalguide.phone_num.sp)
  - 파일: seocho-current-facts-recheck-20261013/raw/hospital-phone.html
  - 현재 SHA256: c482094ed7afc3f91e2792a8d76e55e35c3db84ff59715842fc36211d46cd494
  - 과거 SHA256: b5c6acd61feff56722c19df22b790b6594114c48b96e303b23270957af38444d
  - 과거 지문 일치: 아니오
- [eltower-route](https://www.eltower.com/brand/route/)
  - 파일: seocho-current-facts-recheck-20261013/raw/eltower-route.html
  - 현재 SHA256: 4c29eec4ee7386d23c2fc09060fad3fa2082312ddd782f62826a277964fc9180
  - 과거 SHA256: 4c29eec4ee7386d23c2fc09060fad3fa2082312ddd782f62826a277964fc9180
  - 과거 지문 일치: 예
- [eltower-wedding](https://www.eltower.com/wedding/info/)
  - 파일: seocho-current-facts-recheck-20261013/raw/eltower-wedding.html
  - 현재 SHA256: d99b3bc1c0630bd3ae88c9fdb245343ab1d355fb7bbf2f248f2669120ed4d269
  - 과거 SHA256: d99b3bc1c0630bd3ae88c9fdb245343ab1d355fb7bbf2f248f2669120ed4d269
  - 과거 지문 일치: 예
- [eltower-faq](https://www.eltower.com/concierge/faq/)
  - 파일: seocho-current-facts-recheck-20261013/raw/eltower-faq.html
  - 현재 SHA256: b2cd3066ff3fd4fb67c2ea4a270127c38a4219cb637250661bea4f156dbc8750
  - 과거 SHA256: b2cd3066ff3fd4fb67c2ea4a270127c38a4219cb637250661bea4f156dbc8750
  - 과거 지문 일치: 예
- [at-hall1](https://www.at.or.kr/contents/acko321111/view.action)
  - 파일: seocho-current-facts-recheck-20261013/raw/at-hall1.html
  - 현재 SHA256: 4cf3448724d4f12eca72818b1373d365dec74271a7128a5f1d4216237e48fc1c
  - 과거 SHA256: 4cf3448724d4f12eca72818b1373d365dec74271a7128a5f1d4216237e48fc1c
  - 과거 지문 일치: 예
- [at-hall2](https://www.at.or.kr/contents/acko321121/view.action)
  - 파일: seocho-current-facts-recheck-20261013/raw/at-hall2.html
  - 현재 SHA256: 514a3bc7fa4036c8b311d02047aa0b315c4172b46ff06a24588ab112b8a63a34
  - 과거 SHA256: 514a3bc7fa4036c8b311d02047aa0b315c4172b46ff06a24588ab112b8a63a34
  - 과거 지문 일치: 예
- [at-operating-guideline-2026](https://www.at.or.kr/file/center/conv04_260107.pdf)
  - 파일: seocho-current-facts-recheck-20261013/raw/at-operating-guideline-2026.pdf
  - 현재 SHA256: 803bccd25efe22968e241fbebc0c6b37a013725fc428cb655bbb2b2d22f658f8
  - 과거 SHA256: 803bccd25efe22968e241fbebc0c6b37a013725fc428cb655bbb2b2d22f658f8
  - 과거 지문 일치: 예
- [at-convenience](https://www.at.or.kr/contents/acko333100/view.action)
  - 파일: seocho-current-facts-recheck-20261013/raw/at-convenience.html
  - 현재 SHA256: d6cdc9bd72c38438935be441f0a6b06e247c675ba8e03ff2b203adda1385e533
  - 과거 SHA256: d6cdc9bd72c38438935be441f0a6b06e247c675ba8e03ff2b203adda1385e533
  - 과거 지문 일치: 예
- [at-2017-wreath](https://www.at.or.kr/article/apko341b10/view.action?articleId=29423)
  - 파일: seocho-current-facts-recheck-20261013/raw/at-2017-wreath.html
  - 현재 SHA256: ab3bc26ac6c938e5d004f473166e85e699fd052b676033ceb971950bfea7d93e
  - 과거 SHA256: f68288553c57af7bf3ec60e774e41a20d4b7c537374420177b28434429c13fff
  - 과거 지문 일치: 아니오
- [sac-museum-rules](https://www.sac.or.kr/site/main/content/museumRentalAgreement)
  - 파일: seocho-current-facts-recheck-20261013/raw/sac-museum-rules.html
  - 현재 SHA256: f7be712ea261ea1b37704449c20593543eeb8335a7c64b1645912ebacb856905
  - 과거 SHA256: f705bcaa31cded968da3dadd6f325d13ea9b326bf548cd1c12e9f4846eed5199
  - 과거 지문 일치: 아니오
- [B201](https://fwith.co.kr/shop/item.php?it_id=B201)
  - 파일: seocho-current-facts-recheck-20261013/raw/B201.html
  - 현재 SHA256: d5e2ffec12030ef8bff561f173747bb5673b4c13ea7c6e64a0477afe61435a53
  - 과거 SHA256: 28beebe534884e071090bd5044b593670c8fc8d9b8f02ebb5fe33cce7a9d800d
  - 과거 지문 일치: 아니오
- [B203](https://fwith.co.kr/shop/item.php?it_id=B203)
  - 파일: seocho-current-facts-recheck-20261013/raw/B203.html
  - 현재 SHA256: bf30871684574aa2c416250c33ff2ba0a83f5d9064afd09df871326a510b97b6
  - 과거 SHA256: 464393f66e923e326f3a077f161cd0bd28a79ec10fa5c6f6e8af9f041d8c76b6
  - 과거 지문 일치: 아니오
- [B205](https://fwith.co.kr/shop/item.php?it_id=B205)
  - 파일: seocho-current-facts-recheck-20261013/raw/B205.html
  - 현재 SHA256: 6d3e39e2eb3403dd1c55f070cc99b6c3d8455369c6cd596740c3bde6c0e3b706
  - 과거 SHA256: 0c3cc1347ea25f42fb145136d1fb771223443e72f0b0bc668cde356bf8b722d4
  - 과거 지문 일치: 아니오
- [B060](https://fwith.co.kr/shop/item.php?it_id=B060)
  - 파일: seocho-current-facts-recheck-20261013/raw/B060.html
  - 현재 SHA256: b9bfbf4710bc3d611df0a2fa9ec7dde1379ac6f66ab35b5f8bf71aae2b7fd84a
  - 과거 SHA256: d6c618f12c773e71a79ad6598850a6da65cf643aaa8c2f326a1f66b00fc9054e
  - 과거 지문 일치: 아니오
- [C200](https://fwith.co.kr/shop/item.php?it_id=C200)
  - 파일: seocho-current-facts-recheck-20261013/raw/C200.html
  - 현재 SHA256: 66fcdc6b423d97a37b47b2f643f6a807c726826b0b70cef1fe2d954045636113
  - 과거 SHA256: 6282016f1df8a7e2482d90ba08be221c706e9ade4927a453884e7b20c68ab9be
  - 과거 지문 일치: 아니오
- [C203](https://fwith.co.kr/shop/item.php?it_id=C203)
  - 파일: seocho-current-facts-recheck-20261013/raw/C203.html
  - 현재 SHA256: c5524d0593903e93e4c60ee90a9a04de768427f0d0296bc1ef1b5978c9ce847e
  - 과거 SHA256: 16f604a8d1d405e9d04fc76a2eb3dc3dc1ee13cf9242b1d3144e14f138f8c02d
  - 과거 지문 일치: 아니오
- [C204](https://fwith.co.kr/shop/item.php?it_id=C204)
  - 파일: seocho-current-facts-recheck-20261013/raw/C204.html
  - 현재 SHA256: bed53813e9b9d70816dec81d80da33ba4c4e7537a658290abfc3812e0691a09f
  - 과거 SHA256: d73d7e9f0146e0dffa55fd8f370e9d0837704b969b6a227b7e8552c1e2566c81
  - 과거 지문 일치: 아니오
- [C205](https://fwith.co.kr/shop/item.php?it_id=C205)
  - 파일: seocho-current-facts-recheck-20261013/raw/C205.html
  - 현재 SHA256: ffc33cbb03108ee46b1a274d89b495896fd86db40dc97368c4e2e06c802b552c
  - 과거 SHA256: 7b4c5bf08264aed7803e264bfe67c95928d5056f89ecf7bbd78fb9ff45b3a1d4
  - 과거 지문 일치: 아니오
- [order-policy](https://fwith.co.kr/shop/img/order-top2.jpg)
  - 파일: seocho-current-facts-recheck-20261013/raw/order-policy.jpg
  - 현재 SHA256: 24c11e1cc413d3f64ad05145fdc0fb4171c8f3e618d4351609777f8e2ff43bc3
  - 과거 SHA256: 24c11e1cc413d3f64ad05145fdc0fb4171c8f3e618d4351609777f8e2ff43bc3
  - 과거 지문 일치: 예
- [change-policy](https://fwith.co.kr/data/common/flower379/de_change_content.jpg)
  - 파일: seocho-current-facts-recheck-20261013/raw/change-policy.jpg
  - 현재 SHA256: 02701dd33c2a09258a882873df005dbe616842c2add159a08d618b68a934944c
  - 과거 SHA256: 02701dd33c2a09258a882873df005dbe616842c2add159a08d618b68a934944c
  - 과거 지문 일치: 예
- [eltower-home](https://www.eltower.com/index.jsp)
  - 파일: seocho-current-facts-recheck-20261013/raw/eltower-home.html
  - 현재 SHA256: 98b85317058017cc246b81964aa95b8e05002d9b6c6b54a3fa8665a9e10966f7
  - 과거 SHA256: e3c209faa49f7cc7dd3b10df7a84a370ca84217818c10431f7bb3799ecf7c7d5
  - 과거 지문 일치: 아니오

## 제품사진 해시

- [B201](https://fwith.co.kr/data/item/flower379/B201/thumb-1_500x500.jpg): 7556b6d29ff31e23da6e8e9cfc42b246974e8f8d5e3d3ba5b789fcd8341667f3
- [B203](https://fwith.co.kr/data/item/flower379/B203/thumb-1_500x500.jpg): 0db53ecefe21b765d042fc4ba96a58fff5287be7b15fbf26ff8d4e92095a5114
- [B205](https://fwith.co.kr/data/item/flower379/B205/thumb-1_500x500.jpg): 1873eb9037478de487a4141e0974b90c994cfd0432e07af818799947ce0db43e
- [B060](https://fwith.co.kr/data/item/flower379/B060/thumb-1_500x500.jpg): a336ca8434249feccafceb257c10acf1a3a81693b794682d29f0bf5d0057c1e3
- [C200](https://fwith.co.kr/data/item/flower379/C200/thumb-1_500x500.jpg): 0e5c0e37f5a02b0448a0dd9b3aa48c4bd1ebe38862a9dde662ef2e1c14eee905
- [C203](https://fwith.co.kr/data/item/flower379/C203/thumb-1_500x500.jpg): d3bd30015f4465f6db3d43c37a3088d383173e1bc0b46ff429ed24b9c251625a
- [C204](https://fwith.co.kr/data/item/flower379/C204/thumb-1_500x500.jpg): 05a71d0a3a624c7e27e0575baab02c21f87cc409a1de5389bd4c42b2789dc16d
- [C205](https://fwith.co.kr/data/item/flower379/C205/thumb-1_500x500.jpg): b0fa2c913adf258617e34ce0175cbdc282b83e6b47db556234380353c047d5e9

## 후속 재검수 조건

후속 수정자는 원고의 해당 문장 2개 표현 위치를 최소 수정하고 다른 승인 문구·사진·가격을 보존해야 합니다. 수정본에는 새 SHA256과 정확한 diff가 필요합니다. 후속 검수는 새 기록으로 만들어 본 검수 파일을 덮어쓰지 않습니다.
