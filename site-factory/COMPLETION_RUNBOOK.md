# Site Factory operation and completion

## Implemented boundary

The existing Airtable/agent generation system produces researched query-first
drafts. This repository provides executable planning/input validation, immutable
snapshot adapters, actual-renderer parity, builds and previews, authenticated
publication gates, exact-revision deployment and live verification. It does not
introduce a second CMS, a new model API, a paid service or a background schedule.

Suwon uses `structured-json-v12` (`src/data/pages.json`). Existing flower sites
retain `markdown-v1`; explicit legacy merged/redirect and home architecture
records are preserved. A snapshot changes its renderer input, manifest, page map
and architecture together. IDs, routes, title/keyword/intent collisions, source
provenance and Blueprint category/type pairs are checked before writes.

## Launch and growth

1. Supply a researched Industry Blueprint and a verified company fingerprint.
   `engine/plan_batch.py INPUT.json --mode launch --volume N` selects query
   intents in commercial priority order and merges synonymous intents. Missing
   required inputs return bootstrap questions. Industry defaults remain marked
   for human review and never become confirmed company conversion channels.
2. Set an explicit initial launch volume. Continuing growth has a separately
   configurable volume; neither is hardcoded to one page/day. `--mode growth`
   returns `paused` while `policy.growthPaused` is true. Planning creates no
   schedule and does not publish anything.
3. External generation researches sources, writes provider-voice customer copy,
   and obtains actual content approval. The existing live Publisher payload is
   accepted for preview, but currently lacks machine-verifiable approval fields.
   Its Draft Lab approval and any external reconciliation are not proved by
   queue creation alone. Suwon/versioned payloads therefore remain preview-only until explicit approval
   is supplied. Existing Markdown sites keep the prior trusted-writer/QA publishing
   contract; their queues are not disabled by this migration. This compatibility
   mode does not claim that upstream Airtable approval was machine-verified.
4. A reviewed frozen request adds `APPROVAL_STATUS: approved` and
   `APPROVED_SNAPSHOT_HASH: <snapshotHash>` returned as `approvalHash` by the preview render or
   `engine/snapshot_proof.py --payload reviewed-issue-payload.txt`.
   These fields bind approval to exact normalized content, metadata and sources. The storage snapshot hash separately binds the
   server-assigned queue identity, without changing the older Markdown payload blocks. The
   authenticated repository writer is responsible for the approval; a hash is
   integrity evidence, not a substitute for review. Live Airtable migration is a separate explicitly reviewed operational step.
5. For an existing page, use a new snapshot ID and new queue record, with
   `SUPERSEDES_SNAPSHOT_ID` equal to its currently deployed snapshot. Unhashed
   legacy snapshot IDs cannot be silently overwritten. The manifest ledger keeps
   retired snapshot/queue bindings immutable. Route changes require a separate
   redirect migration.
6. The snapshot workflow builds and uploads a reviewable preview. A verified
   approved request may commit its frozen artifacts. `snapshot_committed` is an
   intermediate state, never `live_verified`, and the issue remains open.
7. Use `site-staging-deploy.yml` with the registered site key and full source SHA
   for an isolated noindex preview. Staging refuses the production Worker/name,
   any production/custom route, or a missing staging configuration. Suwon's QA
   Worker is `suwon-flower-guide-qa`; production remains
   `suwon-flower-guide-test` on `suwon.fwith.kr`.
8. Independent QA reviews that exact code/build. For Suwon, only after clearance
   update the trusted registry's `approvedRevision` and `approvalEvidenceUrl`,
   enable `productionEnabled`, and set `launchMode=live`. Leave
   `growthPaused=true` and `autoDeploySnapshots=false` unless separately approved.
9. Dispatch `site-production-deploy.yml` with `site_key` and the full
   `expected_revision`. Production has no Suwon push-trigger shortcut. The
   revision must belong to the registered production branch; builds record the
   exact source SHA and artifact hash. Source changes invalidate SHA clearance.
10. Deployment is followed by every manifest route/hub, exact revision/snapshot,
    canonical/H1/schema, robots, sitemap and 404 checks. HTTP403 or a network
    block is a nonzero incomplete result requiring independent verification.
    IndexNow runs only after exact live QA. An accepted submission is not a
    search-engine indexing or ranking guarantee.

