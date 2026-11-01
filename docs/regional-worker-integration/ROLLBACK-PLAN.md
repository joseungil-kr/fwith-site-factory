# Pilot rollback readiness review

Review date: 2026-11-01. Plan only: no deployment, domain update or rollback executed.

GET-only helper run 41279215220, artifact 13072248505, reported main 5448bd5f. Saved sanitized responses are in current-api/. Offline assertions verified returned version IDs, latest deployment at 100%, empty bindings and GET-only provenance for both files.

| Worker | Retained active version | Version number | GET checked UTC |
| --- | --- | --- | --- |
| seoul-dongjak-flower-guide | 3720873d-5c57-4c0f-a25c-80dba048ddd1 | 1 | 06:02:46.466131 |
| seoul-geumcheon-flower-guide | c3d0ea60-ca39-47b6-a119-e692d66a1658 | 2 | 06:02:47.106380 |

Both settings responses show compatibility 2026-10-09, empty flags/bindings/placement, standard usage model and logpush false. Assets and source SHA are absent, not empty inventories. Earlier UI evidence records Custom Domains, no Routes and disabled workers.dev/previews. The new response is not a full export of every account/zone policy.

## What is now sufficient

Cloudflare documents that a version contains bundled code, static assets, bindings and compatibility settings. Re-selecting the retained UUID is therefore a provider-managed asset rollback; downloading all live hashes or discovering an unavailable source-SHA field is not a prerequisite for that mechanism. This is an inference from the documented contract plus successful version GETs, not a performed recovery test. [Version scope](https://developers.cloudflare.com/workers/versions-and-deployments/).

Rollback selects one version at 100%; only the latest 100 published versions are eligible. External storage state is not reverted. Both originals currently have empty resource bindings and very low version numbers; one controlled pilot upload should leave the original within that window. Recheck immediately before activation and stop on drift. Do not delete Workers, resources or versions, or add migrations. [Rollback rules](https://developers.cloudflare.com/workers/versions-and-deployments/rollbacks/).

The retained builds (19/19 each), public hash checks (16/18 each), explained managed robots bytes and captured 307 redirect independently support candidate fidelity. They do not establish a direct provider UUID-to-source-SHA identity. That provenance limitation remains documented, but no longer blocks rollback readiness by itself.

## Exact staged transition proposed for parent review

1. Preserve seoul-geumcheon-flower-guide at its original UUID. Keep its source, assets and configuration untouched throughout the pilot and observation period. Do not reuse the freed Worker yet.
2. Before stage 1, read Dongjak active deployment/version and confirm its expected UUID at 100%, with both original hostname mappings unchanged. Confirm the existing authorized version rollback path; GET success alone does not prove write permission. Before stage 2 only, refresh both deployments and obtain both Custom Domain records; save domain record identifiers, zone reference, service, enabled and preview fields privately and verify the existing domain attach recovery path. Missing Geumcheon restore payload blocks stage 2, not the Dongjak-only stage 1. No new token or permissions.
3. Prepare the integrated artifact for existing seoul-dongjak-flower-guide, preserving non-versioned settings and both hostname allowlist entries. Review the exact production configuration separately: the tested local config name is not a production deployment config. The two originals must stay reachable until their respective stage begins.
4. Activate the integrated version on Dongjak only. Its existing hostname stays on the same Worker; Geumcheon still uses its original. Verify Dongjak bytes/headers, robots managed block, redirect chain, missing-page status, canonical/sitemap/auth file, links/images and mobile/desktop. If any fails, immediately restore Dongjak's original UUID and stop.
5. Only after Dongjak passes, attach seoul-geumcheon.fwith.kr to seoul-dongjak-flower-guide. Read back the exact mapping and verify both hosts, including repeated cross-host requests and internal-path rejection. Do not claim atomicity or zero propagation time.

Domain mutation uses the existing authorized account's PUT /accounts/{account_id}/workers/domains attach operation, with the observed hostname/zone fields and service changed to the intended Worker; restore uses the same operation with the original service. Preserve observed enabled/preview fields using supported request fields. Account/zone values stay in the existing private execution context. Never delete first as a workaround for a rejected attach. [Domain API](https://developers.cloudflare.com/api/resources/workers/subresources/domains/methods/update/).

## Failure recovery order

If Geumcheon has moved (or a move timed out), first GET its actual binding. If it points at Dongjak, reattach seoul-geumcheon.fwith.kr to seoul-geumcheon-flower-guide; verify readback and public response before rolling Dongjak back. Otherwise restoring Dongjak to its single-site assets while Geumcheon still points there can serve wrong-region content. If the reattach fails, keep the multi-host version active and stop/escalate that operation; do not blindly roll back underneath Geumcheon. Unknown outcomes always require readback before retry.

Then restore Dongjak using the installed, pinned Wrangler binary:

```text
wrangler rollback 3720873d-5c57-4c0f-a25c-80dba048ddd1 --name seoul-dongjak-flower-guide
```

Geumcheon needs no version rollback if unchanged. Only if verified drift occurred and its restoration is authorized, its exact recovery target is:

```text
wrangler rollback c3d0ea60-ca39-47b6-a119-e692d66a1658 --name seoul-geumcheon-flower-guide
```

Read back original UUIDs at 100%, original host-to-service mappings and relevant settings. Repeat public body/status/redirect/robots and cross-host checks. Command success alone is not recovery success. Provider unavailability can prevent immediate recovery; elapsed recovery time is unmeasured because no live rehearsal was performed.

## Stage 1 gates: Dongjak code only; no domain mutation

- Parent independent review and exact production artifact/configuration approval. Keep Geumcheon deployment and domain unchanged.
- Immediately before activation, GET Dongjak deployment and retained version: require UUID 3720873d-5c57-4c0f-a25c-80dba048ddd1 at 100%, compatibility/settings matching the saved baseline, and original hostname mappings. On drift stop and review. Record the new candidate UUID separately after upload; the old UUID remains the explicit rollback target.
- Prepare the existing pinned Wrangler rollback command above with the existing authorized credential path, without printing credentials or changing permissions. Confirm the original version remains GET-accessible within the latest 100 versions. No live rollback rehearsal is claimed. Stage 1 recovery requires only Dongjak version rollback; it must not wait for a Geumcheon domain restore payload because no domain moved.
- Obtain timestamped public Dongjak baseline for /404.html first hop, final /404 and a genuinely missing URL using the helper's normally permitted path. Save status, Location, selected headers and body hashes. Capture robots body and managed prefix plus unchanged original suffix. Existing local expectations are 307 to /404, direct /404 document 200, and missing URL 404; use the actual baseline, not this expectation, as the edge comparison. An access refusal remains unverified and is not bypassed.
- Capture homepage, regional pages, sitemap, authentication file, critical images/styles and links as the comparison set. Immediately after activation verify the same set plus cross-host/internal-path rejection and robots policy. Any wrong-region bytes, broken critical resource, unexplained status/redirect, policy loss or quota error triggers Dongjak rollback and readback at the original UUID/100%, followed by public recheck.
- Refresh account daily execution total and reset window immediately before activation; do not use the old 2,357 reading as current capacity. Proposed observation: check at activation, +5 and +15 minutes, then hourly during the first day in an explicitly approved monitoring task. Do not leave an implied unattended monitor. Record request/error deltas and remaining quota; account deltas include other Workers and are only an upper-bound indicator for this pilot.
- Proposed conservative capacity stop: do not start with under 20,000 requests remaining; recover if remaining capacity falls below 20,000, quota errors appear, or observed account rate projects exhaustion before reset. These are proposed operational guardrails for parent approval, not measured demand forecasts. If live usage metrics cannot be observed, hold activation. Static request volume remains unknown.

## Stage 2 additional gates: Geumcheon domain reassignment

Stage 1 must pass its immediate checks and agreed observation window. Refresh both UUIDs/settings and domain ownership; obtain the private complete domain restore payload and verify the existing authorized attach path before moving Geumcheon. The current API folder has version/settings responses, not domain records. Recover Geumcheon domain and public content first, then Dongjak UUID, exactly as described above. Keep the original Geumcheon Worker unused for other work throughout the rollback window.

No further search for a nonexistent source-SHA API field is required. The unresolved items are execution readiness and observable edge behavior, not a demand for stronger provenance than the API supplies.

The accompanying recovery_plan.py is an offline one-action-at-a-time guard, not a provider executor. Four tests passed: moved-domain ordering, binding/public verification separation, already-restored verification, and stale/unknown/drift refusal. A live executor is not armed. Its current recovery logic covers the combined two-site state; the stage-1-only rollback command above does not depend on a domain mutation.
