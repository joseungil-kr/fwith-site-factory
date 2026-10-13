# Independent actual CI review: FAIL confirmed

Run https://github.com/joseungil-kr/fwith-site-factory/actions/runs/38335701874, attempt1, push, one Yeongdeungpo job. This run is failed and must remain failed.

## Direct verification
- Independently read actual GitHub commit/tree, all14 added blob payloads, run, job and artifact APIs. Control5cccbd024602e393e77ac3d5f7754ef3fc3247a4 / tree107f01cc9d67a861d37238d59689bc10a393b9e4 / parenta12c406b2d6b4254a7a5541e7d1e631bf09701f2 match the reviewed proposal exactly. All1113 prior non-tree entries remain unchanged.
- Run sourceccc6acd7a0f1beb20e4aa346b11ee35ae516ba58, site tree69e6a349b682e05e168dc3f2e260e517d254108e, repository tree8f38fc32a55435e99d1379ac87253ffc356c895e match the previously independently verified308-file source. Runner binding, revision facts, evidence manifest and workflow pins agree.
- All five downloaded ZIP byte lengths and SHA256 digests match the independently obtained artifact API metadata and exact run/head. All ZIP CRCs pass. Reviewer independently extracted to a separate directory and checked all121 evidence-manifest file hashes,122 files including the manifest itself. Both deterministic build manifests and all21 dist bytes match. No unverified screenshot substitution was used.
- Re-executed recorded-facts assertions without a browser or sockets:267 complete ordered geometry cases including15 header-special checks and15 footer-content checks;32 representative screenshots and24 initial-anchor screenshots;27 interactions. Supplemental selection/reasons, signature deduplication, image dimensions and hashes all reconcile. Screenshots are evidence of the reported failure, not grounds to override it.
- Opened all78 captured image files:15 full-page JPEG overviews,32 focused JPEGs,24 initial-anchor JPEGs and7 retained native PNGs. Detailed path/hash/observation inventory is pixel-review.json. Long full-page text was corroborated with readable focus views and recorded DOM data. Native element captures include sticky UI at the capture scroll position; supplemental safe-area and first-landing captures provide the relevant readability evidence.
-853 recorded response URLs are loopback HTTP; none external. Console/page-error arrays are empty. Playwright1.63.0 and Chromium153.0.8010.12 are recorded. Font log identifies Noto Sans CJK KR. External order/phone links were inspected, not activated against their remote destinations.

## Confirmed source defects
1. 320px home: full-page JPEG is321px wide, scrollWidth321. Right hero card reaches outside expected content margin; recorded A.hero-product width147.375. The unchanged capture assertion rejects Horizontal overflow and exact image width. The intrinsic minimum of 1fr tracks plus nowrap price prevents shrinkage. Hiding overflow or relaxing tolerance is not an acceptable fix.
2. Funeral initial anchors: all five H3 targets at320/390/1280 land near top0, underneath safeTop63/71. All nine heading hit tests are false. All15 relevant screenshots visibly hide the heading. Wedding H2 targets pass at all widths. Frozen CSS has90px scroll margin for H2 but none for H3. Centered geometry passes do not erase the initial-landing defect.

No additional source defect found in the selected views. Focused banners preserve full artwork and readable AI provenance captions; complete FAQ answers, footer links above CTA, longest legal/admin rows and final rows are readable. The machine and pixel evidence are consistent.

## Runner reports inspected
The unchanged native browser report passes15 route/viewport checks; the additive settled capture correctly fails the320px home. Original native checks alone are therefore insufficient evidence of final layout. Native build/test/QA logs report two successful runs,120 Node tests each; control offline tests report65 passing. These processes ran in CI, not in the reviewer's workspace. Reviewer independently checked their resulting dist bytes, logs and report assertions.

## Correction and limits
The separately reviewed candidate changes only global.css: anchored H3 scroll-margin90px, narrow hero zero-minimum tracks/item and wrapping price. Source-save-only review is ../source-fix/FINAL-SOURCE-FIX-REVIEW.md. It is not a corrected browser PASS. A new committed source SHA/tree, immutable corrected source manifest and reviewed rebind must precede a new authorized CI run. Keep this failed run and original source/copy approval manifests unchanged.

No public deployment, HTTP, search/indexing, live phone/order action or publication authorization was verified. Current data remains productionApproved=false, noindex, empty sitemap scope. Reviewer made no remote writes, no CI triggers, and ran no local Chromium/socket server.

## Revalidation notes
Reviewer script first applied content-band rules to header rows; actual adapter intentionally checks the header itself for visibility/hits instead. It also first passed outer facts rather than facts.extra to the extra-facts validator. These harness mismatches were corrected to the reviewed runtime's exact rules; all expected failures above were then reproduced. No guard or artifact was changed. Initial Git Blob API decoding likewise required treating connector-returned content as decoded bytes rather than JSON; all14 blobs were subsequently rehashed independently.

Evidence: control-run-binding-verification.json; run.completed.remote.json; artifacts.remote.json; artifact-integrity.json; report-revalidation.json; pixel-review.json; original independently extracted evidence/.