## Initial partial-release quantity policy (2026-10-09)

For new initial launches, the owner's acceptance condition is at least90% of
planned pages complete, with the remainder (up to10%) deferred or completed later. Apply
this through the exact reviewed release subset described in
`engine/WHOLE_INITIAL_RELEASE.md`, not by shrinking the geographic inventory,
changing old hashes/counts, or marking unfinished content PASS. Current
Pyeongtaek scope is35 of original37; Chilwon/Wolgok remain deferred. Historical
exact20/24/full releases keep their existing contracts.

Pyeongtaek's exact35-of37 preparation binding is registered with an approved-empty
baseline. Other regions remain unregistered; production approval is still closed. Keep original membership/frozen lineage, source
and security boundaries. Finish the exact released set, build and inspect its
isolated noindex preview, then run the existing batch/hosted/visual/public gates.
Do not wait for deferred content after the authorized released set meets every
other gate. Do not call CONTENT_PASS, a code test, or a snapshot commit live.
Use actual approved-revision deployment, HTTP verification and IndexNow receipts;
record GSC verification/sitemap submission separately from indexing/ranking.

## States, failures and recovery

- `preview_ready_approval_required`: versioned input passed preview QA; no branch
  publication or deployment occurred. Review it and send a new approved request
- `snapshot_committed`: immutable content is in Git; live verification is pending
- `live_verified`: the exact production source and all registered routes passed
  live checks; IndexNow reception remains pending and the publishing issue stays open
- `live_verified_indexnow_received`: exact live QA plus a durable HTTP 200 or 202
  receipt for the exact public URL set; only this terminal success closes a publishing issue
- `indexnow_blocked_or_failed`: missing ownership proof, rejected request, uncertain
  response, or receipt failure; never a successful skip and never indexing proof
- `failed`, `verification_failed`, `verification_blocked`: keep the issue open;
  inspect the linked run/report, fix the specified input or gate, and retry the
  same immutable request or explicit superseding snapshot

Retries do not force-push or merge competing JSON registries. A push race fetches
the newest target, rerenders the exact frozen payload, reruns gates, and retries.
An unchanged approved snapshot can still enter exact-revision deployment, which
recovers a commit-before-deployment interruption. Build revision files are not
committed by the snapshot publisher. Whole-file replacement failure restores the
prior snapshot file set.

Issue-triggered privileged jobs verify both actor and issue author as repository
owner/write/maintain/admin. Public issue titles alone never authorize writes or
use of deployment credentials. Reusable workflows retain the original caller's
identity; there is no broad bot allowlist. Reusable deployment calls pass only
the two existing named Cloudflare bindings, never all repository secrets.
Snapshot jobs no longer have Actions write permission; only the publishing job
has Contents write, and deployment/preview jobs have Contents read.

## Reproducible checks

From repository root:

```sh
python3 -m unittest discover -s site-factory/engine/tests -p test_engine.py -v
python3 site-factory/engine/tests/test_legacy_baselines.py
python3 site-factory/engine/tests/test_rendered_growth.py --suwon-root /path/to/site-factory/suwon-flower
```

From the Suwon root, use its committed lockfile:

```sh
npm ci
npm test
python3 tests/test_static_gate.py
npm run test:growth
ASTRO_TELEMETRY_DISABLED=1 SITE_INDEXABLE=false SITE_URL=https://preview.example.com SITE_FACTORY_REVISION=<full-sha> npm run build
ASTRO_TELEMETRY_DISABLED=1 SITE_INDEXABLE=true SITE_URL=https://suwon.fwith.kr SITE_FACTORY_REVISION=<full-sha> npm run build
```

The isolated integration test creates and builds a real additional route through
the common adapter, verifies hub inbound link/CTA/snapshot parity and replay, and
leaves working source unchanged. Test fixture content is never deployed.

Required external dependencies remain the existing GitHub/Airtable connections,
Cloudflare account deployment credentials and DNS, factual company/source inputs,
content approval, and search-engine account ownership/verification. Credentials
are not copied into source, previews or logs. External scheduled growth and queue
reconciliation require a separate verified operational integration; they remain
paused, and this repository alone does not claim they are active.

