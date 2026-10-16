# Damyang private static purchase home

Run from this directory with ASTRO_TELEMETRY_DISABLED=1. Reuse the pinned Astro dependencies in package-lock.json; no dependency upgrade is needed.

- node scripts/verify_inputs.mjs
- node node_modules/astro/bin/astro.mjs check
- node node_modules/astro/bin/astro.mjs build
- python3 scripts/qa_damyang.py
- node --test tests/damyang-runtime.test.mjs
- python3 scripts/test_damyang.py

Exact reviewed input is ../inputs/reviewed-copy/customer-copy.json. Five native keys; only / and /404.html. Production credentials and origin flags fail closed. Preview has no canonical, no public origin, no sitemap URLs, and noindex/nofollow/noarchive. FAQ and all four product reference totals render on home, always present in static HTML. No form, script, external submission or invented facility page is generated.

Static tests do not claim computed browser visibility or real HTTP status. Separate adapter tests transform only the head and controls, keeping exact body/asset bytes; source-only tests generate their fixtures from the rebuilt private output. Source must be frozen and independently reviewed before any remote save/publication.

## Local r2 timing correction

This separate source revision consumes the exact r2 manuscript review (copy 3bc9a15e452efbc3afac06f366f711ac45008b136d3597a6a15d997ddfb741d0). Only one customer paragraph changes. Both upper/lower timing notices, unresolved applicability and separate B06021 condition remain together. Original165/24/16/3 and null scores are retained; supplemental6+1 are separately validated. Exact r1 review identities remain historical, with timing scope superseded. Rebuild fixtures from source; never copy r1 outputs or claim public verification. Source inventory is derived from the frozen manifests, not the historical74.
