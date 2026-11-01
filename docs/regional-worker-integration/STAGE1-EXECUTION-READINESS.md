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

Local tests: executor 18/18, earlier recovery 6/6 and stage-1 planner 2/2 (26 total). Cases include successful deployment, preflight and recovery read failures, pre/post-deploy concurrent changes, absent/ambiguous UUID output, failed command with a known UUID, public verification failure, recovery failure and uncertain recovery with independently restored state. API parser tests cover pagination, domain collision, split percentage and missing retained-version identity. YAML parsing confirms manual-only, disabled-by-default execution and the fixed concurrency/permissions. Reproduced payload and pinned installed Wrangler checks pass offline.

Network calls are bounded (10 seconds per request, 60-second API snapshot and 120-second public probe budgets); command timeouts are 180 seconds. These reduce exposure to the 25-minute workflow timeout, but cannot guarantee recovery if the runner is terminated or Cloudflare is unavailable. Operator/dashboard writes still require coordination because no API compare-and-swap is available. The executor deliberately fails closed on unexpected response/settings formats; current authenticated write execution has not been tested. Review current domain pagination/schema and pilot ASSETS binding representation before dispatch. Capacity input is an operator observation, not automated live metering; post-success longer-term monitoring remains a separate explicit operational step.

GitHub must recognize the new workflow on its default branch before workflow_dispatch can be used; exact publication/merge is still pending independent review, with no dispatch performed here. Run SHA must be the final reviewed commit containing these files. Do not substitute the prior a750 commit because it lacks the executor. Stage 2 domain migration is excluded.

Latest verified remote storage remains a750d0bc. Local follow-up bundle for one complete review contains six paths: this report, ROLLBACK-PLAN.md, prepare_stage1.py, execute_stage1.py, test_execute_stage1.py and .github/workflows/regional-dongjak-stage1.yml. No partial push is attempted. The historical held-push text was corrected in the related local documentation update.

## Independent settings-drift regression fix

The a355 independent review reproduced a Geumcheon logpush change immediately before rollback that the UUID-only guard missed. Recovery now retains the first post-deploy snapshot. Geumcheon must equal its full original version/settings in both that snapshot and the fresh recovery snapshot. Dongjak must equal its full first post-deploy version/settings at recovery time. Further settings drift stops without rollback. If the first snapshot failed, there is no verified settings baseline and recovery writes stop.

An initial Dongjak settings error visible in the first post-deploy snapshot can still trigger rollback when the fresh snapshot is identical and Geumcheon is unchanged. This separates observed initial deployment-state errors from observed later changes; it cannot prove causal ownership of a change that races before the first snapshot. External writer coordination and exact parent-approved dispatch ref remain required. reviewed_sha is an operator assertion, not a built-in immutable allowlist.

Four new regression tests cover both Workers' pre-recovery drift, initial Dongjak error versus later drift, initial Geumcheon drift, and missing first snapshot. Total 26/26 tests pass locally; no provider calls or dispatch occurred. The final review bundle remains the same six files.

## Stage 1 stop diagnosis and single-page API correction

Run 41289365725 at reviewed d260ef1 completed tests, exact bundle preparation and dry-run, then stopped with domain_pagination_unverified. Artifact 13076353323 contains only finished at runner UTC 08:33:54.394179, status stopped and that reason; no deploy_started/pilot_recorded/rollback_started event exists. The checked-in execution path performs domain reads before recording deploy_started or invoking Wrangler. Together the artifact, source ordering and job logs establish no provider write by this run. This does not claim exclusion of unrelated external writers. GitHub displayed an offset creation time, but runner logs and artifact UTC agree; freshness was not the failure.

