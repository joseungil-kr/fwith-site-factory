# Independent source-save verdict

Status: **PASS_SOURCE_SAVE** for the two exact frozen local source candidates only.
Review completed 2026-10-13. No source files, Git refs, main controls, provider state, or remote objects were changed by this review. No installation, network request, or browser launch was performed.

## [직접 확인] Scope and source identity

The actual historical source files and actual successor files were read in full, inventoried with exact Unix modes, hashed with SHA-256 and Git blob hashing, and reconstructed into Git trees independently of the author's manifest generator. All historical source blobs/modes matched the saved GitHub tree responses, whose source → site-factory → repository-root → commit chain was checked. Saved GitHub responses are historical evidence; this review did not perform a fresh branch-head read.

| Region | Historical commit | Original → final files | Modified + added | Preserved files |
|---|---|---:|---:|---:|
| Geumcheon | d380d73a2e7d0f25014bad4c07d9959da4f7265d | 210 → 213 | 11 + 3 | 199 |
| Yeongdeungpo | a52b71fac2cbd9befafd5c60b7b4e6250c44ddcd | 316 → 319 | 13 + 3 | 303 |

Exact computed successor trees:

- Geumcheon source: 113970c56a8b4ff8c3a99b724767f82e6daa8e35
- Geumcheon entire branch root, with all other subtrees preserved: ac068dc9669646b127481604c91fbfc0378a092e
- Yeongdeungpo source: 367d2c1827f13bdf9f229d9cd767f98e48a0d19c
- Yeongdeungpo entire branch root, with all other subtrees preserved: 68e7624876b7e41300446ee25dc19584a5e0e963

These are expected trees, not saved new commits. The original save plans match exactly the verified 14/16 changed paths, hashes, modes, and local file locations. All files are regular 0644/0755 files; no symlink, special file, unexpected extra file, generated build revision, dist, package directory, or Python cache is included in either frozen source tree. There are no deletions or mode changes.

## [직접 확인] Requested delta and historical preservation

Exactly five customer files change per source: three shared WebPs, SharedFlowerBanner.astro, and shared-banner-manifest.json. The component is exactly the original after removal of the one specified figcaption line and addition of “ 전화 1844-0644.” to each complete original description. All component style bytes and image attributes remain unchanged. The WebPs match the previously approved source assets and exact SHA-256 pins; Pillow successfully decoded all three at 1774×887 in both sources. Pixel appearance was not newly reviewed here.

Every other changed file is a test, native QA gate, or successor seal. No article, common-copy file, customer-content hash map, product name/price/photo/order CTA, facility/region plan, non-banner component, layout, stylesheet, route, package/lockfile, build command, or original reference fixture changed. The original approval bytes are archived exactly; the active approval differs only in pending visual-verification text and the pinned five-file overlay. Existing publication/host/proof fields are preserved, not expanded. Neither current metadata nor this review claims the successor is public.

## [직접 확인] Independent executions

- Geumcheon offline npm test: 131 inherited + 122 active = **253**, exit 0.
- Yeongdeungpo offline npm test: 131 inherited Guro + 116 inherited Geumcheon + 126 active = **373**, exit 0.
- Additional release-seal mutation checks: **73/81** rejected changes, including every sealed customer path, approval/overlay/history, all five historical asset/component rollbacks, scope widening, deletion, repinning and wrong ancestor.
- Geumcheon synthetic-only npm run qa: native gates passed, **39** regression tests (5+8+17+9), exit 0.
- Yeongdeungpo synthetic-only npm run qa: native gates passed, **54** regression tests (5+8+17+9+15), exit 0.

The synthetic output was independently reconstructed from historical actual output only after verifying every output file against its saved release manifest. Only the precise captions/alts and three WebPs were transformed. The resulting output hashes matched the author's synthetic fixture exactly. This proves useful diagnostic regression behavior only. It is **not a fresh Astro build, browser evidence, deployment artifact, or public response**.

## [직접 확인] Source-push workflow safety

Both historical .github directories independently reconstruct to db871bd0c7dd97d5e5c7a0f6c44f4e38da94926a. All 59 workflow event definitions were inspected. The only three push workflows are:

- ansan-indexnow-production.yml: branch site-factory-ansan-v1
- ansan-live-qa.yml: branch site-factory-ansan-v1
- namyangju-production-gate-check.yml: branch codex/namyangju-production-gate

Neither site-factory-seoul-geumcheon-direct nor site-factory-seoul-yeongdeungpo-direct matches. There are no workflow_run or create events. An exact source save therefore does not match a repository workflow push trigger. Arbitrary external provider webhooks were not inspected and are not covered by this statement.

## [미확인] Required later stages and gate boundaries

- Fresh GitHub source save/readback, exact-SHA build, independently inspected real screenshots, production artifact binding, live HTTP/function verification and public update remain pending.
- Native assert_release_approval protects the explicitly sealed historical content plus exact overlay. It is not a whole-checkout inventory guard. The separate QA/production controls must verify complete committed tree identity, actual file bytes/modes, extra files and symlinks before executing build/capture/publication.
- Both sources keep build-revision.json generated/untracked. A later postbuild gate must admit only the exact generated revision file bytes for the saved source HEAD; it must not copy a tracked-revision exception blindly.
- Existing initial-publication controls are not approved for updating live targets by this source-save review.

## Evidence

Under evidence/:

- source-review-results.json: independent source identities, counts, SHA pins and test outcomes
- {region}-independent-final-manifest.json: full actual byte/mode inventories
- {region}-independent-delta.json and {region}-independent.diff: independently computed exact deltas
- {region}-independent-npm-test.log: newly executed source suites
- {region}-adversarial-release.json: every rejected mutation case
- native-review-results.json: historical artifact binding and synthetic transformation scope
- {region}-independent-synthetic-native.log: newly executed synthetic-only diagnostics
- workflow-trigger-inspection.json and workflow-push-verdict.json: original workflow triggers and exact .github tree

Reproduction scripts: review_source.py, review_native.py, adversarial_release.mjs. Copies and evidence remain isolated under this review directory. Source reproduction refuses to overwrite the original test-copy paths.
