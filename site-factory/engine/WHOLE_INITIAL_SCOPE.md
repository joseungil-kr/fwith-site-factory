# Whole-dong initial scope: local proposal contract

## Status and boundary

This adds an explicit whole-dong initial scope to `provision_goyang.py`. It is
still a local, zero-customer-page infrastructure proposal builder, not a Writer,
Reviewer, Publisher, domain tool, registry updater or scheduler.

**No actual runtime-ready initial profile is registered by this change.**
`INITIAL_SOURCE_PROFILES` is intentionally empty. A whole-initial request fails
closed until an independently reviewed clean runtime profile is pinned in that
code allowlist and in the trusted template registry. The existing 54-file
Goyang/Seongnam pin and 65-file Bucheon pin cannot substitute for that profile.
The prospective positive tests inject local synthetic fixture pins only; they
are not a real profile registration, geographic finding or runtime review.

The site allowlist remains exactly Goyang, Seongnam and Bucheon. This is not an
arbitrary-site framework. A different region needs a separately reviewed target
contract and clean source profile. No new region, record, remote branch, source
pin, approval or schedule is created here.

Current Bucheon already has source and customer content. Continue its existing
source, exact content lineage and whole-dong scope; do not run this helper to
rebootstrap it. Initial-scope metadata does not rewrite or reopen its historical
completed trial.

## Historical compatibility versus new initial selection

These published invocations retain their exact old output/provenance bytes,
source pins, six adaptations, zero-page bootstrap and exact-resume behavior:

- Goyang: omitted site/key defaults, or `goyang-flower-v2-launch`
- Seongnam: `seongnam-flower-v2-trial-20261002`
- Bucheon: `bucheon-flower-v2-trial-20261004`

The known keys are historical-replay compatibility, not the default selection
for new scheduled creation. They retain `trialDetailTarget=1` only where the
original contract had it. A different old trial key can resume only an existing
exact matching bootstrap provenance; it cannot create a new trial. Original
customer content, changed bytes or unrecognized provenance continue to block.

Every other omitted mode selects `whole-dong-initial` and requires its inputs.
It never invents a one-page trial or silently falls back when unsupported. New
scheduled initial creation must explicitly provide `--scope-mode
whole-dong-initial`, even for an allowlisted site, so it cannot accidentally use
a historical compatibility identity. `--scope-mode legacy-trial` is for replay
only and cannot consume initial-membership arguments.

## Required invocation

After reading the exact current trusted control SHA and observed target state,
obtain the pinned Git objects locally and pass independently collected regional
membership and coverage artifacts:

```sh
python3 site-factory/engine/provision_goyang.py \
  --repo /path/to/verified/repository \
  --control-revision FULL_CURRENT_MAIN_SHA \
  --target-revision absent \
  --site-key ALLOWLISTED_SITE_KEY \
  --scope-mode whole-dong-initial \
  --launch-key SITE_KEY-initial-YYYYMMDD \
  --scope-key SITE_KEY-dong-coverage-YYYYMMDD \
  --membership-json /path/to/membership.json \
  --membership-sha256 MEMBERSHIP_RAW_BYTE_SHA256 \
  --coverage-json /path/to/region-coverage.json \
  --coverage-sha256 COVERAGE_RAW_BYTE_SHA256 \
  --dry-run
```

Use `--output` instead of `--dry-run` only for a local bundle. Full SHA and
remote-absence requirements, collision checks and atomic materialization are
unchanged. `absent` is never inferred from local refs. For an exact resume use
the observed full target SHA and original identical artifacts.

## Input types, hashes and complete membership

Both input files are UTF-8 JSON objects, not JSON strings containing JSON,
arrays or Python dictionaries. Duplicate object keys and non-finite numbers are
rejected. Both explicit hashes are 64 lowercase hex characters and cover the
**entire exact file bytes**, including whitespace and final newline. They do
not cover a JSON reserialization. Both objects bind the exact site and scope.
Launch and scope date suffixes must be the same valid calendar date; neither
identity contains `trial`.

The membership object uses the existing regional research shape:

- `schema`: `<region>-all-dong-membership-research-v1`
- `site_key`, `scope_key`: exact identities
- `prepared_at_utc`: timezone-aware ISO observation metadata
- `count_is_page_quota`: JSON `false`
- `content_membership_approved`, `publication_approved`: JSON `false`
- `official_evidence`: nonempty objects with an HTTPS government `url`, or the
  existing district evidence `general_status_url`
- `counts.legal_units`: integer equal to declared legal-dong units;
  `eup_myeon_units` is an integer if there are eup/myeon units (otherwise zero)
- `counts.administrative_units`, `counts.administrative_legal_relations`:
  integers equal to the explicit alias and edge sets
- `members`: complete nonempty canonical members, each with string `unit_key`,
  `name`, `district_key`, `page_key`, `intent_key`, `slug`, `route`
- `administrative_alias_routes`: explicit alias rows and canonical target
  `unit_key`/`scope` edges, with `scope` equal to `whole` or `partial`

The coverage object uses existing schema 2, including `siteKey`, `scopeKey`,
`membershipSourceSha256` equal to the membership raw hash,
`unitBasis=legal-dong-plus-eup-myeon`, `countIsPageQuota=false`,
`officialSourceUrls`, `units`, `representatives`, `administrativeCrosswalk`.

