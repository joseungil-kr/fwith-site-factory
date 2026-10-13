# Independent Dongjak actual-source QA rebind review

PASS_LOCAL_ACTUAL_SOURCE_REBIND_ONLY, for the exact 18 additive files on base control 34a6c6f4aa9b0d5d031e378c245a437e2fafc5fb, tree 79f5d06ada14848b220312d1b19cbad1fde1c5f0. A fresh independent QA branch GET still resolved to that exact base during review.

## Direct checks
- Bound actual source 430dada32f3f8b53f24aec8d9fdf3724529604e1 / repository tree 5d64d0467d6b900c549a8b26660b95b6f2b1e882 / site tree a032dbdad16e044af8bca7163e26ca795f3b7d6c. Separate source review verifies all 629 bytes and actual 16-file build output.
- All 1,130 base files remain byte-identical. All 18 proposed additions match SHA-256, byte count, mode and predicted Git blob; exact additions-only patch content and proposed API payloads were independently reconstructed. No existing regional workflow or guard changed.
- Accepted rev2 capture script and upstream guards remain byte-identical. Original 629-file manifest is preserved, alongside current actual 629-file manifest. Runtime pins the lineage document digest, both manifest digests, exact source/tree identities and the sole accepted CSS hash/blob. Duplicate/deleted/unrelated source changes, old source and old generated revision fail.
- The tracked build-revision exception remains restricted to the exact single path and native JSON bytes for the actual current HEAD, without a trailing newline. It does not allow arbitrary generated files, JSON values, whitespace or symlinks. Pristine binding still verifies committed original bytes first; built HTML additionally binds the actual revision.
- Independently reran 93 offline tests on a pristine local clone of the saved commit, then ran the inspected native revision writer in the reviewer fixture and reran all 93 tests. Socket creation was blocked. All passed. Also independently reran 25 workflow mutation tests.
- Exact 150 geometry checks retain all four home product-card targets without the hero duplicate; 12 full-page captures, six initial anchors and all existing interaction/occlusion/overflow checks are retained. Actual screen selection count awaits rendering.
- Parsed all 62 workflows and six shell blocks. This exact 18-file QA-branch push selects only the Dongjak workflow. Contents-read, credential persistence disabled, one pinned source row, no service-secret/deploy/index command, native gates/two-build equality, loopback-only browser route and five failure-retained artifact groups remain intact. External provider webhooks are outside static workflow inspection.
- All 50 preparation-manifest entries and 51 distinct safe ZIP members pass independent byte/CRC verification. Prior accepted package bytes remain intact.

## Exact accepted proposal
- Full control-proposal.diff SHA-256: 324bbd08a20828b7c2ef1227d3bcab0a08c2eafbe66f17c8703a46cd02772096
- Preparation manifest SHA-256: 727fa07ed79c444143c0e89df8aec481c95849d6a129a977c327b6e743871a08
- ZIP SHA-256: 7105d70d9bf049b7d5e4fafdb56254ed7e7ad0692edb790e367e58d4c3c84c78

## Execution boundary
No actual Dongjak control commit or CI artifact exists at this review. Under the parent's specific authorization, refresh the shared QA ref, preserve the expected base/lease and save only these 18 additions; independently verify the actual commit/tree/blobs. Its scoped push is the one intended execution trigger. Do not duplicate dispatch or weaken failures. Real CI source/control/run binding, artifact/API digests, manifests and selected pixels require a subsequent independent review before browser PASS. Public HTTP, deployment and IndexNow remain separate and unverified.

No remote mutation, local Chromium/socket or CI trigger was performed by this reviewer. Machine provenance's publicationAuthorization=not-issued describes this QA package's non-publication authority, not a revocation of the user's separately valid public-release instruction.
