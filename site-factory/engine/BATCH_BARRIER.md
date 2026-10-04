# Initial 50: read-only completion barrier

`batch_barrier.py` consumes evidence from the existing Writer → Reviewer →
Publish Queue → issue Publisher → `render_snapshot.py` loop. It does not generate
copy, create records/issues, change schedules, publish, approve content, deploy,
or submit IndexNow. `plan_batch.py` remains the candidate selector; a shortage
of actual evidenced intents blocks the target instead of reducing it.

One batch belongs to **one regional site**. Its exactly **50 detail members
include the Seongnam canary** for the Seongnam launch. HOME and HUB routes are
counted separately and never satisfy detail membership. This is an initial-50
contract, not a configurable growth scheduler.

## Frozen batch contract (JSON)

- `schemaVersion`: 1
- `batchId`, `siteKey`: nonempty stable identifiers
- `targetDetails`: 50 (cannot be reduced)
- `canaryPageKey`: the real canary member's page key
- `ruleRevision`, `templateRevision`, `registryRevision`: full lowercase Git SHAs
  for the approved inputs. Registry is read from that exact commit's
  `.github/site-factory-sites.json` in the provided repository.
- `members`: exactly 50 objects with only `pageKey` and `intentKey`; both unique
- `membershipHash`: `batch_barrier.identity(batch)` after membership is frozen

Store the original frozen contract in a trusted reviewed location. Identity is
SHA-256 of canonical sorted-key compact UTF-8 JSON containing the identity fields,
pinned revisions and page-key-sorted membership. Reordering is harmless; changing
membership, intent, canary, revisions or target creates a different identity and
requires a new approval cycle. A self-computed digest is not authorization.

## Checkpoint evidence contract (JSON)

Top-level `batchId`, `membershipHash`, `finalSourceSha`, `items`, `qa`.
`items` must exactly match frozen membership, with no missing/extra/duplicate item.
Each item contains:

- `pageKey`, `intentKey`, all three pinned revision fields
- `draftRevision`: exact external Writer revision, not just the draft record key
- `payload`: exact frozen approved issue body accepted by `render_snapshot.py`
- `reviewDigest`: existing `site-factory-review-sha256-v1` digest
- `snapshotHash`: immutable storage digest including the actual Queue record ID
- `reviewerApproval`: `status="approved"`, `reviewer`, `evidenceUrl`,
  `draftRevision`, `reviewDigest`, and frozen `membershipHash`
- `queueRecordId`, `issueUrl`, `snapshotId`: unique Publisher checkpoints;
  issue URL must belong to the registered repository
- `reviewSourceSha`: committed current manifest used during review
- `commitSha`: resulting immutable single-snapshot commit

All checkpoint commits must be ancestors of `finalSourceSha`; each review source
must be an ancestor of its checkpoint. Both checkpoint and final manifests must
match the exact approved snapshot, queue, draft/source IDs and route. Final
architecture must retain the planned intent and route. The helper reads committed
Git bytes, never dirty working-tree manifests.

Related links are allowed only to pages present and explicitly approved in the
manifest at `reviewSourceSha`. Future planned members are not link targets. Even
an otherwise reapproved new graph fails if it links to a future page. A graph or
content change invalidates its digest; it requires a new Writer revision and
actual Reviewer approval before obtaining new Queue/snapshot evidence. Retain
prior checkpoints externally; this helper does not silently rewrite them.

## Final independent QA contract

`qa` contains:

- `state="passed"`, `environment="staging"`, `noindex=true`
- `sourceSha`: exactly `finalSourceSha`, not an earlier canary/intermediate SHA
- `manifestSha256`: SHA-256 of final committed publish-manifest **raw bytes**
- `reviewer`, `evidenceUrl`: independent QA identity and retrievable report
- `gates`: exactly `build`, `static`, `graph`, `canonical`, `h1`, `schema`,
  `robots`, `sitemap`, `404`
- `routes`: exactly every final manifest route, every architecture hub, and `/`;
  each object has `url`, `state="passed"`, `noindex=true`

A canary-only QA report is insufficient. HTTP403, missing routes, absent approval,
partial commits, missing manifests and a changed final SHA remain blocked. A new
source revision requires a fresh whole-route QA report. Existing preview helpers
may contribute evidence but their limited-route reports do not automatically
satisfy this whole-site contract.

Reviewer and QA assertions must be collected by a trusted operator/consumer from
actual upstream review and QA runs. This helper checks integrity and completeness;
it does not authenticate identities, fetch external Airtable/GitHub review state,
verify signatures, perform HTTP QA, or turn synthetic/local fixture reports into
real approval. Pinned rule/template revisions are identity inputs, not assertions
that their semantic requirements were independently audited.

## Invocation and states

