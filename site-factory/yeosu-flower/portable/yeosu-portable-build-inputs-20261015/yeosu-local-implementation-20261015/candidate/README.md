# Yeosu private local candidate

This is a local-file-only Astro candidate built from the reviewed Yeosu drafts and page-spec addendum. It is not a deployed site or a release. No remote writes, deployment, hostname reservation, IndexNow, browser/socket retry, package installation, new images or new task environment occurred.

## Scope

- `/`: reviewed home, zero product cards, three approved banners.
- `/regions/yeosu-jeonnam-hospital-funeral-wreath/`: one original Yeosu article, four product cards, three expanded FAQ pairs, three approved banners.
- `/regions/`: one-child support navigation, excluded from main menu, no products/FAQ/banners.
- `/404.html`: technical not-found document. Its existence does not verify HTTP 404 routing.

All four pages have `noindex,follow`, no canonical, no absolute Open Graph origin, no script/form/iframe, and a `main#main-content[tabindex="-1"]` skip-link target. Sitemap has zero URLs; robots allows fetching so noindex can be read. Noindex is not access control. Privacy comes from keeping these files unpublished. No production adapter, mode switch, deployment script or indexing proof exists in this candidate.

Official order remains Mokpo 26 pending, Yeosu 27 independent preparation only. Core/full release status remains NOT_ASSESSED.

## Original-source binding

Spec SHA-256: b7fd276f969d473b60619cafca6ed160a442fdf5feb36b1bb1addccdaeb96b1f.
Home SHA-256: 3b5e5b50f67f32f82851fab6f1e4224ad26cbabd27f804c976a0ba9036089683.
Article SHA-256: 6815d1d6e6fbc03e8976e914f656062a2cb7e85eab93def67067edafbd63b8a9.

Original Markdown files are read directly from the sibling `yeosu-customer-copy-20261014` directory. They are neither rewritten nor copied into this candidate. Full original-source bytes, product span, FAQ span and scoped nine-field review are verified before rendering. The stale `pending` status in the original spec is resolved only by its detached exact-nine-field binding, not by editing the original. Required sibling inputs and the original Mokpo template must remain available for the integrity gate.

The strict renderer preserves original headings, prose, punctuation, links, list items, FAQ order, CTA order, and the original PRODUCT_CARDS position. Only the one declared local draft link and four declared image paths are mapped. No second first-answer paragraph, extra FAQ component, product duplicate or source heading is added. The three existing approved banner assets are inserted immediately before the specified H2 sections. Product price/stock observation dates remain October 13; no current commercial availability is implied.

## Reuse

The approved Mokpo private template provides byte-identical global/Gangdong/Mokpo CSS, directory helper/tests, static HTML tree parser, robots/sitemap/headers/favicon, and tsconfig. The dependency lock is reused with only its two project-name fields changed; dependency versions and integrity are unchanged. Layout, page rendering and Markdown parsing are narrowly adapted for the actual Yeosu originals; no Mokpo prose is name-swapped. `src/data/reuse-provenance.json` records file hashes. The only lockfile changes are the two project name fields. Existing node_modules is linked; nothing was installed. Four retained product photos and three approved shared banners are byte-identical and were visually opened on this executor.

## Run

Run from this candidate directory with the existing dependencies and original sibling inputs available:

```
ASTRO_TELEMETRY_DISABLED=1 npm run build
ASTRO_TELEMETRY_DISABLED=1 npm test
```

Using this cwd keeps source resolution stable during Astro's prerender bundle. Build verifies all original input hashes, checks TypeScript, generates four HTML files and performs separate Python Markdown-to-HTML comparison. Tests include unchanged directory-helper tests, private-boundary/parser tests, and negative mutations of actual output. Static checks directly inspect FAQ answers and required CTAs plus ancestors/descendants for hiding attributes, inline styles and straightforward stylesheet rules. Unknown hiding pseudo-selectors fail closed and require browser verification. These checks are not a browser/CSS cascade engine.

## Verification limits

The previously observed Chromium socket failure and loopback HTTP failure were not retried or bypassed. No screen capture, mobile/computed layout, keyboard focus interaction, menu interaction, browser navigation, unknown-URL HTTP 404 response, public URL, telephone, checkout, live prices/stock, delivery, deployment or search-indexing result is claimed. Node 24 was used; Node 22 and a fresh dependency installation were not tested. The prior input research and current private implementation are separate from production readiness.

Evidence is in the parent `evidence/` folder and independent static review in `independent-review/`. Logs retain early type/path/parity failures and final passing runs with their actual scope.
