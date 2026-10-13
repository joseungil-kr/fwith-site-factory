# Independent three-region QA artifact baseline verification

Verified 2026-10-13 UTC. Scope: immutable recovered source snapshots and exact unpublished CI artifacts. No remote mutation, browser launch, socket server or package/network installation was performed. All generated verification files and isolated test copies remain under this directory.

## Directly verified results

- Reconstructed full Git repository tree and regional site subtree from actual recovered file bytes and modes. All six tree IDs match the pinned manifests. Fresh read-only GitHub Git-commit API responses independently bind each exact source SHA to the matching reconstructed repository tree.
- Geumcheon: source bbb016305dd2fe29f7d985a669acaa02224a9f2f, site tree 1f2397c6a00c34e74ec2d3441001b233934fbb25; run38318719004.
- Yeongdeungpo: source ca5c98b12420212d0aa8dd0c9a742f3e94237c07, site tree 2fd8165667a6d6e656b3c52a5ee50b6f07f47953; run38338256404.
- Dongjak: source430dada32f3f8b53f24aec8d9fdf3724529604e1, site tree a032dbdad16e044af8bca7163e26ca795f3b7d6c; run38343055625.
- All267 manifest-listed files are now locally present and independently SHA-256 verified, with zero missing or mismatched files:52/121/94 respectively. This includes all153 screenshots (19/78/56), all53 dist files (16/21/16), native reports and logs. Reports/dist ZIPs plus downloaded native/supplemental/full-page archives have valid CRC, sizes and SHA-256 matching the original recorded API artifact metadata. Geumcheon's12 full-page JPEGs were reused from main and directly hashed against the exact original manifest.
- Every dist file equals both first-build and second-build CI manifests. Each HTML output has the exact source revision marker. All13 HTML routes have exactly one H1, no empty image alt and no duplicate IDs. All internal anchor destinations, local assets and referenced fragments resolve to actual output files/IDs. Source-native static QA independently rechecked metadata, rendered copy, FAQ, product/SKU price and link bindings, banner identities/order and geographic links.
- On isolated copies, all three npm test and npm run qa commands completed with exit0. Node tests executed, including inherited suites: Geumcheon131+116=247; Yeongdeungpo131+116+120=367; Dongjak131+116+120+79=446. Python static/mutation tests:34/45/54. No test assertion was edited. Running each original production guard with SITE_INDEXABLE=true failed with its expected unapproved-template error and exit1.
- Independently reasserted source revision, canonical, robots, one-H1, no horizontal overflow and loaded images over all117 saved fact sets:39 route/viewport captures, three phases each, at320/390/1280px. These are assertions on recorded original browser facts, not newly executed browser sessions.
- Opened and visually inspected17 exact saved images: for each region mobile home, mobile detail top, desktop detail top, mobile FAQ and320px404; plus Yeongdeungpo's corrected320px price-wrap view and Dongjak's320px first facility anchor. Product imagery, Korean text, CTA layout and selected FAQ/anchor content are visible and readable in the sampled viewport images. No new blocking defect observed within that sample. The other136 screenshot bytes were verified but were not newly opened; their complete prior independent pixel reviews remain explicitly referenced below.
- Existing main evidence is consistent with recovered evidence: Geumcheon main evidence-manifest equals the recovered one; Yeongdeungpo and Dongjak main corrected-run machine-reports ZIPs equal the recovered reports ZIPs byte-for-byte. Earlier pending machine labels are preserved historical states, while the separate independent pixel reviews provide the later unpublished-QA result.

## Actual preview behavior and release boundary

- All three source configs are productionApproved=false. Every HTML page currently has noindex,nofollow,noarchive. robots.txt is exactly User-agent:* plus Disallow:/. No sitemap file exists, matching the intentional empty preview sitemap scope. _headers likewise preserves the preview noindex response policy.
- Geumcheon canonical origin is https://seoul-geumcheon.fwith.kr; Yeongdeungpo is https://seoul-yeongdeungpo.fwith.kr; Dongjak is https://dongjak-preview.invalid. Each404 has no canonical and stays noindex. Dongjak also has hostnameOwnershipVerified=false.
- 404.html content and navigation are verified as actual bytes and sampled pixels. Opening /404.html as an ordinary runner static file returned200 in the saved browser report. That does not establish real unknown-path HTTP404 behavior, which must be tested on the final deployment.
- Each one/two-card /regions/ directory is intrinsically noindex and sitemap-excluded even after a production release; source code preserves the <3 threshold.

## Tool reports, independently bounded

Fresh GitHub run API reads report completed/success for the specified attempt1, expected control SHA, branch, event and workflow. Native log files report two successful test/build/QA cycles and Astro checks with zero errors/warnings. The downloaded output and independently rerun source/static tests corroborate those reports. This review did not rerun Astro compilation or a browser: no installed dependencies were added, and original browser restrictions were respected.

## Judgment for an approval-only successor

These are trustworthy exact unpublished baseline artifacts. A narrow release successor can reuse their existing visual review only after proving the unchanged visible-output contract against these53 dist files: preserve customer copy, HTML body and structural markup, route set, anchors, product/brand/banner assets, CSS, fonts and interactions. Explicitly review only authorized nonvisual differences such as revision markers, production/ownership configuration, canonical origin, robots metadata/headers, robots.txt, sitemap outputs and approved public proof addition. Dongjak must replace its reserved preview origin; that change cannot be missed. This report does not verify any successor that has not yet been produced.

Required successor checks remain: exact diff/source readback, fresh build/test/static gates, deterministic output manifest and baseline-normalized output comparison; then actual public HTTP/status/content/links/canonical/robots/sitemap/unknown-path404 checks after release. A layout, copy, asset or interaction difference requires renewed relevant visual QA rather than labeling it metadata-only.

## Unverified / not claimed

No public deployment, DNS/host ownership, live HTTP, real phone/order checkout, IndexNow receipt or search indexing was established by this review. Existing source and main records cannot themselves grant permissions. No current market/product-price refresh or external facility assertion audit was performed; this task verifies the exact previously reviewed source/output contract. Success is limited to baseline source/artifact integrity and the offline checks described above.

## Original references

- Geumcheon: main/docs/direct-regional-release/unpublished-visual-qa-20261012/independent-visual-review.json and qa-evidence-summary.json; https://github.com/joseungil-kr/fwith-site-factory/actions/runs/38318719004
- Yeongdeungpo: main/docs/direct-regional-release/seoul-yeongdeungpo/visual-qa/20261013/corrected-run/independent-review.md and summary.json; https://github.com/joseungil-kr/fwith-site-factory/actions/runs/38338256404
- Dongjak: main/docs/direct-regional-release/seoul-dongjak/visual-qa/20261013/corrected-run/independent-review.md and summary.json; https://github.com/joseungil-kr/fwith-site-factory/actions/runs/38343055625

## Verification evidence in this directory

- baseline-integrity.json: reconstructed trees, per-file dist SHA-256, actual parsed HTML metadata/links, original logs and preview configuration.
- complete-evidence-verification.json: all267 sealed file hashes, artifact ZIP checks,117 fact-set assertions, source test rerun results and network-report readback.
- pixel-spot-review.json: exact17 newly opened image paths/hashes and scope.
- {region}-git-commit-api.json and {region}-run-api.json: compact fresh read-only identity/run responses.
- {region}-rerun-node-tests.log, {region}-rerun-static-qa.log and .exit files: actual independent command output.
- {region}-production-guard.log and .exit files: successful negative guard checks.
- verify.py, verify_evidence.py and finalize_report.py: reproducible verification helpers.
