# Flower Matrix Prototype

이 폴더는 기존 "한 서브도메인 = 한 지역" Flower Local v2를 그대로 복제하는 사이트가 아니다.
검토된 Astro/SEO/상품/정책 자산을 재사용하되, 한 사이트 안에서 여러 지역 × 여러 상품군 조합을
정적 생성하고 동일 코드를 여러 사이트 인스턴스로 빌드하는 원형이다.

## 현재 안전 경계

- source branch: source/flower-matrix-prototype-20261020
- productionApproved=false
- prototype-a / prototype-b 모두 example.invalid origin, deployable=false
- 기존 지역 사이트 registry, Writer/Publisher, Cloudflare binding을 변경하지 않는다.
- 남동구 준비 commit 0823ce3551adcd17eaa98b2d757d1bd411077db5와 별개다.

## 현재 첫 검증 행렬

5 regions × 4 product groups = 20 detail pages.

Regions:
- 안산시
- 수원시
- 성남시
- 평택시
- 인천 남동구

Product groups:
- 근조화환
- 개업·축하화환
- 승진·취임 화분·난
- 꽃다발

Home 1 + region hubs 5 + product hubs 4 + detail 20 = 30 routes.

## 복제 방식

SITE_INSTANCE=prototype-a 또는 prototype-b를 선택하면 같은 코드와 지역/상품 데이터를 사용하고
사이트명, origin, 연락처, 디자인, 활성 지역/상품군만 인스턴스 설정에서 바뀐다.
qa_matrix.py는 다른 인스턴스 origin 누출, canonical, OG URL, sitemap, 내부링크를 검사한다.

실제 배포를 허용하려면 별도 검토 후 site-instances.json의 정확한 도메인과 deployable,
site-config.json의 productionApproved를 함께 승인해야 한다. example.invalid 상태에서는 indexable build를 거부한다.

## 상품 사실

product-sources.json은 fwith.co.kr 상품 코드와 원문 URL을 보관한다.
현재 가격을 재확인한 항목만 priceVerifiedAt이 있으며, C206의 과거 120,000원 값은
현재 가격 재확인 전에는 고객 화면 가격으로 표시하지 않는다. 상품 사진은 사용 허락 범위지만
현재 원형에는 원본 이미지 복사를 아직 수행하지 않았다.
