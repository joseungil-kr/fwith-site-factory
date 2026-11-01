# Local pilot implementation review — 2026-11-01

This supersedes the initial REVIEW.md preflight. **No production deployment, hostname change, Worker creation/deletion, account change or CI dispatch occurred.** The implementation is ready for independent review; cutover is blocked on live artifact/rollback proof and request quota headroom.

## Scope and source evidence

Base main: `3a41390c7d1674cd8df25148c84cd91c205536dc`. Branch: `integrate/regional-worker-pilot-20261101`. Initial audit commit `79115d3f772bf7e093edc6c2e2025bc50cc969e7` was pushed and read back through the GitHub connector.

`repository-inventory.json` now has **71 unique regional hostnames and 73 declarations**. Duplicate source declarations are retained rather than silently resolved. The missing hostname was in `scripts/direct-seoul-gwanak/publication-binding.json`, despite HOSTNAME=None in its publisher. This is source inventory, not account-wide live inventory. No new crawl was performed.

| Hostname | Existing Worker | Active UUID, helper UI at 100% | Candidate source SHA |
| --- | --- | --- | --- |
| seoul-dongjak.fwith.kr | seoul-dongjak-flower-guide | 3720873d-5c57-4c0f-a25c-80dba048ddd1 | 2935ac394dd63e81c443995a66fab46981f652bf |
| seoul-geumcheon.fwith.kr | seoul-geumcheon-flower-guide | c3d0ea60-ca39-47b6-a119-e692d66a1658 | 673ff52bb8f21f58bb104b447f3f105fd1a52a98 |

Parent-supplied helper observations were read from the specified PC file. `cloudflare-helper-observations.json` preserves its SHA-256 and observations, omitting the account identifier. Timestamp: 2026-11-01T05:15:22.4482434Z. Both have Custom Domains, no Routes, static-only assets, zero bindings, workers.dev/version previews disabled, compatibility date 2026-10-09, no flags displayed, default placement. UI logs/traces/cache labels were disabled; do not infer global asset-cache behavior from that label. Static-only metrics were unavailable. Ego was not accessed.

**Active UUIDs are observed; their deployed source SHA and complete asset bytes remain unverified.** Candidate builds must not be asserted to be the current production version.

Proposed survivor after review: existing `seoul-dongjak-flower-guide`. Dongjak retains its domain; Geumcheon would move only in a separately approved step. Keep both old Workers. Never touch generic-skycar-shadow, flower-a/b, V5, fwith.kr or blog.fwith.kr.

## Exact builds and implementation

- Geumcheon `673ff52b` has exact parent `d380d73a`, exact planned source tree and matching planned file hashes. Its retained production-output contract names the successor and contains 19 files. See `geumcheon-successor-evidence.json` and `geumcheon-source-check.json`. CI guards were not fabricated or weakened.
- Each candidate's rebuilt **19-file dist** matches every SHA-256 in its retained production-output contract. This establishes retained-artifact equivalence, not current public equivalence.
- Builds used independent sibling directories to avoid unrelated parent PostCSS config. Customer source and lockfiles were not changed. Local npm 10.9.4 ran `npm ci --ignore-scripts --no-audit --no-fund`; original build/test scripts completed. No dependency upgrades or audit fixes were performed.
- `router.mjs` uses an exact two-host allowlist and isolated `/__regional/dongjak` and `/__regional/geumcheon` paths. It preserves request method/query/headers and response bytes/status, strips its own namespace from redirects while retaining relative Location form, rejects encoded separators/double-encoding, and never routes unknown hosts to assets. No custom Cache API layer is added.
- `package.py` accepts only the two pinned candidates, checks exact file sets/hashes, refuses existing output folders, and copies customer files byte-for-byte. Header rules are namespaced. `auto-trailing-slash`, `404-page`, canonical/sitemap/robots/proof files, noindex metadata, telephone and product links are preserved.
- Local config uses run_worker_first=true, a local-only name, no production account/domain configuration, and workers.dev disabled. It is not a production deployment configuration.
- **37 package files: 36 uploadable static assets plus one `_headers` configuration file**, total 1,961,438 bytes, maximum 171,698 bytes. Router/config/inventory outside the assets directory are separate. See `final-local-inventory.json`. No asset deduplication is attempted in this small pilot.

## Checks completed

