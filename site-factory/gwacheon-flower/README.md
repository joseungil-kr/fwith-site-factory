# Gwacheon direct static source

Cloud-only Astro source for the fixed candidate hostname `gwacheon.fwith.kr`.
The immutable original plan is 10 legal-dong commercial articles, independently
verified against Gwacheon City official membership. The 7 administrative names
are aliases, not additional canonical pages. At least 9 independently reviewed
articles are required before publication. Omitted planned routes remain deferred
and must return a real 404. Legal Galhyeon-dong is shared in part by administrative
Galhyeon-dong and Wonmun-dong; those boundaries are not treated as identical.

## Reuse and source integrity

Runtime, catalog and unchanged product-image blobs are reused from operator-owned
repository revision `f13a51b75707e5b2e4cfb499da48372faa314858`.
Every reused source blob was checked against the exact remote tree. No external
license is assumed: no LICENSE file was found at the pinned repository revision.
No prior city's regional articles or geography records are reused. Product images
illustrate catalog products, not local delivery or installation evidence.
Public customer fields are bound by SHA-256 snapshots.

## Local verification

Use Node 22 or later, then `npm ci`, `npm test`, and:

    SITE_URL=https://gwacheon.fwith.kr SITE_INDEXABLE=true \
      SITE_FACTORY_REVISION=<exact-40-character-source-commit> \
      ASTRO_TELEMETRY_DISABLED=1 npm run build

The build includes Astro type checks, rendered HTML/asset/SEO/catalog gates and
content graph checks. Generated dist, .astro, node_modules and local build
revision files are not source artifacts.

## Publication boundary

Only the fixed explicitly dispatched Gwacheon workflow on main publishes. It
builds the exact source SHA without provider credentials, validates an exact
artifact manifest, checks actual account/Worker/hostname state through GET,
applies the existing no-override native binding operation, verifies live bytes,
SEO, assets and real 404s, and journals the deduplicated IndexNow receipt in issue
266. No queue, Factory controller, Airtable or paid API is involved.

Source alone is not deployment, IndexNow acceptance or search indexing proof.
