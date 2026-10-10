# Yeoju flower guide: direct static source

This directory is the Yeoju-only static source for branch `site-factory-yeoju-direct`, directory `site-factory/yeoju-flower`, Worker `yeoju-flower-guide`, and intended HTTPS origin `https://yeoju.fwith.kr`.

## Fixed regional scope

The frozen official canonical plan contains 32 legal units: 23 legal dongs, 1 eup and 8 myeon. The administrative crosswalk contains 12 aliases and 32 whole-unit relationships, with no partial relationships. These membership counts are not article quotas and do not shrink if an article is held.

Only independently reviewed articles may enter `src/data/pages.json`. At least 29 of the 32 planned articles must pass the content gates. Held routes remain recorded in the plan and release manifest, but must not appear as pages, internal article links or sitemap URLs. Actual approved counts and held routes are generated from the reviewed release inputs; this README does not claim that all 32 articles are approved.

The only emitted normal page categories are the home page, `/regions/`, and approved `/regions/<slug>/` articles. Therefore approved article count plus two equals the normal HTML route and sitemap URL counts. The real 404 page is outside that normal route count and is non-indexable.

## Catalog and images

Eight operator-owned product catalog entries and their unchanged local product image assets are reused. Catalog names, base prices and official product-detail image links were freshly checked against `https://fwith.co.kr` on 2026-10-10. Product-only social image provenance is regenerated from verified asset SHA-256 values, measured dimensions and MIME types. Product photographs are examples of catalog goods, never evidence of delivery or installation in Yeoju.

## Local checks

Use Node.js 22 and the pinned lockfile. The source contracts contain 64 tests. The separate direct publisher retains 34 helper tests. Build and source tests run without provider credentials. For a credential-free local build, set the intended `SITE_URL`, `SITE_INDEXABLE=true`, and a full 40-character `SITE_FACTORY_REVISION`, then run `npm ci`, `npm test`, and `npm run build`.

Build output is a static artifact. Public customer fields are bound to SHA-256 snapshots. The publisher separately verifies the exact source revision, artifact digest, approved route set, all local assets, canonical metadata, robots directives, CTA destinations and real 404 behavior.

## Publication boundary

The direct workflow is dispatch-only on main and verifies the exact Yeoju branch head. It separates the credential-free build from deployment. Provider preflight checks use actual GET responses; hostname attachment uses the existing fixed no-override operation. Public readback and IndexNow receipt verification are distinct gates.

Prepared source, local tests, a successful upload or a worker report are not proof of a live release. Completion requires independent verification of the exact remote source/control revisions, Actions result and artifact, provider binding, live HTTPS response bytes/metadata, and the IndexNow receipt. Browser screen QA remains separate and must not be represented as passed unless it was performed. Search indexing is not guaranteed by submission or by a receipt.
