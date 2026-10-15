# Direct regional release state

Before any resume or new-region selection, read `national/fixed-plan.json`, `national/source-evidence.json`, `checkpoint.json`, and `latest-progress.json` from the latest remote main. Follow the scoped progress and evidence paths listed there.

The historical checkpoint is retained without rewriting its large history. Some legacy `current` and national progress fields are stale. `latest-progress.json` is a compact reconciliation supplement, not permission to skip checking actual source/main commits, active ownership, Actions runs, artifacts, public HTTP, and IndexNow receipts. Never republish a completed region solely because a legacy field says incomplete. If evidence conflicts, resolve the conflict before claiming completion or selecting a new region.

## Current release boundary, 2026-10-14

Gangdong public release and the original three-URL IndexNow HTTP 200 receipt are verified in `../direct-seoul-gangdong/release-completion-20261014.json`. Source `5f27c11cc0aa3c22c2793d9e0a6cd0aa6e350cc6` preserves the frozen customer data and images. Actual build run 38603054270 has 23 release files and successful sandboxed runner QA; the required 42 screenshots and 15 keyboard-focus samples were independently reviewed. Publication run 38605093414 has an inspected 12-file result archive and verifies 22 public paths, including a real 404, with five strictly bounded Cloudflare beacon normalizations.

The separate independent HTTP pass is explicitly partial: 16 of 22 responses, including all four normal HTML pages, match raw production bytes exactly. Polling was interrupted by `automatic approval review was cancelled`; the remaining six GETs were not retried. They are the consultation/message banners, robots.txt, both sitemaps and the real missing-route 404. A separate root homepage GET also matched exact bytes and adds no unique path. Workflow verification is not an independent 22-path pass. No live public-browser pass or actual search indexing is claimed.

Current reconciled release count is 56 of the frozen 230 regions; 174 remain. Earlier 55 hosts retain carried-forward release evidence, not 56 fresh simultaneous HTTP checks. Songpa, Gangnam and Seocho prior completion records remain in `../direct-seoul-songpa/`, `../direct-seoul-gangnam/` and `../direct-seoul-seocho/`. Do not recreate or republish completed regions or repeat received IndexNow batches merely to refresh records.

The next frozen-plan unit is 전남광주통합특별시 목포시 (12110, order 26). Reconcile current official evidence, existing prepared work, ownership and collisions before new development; no new hostname or source branch is claimed here. Existing-site SEO expansion is deferred. Apply `SALES_COPY_ACCEPTANCE.md` and `SEARCH_CONTENT_STRATEGY.md`; shared-banner followups retain separate ownership.

## Release readiness and parallel progress, 2026-10-15

The user's 2026-10-15 instruction supersedes prior requirements to wait for an earlier region to be published. Preserve the frozen official-code order for selecting new regional work, the plan denominator, source evidence, holds, and history; selection order is not publication order.

- Publish each region as soon as that region's required content, technical, visual, and final pre-publication checks are complete and its applicable approvals are valid. Do not wait for another region's publication or supplemental re-verification. This does not waive any regional quality gate, explicit hold, or required approval.
- Continue the next independent regional research, preparation, implementation, and review while another region undergoes final pre-publication re-verification. Reconcile current ownership first; keep region-specific branches and evidence separate, serialize shared main/state writes, and prevent duplicate builds or releases.
- Treat legacy predecessor-publication dependencies or release-concurrency fields as historical where they impose an ordering wait. They do not block independent next-region work or readiness-based publication. Actual shared-resource collisions must still be serialized; this instruction does not itself change a controller, workflow, permission, or historical completion record.

## Execution priority

- Prefer the existing web chat, dot, connected tools/APIs, and existing approved GitHub Actions routes that can perform the assigned work without consuming Codex or Work usage. Inspect prior successful execution history, exact commits, workflows, artifacts, and saved source before choosing a new route or rebuilding anything. Do not assume that these alternatives are free or that their billing is known.
- Before new development, investigate existing GitHub implementations, open source, starter kits, boilerplate, and relevant API examples. Check license, recent updates, maintenance, stack, and reuse fit; prefer reusing, modifying, or combining verified existing code. Business ideas also need separate real-market and competitor research.
- Do not create, resume, or run Codex or Work tasks that consume usage without prior user approval. Check actual supported alternatives first; when usage is required or whether it will be charged is uncertain, explain the necessary task, available model and usage/cost information, and uncertainty, then request approval before the consuming action. After approval, prefer the available model with the lowest consumption that still meets the required quality. Do not trade away verification or quality to reduce usage. Do not infer that a disconnected user PC blocks web/API/cloud work. The user PC is explicitly disconnected and is not authorized for this continuation.
- Keep the direct GitHub/static production route. Do not revive v2 or Airtable workflows. Do not change credentials, secrets, security, permissions, DNS ownership, or hostname attachment scope without the required explicit approval. Mandatory approval and security requirements for personal-data disclosure, sensitive-data transmission, irreversible deletion, payments, contracts, and other chargeable commitments remain in force.
- For the bounded Songpa/Gangdong continuation and its records, the user approved the connected GitHub file create/update APIs. Do not use a separate `create_blob` call, the user PC, Codex, or Work. This exception does not silently replace any future explicitly requested Git transport.
- Use the existing successful route and the fewest necessary calls and changes. Do not redeploy, reupload a Worker, resubmit an already received IndexNow batch, or recreate prepared sources merely to refresh records.
- Report directly inspected evidence, tool reports, judgments, and unverified matters separately. Completion requires the action, an actual output, and verification against the requested criteria; a tool's success label alone is insufficient.

## Cancellation and blocked actions, 2026-10-15

The user states that they do not manually cancel these operations. A tool response such as `cancelled` or `automatic approval review was cancelled` is therefore an error with an unverified cause, not evidence that the user cancelled or withdrew the task.

- Record the exact action, target, time, returned error, and any available request/run identifier. Inspect permitted tool records, logs, current repository state, and outputs to determine whether the action executed before deciding on a retry; do not invent a cause.
- Continue independent authorized work while investigating. Retry only when permitted by the actual error and approval state; do not bypass a system denial, switch routes to evade a restriction, fabricate consent, or automatically answer YES.
- If execution requires new approval, report the exact blocker and request that approval. Keep an unresolved operation unverified rather than reporting success.

Preserve fixed-plan denominators, source evidence, URLs, holds, and history. Report submission separately from actual indexing/rank, and deferred visual QA separately from a visual pass.

