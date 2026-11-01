# Public response differences and preservation policy

2026-11-01. This updates the public-comparison and usage portions of IMPLEMENTATION-REVIEW.md. **Cutover remains on hold.** No provider operation, browser access, new public request or policy change was performed in this follow-up.

## Evidence verified offline

The parent's helper files under `regional-worker-evidence-20261101` were read. `live-differences/` contains normalized copies of the two release receipts/configs and helper comparisons/usage report; `reconciled.json` records SHA-256 of each original file for provenance.

- Dongjak receipt: source `2935ac394dd63e81c443995a66fab46981f652bf`, run `38428129720`. All 19 hashes match our retained candidate ZIP.
- Geumcheon receipt: source `673ff52bb8f21f58bb104b447f3f105fd1a52a98`, run `38444879929`. All 19 hashes match our retained candidate ZIP.
- Current public bodies, as recorded by helper: **16 of 18 per site match**. Neither site has an 18/18 public equivalence verdict. `_headers` is a configuration file and was excluded from public body requests.
- Full raw live robots bodies and full live response headers are not included in these supplied files. Do not invent missing directives or redirect targets.

## Actual difference table

| Site / request | Retained file or origin baseline | Helper's current public observation | Integrated local result | Conclusion |
| --- | --- | --- | --- | --- |
| Dongjak `/404.html` | HTML SHA `c3faa624…` | 307, empty body SHA `e3b0c442…`; helper separately confirms Location `/404` | 307, empty body, relative Location `/404` | Redirect response is not the 404.html file body. Observed first-hop behavior agrees; public target-chain behavior remains unverified. |
| Geumcheon `/404.html` | HTML SHA `b766200f…` | 307, empty body SHA `e3b0c442…`; Location not supplied | 307, empty body, relative Location `/404` | First-hop status/body agree. Public Location and final target response remain unknown. |
| Dongjak `/robots.txt` | SHA `3c6b698b…`; general Allow plus own sitemap | SHA `e38bdaf3…`; helper observed Cloudflare Managed Content before original rules | Original retained bytes, no simulated edge transformation | Public bytes differ. Managed prefix is observed, but exact raw directives/suffix have not been independently compared. |
| Geumcheon `/robots.txt` | See full retained SHA in reconciled.json; own sitemap | SHA `ac6bcaf2…`; cause not inspected | Original retained bytes | Unexplained public difference. Do not infer the same managed prefix merely because both sites share a zone. |
| Both, other 16 requested files | Candidate retained hashes | 200 and exact corresponding hashes | Prior local tests match | These specific bodies match; this does not bind active UUID metadata to source or prove all provider settings. |
| Both `_headers` | Retained file exists | Not served/requested as a public asset | Namespaced rules verified locally | No public body hash claim. Full current header/config comparison is still needed. |

All full hashes and paths are machine-readable in `live-differences/reconciled.json`.

## 404 policy

Preserve the existing `html_handling=auto-trailing-slash` and `not_found_handling=404-page` settings. Do not replace `/404.html`'s redirect with a direct 200 body merely to make a file-hash comparison pass. Retain the relative Location and query string; never expose `/__regional/...`.

Distinguish three checks: (1) `/404.html` first-hop canonical redirect, (2) the resulting `/404` response, (3) an actually missing URL returning the branded **404** body and noindex metadata. The existing 115 local checks cover the first hop and missing paths against original static-only baselines. They are not live target-chain evidence. Before cutover, obtain current public Location and final-target status/body for both hosts, plus a real missing-path response, through the parent's already permitted observation path. This worker will not retry the earlier denied public requests through a different UA/path.

## robots policy

Keep each original robots asset byte-for-byte, including its own sitemap URL. Preserve existing Cloudflare policies/settings. Do not strip managed text as cosmetic noise, disable bot settings, hardcode a guessed prefix, or copy a captured managed block into the asset; the latter could duplicate policy text if the edge prepends it again.

[Cloudflare's managed robots documentation](https://developers.cloudflare.com/bots/additional-configurations/managed-robots-txt/) describes prepending policy directives to an existing HTTP-200 robots file. This can express crawler/content-use preferences; it is not merely a formatting difference. The supplied observation supports that explanation for Dongjak, but does not establish exact directives or prove post-integration behavior. Geumcheon's cause remains unknown.

Required comparison before release: capture raw live bodies and relevant response headers; identify each managed block and the original suffix; compare the origin suffix exactly to the retained file; retain every observed crawler/content signal and sitemap. Confirm the same transformation still applies when the response goes through worker-first routing. Matching local origin bytes alone does not prove this. Unexpected changes or absent evidence keep the gate closed. No broad comment/whitespace removal is used to manufacture a pass.

## Usage and configuration corrections

Helper observed **2,357 / 100,000** account requests at `2026-11-01T05:37:34.6778902Z`, leaving **97,643 at that instant**. This is an observed account execution count, not a forecast. Per-site static asset requests are unavailable, not zero. Migrating them to worker-first adds executions; their unknown volume plus future account traffic must fit within a refreshed budget with headroom. The previous statement that no account count was available is superseded; sufficient post-migration capacity remains unproven.

Recovered historical configs both specify static-only assets, the same HTML/404 handling, compatibility 2026-10-09 and workers.dev=false. Geumcheon additionally records empty compatibility flags, logpush=false, observability.enabled=false and preview_urls=false. Preserve these observations for restoration, but do not treat the historical files as a complete export of current provider configuration. The local test config is not a production deployment config.

Active UUID→source metadata, current full configuration, rollback eligibility/assets, and Custom Domain restoration remain pending helper evidence. Recorded rollback commands were not executed. Version rollback and domain reassignment are separate operations.

## Added tests and unchanged runtime

- Router tests **9/9**: added exact 307 `/404.html` redirect/query/empty-body coverage and opaque robots-policy pass-through. The policy fixture is synthetic and is explicitly not presented as a current public robots body.
- Difference classification tests **3/3**: redirect cannot be called a file-body match, robots mismatches cannot be normalized into a pass, matching hashes with error statuses cannot be accepted.
- Offline reconciliation verifies both 19-file receipts against saved ZIP bytes and recomputes the 16/18 counts. Unknown cases remain labeled as unknown.

Router/package runtime and candidate ZIPs are unchanged from `137bfb4f837d0bb30b441085643e64fd9d409cff`; previous local HTTP/pixel results remain local evidence, not a global live-equivalence verdict.
