# Regeneration and verification boundaries

## Inputs and reuse

Geumcheon N1 base: bbb016305dd2fe29f7d985a669acaa02224a9f2f. Guro ancestor: 500d82d01c1cdaed3ebde047bb3ce056705daac1. Latest upstream main observed for the plan: b68fa7801b080da5a65fbaeceeba3aa9a81ac365. Yeongdeungpo's current local fixes were inspected and reused for geography-only administrative rows, H2/H3 checking, base-price mutations and exact card-label bindings. This is reuse provenance, not a Dongjak source commit.

Frozen input SHA-256:
- fixed-plan.json: 8c17e681bc49944eec59698fbd6dfea3ff4c91773e0d45dbe955dae20b443e7c
- article-copy.rev6.json: 428b4c3a66e648c15cf35c3887aee619c1e8eeb724f98ea8cdaa044e55001489
- common-visible-copy.rev6.json: b158fa9b9faa4049f11b94c8023073ab3aee7fa8fdd3088b7e5b6d5a9701649f
- independent PLAN review: 921a64d860efdf1a86cce4ea56c349ad1e917d45315523b40f760c64fa84aa3d
- independent COPY review rev6: fda619d326350cc6e1c47d6e67e6d3e8411e1872690089efd4ce89a5040b1c6b

review-inputs/dongjak retains those exact input/review bytes. They are evidence for their original scoped review, not publication authority. The plan/handoff's historical earlier-stage authorization labels remain unchanged; the current task authorizes local implementation only.

## Adapter and preserved controls

src/lib/dongjak-regions.mjs is additive. Original legacy, Guro, Geumcheon and Yeongdeungpo adapters, their frozen bindings, original heading helper, directory midpoint helper and shared banner component retain their bytes. The current dispatcher rejects cross-site mode collisions. Dongjak's legal/admin mapping is exact; partial administrative relations never become facility assignments. Directory administrative rows contain geography only, while two precise facility links live in the legal-dong list.

scripts/assert_preview_boundary.mjs, qa_static.py, qa_faq_products.py, test_faq_products.py, qa_shared_banners.py, test_shared_banners.py and test_directory_spacing.py are preserved. Directory-link QA adds Dongjak to the existing grouped/H3 model and requires zero administrative facility links. Directory-spacing QA selects the region by siteKey to prevent preserved historical copy inputs from masquerading as current data, then binds exact Dongjak card labels without changing >=3 eligibility. Base-price mutation tests reuse Yeongdeungpo's exact '상품 기본가격' label fix.

## Original assertion preservation

scripts/test_inherited_regressions.mjs runs each complete original Guro, Geumcheon and Yeongdeungpo test suite in an isolated temporary directory, overlays current shared lib modules and supplies additive import dependencies, then removes only that temporary directory. Original expected N3/N1/N2 values, old source hashes and all native negative assertions are unchanged.

The two root duplicate files tests/answer-opening.test.mjs and tests/sources.test.mjs have original bytes at tests/reference/geumcheon-answer-opening.test.mjs.txt and tests/reference/geumcheon-sources.test.mjs.txt, as well as the complete original test fixtures. Their template-specific expectations cannot express the new exact structured section/H3/source-last layout. tests/dongjak-grouped.test.mjs supplies current source/identity assertions; scripts/qa_dongjak.py and scripts/test_dongjak.py independently parse and mutate the actual compiled HTML to verify full paragraph ordering, H3 anchors, exact copy, FAQ, per-SKU prices/links, geography, banner placement, footer, 404 and preview boundaries.

## Commands and limitations

npm test
ASTRO_TELEMETRY_DISABLED=1 XDG_CONFIG_HOME=/tmp/dongjak-config npm run build
npm run qa
SITE_INDEXABLE=true npm run build (must fail before Astro runs)

Use the normal lockfile in a permitted environment. The source manifest excludes node_modules, dist, .astro, Python caches and generated QA reports. The output manifest covers every file under dist. A valid local result needs successful commands, actual artifacts and independent source/output inspection. Browser screenshots and public HTTP have not been verified here. Do not retry previously blocked Chromium/socket routes, invent a public hostname, remove guards, dispatch workflows, create Git objects, deploy or submit IndexNow under this local scope.
