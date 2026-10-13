# Unpublished regional source visual QA

**PASS for the exact saved-source, runner-loopback scope only.** All 51 original JPEG captures were independently opened and inspected. No blocking visual defect was found. The three sites remain unpublished, and this evidence does not grant release approval.

## Run and immutable inputs

- [QA control commit a12c406b](https://github.com/joseungil-kr/fwith-site-factory/commit/a12c406b2d6b4254a7a5541e7d1e631bf09701f2)
- [GitHub Actions run 38318719004, attempt 1](https://github.com/joseungil-kr/fwith-site-factory/actions/runs/38318719004)
- Gangseo source: `f7f2b9d017b8b8352aae8b0339b5a2cac0da1d32`; 7 routes × 3 widths = 21 captures
- Guro source: `500d82d01c1cdaed3ebde047bb3ce056705daac1`; 6 routes × 3 widths = 18 captures
- Geumcheon source: `bbb016305dd2fe29f7d985a669acaa02224a9f2f`; 4 routes × 3 widths = 12 captures

Widths are 320, 390 and 1280 pixels. Every home, directory, detail and local `/404.html` route was covered. Playwright 1.63.0 used Chromium 153.0.8010.12 with Noto Sans CJK KR. Source checkout bytes, site and repository trees, original browser script blob, source approval facts and canonical origins were checked before execution.

The original native build, test, QA and browser assertions ran unchanged. Each source was built twice, with identical complete file manifests. The supplemental browser pass decoded images, waited for fonts and paint, captured all routes, and checked safe internal navigation, Back and Reload. Telephone and shop anchors were inspected without opening calls or external orders. All 1,931 recorded network responses were runner-loopback HTTP 200; no external attempt, page error or console error was recorded.

## Review and preserved original screenshots

- [Independent visual review](independent-visual-review.json)
- [Bound summary and all 18 artifact IDs/digests](qa-evidence-summary.json)
- [Preserved file mapping and SHA-256 hashes](preserved-files.json)
- Gangseo: [320](gangseo/screenshots/320/) · [390](gangseo/screenshots/390/) · [1280](gangseo/screenshots/1280/)
- Guro: [320](guro/screenshots/320/) · [390](guro/screenshots/390/) · [1280](guro/screenshots/1280/)
- Geumcheon: [320](geumcheon/screenshots/320/) · [390](geumcheon/screenshots/390/) · [1280](geumcheon/screenshots/1280/)

All 51 JPEGs here are the exact original artifact bytes, without cropping, recompression or modification. The independent reviewer inspected all full-page images; long 320-pixel detail pages and the Geumcheon 390-pixel detail were additionally inspected end-to-end using original-width analysis crops. Temporary crops and contact sheets are not stored in this repository.

The original automated `capture-results.json` and `evidence-manifest.json` retain `pixelReview: pending`: they predate the independent review. Their bytes were not rewritten. The later verdict is recorded separately in `independent-visual-review.json`.

## Artifact retention boundary

This documentation preserves a deliberate subset of the full CI artifacts: all 51 original JPEGs, the three native browser reports, capture/source/network/console reports, and both build/test log sets. The `build/` directories are byte-identical copies of the artifacts' original `logs/` paths.

Original evidence manifests describe the entire 190-file artifact set, including 67 `dist/` files and 21 native PNGs that are **not duplicated here**. The artifact ZIP IDs and SHA-256 digests are recorded in the summary and independent review. Actions retains those ZIPs for seven days; their recorded identities, full manifest hashes and source revisions remain available here afterward. This directory is not presented as a complete extraction of every ZIP.

## Native boundary and remaining limits

- Guro and Geumcheon retain `productionApproved: false`, noindex metadata/response-header files and `Disallow: /`. Guro's unchanged native build retains its exact five-route sitemap; Geumcheon's unchanged native build emits no sitemap URLs.
- Gangseo's source `productionApproved: true` is an immutable source fact, not authority to publish.
- No public HTTP endpoint, provider routing, actual deployed 404 status, DNS, IndexNow, production availability or release permission was established. Native local `/404.html` checks intentionally received HTTP 200 from the static test server.
- Full-page captures do not prove that every dynamically scrolled viewport is free from fixed-CTA occlusion. No independent real-device scrolling test was performed.
- Some original native element-level FAQ PNGs have sticky-header/fixed-CTA overlays. They are not sufficient standalone FAQ evidence; the supplemental full-page JPEGs expose the FAQ sections without those element-capture overlays.
- The Geumcheon home guide card remains narrow/half-width on mobile, leaving unused space beside it. Text remains visible; this is a nonblocking observation in the unchanged source layout.
- This review does not claim exhaustive character-by-character proofreading at every width. Original build/source/native approval files, public-release flags and the national 46/230 release count were not changed by this QA.
