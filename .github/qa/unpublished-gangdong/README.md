# Gangdong runner-loopback QA controls

Status: **local candidate, offline checks only**. These files do not establish a browser result, GitHub run, deployment, public availability, ownership verification, or search submission.

## Immutable scope

- Repository: `joseungil-kr/fwith-site-factory`
- Existing QA base: `136fa1c87e5fce4041817f7e6fa3a79a90fe9643`
- Proposed isolated branch: `qa/gangdong-local-preview-20261014`
- Source commit: `9c044584505eec60c71f2bc7add497f0902f5424`
- Source parent: `318e33a6430506d138eda8c4cb736159c61927a4`
- Repository tree: `ed67c4474d713452e51b2abbc5dd7119a0d4787f`
- Project tree: `a7e8ff540822dc7ee326f1503a9a2bbccf07f996`
- Project: `site-factory/seoul-gangdong-flower`
- 69 frozen source files: `7d483a76b13f07251b4b12baac3c8f0517d9c7735a642df9ce94c73acbae3137`
- 21 frozen output files: `a848243530757c43133c4b1645abc5619cb03c8fddf5039b004e679d200e1cc3`
- Exact dependency lock SHA-256: `cb4632b121bee8506eae3b629362c4618c9e9e27b4f6e240faa27f5d253ac749`

The source is `LOCAL_PREVIEW`, uses `https://seoul-gangdong.local.invalid`, has an empty sitemap, and keeps indexable, production, public, ownership and IndexNow flags false. Its 249 customer strings remain frozen. No source change, revision injection, public-mode substitution or banner re-encoding is permitted.

## Deliberate reuse and schema adaptation

`upstream/controls.py` and `upstream/capture.py` are byte-identical copies from the verified QA base; their SHA-256 values and repository paths are in `reuse-provenance.json`. The adapter reuses the loopback-only server, strict path resolver, request guard, JPEG dimensions/hash utilities and lazy-image/font/two-paint-frame settling. Scroll-only safe-band and focus checks are explicitly adapted from the source-bound Gwanak capture approach.

Gangdong does not contain the older `qa_browser_rendering.py`, `pages.json`, `site-config.json`, or revision meta tag. Consequently the legacy browser entrypoint is not invoked or represented as an unchanged native pass. The unchanged Gangdong native gates are `npm run build`, `npm test`, and `npm run qa`. The additive browser adapter uses `gangdong-runtime.json`, `[data-page-id]`, source-card links, native `<details>` menu, and product SKU selectors. The precomputed DOM contract binds all anchor hrefs and the complete viewport-specific keyboard sequence to exact frozen HTML hashes.

## Future runner requirements, not executed locally

The new job requires an exact repository/ref/push event, actor and triggering actor `joseungil-kr`, run attempt 1, immutable source identity, and clean source/control checkouts. Source checkout depth 2 allows parent verification. The actor guard is based on retained historical push run `38428439688`; the actual future run actor and trigger must still be independently verified.

Runner-only dependencies are Node 24 with the source's locked Astro 7.3.5 dependency graph, `npm ci --ignore-scripts --no-audit --no-fund`, official `playwright==1.63.0`, its Chromium, and `fonts-noto-cjk`. Every native gate runs twice; both 21-file outputs must equal the original frozen manifest, not merely one another. All tracked repository changes, project source bytes/modes, and output bytes are checked before/after.

The old `visual-evidence` job, its old branch guard and all 64 other workflows are unchanged. Only the existing generic workflow receives an added branch/path filter and one separately guarded Gangdong job. No new dispatch, write permission, secret, public operation, DNS, deployment, or IndexNow capability is added.

## Required browser observations

For each of the five routes at 320×740, 390×844 and 1280×900:

1. Exact metadata, visible H1/first answer, frozen DOM links, FAQ questions and full answers, source-card links/note, required anchors, no horizontal overflow.
2. All images scrolled into view, fully decoded, and painted before full-page screenshots. Three banners retain intrinsic 1774×887, 2:1 contain geometry and approved identity. Eight distinct SKUs retain matching product image/link/name/price/description/sample labels, 500×500 intrinsic dimensions and square contain geometry.
3. Actual full-page JPEG plus separate unaltered risk-viewport screenshots for header, footer, H1/answer, banners, each product image/description/sample/CTA, FAQs, section headings, source links, directory cards and facility subanchors.
4. Native mobile menu click open/close, Enter/Space toggles, and actual distinct local navigation, Back, Forward, Back, reload; desktop visibility checked separately. Menu-open and final keyboard-focus screenshots are retained.
5. Every expected focusable element reached in the exact frozen DOM order; real focus outline, bounds and hit-test evidence checked. No tel or external link activation.
6. Every internal URL/hash resolved and screenshot captured on its first landing, without corrective centering. A distinct initial document prevents same-document `goto` returning no response. Hash target geometry is checked without changing source DOM/CSS.
7. Real missing-route HTTP 404 and browser 404 both return the exact frozen error body. `/404.html` itself returns 200. Only the exact missing-route Chromium resource error is classified as expected; all other browser/page/network failures fail.

Only HTTP GET/HEAD on the chosen 127.0.0.1 port are permitted in browser contexts. Service workers, external requests, WebSockets, downloads and external/tel/checkout navigation are forbidden. The browser entry guard runs before importing Playwright.

## Evidence and limits

Reports distinguish immutable source/static results, observed browser results, screenshot bytes/SHA/dimensions, and GitHub upload receipts. A machine success remains `machine-checks-only-awaiting-independent-pixel-review`; `pixelReview` stays pending and public HTTP verification false.

Evidence is partitioned without omission into reports, frozen dist and 15 route/viewport screenshot groups. Each group is below 24 MiB uncompressed with per-file overhead allowance, safely below the 32 MiB retrieval limit. A separate index lists every original evidence path once, and upload receipts bind unique artifact IDs/URLs/digests to the exact source/control/run/attempt. Receipts alone do not prove successful independent download. A bounded diagnostic artifact is retained even if grouping fails. Missing/partial browser evidence is explicitly labeled incomplete or failed.

The offline tests use synthetic JPEG headers and synthetic browser facts only to test rejection behavior. They never assert screenshot or browser success. Run them with `PYTHONDONTWRITEBYTECODE=1 GANGDONG_TEST_SITE=/absolute/frozen/project python3 test_controls.py -v`. On the runner `SOURCE_ROOT` selects the source project; prebuild output-only tests are explicitly skipped until the native build steps compare the actual output.

Remaining gates: independent final local control review, separately authorized exact control save/run, actual run/actor/commit readback, all artifact archive downloads and hash/manifest checks, and independent pixel inspection of the screenshots. Any source/layout failure requires a separately reviewed successor source; these controls do not edit frozen content to make checks pass.
