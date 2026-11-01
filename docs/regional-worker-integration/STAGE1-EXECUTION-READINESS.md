# Stage 1 execution path review

No operational command, workflow dispatch, domain mutation, credential read or permission change performed.

## Existing authenticated environment

GitHub Actions in joseungil-kr/fwith-site-factory is the demonstrated environment. Connected GitHub job summaries for run 38428129720 show publish job 115403207465 succeeded, including preflight, pinned Wrangler deployment and public verification. The existing workflow references repository-held CLOUDFLARE_API_TOKEN and CLOUDFLARE_ACCOUNT_ID and runs ubuntu-latest without a named environment. Only reference names were inspected, never values. Historical success proves that path worked then, not that present write capability is guaranteed. The recent GET workflow provides read-access evidence only.

Do not dispatch seoul-dongjak-direct-publish.yml: it has first-publication assumptions, domain attach and IndexNow. The deployment command can run separately in the same Actions environment using the existing secret references; no credential export to the PC or new secret is needed. A new, reviewed stage-1-only manual workflow is required before execution.

## Portable exact payload

New local prepare_stage1.py verifies the already-committed ZIP SHA, complete entry set, router hash, 36 asset hashes and _headers, then creates a new destination with wrangler.stage1.json. It has no network or credential handling. It reproduced the tested sibling bundle byte-for-byte (config, router and all 37 asset-directory files).

- ZIP SHA: da8817cc8b501a4728e838f415447735e9932e9256b48c1df7a7504ac0ee9cb9
- Router SHA: df119c463b2a1c0a25a4323b8ec4575c6c386d1f539d95e3efb48569219538f1
- Config SHA: 1f0e9c1e3047a0e33df1113d65dbf13c820a8ab6f4fc5b1856f562303027fea3
- Local reproduced path: sibling stage1-portable-reviewed/wrangler.stage1.json.
- Runner path: $RUNNER_TEMP/regional-stage1/wrangler.stage1.json, generated from a pinned reviewed checkout, not copied from this PC.

Exact config:

```json
{
  "name": "seoul-dongjak-flower-guide",
  "main": "router.mjs",
  "compatibility_date": "2026-10-09",
  "workers_dev": false,
  "assets": {
    "directory": "./assets",
    "binding": "ASSETS",
    "run_worker_first": true,
    "html_handling": "auto-trailing-slash",
    "not_found_handling": "404-page"
  },
  "preview_urls": false,
  "compatibility_flags": [],
  "logpush": false,
  "observability": { "enabled": false }
}
```

Intended change: static-only becomes router plus ASSETS, with worker-first and two internal asset directories. Compatibility/date/flags, HTML handling, missing-page handling, disabled workers.dev/previews/logging remain as captured. Routes, custom domains, secrets, storage bindings and placement are not configured for mutation. usage_model=standard and default placement are baseline readback assertions, not assumed proven unchanged by omission; verify after deploy. No claim that unrelated zone robots/cache policy is part of this config.

## Concrete runner sequence, not executed

1. Manual owner-authorized run; pin reviewed control commit and artifact hashes; reject mutation reruns. Use contents:read. Use the exact existing concurrency group seoul-dongjak-direct-public-release with cancel-in-progress:false, so the legacy publisher cannot overlap. This does not lock manual dashboard writes or another workflow group; operator coordination remains required.
2. Before injecting existing provider secret references, prepare payload using `python3 scripts/regional-worker-integration/prepare_stage1.py --output "$RUNNER_TEMP/regional-stage1"`. Install Wrangler 4.148.0 in a runner-local tool directory and assert its package version. Run deploy --dry-run against the generated config without provider credentials.
3. In the same serialized job, use the existing references for a GET-only preflight: both deployments and exact versions; all pages of account Workers domains (or an exact supported query with uniqueness proof); both expected host-to-service mappings. Require Dongjak original UUID 3720873d-5c57-4c0f-a25c-80dba048ddd1 at 100% and Geumcheon c3d0ea60-ca39-47b6-a119-e692d66a1658 at 100%. Fail on unavailable data, drift, extra ambiguous binding or split traffic. Record sanitized settings/baselines only. Refresh public comparisons and account usage.
4. Immediately re-read state, then invoke the installed Wrangler binary with `deploy --config "$RUNNER_TEMP/regional-stage1/wrangler.stage1.json"`. No attach, route, IndexNow or account mutation commands. Logs remain private/sanitized. Record the UUID attributed by the deployment result, then require GET active UUID to equal that exact returned UUID at 100%. Do not adopt an arbitrary newly observed UUID as the expected pilot if deployment outcome is uncertain.
5. Run the public comparison suite and read back both domain mappings and relevant settings. Capture metrics at agreed intervals. On failure, obtain fresh deployment readback; rollback only if current Dongjak UUID equals the recorded pilot at 100% and Geumcheon remains on its original Worker/version. Invoke the same installed binary with `rollback 3720873d-5c57-4c0f-a25c-80dba048ddd1 --name seoul-dongjak-flower-guide --config "$RUNNER_TEMP/regional-stage1/wrangler.stage1.json"`. Verify original UUID/100%, settings and public responses. Unknown UUID/uncertain writes stop for reconciliation rather than blind retry.

## Minimum remaining implementation

One preparer file is implemented locally. Two operational files remain to implement and independently review: a manual stage-1-only workflow and a strict provider transport/executor that performs fresh GET checks, captures the actual deployment UUID, runs only the fixed deploy/rollback argv, and sanitizes reports. The existing stage1_commands.py is a command planner with PC sibling paths, not that executor. Its guard logic can be reused, but must accept explicit verified runner tool/config paths rather than assume the PC layout. Add focused transport/uncertain-result tests before arming execution. No extra secrets or privileges are proposed.

Thus existing authenticated hosting is identified and payload portability is resolved; live write capability, race-aware execution and automated post-deploy recovery are not yet demonstrated. Stage 2 domain restore payload is not a stage-1 prerequisite. The latest successful GitHub storage is a750d0bc; the historical 'Push remains held' sentence in ROLLBACK-PLAN.md has been corrected locally in this related update.
