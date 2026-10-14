# Gangdong explicit production-mode technical successor

This local-only technical successor reuses Songpa production source b8707da0005ca9eea83b3f36956b775de0801f9f. The frozen Gangdong source is 9c044584505eec60c71f2bc7add497f0902f5424, project tree a7e8ff540822dc7ee326f1503a9a2bbccf07f996. Its 69 source files were enumerated, including .gitignore. No dependency, source copy, product data, asset, customer string, geography, facility or hold is changed. All src/data files and the frozen runtime validator retain exact bytes. package-lock.json is unchanged.

The original README and template-provenance are historical preview evidence. They remain exact bytes. release/successor-provenance.json records exact reversible transformations for changed legacy source files. The reuse verifier checks both historical source hashes and current successor hashes; original evidence is never resealed to make a changed file look unchanged.

Default mode stays preview: reserved invalid origin, five noindex routes, deny-all robots, exact empty sitemap, no proof output. Production requires SITE_RELEASE_MODE=production, SITE_INDEXABLE=true, https://seoul-gangdong.fwith.kr, a pinned source revision, and an external SHA256-bound production-binding.json. Existing approved proof bytes are reused, not generated. Builds reject provider credentials and unbound approval flags; no network, deployment, hostname attachment or IndexNow submission is performed by source code.

Production semantics follow frozen presentation-contract.json and public-preview-contract.json: home and two articles index,follow with exactly three sitemap URLs; directory noindex,follow and absent from sitemap and primary navigation; 404 noindex,follow without canonical/social metadata. Actual HTTP404 is a later deployment obligation.

Technical accessibility changes are only focusable main (tabindex=-1) and 83px desktop scroll clearance. The mobile clearance is unchanged. Five pages retain 8 products, 11 images, nine banner placements and FAQ counts 2/4/4/0/0. Static checks do not establish computed layout, actual keyboard behavior, public HTTP or indexing.

npm run build runs frozen inputs, exact reuse provenance, diagnostics, output metadata and customer-copy checks. npm test runs source and compiled negative fixtures. npm run test:production additionally validates the actual 23-file production artifact and corruption fixtures. Local synthetic binding fixtures outside source are test inputs only; they are not provider or user approval evidence.
