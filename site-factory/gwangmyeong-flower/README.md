# Gwangmyeong direct static site

Canonical origin: https://gwangmyeong.fwith.kr
Source branch: site-factory-gwangmyeong-direct
Cloudflare Worker: gwangmyeong-flower-guide
Initial scope: gwangmyeong-direct-initial-20261010

## Reuse and build

Reuses the operator-owned Astro static runtime, components, dependency lockfile, catalog and image bytes from confirmed source c047f1127f7908085fce55ab41504a23ff9b199c of joseungil-kr/fwith-site-factory. This is the successful Uijeongbu direct source, current as of 2026-10-09. Every one of its 69 source files was checked against the remote Git tree before reuse. Prior-city customer records and geographic provenance are excluded. No new framework, factory controller, queue, Airtable or paid AI API is used. The runtime has a site-specific directory caption and newly derived source collections.

Repository reuse is under the owner's authorization; no external starter code was added. Existing dependencies retain their own licenses: Astro 7.3.5, @astrojs/sitemap 3.7.4 and @astrojs/check 0.9.10 use MIT; TypeScript 5.9.3 uses Apache-2.0. Source and dependency lockfiles are pinned; active repository maintenance and the successful exact-source release were verified before reuse.

Run with Node 22:

    npm ci
    npm test
    SITE_URL=https://gwangmyeong.fwith.kr SITE_INDEXABLE=true SITE_FACTORY_REVISION=<source commit SHA> npm run build

## Initial scope and evidence

The initial plan is 8 legal-unit commercial pages. Separate facility articles are not part of this initial scope. The current official Gwangmyeong administrative crosswalk has 19 administrative names, which are navigation aliases rather than additional canonical pages. One city group is displayed; no district is invented. Legal Gwangmyeong-dong and Okgil-dong both appear under administrative Gwangmyeong6-dong. Legal Noonsa-dong and Gahak-dong share Hak-on-dong. Iljik-dong is a separate current administrative dong and is not collapsed into Soha2-dong. Relation labels are deduced from name membership in the official table, not claimed as street-level boundary evidence.

The reviewed candidate has 10 normal HTML routes and 10 sitemap URLs: home, regional hub and the 8 articles. The 404 page is additional and never indexable. Every other empty category is absent. The original denominator stays 8; the minimum of 90% means all 8 articles must pass. All candidate routes must pass fixed exact-artifact and HTTP contracts before publication.

Snapshot identifiers are local direct-content digests and do not identify Airtable records, queue runs or issue-published drafts. All four page collections agree. The public IndexNow ownership proof is site-specific and is not an account credential.

The source checkpoint deliberately records publication as pending. A source commit cannot contain its own final SHA or prove future deployment. Exact Actions source/control revisions, artifact hashes, public revision/hash readback and the IndexNow receipt establish publication separately. Submission does not establish search-engine indexing.
