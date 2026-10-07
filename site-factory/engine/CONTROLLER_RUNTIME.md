# Site Factory v2 controller runtime

Run `controller_runtime.py` from a trusted checkout. The dispatch workflow
uses the existing PR's controller code after merge and stores checkpoints on
`site-factory-controller-state`. The state branch must exist before dispatch.
Each invocation advances up to 16 gates, stopping at the first pending readback.
Rerun the same workflow to resume. A Pool read, state read, lease CAS, role
request, gate validation, and checkpoint CAS occur in that order.

The Region Launch Pool adapter reads the real Airtable fields `priority`,
`status`, `site_key`, `launch_key`, and `region_key`; it never creates Page
Plans, Drafts, Content Jobs, or Publish Queue rows. PREPARE is a read-only
bootstrap request. It returns `source_sha` (40-character Git SHA),
`publication_scope_key`, and the complete `members` array with unique
`page_key` values. Those pins are committed before any stage action.

Configure `SITE_FACTORY_STAGE_ENDPOINTS` as a JSON map from every phase
`BOOTSTRAP` through `RECONCILED` to an HTTPS endpoint. Every endpoint
accepts `phase`, `state`, `actor_id`, and `idempotency_key`; it returns
`{"receipt": {...}}` when the corresponding existing system's readback is
complete, or `{}` while pending. PREPARE receives `region` instead of
`state`. The endpoints are interfaces to the recovered roles and existing
Publisher/deployment paths, not old scheduled ChatGPT reservation objects.

`WRITING` must return `writer_id` and `draft_count`. `REVIEWING` must
return a different `reviewer_id`, `approved_count`,
`independent_review=true`, and complete `payloads` and `reviews` maps.
The runtime verifies exact payload hashes and complete membership before
freezing the batch. The `FROZEN` endpoint must hand the already frozen,
approved batch to the existing Airtable Publisher and return its receipt only
after readback. `SNAPSHOTTING` through `RECONCILED` endpoints read receipts
from the existing Snapshot, staging, production, and IndexNow workflows.
The state gate checks the pinned source, membership, frozen hash, count,
hosted QA, production revision, and IndexNow result as applicable.

Secrets: `AIRTABLE_TOKEN`, `SITE_FACTORY_RUNTIME_TOKEN`. Variables:
`SITE_FACTORY_AIRTABLE_BASE_ID`, `SITE_FACTORY_STAGE_ENDPOINTS`,
`SITE_FACTORY_WRITER_ID`, `SITE_FACTORY_REVIEWER_ID`. Writer and Reviewer
IDs must differ. All external action handlers must honor the supplied
idempotency key and return the same immutable receipt on replay; a pending or
failed readback must never be reported as complete.