Confirmed implementation mismatch: the [official API](https://developers.cloudflare.com/api/resources/workers/subresources/domains/methods/list/) describes all Worker domains, permits hostname/service filters, does not list page/per_page request parameters, and makes result_info optional. The [official Python SDK](https://github.com/cloudflare/cloudflare-python/blob/main/src/cloudflare/resources/workers/domains.py) implements list with SyncSinglePage and no page/per_page parameters (reviewed 2026-11-01). Earlier successful local publisher code also handled optional metadata, but its saved binding receipts do not contain original response shape. Thus missing metadata can be a normal documented response; the exact missing field in the failed live response is not recoverable from the old sanitized receipt and remains unconfirmed.

The minimal correction uses the documented unpaginated GET, validates success/errors/row shape/unique IDs, and accepts absent pagination metadata under the documented single-page contract. Any supplied count/page/total contradicting completeness, continuation marker, malformed metadata or unknown metadata field stops. Each target's hostname-filtered and service-filtered result must agree exactly with corresponding full-list records; ignored filters, missing target records and additional Worker aliases stop. This is not treating an arbitrary empty metadata object as proof on a generic API: the endpoint's published single-page contract is the completeness basis, and the four exact-filter reads cross-check the relevant scope. If the service advertises multiple pages in reality, execution stops rather than inventing unsupported pagination parameters.

Provider reports now retain only response field names, result type/count and integer pagination fields for domain reads. Account/token/domain record values are excluded. A GET-only independent diagnostic using the existing authenticated environment should capture these shapes and confirm the five-query agreement before another operational dispatch. No new diagnostic workflow or dispatch was created here; no credentials were inspected or exported. Actual live response capture and independent review remain pending.

Tests now include metadata absent/empty/partial/complete, advertised truncation/continuation, malformed integer types, duplicate IDs, ignored filters and missing full-list records. Executor tests 21/21 plus prior guards 8/8 pass (29 total). Changed files are execute_stage1.py, test_execute_stage1.py and this report only. No push, deployment or re-dispatch was performed for this correction.


## Official endpoint audit and GET-only diagnosis (supersedes historical readiness above)

Current published integration commit is d260ef1ab8126fd0e3f5ef0a1901c6d1d19fa904; main workflow registration is ea8552dc5649163ec152e46af6a94fbcb2a634b6. The one run described above stopped before deploy. The 05dc pagination correction and this subsequent correction remain local; no retry or diagnostic dispatch has occurred. Earlier not-dispatched/publication-pending paragraphs describe their original review stage only.

Independent review found a second schema mismatch: domain rows were incorrectly required to contain enabled and previews_enabled. The official [DomainListResponse](https://github.com/cloudflare/cloudflare-python/blob/main/src/cloudflare/types/workers/domain_list_response.py) contains id, cert_id, environment, hostname, service, zone_id and zone_name. Fixtures now use precisely these fields with synthetic values, without invented exposure flags. Mapping requires hostname/service/environment=production. Exposure is verified separately.

All executor GET endpoints were compared with the official Python SDK on 2026-11-01:

| Account-relative endpoint | Verified contract and safety assertion |
| --- | --- |
| workers/domains | [Single-page list](https://github.com/cloudflare/cloudflare-python/blob/main/src/cloudflare/resources/workers/domains.py), optional metadata; full list plus hostname/service filters for each target must agree. |
| workers/scripts/{name}/subdomain | [Separate response](https://github.com/cloudflare/cloudflare-python/blob/main/src/cloudflare/types/workers/scripts/subdomain_get_response.py) has enabled and previews_enabled; both must explicitly be false. Missing values stop. |
| workers/scripts/{name}/deployments | [List contract](https://github.com/cloudflare/cloudflare-python/blob/main/src/cloudflare/resources/workers/scripts/deployments.py): first deployment is actively serving. Use first, not maximum timestamp. Require percentage strategy and one valid version at 100%. |
| workers/scripts/{name}/settings | [Script-and-version settings](https://github.com/cloudflare/cloudflare-python/blob/main/src/cloudflare/resources/workers/scripts/script_and_version_settings.py), distinct from script-settings. Optional schema fields do not prove safe defaults: require observed compatibility/date/flags/logpush/usage/bindings baseline and compare full returned settings. |
| workers/scripts/{name}/versions/{id} | [Exact-version GET](https://github.com/cloudflare/cloudflare-python/blob/main/src/cloudflare/resources/workers/scripts/versions.py). Matching returned id is a deliberate safety assertion even though the SDK marks it optional. Absence stops. |

ASSETS name/type follows the [settings response model](https://github.com/cloudflare/cloudflare-python/blob/main/src/cloudflare/types/workers/scripts/script_and_version_setting_get_response.py). Actual post-deploy representation is not yet verified. Domain mapping and separate subdomain response are now included in recovery state comparisons, preserving concurrent-change guards.

The existing manual workflow gains diagnose_only (default false), mutually exclusive with execute_stage1. The GET-only mode collects all 13 fixed endpoint reads, continues collecting other shapes after a failed endpoint, and validates the cached snapshot. A distinct observed active UUID adds an exact-version GET. It never constructs Wrangler, invokes subprocesses, probes public pages or writes provider state. The existing workflow preparation/dry-run still precedes this mode without provider credentials. It uses only the same existing secret references in its diagnostic step; no authentication extraction or new credentials. Retained evidence contains endpoint paths without account IDs, field names, types, counts, integer pagination metadata and fixed error codes, not response values.

After independent review and publication/registration of this workflow revision, the diagnostic invocation is the integration ref with reviewed_sha set to its exact reviewed commit, diagnose_only=true and execute_stage1=false. Capacity inputs are unnecessary for GET-only mode; execution still requires fresh values. Do not dispatch this local revision yet. The helper's unauthenticated 9106 failure supplies no schema evidence. Real authenticated shapes, five-query domain agreement and subdomain flags remain pending the authorized existing GitHub environment diagnostic. No claim of live schema verification is made from fixtures.

Local verification: executor 25/25, recovery 6/6, planner 2/2 (33 total). New cases use the official seven-field domain fixture, absent/enabled subdomain flags, first-active ordering, all 13 diagnostic reads with write adapters forbidden, and continued collection after endpoint failure. Final change bundle relative to 05dc is four files: workflow, execute_stage1.py, test_execute_stage1.py and this report. No assets, credentials, permissions or production connections changed.


## Public preflight failure evidence

Run 41291898548 stopped at the initial public baseline with public_verification_failed, after the original API snapshot passed and before deploy_started. Its failed-step log contains only status stopped and exit 1, so it cannot identify the historical URL or transport cause. No deployment or rollback occurred. The first candidate URL is the first retained contract entry in Dongjak; the old receipt does not prove that this was the failing entry.

The local diagnostic change preserves all response/hash/robots/redirect assertions and the no-redirect transport. public_probe_failed records only the fixed public URL, HTTP status, expected/actual SHA256, safe redirect destination, exception class and fixed reason. Unknown external redirects and non-contract destination paths are redacted; queries are omitted. Raw bodies, exception messages and credentials are excluded. Managed robots additionally records original-suffix and policy-presence booleans; its full expected hash is intentionally null because the managed prefix is not fixed bytes. Transport failures retain null HTTP/hash values instead of inventing a status.

New --public-preflight-readonly --report PATH mode calls only the public probe, before any provider credentials or Wrangler construction. It requires no authentication and cannot deploy or recover. This mode has not yet been run against production; independent review should precede use. A local result would not by itself prove the previous GitHub runner response. No UA change, retry loop, proxy or alternate access route was added.

Verification: executor/evidence tests 27, recovery 6, planner 2 (35 total), all pass; diff whitespace check passes. Tests cover transport message redaction and a 403 block response with external sensitive redirect. Changed files: execute_stage1.py, test_execute_stage1.py and this document. No workflow/publication/dispatch or provider write in this follow-up.


## URLError classification and redirect contract

Helper's 09:13:51 UTC local receipt shows URLError on Dongjak /404.html with no HTTP status, redirect or body hash. It is not evidence of a 403, wrong redirect or site outage. Historical GitHub failure cannot be assigned the same cause from this separate environment.

Python's [urllib.error documentation](https://docs.python.org/3/library/urllib.error.html) permits URLError.reason to be either an exception or a string. Diagnostic classification now records only its class, fixed transport category and integer errno/winerror/verify_code. Categories distinguish certificate verification, other TLS, name resolution, timeout, connection and generic OS errors. A string reason remains unclassified: its text may contain proxy URLs or other private data and is never logged. This cannot reliably distinguish a proxy tunnel error whose only evidence is a string. Default TLS verification and proxy discovery remain unchanged; no network settings are inspected or modified.

The [urllib.request contract](https://docs.python.org/3/library/urllib.request.html) and installed implementation were checked. Returning None from redirect_request declines automatic following; the default error handler then raises a readable HTTPError. The public probe catches HTTPError before its generic exception handler and reads status/Location/body. A network-free opener regression test confirms a normal 307 Location:/404 produces HTTPError(code=307), preserves the empty body, and never calls open again. Therefore normal 307 handling itself does not explain the observed bare URLError. The existing /404.html contract remains 307, Location /404, empty body.

29 executor/evidence tests pass, including classification/redaction and real urllib handler-chain simulation; earlier recovery/planner 8 tests were unaffected. No additional URL fetch, push, dispatch, deployment, recovery or configuration change was performed. Live underlying classification still needs an independently reviewed GET-only observation.


## GitHub public-only diagnostic wiring (local, not published)

public_preflight_only defaults false. The first workflow gate counts all three mode booleans and rejects more than one, retaining exact reviewed SHA and first-attempt requirements. The public step has no env/Secret references and calls only --public-preflight-readonly. Both provider-API diagnosis and deployment steps explicitly exclude this mode. The existing no-credential tests/build/dry-run remain; the sanitized artifact condition includes public-only mode. No new permissions, network settings or dependencies are introduced.

Regression checks cover static workflow exclusion/defaults/guards and a public CLI run whose Provider, Wrangler and subprocess adapters raise if called. Total tests: executor 31, recovery 6, planner 2 = 39 PASS. The complete unpublished delta against remote integration 9867dc3 is confined to four paths: workflow, execute_stage1.py, test_execute_stage1.py and this report. Publication and any GitHub public diagnostic dispatch remain pending independent review; no provider write or additional URL request was made during implementation.
