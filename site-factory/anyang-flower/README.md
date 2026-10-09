# Anyang direct static site

Canonical origin: https://anyang.fwith.kr
Source branch: site-factory-anyang-direct
Cloudflare Worker: anyang-flower-guide

## Reuse and build

The existing operator-owned static Astro runtime, components, tests and product image bytes are reused from joseungil-kr/fwith-site-factory commit de67be7764eecd2ef96136d99574b54f4e6abd1b. The reusable runtime is current as of 2026-10-09 and pinned by package-lock.json (Astro 7.3.5); no new framework or paid AI API is used. Repository reuse is under the owner's explicit authorization; no separate third-party starter code was added. Upstream dependency metadata was checked locally: Astro 7.3.5, @astrojs/sitemap 3.7.4 and @astrojs/check 0.9.10 use MIT; TypeScript 5.9.3 uses Apache-2.0. Upstream dependencies retain their own package licenses.

Regional customer text, geography and source bindings were written specifically for Anyang. Legal-dong membership uses the current Anyang City official administrative-area table. Seven legal-dong pages cover all 31 administrative names without creating duplicate canonical pages for administrative aliases.

Run with Node 22: npm ci; npm test; SITE_URL=https://anyang.fwith.kr SITE_INDEXABLE=true SITE_FACTORY_REVISION=<source commit SHA> npm run build.

The retained runtime fields snapshotId and snapshotHash identify local direct-content snapshots and their SHA-256 content digests. They do not represent Airtable records, factory queue runs or issue-published drafts. The four page collections must agree. Release review and full remote commit readback occur before deployment. The public text ownership file is a per-site IndexNow proof, not an account API credential.
