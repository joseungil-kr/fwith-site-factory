# Gangseo source regeneration and release gates

The original copied skeleton contained Yangcheon customer records and approval fields. They were replaced before any source commit or publication. No previous region’s content/tone approval was carried forward.

Four candidate articles were drafted after official/market research while independent plan review was still pending. The actual order is documented in regional evidence; do not claim that independent plan approval preceded drafting. Local route metadata uses approved/approvalVerified for runtime inclusion, while direct-checkpoint and publish-manifest carry the real independent-review state and productionApproved remains false until review.

## Bound regional inputs

Membership is 13 legal dongs, 20 administrative dongs and 35 relations from the current effective MOIS package. The fixed facility/purchase plan is N=4, covers three distinct legal dongs and preserves all four planned URLs. The Gallery Seo exclusion is pre-plan, not a removed planned article. Facility permission and current delivery timing remain order-specific.

Shared banner bytes and manifest come from the approved common three-design set. FAQ object/array normalization and visible rendered text are tested. Eight product-detail URLs and official image bytes were freshly checked, with policy images checked for the eight SKUs only. Do not invent a general catalog policy, refunds, dimensions, delivery guarantees or collection service.

## Exact customer snapshot algorithm

For each complete page, omit only these top-level keys:
`approvalVerified`, `status`, `file`, `order`, `sourceMode`, `snapshotId`, `snapshotHash`.
Recursively sort every non-array object's entries lexicographically by key using JS `<`/`>` ordering. Preserve array order. Apply compact `JSON.stringify` with no trailing newline; hash UTF-8 bytes with SHA-256. This is `sha256-sorted-utf8-json-v1`. Set `snapshotHash` to the lowercase digest and `snapshotId` to `direct-content-${slug}-${digest.slice(0,16)}`. Manifest contentHashes uses this as publicSourceSha256 and SHA-256 of exact UTF-8 contentMarkdown (not canonical JSON) as bodySha256. Copy the same snapshotHash/ID into all four collections: pages, architecture.pages, page-map.pages and publish-manifest.pages.

Python compact `json.dumps(..., ensure_ascii=False, sort_keys=True, separators=(',', ':'))` is equivalent for the current ordinary text/object/array fields, but prefer the JS canonicalizer in tests for fidelity.

## Release expectations and control gates

`tests/direct-source.test.mjs` retains original full release checks but now loads `tests/direct-source-expectations.json`. This placeholder must be populated from separately verified frozen inputs, never merely adjusted until tests pass. Required keys:
administrativeCrosswalk, approved, approvedDistinctUnitCount, assetManifestSha256, assetSubstitutions, commonSourceSha256, contextBySlug, facilities, held, membershipCounts, membershipSourceSha256, partialRelationCount, partialUnitKeys, plannedDistinctUnitCount, plannedUnitKeys, proofFile, queryEvidenceBySlug, representativeAssignment, reviewedCommon, reviewedProductDescriptions, runtimeRegionsSha256, slugs, unitKeys, unitTypeCounts.

Source hashes include the regional runtime file and all independently reviewed common-source files. Product descriptions, image substitution manifest, reviewed intro text, context registry and query evidence are bound exactly. Original expectation shape is inspectable in the exact Mapo template.

`scripts/direct-seoul-gangseo/publish.py` pins four exact facility slugs and uses the existing receipt journal. The workflow requires an exact reviewed source SHA and owner-only issue trigger or authorized dispatch. Never trigger it without the required authorization. DEFERRED_SLUGS/DEFERRED and any hub exceptions must match the reviewed held plan. Workflow is dispatch-only, exact source SHA/branch locked, provider-credential-free build, digest-bound artifacts, no-override hostname attach, public byte/SEO/404 checks and idempotent IndexNow journal.

## Required final verification

Run Node 22 source tests, Astro check and clean preview/production builds. The build includes static graph/metadata/route checks, exact visible FAQ and product links, and shared-banner heading/alt/asset/404 checks with negative tests. Publisher safety tests bind four articles, six sitemap routes, exact artifact digests, source revision, provider no-override checks, public byte parity and the IndexNow journal.

Read back exact committed source bytes and build that revision. Check Actions artifacts, actual public HTTPS status/canonical/robots/sitemap/real404, image and CTA paths, and IndexNow receipt. A receipt is not actual indexing, traffic or ranking. Local Chromium socket launch failed in this execution; use the supported cloud browser against public HTTPS after publication, or explicitly retain visual QA as unverified.
