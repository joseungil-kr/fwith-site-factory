# Dongducheon direct static source

Cloud-only Astro source for the fixed candidate hostname `dongducheon.fwith.kr`.
The original plan is 12 legal-dong commercial articles, based on the current
Dongducheon City administrative/legal crosswalk. The 8 administrative names are
aliases, not additional canonical pages. At least 11 independently reviewed
articles are required before publication; omitted planned routes must remain
explicitly deferred and return a real 404.

## Reuse and source integrity

Runtime, catalog and unchanged product-image blobs are reused from operator-owned
repository revision `9eea3825094c17689936987319e7b5e026f6b7bf`.
No prior city's regional articles or geography/provenance records are reused.
Product photographs illustrate catalog products; they are not local delivery or
installation evidence. Geographic schema rules remain the previously reviewed
shared adapter. Full original customer fields are bound by SHA-256 snapshots.

## Local verification

Use Node 22 or later, then `npm ci`, `npm test`, and:

    SITE_URL=https://dongducheon.fwith.kr SITE_INDEXABLE=true \
      SITE_FACTORY_REVISION=<exact-40-character-source-commit> \
      ASTRO_TELEMETRY_DISABLED=1 npm run build

The build includes Astro type checks, rendered HTML/asset/SEO/catalog gates and
content graph checks. Generated `dist`, `.astro`, `node_modules` and local build
revision files are not source artifacts.

## Publication boundary

Publication is performed only by the fixed, explicitly dispatched Dongducheon
workflow on `main`. It builds an exact source SHA without provider credentials,
validates an exact artifact manifest, inspects account/Worker/hostname state via
GET, applies the existing no-override native binding operation, verifies live
bytes/SEO/assets/404s, and records the deduplicated IndexNow receipt using existing
issue 266. No queue, Factory controller, Airtable or paid API is involved.

This source alone is not deployment, IndexNow acceptance, or search indexing proof.
