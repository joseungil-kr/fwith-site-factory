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
2. Immediately before any mutation, read both active deployments/versions and both Custom Domain records. Require the exact original mapping and UUIDs above. Save domain record identifiers, zone reference, service, enabled and preview fields privately; publish only host/service evidence. Confirm the existing authorized execution path can perform version rollback and domain attach; GET success alone does not prove write permission. No new token or permissions.
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

## Remaining concrete release gates

- Parent independent review and exact production artifact/configuration approval.
- Fresh preflight UUID/domain records and an existing authorized write path for both recovery operations. Current API folder lacks Custom Domain API records; earlier UI confirms the mapping but not the complete restore payload.
- Public final /404 and truly missing-path baseline captures; preserve 200 direct-document versus 404 missing-resource behavior without assuming the local result proves the edge chain.
- Refreshed execution usage and an agreed monitored observation window/abort threshold: worker-first adds previously unmetered static deliveries to execution demand. Per-site volume is unknown. No budget guarantee from the earlier 2,357/100,000 reading.
- Verify managed robots transformation and cache isolation at each actual stage; this cannot be conclusively proved by offline tests. Any wrong-host bytes, unexpected status/redirect, missing policy block, critical asset failure or quota error triggers recovery above.

No further search for a nonexistent source-SHA API field is required. The unresolved items are execution readiness and observable edge behavior, not a demand for stronger provenance than the API supplies.

The accompanying recovery_plan.py is an offline one-action-at-a-time guard, not a provider executor. Four tests passed: moved-domain ordering, binding/public verification separation, already-restored verification, and stale/unknown/drift refusal. A live executor is deliberately not armed until the private domain payload and existing write path are verified.