Each canonical unit must have exactly one matching candidate representative
with the matching page key, intent, slug and route. Representative `status`
remains `candidate`; this initial input is not an approved release payload.
Legal/admin names and whole/partial relationships stay separate. Unit IDs,
page/intent IDs, slugs and routes cannot be duplicated. Full declared official
unit and representative sets must match all members, and the administrative
edges must agree in both artifacts. Missing/extra/duplicate members or partial
crosswalks fail rather than being dropped.

Counts are consequences of those complete sets. There is no quota of 50, no
50-page ceiling, no filler requirement, and no `trialDetailTarget` or
`first_detail_limit` in an initial scope. Explicit quota/cap fields are rejected.
A 51-unit fixture succeeds as a 51-unit set, not as a quota. Observation times
do not have an invented TTL. Current official-source revisions, hashes and
actual membership changes must be compared during independent review; an old
source basis date alone does not force duplicate research.

Structural agreement between two caller-supplied artifacts cannot prove that
all real geographic units were collected. Government URLs are source pointers,
not proof that content was read or validated. The helper does not award factual,
content, runtime, frozen-payload, domain or deployment approval.

## Reviewed clean source profile gate

A future reviewed per-site entry in `INITIAL_SOURCE_PROFILES` must contain
exactly `registryKey`, full `sourceRevision`, full `sourceTree` and positive
integer `sourceCount`. It must use a distinct registry key, never either trial
profile key. The branch remains `site-factory-flower-v2-template`; the new initial
root is fixed to `site-factory/templates/flower-local-v2-initial`. The historical
root and pins remain unchanged. An exact tree pin
is the review boundary; editing registry claims alone cannot enable a source.

The corresponding trusted template entry must exactly contain:

- `sourceBranch`, `sourceRoot`, `sourceRevision`
- `sourceTree`, `sourceFileCount` matching the reviewed code profile
- `productionReady=false`, `initialScopeMode=whole-dong-initial`
- `regionsRuntimeReady=true`, `zeroCustomerContent=true`

Before adding such a real profile, independently verify its empty generic
region runtime and test coverage, absent customer originals/approvals, absence
of fixed regional names/membership, and the dedicated eight-adaptation initial
contract described below. The legacy 54/65-file counts and six-adaptation path
stay untouched; a new profile has its own exact reviewed tree/count contract.

### Dedicated initial adaptation

Only a reviewed initial source may have seven neutral hidden/noindex hubs: the
six historical hubs followed by `/regions/`. All customer pages, architecture
pages, page-map entries, publish-manifest entries and snapshot ledger stay empty.
The source's schema-2 coverage and schema-1 policy must be the exact unbound
`template-only` sentinels with no regional membership, official URLs, scope,
visual bindings or approval. They are template configuration, not geographic
claims and never consume customer snapshots.

The initial adapter preserves all source bytes except these eight explicit files:

- Existing six: site-config, architecture, publish-manifest, page-map and both
  disabled-production/staging Wrangler JSON files
- `src/data/region-coverage.json`: exact validated input bytes, preserving the
  raw coverage hash, complete membership and `candidate` representative status
- `src/data/region-policy.json`: deterministically bound to site/scope/membership,
  with official hostname and unit-type sets derived only from that coverage;
  `rulesRevision` pins the reviewed source commit, `enabled=false`,
  `state=candidate-pending-independent-review`, and `visualBindings=[]`

The bound coverage must also satisfy the runtime's provenance/date, district,
legal-ri, administrative district, representative-query and regional-route shape.
Dates remain metadata, with no TTL. Structural shape does not replace genuine
query research or independent content review.

Only the initial registry proposal adds `regions`/`regional-service` and the
exact definition/policy paths under `regionalService`. Its `enabled=false`;
production, growth and snapshot gates remain closed. Historical site registry
outputs remain byte-identical, and the initial path cannot mutate shared legacy
category constants. Independent approval must later enable the exact scope and
provide each reviewed source/visual/content binding before snapshot consumption.

## Output and downstream gates

Initial output carries identical `initialScope` in the plan and provenance:
`scopeKey`, `membershipSourceSha256`, `coverageSha256`, full ordered `members`,
`memberIdentitySha256`, unit/crosswalk counts, source URLs and observation time.
The identity digest alone uses UTF-8 compact sorted-key JSON of the ordered
seven-field member projection, with no terminal newline. It is distinct from
both raw-file hashes and the existing pretty-JSON bootstrap digest.

`sourceRegionsRuntimeReviewed` records only the matched future source profile.
`regionsRuntimeVerified` and `readyForContentSnapshots` stay false for the new
site. All content, snapshot, final-batch, domain and production approval flags
stay false. `preliminaryTrialRequired=false`; `trialDetailTarget` is absent.
The initial registry proposal also has a disabled regionalService binding and
closed production/growth/approval settings. Input artifacts are evidence, never executable runtime permission.

The existing Writer/Reviewer/Publisher process must then:

1. Compare actual current official membership and preserve its exact scope/hash.
2. Independently verify the site's real regions runtime and catalog/truth path.
3. Prepare every original body and regional evidence, then independently review
   every exact content revision. A failed member blocks completeness.
4. Freeze every approved payload through the existing frozen Publisher. Reconcile
   the final full batch barrier against exact membership, coverage, policy,
   products and post-adapter baseline source hashes; do not mix source revisions.
5. Verify the complete route/alias graph, canonical/robots/sitemap and narrow/wide
   UI, plus intended existing `fwith.kr` domain connection.
6. Release the complete initial site once. No preliminary one-page experiment.

This helper does none of these external steps and cannot represent them as
complete. A missing profile, runtime contract, review or final barrier is a
blocker rather than permission to skip membership or revert to a trial.