```sh
python3 site-factory/engine/batch_barrier.py \
  --batch /path/to/frozen-batch.json \
  --evidence /path/to/checkpoint-evidence.json \
  --workspace /path/to/full-history-repository
python3 -m unittest discover -s site-factory/engine/tests -p test_batch_barrier.py -v
```

On success, exit 0 emits `staging_complete` with exact SHA, membership hash, detail,
HOME/HUB and QA-route counts. `productionApproved=false` and
`indexNowAllowed=false` always. It never emits `live_verified` or closes publishing
issues. Invalid/incomplete input exits 1 with `state="blocked"`. Missing Git
objects require fetching the ordinary authorized repository history; never guess
at evidence. No workflow is wired to invoke or bypass this barrier automatically.
Production/indexing remain separate, explicitly authorized gates.

## Goyang all-remaining coverage (schemaVersion 2)

The original schemaVersion 1 contract above is unchanged. Schema 2 is an opt-in
for `goyang-flower-v2` / `goyang-flower-v2-dong-coverage-20261003`, using the
existing registered structured-JSON source and single-snapshot Publisher. It is
not a new scheduler, publisher, approval service or configurable page quota.

Its batch fields are:

- `schemaVersion: 2`, `contractType: "goyang-all-remaining-legal-dongs"`
- `batchId`, the exact `siteKey` and `scopeKey`
- `baselineSourceSha`: the full committed source SHA before this batch
- `baselineManifestSha256`: SHA-256 of its raw committed manifest bytes
- `coverageSha256`: SHA-256 of its raw committed `region-coverage.json`; final
  source must preserve these bytes, including all legal/administrative aliases
- the same full `ruleRevision`, `templateRevision`, `registryRevision` pins
- `members`: unique `{pageKey, intentKey}` objects, exactly every legal unit in
  coverage minus already committed baseline details
- `membershipHash`: `identity(batch)` after freezing this complete identity

There is no `targetDetails` or numeric cap in schema 2. The current researched
contract has 52 new members and preserves two baseline details, but counts are
computed from the reviewed pinned source and membership. Reordering members does
not change identity. Shrinking the list and recomputing the hash still fails the
coverage difference check. A digest alone does not authorize this contract.

The registry must retain `growthPaused=true`, `autoDeploySnapshots=false`, and
both exact revision/snapshot approval requirements. All required customer drafts
are saved and independently reviewed before creating any new Publish Queue row.
That row's `recordCreated` trigger immediately creates a GitHub Issue, so never
pre-create incomplete/pending placeholders and fill them later. The operator
creates one complete approved row, reconciles its emitted payload and committed
snapshot, and only then creates the next. Notes are metadata, not an executable
lock; the existing snapshot workflow's concurrency lock is per Issue, not site.

`evidence.items` covers only new members, in actual sequential checkpoint order.
Each item has the schema 1 fields plus a nonempty `writerRunId`. The independent
content reviewer's identity must differ from that Writer ID. Review approvals
bind the exact draft revision, digest and new membership identity; baseline
approvals are preserved rather than retroactively reissued. Snapshot/Queue/Issue
and commit IDs are unique. The review source is between the batch baseline and
the preceding checkpoint. Each commit adds exactly one next member and preserves
every earlier frozen table entry. At each checkpoint the whole snapshot ledger
must equal the prior ledger plus exactly the new snapshot, including all historical
entries. New page order is the prior renderer maximum plus one, and
`sitemapIndexable` is computed from the pinned registry production flag, matching
the existing renderer. Self-reported values and later repairs cannot satisfy these
checks. Future/unapproved related links are refused.

The final manifest, page-map, pages and architecture sets must equal baseline
plus all new members. Existing baseline entries and ledger are preserved. Each
new entry's complete frozen customer content, display fields, sources and related
graph are checked against its actual approved payload, not merely a claimed hash.
Every checkpoint is replayed through the actual `render_snapshot.render` using
its complete approved Issue payload, the pinned registry, and the preceding four
JSON files copied from committed Git bytes into a disposable temporary directory.
The executing renderer file must be byte-identical to `render_snapshot.py` at
`registryRevision`; it is not loaded or executed from arbitrary evidence. The
resulting complete four files must match the checkpoint byte-for-byte, including
all top-level metadata, HOME/hub state, ordering and historical ledger. Unexpected
output files are rejected. Temporary replay files are removed; the evidence
checkout, records, repository refs and external services are never modified.

The final four content-data files must be byte-identical to the last snapshot
checkpoint. Unrelated source UI changes, if any, remain separate reviewed commits
and require final exact-source QA as usual.

The final `qa` object retains schema 1 source/manifest/state/environment/noindex,
reviewer and evidence fields, and adds:

