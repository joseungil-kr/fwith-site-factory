# Independent Dongjak first actual-run review

Verdict: FAIL_PRESERVED_ADAPTER_404_CONTRACT_MISMATCH_CONFIRMED.

## Direct evidence
- Source 430dada32f3f8b53f24aec8d9fdf3724529604e1, actual control 57b63dc8a037b7a25e55c1cd40f2af5ed0ef54b3 / tree 6dd07c2586ce4d0e67162455b02434fc7d6c71ea / parent 34a6c6f4aa9b0d5d031e378c245a437e2fafc5fb; run 38341440858 attempt 1, one push job 115113099565. Independent GitHub commit/tree/ref/run/jobs readbacks and 18 full decoded payload comparisons confirm exact accepted additions, preserving 1,130 base files.
- Run conclusion is failure at the browser gate. Native build/test/two-build stages and all five artifact uploads completed successfully. Independently verified five archive API sizes/SHA-256 digests, every ZIP CRC/safe member and all 94 runner-manifest files. There are 95 extracted files including the manifest.
- Independently reran saved-data assertions without sockets. Native 12 checks pass; all 150 supplemental geometry/occlusion rows, 31 focus screenshots, six initial anchors and nine interactions meet the existing assertions. All nine non-404 route/width rows pass both initial and final facts. 437 recorded browser responses are runner-loopback only; no console/page errors. Both CI build manifests match the independently accepted actual-source 16-file local output.
- Opened all 56 actual screenshots: 12 full pages, 31 focused viewports, six first-anchor landings and seven native images. Long images were inspected in contiguous full-resolution tiles with a path/offset map. No additional source layout defect was observed. Both facility H3s are visibly below the sticky header at all three widths. Prices, product cards, FAQs, legal/admin text, banners/captions and readable footer focus evidence are intact. Four decoded product JPG assets are not counted as extra screenshots.

## Failure and classification
All three 404 route/width rows stop at upstream capture.py's generic `CTA order href` assertion. Independently replaying initial/final facts reproduces precisely that failure six times. The approved pinned 404.astro uses the source-approved notFound copy and guide CTA; its layout supplies phone/home/directory links, with no external store order link. Actual 404 pixels and all recorded href/text pairs match this source behavior. The unchanged native gate itself passes the 404.

This is a reused adapter contract mismatch, not evidence of a source defect requiring a new order CTA. The prior offline preparation review missed this route-specific assumption. The first run and all original reports remain FAILED and immutable; later analysis does not relabel them PASS.

## Required bounded correction
Keep source and upstream/native guard bytes unchanged. Add a strictly source-bound 404 contract for exact H1 and complete href/text sequence. Handle only this exact route and the exact missing-order assertion; preserve all upstream checks before it and explicitly run the skipped font-ready check after it. Non-404 store requirements and every other exception remain failures. Require mutation tests for route/source drift, wrong or missing phone/guide/home/directory anchors, unexpected external links, bad official-store hostname, font readiness, overflow, canonical/robots/revision, and unrelated upstream exceptions. Do not mutate facts or synthesize an order link to make the old assertion pass.

A separately reviewed minimal adapter correction, actual control save/readback, one authorized new CI run, artifact binding and pixel review are still required for browser PASS. Public deployment/HTTP/IndexNow remain unverified. No local browser/socket, remote write or CI trigger was performed by this reviewer.

Evidence: artifact-integrity.json, control-run-binding-verification.json, report-revalidation.json, pixel-review.json, pixel-sheet-map.json and independent API readbacks. Run URL: https://github.com/joseungil-kr/fwith-site-factory/actions/runs/38341440858
