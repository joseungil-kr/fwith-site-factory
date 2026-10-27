# 날마다꽃 flower.nalmada.net — 1,080장례식장 페이지 운영 도메인 연결 기록

검증일: 2026-10-27 (Asia/Seoul)  
범위: **홈 + 전국 장례식장 1,080개 HTML + 지역 검색 JSON + 정적 이미지**

## 1. 실제 운영 도메인 연결

- 정확한 새 호스트: **https://flower.nalmada.net/**
- Cloudflare Zone: `nalmada.net` (V4 운영 도메인과 Worker 매핑을 통해 기존 소유 계정 검증)
- 기존 연결: 없음. 공개 DNS A/AAAA/CNAME/TXT 모두 NXDOMAIN 확인 후 신규 Cloudflare Worker Custom Domain 생성. 기존 DNS 레코드나 V4 운영 Worker를 덮어쓰지 않음
- 연결 Worker: `sfv5-nalmada-flower-preview`
- 활성 검수 산출물 버전: `92ed9a9f-2179-44c4-a223-8ff7a51a506a`
- 원본 코드: `joseungil-kr/site-factory-v5` SHA `30c8f5a2507df1da3073e9c236c0ba697c39962b`
- [도메인 연결·Cloudflare API readback·HTTP 200 검증](https://github.com/joseungil-kr/fwith-site-factory/actions/runs/40446483854): SUCCESS

## 2. 독립 전체 HTTP 검사

[GitHub Actions run #40446620487](https://github.com/joseungil-kr/fwith-site-factory/actions/runs/40446620487): SUCCESS

- 장례식장 1,080개 고유 `/fh-<id>.html` 링크에 대해 HTTPS GET 수행
- **200 응답 1,080개 / 오류 0개**
- 각 본문: `날마다꽃`, `근조화환 주문 가격안내`, 실제 원장의 해당 장례식장명 포함 확인
- 모두 `<meta name="robots" content="noindex,nofollow">` 포함 및 `X-Robots-Tag: noindex` 확인
- `/`, `/halls.json` (1,080개), `/robots.txt`, `/assets/css/site.css`, 공통 상품 이미지 5개가 모두 HTTP 200
- `robots.txt`: `Disallow: /` (검색 색인 차단 유지)

## 3. 제한 및 주의

**1080개 페이지는 실제 외부 접속 가능한 공개 상태이나 검색 색인은 차단 중입니다.**

원본 시설 데이터에는 `publicationAllowed=false`, 문구 원본에는 `readyForPublication=false`가 기록되어 있고 시설 주소·운영상태는 아직 외부 확인 전입니다. 별도의 상품 현재 가격·지역별 배달 제약 및 사실성 검수 없이 `index,follow`/사이트맵/IndexNow를 자동 실행하지 않습니다.

사용자 승인 범위는 `flower.nalmada.net` 전체 페이지 배포입니다. 별도 V4 사이트·도메인·Secrets/보안 정책·광역 DNS 레코드는 수정하지 않았습니다.