- `gates`: the schema 1 set plus `source`, `snapshot`, `assets`, `banner`, `og`,
  `cta`, `inbound`, `aliases`, `responsive`, `isolation`
- `routes`: exactly `/`, every detail route, and hubs with actual children,
  each with `state="passed"`, `noindex=true`
- `notFoundRoutes`: exactly empty registered hubs and
  `/site-factory-live-qa-definitely-not-found/`, each with `state="passed"`,
  `status=404`, `canonicalAbsent=true`
- `aliasCoverageSha256`: the pinned coverage digest
- `discoverableNames`: sorted unique legal and administrative names from that
  definition, verified in the rendered hub/crosswalk by the independent consumer

Existing fixed canary, product/Truth/images and Worker/domain contracts, full
strict HTTP/artifact verification and independent visual QA still apply. Use
one final immutable-version noindex preview after all snapshots, preserve active
public assets/binding/settings during upload, and never externally retry an
uncertain upload. Version probe is not a detail/hub or customer route and must not
enter production. HTTP403, unknown response, missing route or changed SHA cannot
be replaced by UI success. A final production release remains a separate exact
approval and public verification step, with growth/auto-deploy still paused.

Schema 2 returns `staging_complete`, calculated baseline/new/total detail counts,
actual hub/route/404/alias counts, and always `productionApproved=false` and
`indexNowAllowed=false`. It neither fetches nor authenticates external evidence;
trusted operators must acquire actual persisted independent approvals and QA
records. Synthetic unit fixtures are never real membership/content/release
approval. This helper is not automatically called by a workflow; a saved result
alone does not open any gate.

## Bucheon whole-dong coverage (exact additional schemaVersion 2 profile)

The same scoped integrity checks also accept only `bucheon-flower-v2` /
`bucheon-flower-v2-dong-coverage-20261004` with
`contractType: "bucheon-all-remaining-legal-dongs"`. This does not enable other
sites or a generic region allowlist, and leaves schema 1 and Goyang contracts
unchanged. The exact Bucheon repository, branch and root are checked against its
pinned registry, whose `regionalService` must contain exactly four matching fields:
`enabled: true`, `scopeKey: "bucheon-flower-v2-dong-coverage-20261004"`,
`definitionFile: "src/data/region-coverage.json"` and
`policyFile: "src/data/region-policy.json"`. Missing, changed or extra fields fail
closed; this is the existing source adapter contract, not a flexible allowlist.

The Bucheon contract adds `membershipSourceSha256`, `policySha256` and
`productsSha256` to its frozen
identity, covering raw `region-policy.json` and `products.json` bytes. Its existing
`coverageSha256` covers the schema-2 geographic definition. Both coverage and policy must carry the same
reviewed membership research artifact digest as `membershipSourceSha256`. This
binding is not authentication or independent review of the research. Each representative
must be approved, represent exactly one legal dong, and the complete representative
set must cover every legal unit exactly once. Membership is those representatives
minus baseline details; the current researched set implies 24 additions while
preserving the existing facility, not a hardcoded numerical quota.

Freeze `baselineSourceSha` only after the reviewed schema-2 source adapter, exact
query bindings and visual/product bindings are committed. Candidate/pending
bindings are not accepted. Geographic membership alone never approves customer
copy or assets. Changing coverage or bindings after the baseline requires a new
frozen contract and actual independent approvals, not merely a recomputed hash.

The existing pinned renderer reads additional Bucheon inputs. For each replay the
helper copies committed coverage, policy, products and all exactly bound local
image bytes into disposable storage alongside the four prior JSON files. Their
bytes must remain unchanged at every checkpoint, review source and final source;
policy image hashes must match. Bucheon's pinned controller registry and renderer,
all four JSON files at baseline/review/checkpoint/final revisions, and these
additional dependencies must be committed regular-file blobs. A byte-identical
blob stored with symlink mode is refused rather than replayed as a regular file.
A `site-catalog.json` at any of those revisions is refused because this registered
Bucheon renderer profile does not support it; replay cannot silently omit a file
that would change the real renderer's behavior. Replay must modify exactly the
four JSON outputs and preserve every dependency byte.

Final exact-source QA has the same complete rendered HOME/active-HUB/detail set,
empty-HUB/unknown-route 404 set, legal/administrative alias discovery and trusted
independent evidence requirements as Goyang. Bucheon content and QA reviewer
identities must be nonblank strings distinct from Writer identities after trimming,
and their evidence references must be nonblank HTTPS URLs without credentials or
whitespace. This format check does not authenticate the reviewer or fetch the URL.
The alias-name set is derived from
schema-2 units and administrative crosswalk, not a guessed route count. This helper
still returns only `staging_complete`, never production authorization, deployment
success or actual HTTP/visual QA. Synthetic test fixtures are not real approvals.
