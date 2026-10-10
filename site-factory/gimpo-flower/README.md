# Gimpo direct static source

Cloud-only Astro source for the fixed candidate hostname `gimpo.fwith.kr`.
The immutable original plan is 15 legal-dong/eup/myeon commercial articles, independently
verified against the official Ministry of the Interior and Safety legal/administrative
code crosswalk effective 2026-09-30. The 14 administrative names are
aliases, not additional canonical pages. At least 14 independently
reviewed articles are required before publication. Omitted planned routes remain
deferred and must return a real 404. The 17 verified administrative-to-legal
relations comprise 13 whole and 4 partial relations. The 장기동 legal unit
intersects 장기본동 and 장기동; 감정동 intersects 김포본동 and 장기동.
The current MOIS crosswalk preserves all four partial relations even though the
municipality summary omits the 감정동–장기동 partial intersection. This jurisdiction crosswalk does not establish
street-level delivery availability or facility reception conditions.

## Reuse and source integrity

Runtime, catalog and unchanged product-image blobs are reused from operator-owned
repository revision `39a23593b6d2134627edccb9a02378dac708e5c4`.
Every reused source blob was checked against the exact remote tree. No external
license is assumed: no LICENSE file was found at the pinned repository revision.
No prior city's regional articles or geography records are reused. Product images
illustrate catalog products, not local delivery or installation evidence.
Public customer fields are bound by SHA-256 snapshots.

## Local verification

Use Node 22 or later, then `npm ci`, `npm test`, and:

    SITE_URL=https://gimpo.fwith.kr SITE_INDEXABLE=true \
      SITE_FACTORY_REVISION=<exact-40-character-source-commit> \
      ASTRO_TELEMETRY_DISABLED=1 npm run build

The build includes Astro type checks, rendered HTML/asset/SEO/catalog gates and
content graph checks. Generated dist, .astro, node_modules and local build
revision files are not source artifacts.

## Publication boundary

The control baseline is pinned to independently reviewed main revision
`adc85e5436e0d778e82a2c0824c8133772bd0fb0`. The Gimpo adaptation must pass
its own independent exact-file review before publication.
Only the fixed explicitly dispatched Gimpo workflow on main publishes. It builds
the exact source SHA without provider credentials, validates an exact artifact
manifest, checks actual account/Worker/hostname state through GET, applies the
existing no-override native binding operation, verifies live bytes, SEO, assets
and real 404s, and journals the Gimpo-identity deduplicated IndexNow receipt in
issue 266. No queue, Factory controller, Airtable or paid API is involved.

Actual browser-screen QA is deferred by the user and must be recorded as deferred,
not passed. Source, content, build, HTTP, SEO, real-404 and receipt checks remain
required. Source alone is not deployment, IndexNow acceptance or search indexing proof.
