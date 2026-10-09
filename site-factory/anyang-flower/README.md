# Anyang direct static site

Canonical origin: https://anyang.fwith.kr
Source branch: site-factory-anyang-direct
Cloudflare Worker: anyang-flower-guide

## Reuse and build

The existing operator-owned static Astro runtime, components, tests and product image bytes are reused from joseungil-kr/fwith-site-factory commit de67be7764eecd2ef96136d99574b54f4e6abd1b. The reusable runtime is current as of 2026-10-09 and pinned by package-lock.json (Astro 7.3.5); no new framework or paid AI API is used. Repository reuse is under the owner's explicit authorization; no separate third-party starter code was added. Upstream dependency metadata was checked locally: Astro 7.3.5, @astrojs/sitemap 3.7.4 and @astrojs/check 0.9.10 use MIT; TypeScript 5.9.3 uses Apache-2.0. Upstream dependencies retain their own package licenses.

Regional customer text, geography and source bindings were written specifically for Anyang. Legal-dong membership uses the current Anyang City official administrative-area table. Seven legal-dong pages cover all 31 administrative names without creating duplicate canonical pages for administrative aliases.

Run with Node 22: npm ci; npm test; SITE_URL=https://anyang.fwith.kr SITE_INDEXABLE=true SITE_FACTORY_REVISION=<source commit SHA> npm run build.

The retained runtime fields snapshotId and snapshotHash identify local direct-content snapshots and their SHA-256 content digests. They do not represent Airtable records, factory queue runs or issue-published drafts. The four page collections must agree. Release review and full remote commit readback occur before deployment. The public text ownership file is a per-site IndexNow proof, not an account API credential.


## Additional venue article release, 2026-10-09

The update appends five source-grounded venue-order articles to the seven existing legal-dong pages. It uses the same runtime, products, photographs, ordering destinations, Worker, hostname and ownership proof. The seven original article bodies and URLs remain intact; reviewed related-reading links connect each venue article to its local district page.

There are 12 customer articles and 16 normal HTML routes. The sitemap has 15 URLs: home, 12 articles, the regional hub and the three-article funeral hub. The two-article event hub remains `noindex,follow` and is excluded from the sitemap under the existing thin-hub policy. The 404 page is additional and never indexable. No tag taxonomy or new content engine was added.

`direct-checkpoint.json` describes the reviewed candidate and deliberately records deployment as pending. A source commit cannot include its own final SHA or prove a future upload. Exact Actions source/control SHAs, release artifact digests, public HTTP hash/revision readback and the IndexNow receipt establish publication separately. Submission does not prove search-engine indexing.
