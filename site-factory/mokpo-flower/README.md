# Mokpo private local static candidate

This folder is a local-only Astro candidate, not a deployed site. No public origin has been chosen. No GitHub write, provider command, credential use, domain operation, new task environment, or installation was performed.

## Exact scope

- Home `/`
- One article `/regions/hankook-hospital-funeral-wreath/`
- One-child support navigation `/regions/`
- Technical `/404.html`

Article count 1, primary pages 2, support pages 1, technical pages 1, total HTML 4. Every preview HTML is `noindex,follow`; canonical and `og:url` are absent; sitemap has zero URLs. `robots.txt` allows fetches so noindex can be read. Noindex is a search directive, not access control. Privacy currently comes from keeping the output in local files with no publication.

The support page has exactly one real child, no marketing banners, no main-menu entry, and no sitemap entry. Core-hub launch, full launch and production are NOT_ASSESSED. The proposed future production two-URL set is inactive and unresolved; this candidate has no production switch or deployment script.

## Reused inputs

The frozen content specification has SHA-256 `90f43c2fb14ca8756453f1b2af1339f68e1ec24d3b38cb06f09a4cf73fd12f44`. Original home/article documents are preserved byte-for-byte, including original source dates. Draft button directives become real links; the first answer, FAQ, and source section render once. Four FAQ pairs are visible in static HTML. Browser/computed visibility is not yet verified.

Template CSS, FAQ normalization, directory banner helper, static HTML parser, actual product images and approved phone banners were reused from retained owner code/assets. `src/data/reuse-provenance.json` records their source and destination hashes. The lockfile's two project-name fields were changed; versions, package entries and integrity are unchanged. Original Gangdong-specific QA is retained unchanged outside this candidate, in `../reference`, and was not relabeled as Mokpo/launch QA.

Three banners keep approved bytes and 1774×887 dimensions. Banner explanations retain descriptive content and end with `전화 1844-0644.` exactly once. There is no marketing caption. Each primary has B201 59,000원, B203 79,000원, B205 109,000원, B060 149,000원 with exact SKU destination links. The Oct 15 retained official product response evidence is bound separately; checkout, stock, telephone connection and delivery availability were not tested.

## Local verification

Tested with Node 24.19.0, npm 11.9.0, Python 3.12.14, Astro 7.3.5, TypeScript 5.9.3 and @astrojs/check 0.9.10. Existing local `node_modules` was linked, not installed or changed. The link is excluded from the deliverable archive. The previously approved runner used Node 22 per the parent report; Node 22 parity has not been tested here.

With the existing approved local dependencies available:

```sh
ASTRO_TELEMETRY_DISABLED=1 npm run build
ASTRO_TELEMETRY_DISABLED=1 npm test
```

The build checks input hashes and preview boundaries, typechecks, produces static HTML, and inspects actual output. Tests include the unchanged directory helper tests plus new narrow Mokpo preview and mutation checks. They do not substitute for existing Core/Production launch gates.

## Verification limits

Installed Chromium was attempted, but it aborted before opening any page with `socket() failed: Operation not permitted (1)` and a read-only Chromium config path. No screenshot, mobile visual inspection, computed visibility or navigation-flow result exists. The loopback HTTP request also failed to connect (`curl` exit 7, HTTP 000). Astro's command reported a running server but that was not independently established. Therefore an unknown-path HTTP 404, including provider behavior, remains NOT_VERIFIED even though `404.html` exists and its static content passed checks.

No flags, security settings or execution environments were changed to bypass these restrictions. No public HTTP, index submission, indexing or ranking claim is made. See `../evidence/browser-and-http-blocker.json` and preserved raw failure logs.

The failed historical browser script/log preserve the original launch arguments. The current prepared browser helper explicitly enables the Chromium sandbox and has not been rerun. It remains an unexecuted harness, not validation evidence.