| Check | Result | Evidence |
| --- | --- | --- |
| Existing publisher tests with portable fixtures | Dongjak 78/78, Geumcheon 76/76 | `*-portable-tests.txt` |
| Native source tests | Final suites Dongjak 85/85, Geumcheon 122/122; inherited suites also pass | `*-native-tests.txt` |
| Builds and static QA | Both pass | `*-build.txt` |
| Router unit tests | 7/7 | `router-tests.txt` |
| Packaging/tamper refusal/local reconstruction | 4/4 | `package-tests.txt` |
| Real local workerd versus separate static-only baselines | 115/115 | `local-http-results.json` |
| 390px mobile and 1280px desktop; home/directory/detail/404 on both sites | 16/16 PNG-identical, no horizontal overflow, zero external requests | `visual-results.json`, `screenshots/` |

Windows fixtures try real symlinks and fall back only on WinError 1314 to copied/empty nodes with mocked link metadata. Five fixtures per region cover the original rejection assertions. Publisher and original tests stay unchanged. Physical OS symlink traversal is not established by the fallback; no security settings were changed.

HTTP comparisons cover public files, redirects, query strings, security/cache headers, 404s, internal/foreign-region paths, unknown hosts, HEAD, repeated requests and conditional requests. Opaque ETags differ with internal paths. Each server's own validator returns 304; an old validator safely receives the complete current body. A migration may cause a one-time revalidation download. Local repetition is not proof of global edge-cache behavior.

Visual QA used a fresh headless local browser, DNS mapped to 127.0.0.1 and an external-request deny rule. It never attached to Ego or accessed public sites. Lazy images were eagerly decoded; consecutive stable screenshots avoid transient WebP scaling differences. Representative mobile home and desktop detail screenshots were visually inspected. Historical failed logs in the initial audit are not the final verdict.

The local reconstruction test separates each namespace and reuses retained original `_headers`, recovering all 19 original hashes per site. **This is not a Cloudflare rollback test.**

## Release gates and restoration limits

1. Obtain full active-version artifacts/settings or prove the retained builds match the observed active UUIDs. Public GETs previously returned 403; no alternative UA/path was tried and no public byte comparison is complete.
2. Prove both UUIDs remain available and that rollback restores the intended assets/settings. UUIDs and retained build ZIPs alone do not prove recoverability. Geumcheon's Custom Domain must separately be restorable to its original Worker; Dongjak's original UUID is 3720873d-5c57-4c0f-a25c-80dba048ddd1, Geumcheon's is c3d0ea60-ca39-47b6-a119-e692d66a1658. Neither rollback nor reassignment has run.
3. Verify account request headroom. Existing static-only delivery is free/unlimited; worker-first invokes code for every request including images/CSS. Free execution shares 100,000 requests/day across the account. Current counts are unavailable. Quota exhaustion can stop delivery despite a tiny file count.
4. Parent independently reviews code, evidence, recoverability and the exact two-host plan. Only afterward consider the existing survivor and then Geumcheon's domain separately; never batch-migrate all 71.

## Reproduction

Use pristine candidate source exports for prebuild tests, then separate sibling `build-dongjak` / `build-geumcheon` folders for builds. Set SITE_URL, SITE_INDEXABLE=true and SITE_FACTORY_REVISION to the exact candidate, ASTRO_TELEMETRY_DISABLED=1, Python UTF-8. Run original npm scripts. Windows uses a local python3.cmd shim to installed Python; no OS settings change.

Run `node --test scripts/regional-worker-integration/router.test.mjs`. Package with `python scripts/regional-worker-integration/package.py --dongjak ../build-dongjak/dist --geumcheon ../build-geumcheon/dist --output ../new-review-bundle`; output must be new. Use Wrangler 4.148.0 `dev --local`, ports 8787 for combined and 8788/8789 for separate assets-only baselines with identical HTML/404 settings. Run `test_local_http.py` explicitly against those local servers. Set PLAYWRIGHT_MODULE and LOCAL_BROWSER_EXE for `visual_compare.mjs`.

Official references: [asset binding/hostname semantics](https://developers.cloudflare.com/workers/static-assets/binding/), [billing and worker-first quota failures](https://developers.cloudflare.com/workers/static-assets/billing-and-limitations/), [limits](https://developers.cloudflare.com/workers/platform/limits/), [version contents](https://developers.cloudflare.com/workers/versions-and-deployments/), [rollback constraints](https://developers.cloudflare.com/workers/versions-and-deployments/rollbacks/). Free assets allow 20,000 files/version and 25 MiB/file. Cloudflare supports rollback among the 100 most recently published versions; associated resources are not restored automatically.
