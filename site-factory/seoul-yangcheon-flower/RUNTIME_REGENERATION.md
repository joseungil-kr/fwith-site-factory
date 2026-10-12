# Release data regeneration gates

This is an intentionally non-publishable skeleton copied from exact Mapo source fd14a190cb853607a8ae743da5068208409746ef. Read the repository `docs/direct-regional-release/SALES_COPY_ACCEPTANCE.md` before authoring. No customer article was authored here. Scope identifier: `seoul-yangcheon-direct-initial-20261012`.

## Inputs to replace after research and independent review

1. `src/data/region-coverage.json`: verified official full legal-dong inventory, administrative crosswalk and membership source digest; separate frozen representatives and facility registry. Empty inventory is not a frozen zero-page plan. Preserve the full original plan including any held representative.
2. `region-policy.json`: same site/scope, verified membership digest, rules revision, reviewed visual bindings, and enabled=true only after ready. Runtime `src/lib/regions.mjs` and synthetic test scope currently bind to the exact identifier above. If scope changes, change both.
3. `pages.json`: individually researched/reviewed approved articles only, with facility/context/intent bindings, source arrays, purchase-family selections, exact product-image provenance and all customer fields.
4. `architecture.json`: home metadata, hub children/indexability, article metadata rows. `page-map.json` and `publish-manifest.json`: route parity, context/unit/intent/product/visual bindings and identical snapshot IDs/hashes. No copied Mapo rows remain.
5. `publish-manifest.directRelease`: real frozen denominator, reviewed numerator, held routes/page keys, official membership counts, render/sitemap counts, dates/revisions, review digests and content hashes. Never derive the denominator from only the approved rows.
6. `direct-checkpoint.json`: actual plan and review evidence; do not inherit old dates, claim/source revisions or approval digests.
7. `products.json`, `business-truth.json`, `social-image-provenance.json`, public product bytes: inherited catalog evidence retained, not newly checked for Yangcheon. Revalidate and bind new evidence without inventing product claims.
8. Homepage `src/pages/index.astro` description/hero and `src/components/RegionDirectory.astro` intro explicitly contain TODOs. Author these after the actual purchase plan. Shared product cards and banner copy are retained for review.
9. Supply a unique public IndexNow ownership proof; the previous region proof was removed. Set productionApproved=true only at the reviewed publication stage.

## Exact customer snapshot algorithm

For each complete page, omit only these top-level keys:
`approvalVerified`, `status`, `file`, `order`, `sourceMode`, `snapshotId`, `snapshotHash`.
Recursively sort every non-array object's entries lexicographically by key using JS `<`/`>` ordering. Preserve array order. Apply compact `JSON.stringify` with no trailing newline; hash UTF-8 bytes with SHA-256. This is `sha256-sorted-utf8-json-v1`. Set `snapshotHash` to the lowercase digest and `snapshotId` to `direct-content-${slug}-${digest.slice(0,16)}`. Manifest contentHashes uses this as publicSourceSha256 and SHA-256 of exact UTF-8 contentMarkdown (not canonical JSON) as bodySha256. Copy the same snapshotHash/ID into all four collections: pages, architecture.pages, page-map.pages and publish-manifest.pages.

Python compact `json.dumps(..., ensure_ascii=False, sort_keys=True, separators=(',', ':'))` is equivalent for the current ordinary text/object/array fields, but prefer the JS canonicalizer in tests for fidelity.

## Release expectations and control gates

`tests/direct-source.test.mjs` retains original full release checks but now loads `tests/direct-source-expectations.json`. This placeholder must be populated from separately verified frozen inputs, never merely adjusted until tests pass. Required keys:
administrativeCrosswalk, approved, approvedDistinctUnitCount, assetManifestSha256, assetSubstitutions, commonSourceSha256, contextBySlug, facilities, held, membershipCounts, membershipSourceSha256, partialRelationCount, partialUnitKeys, plannedDistinctUnitCount, plannedUnitKeys, proofFile, queryEvidenceBySlug, representativeAssignment, reviewedCommon, reviewedProductDescriptions, runtimeRegionsSha256, slugs, unitKeys, unitTypeCounts.

Source hashes include the regional runtime file and all independently reviewed common-source files. Product descriptions, image substitution manifest, reviewed intro text, context registry and query evidence are bound exactly. Original expectation shape is inspectable in the exact Mapo template.

`scripts/direct-seoul-yangcheon/publish.py` has SLUGS=[] and RECEIPT_ISSUE=None. CLI fails closed with release_plan_and_receipt_issue_not_configured. Configure them from the frozen plan and dedicated receipt issue, then regenerate matching publisher test fixture slugs/counts and receipt ID (old Mapo values remain only in the inherited test fixture). Keep the plan guard. DEFERRED_SLUGS/DEFERRED and any hub exceptions must match the reviewed held plan. Workflow is dispatch-only, exact source SHA/branch locked, provider-credential-free build, digest-bound artifacts, no-override hostname attach, public byte/SEO/404 checks and idempotent IndexNow journal.

## Verification performed during preparation

Python publisher/test files compile. CLI is blocked as designed. 80 Node unit/synthetic tests passed; one integration-file import failed `Regional service: missing provenance` because research data is intentionally empty. Publisher tests: 42 total, 33 passed, 6 failed, 3 errors because receipt/route plan and fixture expectations are intentionally unresolved. These are partial checks, not a release pass. Environment Node was v24.19.0; release CI specifies Node 22. Dependencies/install/full production build were not run here.

Once populated run Node 22 + npm ci + npm test + exact production build; then publisher safety tests, reviewed source/control remote SHA checks, Actions artifact validation, provider readback, public HTTPS content/metadata/404 checks and IndexNow receipt. No deployment or publication was performed by skeleton preparation.
