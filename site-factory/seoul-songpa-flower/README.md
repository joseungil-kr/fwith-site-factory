# Songpa local static implementation

This is the assigned LOCAL_PREVIEW successor for Songpa. It is not a commit, deployment, public site, ownership proof, IndexNow submission, or completed release. National publication order remains Seocho 22, Gangnam 23, Songpa 24.

## Exact source and scope

- Gwanak Astro template revision: `ecc62ab4053365e451b697867bdf68c3d26b78d2`. All 679 retained template files were rehashed against the recorded SHA256 and Git blob SHA1 before selected reuse. The runtime reuses its global styling, safe text utilities, FAQ normalization and directory-spacing algorithm; layout, product/FAQ/banner rendering and static routes are adapted to Songpa's frozen structured copy. `src/data/template-provenance.json` records reused and adapted files.
- Frozen author copy manifest: `e99c4256f38cf7c0e19392492840ebe4968b1494475d866b404a5395fb309116`.
- Independent COPY_ONLY review manifest: `d06379ab5f3704af697f82350c4145c2b6659a9e5b308e385a8ce45882484e6c`.
- Pre-copy plan/rubric review manifest: `48b0a9f14a970b4082a4358259627c96e5d4786afaa3c20ff6a17a7d4cb4a784`.
- Selected input seal: `bd62488171b10f6b0441baa9598dcff99bafb3ee64339504d9119a128c0bae80`. The generator verifies every embedded frozen input and all 11 actual image files against it, rejects extra frozen files and symlinked replacements, and produces deterministic runtime data without generating prose.
- N=2 substantive purchase articles: condolence (Asan context merged) and wedding (three venues). Home + two articles are three intended primary pages; the two-child directory is a support page. Total content routes=4; utility404 makes five HTML files. No facility or dong alias page is created.
- Geography retains exactly 13 legal units, 27 administrative units and 30 relationships. All 14 contextual facility records have administrativeDong=null. Unknown legalDong values remain explicitly unassigned; holding records are not rendered as active offers. These contextual records are not a count of independently verified, deliverable or active sales facilities.
- Eight exact SKU/basic-price/photo/alt/individual-detail-CTA records remain unchanged. Home renders all eight, each article its matching four. The three current shared banners show 1844-0644, retain exact 1774×887 bytes, have no captions and are separated by real content. Directory and404 have no banners. Product samples remain uncropped 500×500 images.

## LOCAL_PREVIEW mode

The immutable presentation-contract JSON describes future intended public indexability. The explicit LOCAL_PREVIEW transformation in `src/lib/songpa-runtime.mjs` preserves that source contract and separately forces all five outputs to noindex,nofollow,noarchive, a robots disallow-all, empty sitemap and reserved `https://seoul-songpa.local.invalid` origin. The utility404 deliberately has no canonical or social metadata. All ownership/publication/indexing/IndexNow flags are false. No public-mode implementation exists: attempts to inject true flags or a real hostname reject before build.

This preview exception does not approve public semantics. A future release needs a separately authorized exact source, real hostname and public-output/core-function verification. The placeholder is not an assigned public URL, and a generated404 file is not evidence of a real HTTP404 response.

## Offline commands

Use the existing lockfile-compatible Node24 / Astro7.3.5 dependency graph. No dependency was installed or updated. package-lock.json is byte-identical to the template; its inert project package name is retained. Local preparation copied the already-installed dependency graph into a separate node_modules directory. Python checks use only the standard library.

```sh
npm run generate
ASTRO_TELEMETRY_DISABLED=1 SITE_INDEXABLE=false SITE_URL=https://seoul-songpa.local.invalid npm run build
npm test
npm run qa
```

The build checks the input seal, exact projection, Astro diagnostics, static HTML and actual asset bytes. Run a build before mutation tests. `npm run generate -- --check` verifies without writing. Native tests include wrong-region/geography/facility/SKU/price/FAQ/source/phone/copy/public-boundary cases. Compiled-output fixtures cover hidden or changed copy/FAQs, wrong CTA/photo/price, source, banner, heading, alias, local route, robots/sitemap, ownership, executable script, CSS-hidden FAQ and actual asset tampering.

The final source-only ZIP excludes node_modules, dist, `.astro`, local reports and the unchanged historical regression copy. Output manifests and command logs are separate. Rebuild output after any source change; do not reuse old output or review hashes.

## Copy interpretation and evidence limits

The final independent customer-string inventory has 266 rows. All source fields are preserved exactly. Banner imageText appears only in image pixels, not duplicate captions. The unused home cardSummary has no separate home-card slot. The generic common viewDetail label is superseded by the exact reviewed SKU-specific CTA in each card; it is not extra display text. All other expected strings are bound to text/attributes in actual HTML.

FAQ questions and answers are plain visible default HTML, outside details/hidden nodes. The only collapsible control is the native mobile menu. Static source CSS checks and responsive rules are not computed browser layout, keyboard or touch proof. No Chromium launch, screenshot, browser click or public HTTP check was attempted. Those stages remain unverified.

`rendered-copy-extraction.json` (generated by QA, excluded from source ZIP) extracts actual compiled HTML, title/H1/first prose and headings for separate independent A04 scoring. Source-only A04=100 is not copied as a rendered score, traffic, ranking or conversion claim.

Original research dates and source URLs are historical frozen evidence references; implementation does not make fresh factual or fulfillment claims. Full PDFs, raw competitor copy, personal-contact appendices, credentials, original regional evidence corpora, release approval and ownership files are excluded from this source candidate. Original 307-file Songpa research, earlier copy, plans and other regional owners' source folders remain unchanged locally.

## Minimal provenance successor

The preceding 68-file source freeze remains unchanged locally. Only the embedded independent review verdict is replaced with `review-verdict.projection.json`: the two internal writer/reviewer task identifiers are omitted, original verdict SHA256 is retained, and every decision and limitation is preserved under `retainedVerdict`. The original copy and plan/research/review artifacts are untouched. This is an anonymous selected projection, not a byte-identical original verdict. Its new input seal changes only the technical `data-copy-sha` attributes in compiled HTML; customer prose, product/FAQ/link/image fields, layout and preview boundaries remain unchanged.
