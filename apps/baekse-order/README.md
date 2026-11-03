# 백세푸드 원재료 주문·재고·거래명세표 (2026-11-03)

기존 Site Factory 성공 경로(독립 branch -> GitHub Actions 테스트 -> Cloudflare Workers 배포 -> 실제 HTTP 확인)를 재사용하는 **독립 업무 웹앱**입니다. 기존 꽃배달·Baekse 웹사이트 소스를 건드리지 않습니다.

## 기능
- 초기사용 제품: 잉어반죽 6,850/11,000, 팥앙금 5,150/9,000, 슈크림 5,150/9,000, 어묵 4,500/7,000, 주전자 9,000/10,000, 갈고리 1,500/2,000원 (매입/출고, **출고가는 VAT 제외**).
- 거래처 상호·이름·전화번호 필수, 사업자번호·주소 선택; 최초 안산 중앙점은 실제 이름·전화번호를 수정해야 출고할 수 있습니다.
- 제품·거래처 등록·수정·비활성화; 과거 거래 기록은 삭제하지 않습니다.
- 입고·반품·재고실사 조정, 단일 SQLite Durable Object를 이용한 일관된 재고 차감·취소, 감사로그.
- 일일 출고 등록 및 **기타(직접입력)** 품명·수량·단가, 재고 비추적.
- 부가세 10% 별도 합산 또는 부가세 미계산. 미계산은 법적 면세를 뜻하지 않습니다.
- 발행 당시 거래처·상품명·단가 스냅샷, 거래명세표 A4/PDF(브라우저 인쇄) 및 58mm/80mm 인쇄 CSS.
- 인증 쿠키 HttpOnly/Secure/SameSite=Strict, Origin 확인, 익명 API 차단, 실패 로그인 IP별 시도 제한, 백업 JSON 다운로드.

## 로컬 테스트
```bash
cd apps/baekse-order
npm test
npx wrangler@4.148.0 dev --local --port 8787 --var ADMIN_PASSWORD:replace-with-local-testing-password
```

## 배포 설정
1. `fwith-site-factory` repository GitHub Actions의 기존 `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID` 사용.
2. GitHub repository Actions Secret `BAEKSE_ORDER_ADMIN_PASSWORD`에 12자 이상의 안전한 관리자 비밀번호를 등록해야 합니다. 채팅/PR/로그에 비밀번호를 넣지 마세요. 미설정 상태에서 로그인 API는 503으로 실패합니다.
3. Cloudflare Free Worker 100개 계정 한도 초과 오류 **10037** 확인됨. 운영 도메인에 이미 붙어 있는 Worker는 절대 재사용 금지. 완전히 사용되지 않는 QA Worker를 충분히 검증한 뒤 재배포하거나 적법하게 여유 슬롯을 확보해야 합니다. 임의 삭제·기존 도메인 덮어쓰기는 하지 않습니다.
4. `order.baeksefood.com`은 Cloudflare의 활성 `baeksefood.com` 영역에 있고 Worker custom domain 기존 매핑은 없었습니다. DNS API 목록은 배포 토큰에서 403. Custom Domain 추가에는 Zone > Workers Routes > Write 권한이 필요할 수 있습니다.
5. 도메인 연결 후 실제 HTTPS 200, 인증 전 API 401, 관리자 로그인, 실제 재고 CRUD/취소, 모바일 폭 390px·PC 1440px 및 영수증/A4 출력으로 운영 검증합니다.

## 테스트/배포 근거
- GitHub Actions `Baekse Order build and deployment capability check` 성공 (run 41569038606, 5/5 tests).
- `Baekse order isolated Worker deploy` (run 41569158032) 실패, **Cloudflare 100 Workers limit, code 10037**. 운영 파일은 배포되지 않음.
- `Baekse order find unused Worker` (run 41569252414) Cloudflare 스크립트 108개/커스텀 도메인 95개, QA 미연결 후보 조사만 완료(미사용 확정 안 됨). 기존 서비스 무변경.

## 보안 및 제약
Cloudflare 무료 사용량과 클라우드 저장비는 플랜에 따라 변할 수 있습니다. `workers.dev` 및 맞춤 도메인은 정적 로그인 화면까지 공개되지만 세부 거래 데이터는 관리자 로그인 전 절대 반환하지 않습니다. `BAEKSE_ORDER_ADMIN_PASSWORD`는 GitHub Actions에만 추가하고, 배포 시 Worker secret으로 저장해야 합니다.

PDF는 네이티브 PDF 엔진이 아니라 브라우저의 인쇄 대화상자에서 'PDF로 저장'하는 방식입니다. 58/80mm는 인쇄용 스타일만 준비되어 있으며 각 프린터에서 실제 폭·잘림 검증이 필요합니다.
