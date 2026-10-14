# Seocho production successor

This is a separate successor of frozen source commit `2a4de872c85da0b66815c5e5668e0c7de9ce4341`. Historical `README.md`, accepted copy, source corrections, `site-config.json`, `publish-manifest.json`, review records, assets and the 98 sealed approval pins remain unchanged. The existing local review records do not assert current public release success.

`src/data/production-target.json` records the proposed `seoul-seocho.fwith.kr` / `seoul-seocho-flower-guide` identity. Its approval and provider-verification fields must remain false. It is not an ownership or publication grant. A production build requires a separate immutable control-side approval record; editing the proposed target cannot enable publication.

## Build modes

The default mode remains the frozen noindex preview. Use the existing dependency lockfile and run `npm ci`, then `npm run build`, `npm test`, and `npm run qa`. Python 3 must be available as `python3`. The added contract tests are also available via `npm run test:release`.

A production build requires all of the following environment values:

- `SITE_RELEASE_MODE=production`
- `SITE_INDEXABLE=true`
- `SITE_URL=https://seoul-seocho.fwith.kr`
- `SITE_FACTORY_REVISION`: exact 40-character committed successor source revision
- `SITE_RELEASE_BINDING_PATH`: absolute path to the separate control-side binding
- `SITE_RELEASE_BINDING_SHA256`: exact SHA-256 of that binding's raw bytes

The binding must have schemaVersion 1 and state approved; match every identity/provenance field in `TARGET` from `scripts/release_mode.mjs`; match the build sourceRevision; identify the exact sourceContractSha256; include explicit publication/hostBinding/indexNowProof approvals and auditable repository issue or commit-pinned evidence references. It must bind the three sorted sitemap routes, thinDirectoryRobots `noindex,follow`, notFoundStatus 404, and the authorized fixed-host proof path and SHA-256. The proof must already exist under `public/` with its exact key body. This change creates no proof or credential.

The trusted publisher must independently verify the external binding digest, source contract, exact Git branch/SHA/ancestry and first attempt before executing source code. This source helper does not establish an external security boundary against a caller who replaces both code and approval evidence. It never contacts a provider or submits IndexNow.

## Output and release gates

Production retains five HTML files: home, two articles, thin directory and 404. Only home and the two articles enter the sitemap. Directory remains noindex,follow and has no banners. The 404 has no canonical, social metadata, schema or banners. All five documents must carry the exact source revision. Home and each article retain the three approved phone banners and unchanged reviewed customer copy.

`scripts/qa_release_output.py` verifies exact output metadata, proof, sitemap, robots and file inventory, then writes `production-artifact-qa.json` outside `dist`. The expected missing-path response is a real HTTP 404 matching the built 404 bytes. This output contract does not itself configure the hosting provider or prove public behavior.

Run browser QA against the exact reviewed output at 320, 390 and 1280 pixels, and manually inspect the screenshots, all route content, FAQ visibility, links, loaded images, native anchor first landing, keyboard focus and sticky-bar clearance. The existing `qa_browser_rendering.py` local `/404.html` request is 200; separately verify the missing-path 404 on the actual public host. Never label static assertions as rendered-browser proof.

Before publication, root must bind the independently reviewed build/artifact digest, run the fixed provider collision checks and obtain any actually required service authorization. After publication, verify every expected public path, exact source revision, canonical/robots/sitemaps, asset bytes and proof before the existing idempotent IndexNow finalizer. No publication or IndexNow success is claimed by this successor.
