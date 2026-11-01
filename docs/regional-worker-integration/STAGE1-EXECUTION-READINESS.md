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

## Local implementation completed; not dispatched

The three new operational/preparation files are prepare_stage1.py, execute_stage1.py and .github/workflows/regional-dongjak-stage1.yml. test_execute_stage1.py exercises the restricted execution state machine with fake provider/command adapters; no real credentials or API are used in tests. The earlier stage1_commands.py remains an offline historical planner; the workflow uses execute_stage1.py with explicit runner-local paths instead.

The workflow is manual-only and execution defaults to false. It requires owner actor, exact reviewed SHA equal to the run SHA, first attempt, read-only GitHub permissions, the existing publisher concurrency group and existing secret references only in the final guarded step. No legacy publisher, domain attach, IndexNow, force, token creation or other Worker write is invoked. Preparation, tests, package installation and Wrangler dry-run happen without provider credentials. Artifacts contain fixed status codes, timestamps and version IDs only; raw provider responses/subprocess logs/credential values are not uploaded.

The executor validates the reviewed ZIP, exact config, fixed router hash, complete 36-asset hashes plus _headers, pinned Wrangler 4.148.0, fresh operator-supplied capacity observation and original deployments. It GETs paginated domain records, requires unique original mapping and disabled preview routing, both active versions at 100%, retained-version GET availability and baseline settings. Failure or incomplete API pagination stops rather than guessing. Public checks cover both sites' retained paths plus canonical /404, actual missing URL, internal namespace attempts, robots managed policy and unchanged original suffix. Status, selected headers and body hashes must match before/after; ETags and volatile telemetry headers are excluded.

Exactly one deploy can occur. The only accepted pilot identity is a unique Current Version ID emitted by the pinned Wrangler process followed by exact active GET readback. An absent/ambiguous output UUID causes read-only reconciliation and stops, even if a candidate-looking UUID is visible. No redeploy or inferred-UUID rollback occurs. If a known pilot fails verification, a fresh original-mapping and 100% snapshot must still show that exact pilot before the one permitted fixed-original rollback. A rollback with uncertain command result is assessed by GET plus public proof; it is never repeated automatically. A third-party version or failed readback blocks all recovery writes.

Local tests: executor 14/14, earlier recovery 6/6 and stage-1 planner 2/2 (22 total). Cases include successful deployment, preflight and recovery read failures, pre/post-deploy concurrent changes, absent/ambiguous UUID output, failed command with a known UUID, public verification failure, recovery failure and uncertain recovery with independently restored state. API parser tests cover pagination, domain collision, split percentage and missing retained-version identity. YAML parsing confirms manual-only, disabled-by-default execution and the fixed concurrency/permissions. Reproduced payload and pinned installed Wrangler checks pass offline.

Network calls are bounded (10 seconds per request, 60-second API snapshot and 120-second public probe budgets); command timeouts are 180 seconds. These reduce exposure to the 25-minute workflow timeout, but cannot guarantee recovery if the runner is terminated or Cloudflare is unavailable. Operator/dashboard writes still require coordination because no API compare-and-swap is available. The executor deliberately fails closed on unexpected response/settings formats; current authenticated write execution has not been tested. Review current domain pagination/schema and pilot ASSETS binding representation before dispatch. Capacity input is an operator observation, not automated live metering; post-success longer-term monitoring remains a separate explicit operational step.

GitHub must recognize the new workflow on its default branch before workflow_dispatch can be used; exact publication/merge is still pending independent review, with no dispatch performed here. Run SHA must be the final reviewed commit containing these files. Do not substitute the prior a750 commit because it lacks the executor. Stage 2 domain migration is excluded.

Latest verified remote storage remains a750d0bc. Local follow-up bundle for one complete review contains six paths: this report, ROLLBACK-PLAN.md, prepare_stage1.py, execute_stage1.py, test_execute_stage1.py and .github/workflows/regional-dongjak-stage1.yml. No partial push is attempted. The historical held-push text was corrected in the related local documentation update.
