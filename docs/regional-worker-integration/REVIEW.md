# Regional Worker integration preflight — 2026-11-01

**NOT READY FOR PRODUCTION. No hostname, Worker, account, CI workflow or deployment was changed.**

## Source evidence

- Control main and locally fetched origin/main: `3a41390c7d1674cd8df25148c84cd91c205536dc`.
- Local integration branch: `integrate/regional-worker-pilot-20261101`.
- Separate checkout: `worker-integration`; source worktrees: sibling `pilot-dongjak` and `pilot-geumcheon`. The existing Ego helper session/checkouts were not accessed.
- Root AGENTS.md was read in all three checkouts. No tracked SKILL.md or .agents skill was found. This work does not modify Next.js.
- GitHub connector confirms main SHA. Local gh authentication is invalid; public Git clone succeeded with approved network access. No authentication/settings were changed.
- `repository-inventory.json` recovers 72 declarations for 70 distinct regional hosts from main's publishers and registry. This is NOT the parent's complete 71-host inventory. One-host discrepancy remains unresolved. Dynamic publisher declarations are not evaluated by the read-only AST collector.
- Goyang registry's `worker` is `goyang-flower-prod-disabled`, while its coverageDeployment worker is `goyang-flower-guide-qa`. This demonstrates why registry names alone cannot establish current live binding.

## Tentative two-site pilot, not selected for cutover

| Hostname | Publisher-declared Worker | Branch head |
| --- | --- | --- |
| seoul-dongjak.fwith.kr | seoul-dongjak-flower-guide | 2935ac394dd63e81c443995a66fab46981f652bf |
| seoul-geumcheon.fwith.kr | seoul-geumcheon-flower-guide | 673ff52bb8f21f58bb104b447f3f105fd1a52a98 |

Roots are `site-factory/seoul-dongjak-flower` and `site-factory/seoul-geumcheon-flower`. Each publisher has one regional article, home, a noindex directory and a noindex 404. These are source declarations, not verified live content.

Proposed eventual survivor is the existing Dongjak Worker, pending proof of live bindings, traffic, backup and independent review. Dongjak would retain its binding; Geumcheon would later move to it. Both old Workers must remain. No new Worker or account is proposed. Do not touch generic-skycar-shadow, national flower-a/b, V5, fwith.kr or blog.fwith.kr.

## Checks actually performed

- Inventory self-check passed: 70 unique hosts, excluded named national/root/blog hosts, live-version fields remain unknown, Goyang coverage worker retained.
- Dongjak existing `test_publish.py`: **78 tests, 74 pass, 4 errors** after restoring Git archive bytes and using Python UTF-8. All four errors are Windows `WinError 1314` creating test symlinks. Full log: `dongjak-tests.txt`. This is existing publisher validation, not integration validation.
- Initial tests exposed Windows checkout CRLF and cp949 failures. Git archive bytes restored the inspected source seals; tracked `git diff --name-only` was empty afterward. Archive CLI reported an unrelated Korean filename decoding error, so whole-checkout byte identity is not asserted.
- Geumcheon direct publisher test run is retained in `geumcheon-tests.txt` as an **unsuccessful preliminary run**, not latest-source approval. Its successor needs the `two-regional-banners/update.py` path and EXISTING_UPDATE mode. That read-only source path also requires CI execution context (`GITHUB_RUN_ATTEMPT`); it was not fabricated. No CI was dispatched.
- Public root probes made exactly one GET per candidate: both returned **HTTP 403**. `live-home-probe.json` records the results. No alternate UA/path/browser was used to evade the denial.
- npm was not available in PATH or the inspected standard installation locations. No dependencies installed; no Astro build, final dist inventory, integration runtime tests or screenshots completed.

## Design constraints from existing code and official documentation

Existing publishers emit assets-only settings with `html_handling: auto-trailing-slash` and `not_found_handling: 404-page`. Generated `_headers` also depend on SITE_INDEXABLE. Preserve all of these semantics, including per-region noindex and 404.

Cloudflare documents that ASSETS.fetch ignores hostname and matches pathname. A candidate implementation needs an exact host allowlist and distinct internal asset prefixes, with no exposed cross-region internal paths. Prefix rewrite must also handle Location redirects and scoped header rules. Byte-preserving HTML and assets should be packaged only from verified production artifacts; do not merge sources directly or infer final file count from manifests.

- https://developers.cloudflare.com/workers/static-assets/binding/
- https://developers.cloudflare.com/workers/static-assets/billing-and-limitations/
- https://developers.cloudflare.com/workers/platform/limits/
- https://developers.cloudflare.com/changelog/product/workers/8/

Free Worker asset limits: 20,000 files per version, 25 MiB per asset. Free Worker execution allowance is account-wide 100,000 requests/day. With run_worker_first all matching requests invoke code, including image/CSS requests; static-only unlimited delivery does not carry over. Official assets billing docs warn of 429s after that quota. Current account usage/headroom is unknown, so this is a material go/no-go item, not merely a file-size check.

## Exact blockers and next evidence

1. **Blocked/unverified, not attempted through UI:** read Cloudflare hostname bindings, full active version UUIDs, settings and asset inventories for both candidates. No suitable Cloudflare connector or environment credential was available. Ego UI is shared with the Naver helper; collision must be coordinated before using it.
2. **Denied by origin:** GET both public root URLs returned 403. Response content/source SHA and current byte comparison remain unknown. Do not retry by changing UA or route.
3. **Pending:** retrieve deployable existing-version assets/settings and prove a rollback restoring both content and hostname bindings. Git source checkout alone is not a production backup. No rollback test has run.
4. **Pending:** identify missing 71st hostname, build exact deployed source, final inventory with hashes/sizes, mobile/desktop checks, slash and header behavior, cross-host paths/404/cache isolation, quota headroom, then independent parent review.

There is no integration runtime or deployable bundle yet: implementing a production-targeted package before identifying the actual versions and artifacts would use an unverified baseline. The audit scripts are read-only and can be resumed with the missing evidence. No production cutover is requested by this report.