## Scoped Publisher migration (requires separate operational approval)

Suwon alone sets `requireSnapshotApproval=true`; other registered sites retain
legacy mode. To make the existing Suwon Publisher emit the new proof, add scoped
`approval_status` / `approved_snapshot_hash` single-line-text fields and optional
`supersedes_snapshot_id` single-line-text field to the queue, populate them only after actual review
of the exact frozen request, and append the three optional headers (`APPROVAL_STATUS`, `APPROVED_SNAPSHOT_HASH`,
`SUPERSEDES_SNAPSHOT_ID`) to its current
issue payload. Empty headers on legacy sites do not change their mode. Test a
controlled new Suwon queue through preview, replay, and the independently approved
pinned-deploy path before resuming any growth. Creating fields or changing the
live Publisher is not performed by this repository change. Do not recreate or
requeue canceled historical records.

Review proof algorithm `site-factory-review-sha256-v1`: parse/validate/normalize
the existing issue payload exactly as `render_snapshot.py` does; omit empty
optional values, `APPROVAL_STATUS`, `APPROVED_SNAPSHOT_HASH`, and only the
server-allocated `PUBLISH_QUEUE_RECORD_ID`; JSON encode with sorted keys, UTF-8
non-ASCII characters preserved, and compact separators; SHA-256 hexadecimal.
All other fields, including snapshot ID, draft/source record, dates, source names
and URLs, related keys, title/description and Markdown, are bound. The helper
never grants approval. Set `approval_status=approved` only after actual quality
review, and copy its `approvedSnapshotHash` output. Before queue creation, a
syntactically valid placeholder queue ID may be used because that field is
excluded from review proof. The committed immutable hash includes the actual ID.



## Mandatory post-publication IndexNow finalization

The existing scheduled Snapshot Publisher calls the common production workflow.
Its final step now invokes `indexnow_finalize.py` from trusted main after live QA;
missing ownership configuration fails closed. No new scheduler or credentials are
created by that step. Existing manual branch-triggered Ansan/Yongin deployments
retain their working legacy submission paths and their existing token permissions.
GITHUB_TOKEN snapshot pushes do not trigger those independent push workflows.

The helper compares the current public sitemap with the built exact-source sitemap,
checks every selected URL's 200 status, canonical, full revision, snapshot identity,
robots/meta/response-header indexability, and the same-host public ownership file.
Preview, thin excluded hubs, 404s and foreign URLs are never submitted. A changing
or incomplete public URL set blocks the request rather than silently dropping URLs.

Machine receipts are comments on the original deployment/Publisher request issue,
with a JSON artifact in the same run. Cross-issue dedupe reads existing repository
comments and binds origin, source SHA, endpoint, key digest and sorted URL-set hash.
A started attempt without a terminal receipt, timeout, redirect or 5xx is uncertain;
never automatically repeat it. HTTP 400/403/422 fail without an in-run retry. Only
explicit HTTP 429 rejection gets up to three delayed attempts, respecting Retry-After.
HTTP 200 means received; HTTP 202 means received with key validation pending. Neither
establishes crawling, indexing or ranking. No key value or private data enters receipts.

For a missing receipt after the site is already public, reuse this production workflow
with `indexnow_only=true`, the exact live full SHA, site key and original receipt issue.
The `[SITE-INDEXNOW]` issue form accepts SITE_KEY and EXPECTED_REVISION and uses that
request issue for receipts. This path builds only for exact-source comparison and has
no Cloudflare environment, deploy, domain-binding or credential steps. It shares the
production concurrency lock and preserves Goyang's exact canonical-header lock rule.

The one-time approved ownership-file setup is separately source-bound. Each new
source differs from its original approved public source by exactly one regular public
text file across the entire repository. Original content/batch QA remains immutable;
its previous SHA is explicitly chained to the new ownership-only SHA. Both sources
are built from their unchanged lockfiles and their output differs only by the new
text file and deliberate full revision metadata. Existing public content and hostname
binding must match before asset redeployment; domain attachment steps are not run.
All existing binding identities, content and public sitemap scope are verified after.
Later content updates do not re-enter that special one-file amendment path.
