# Independent actual production artifact and binding review

Reviewed 2026-10-13 UTC. Verdict: **PASS for the exact production-output bindings and nine-file save scope identified below**, with the expressly disclosed provenance, browser and dependency-security limitations. This review does not establish a public release, hostname attachment, IndexNow receipt or search indexing. No remote mutation, deployment, package installation or fresh browser session was performed by this reviewer.

## Directly verified results

### Immutable identities and actual downloaded output

The control commit is `c4a4143512eac6cc39654703f4ddaf6fa9aec0ad`, tree `ff2a79a61fdafc8a6dd1ec6a45d6b45a06b8873b`, parent `53740cac7f25890af0ee24d6a2cd8791e6bebb87`. Fresh GitHub commit/ref responses match the previously independently reconstructed tree. All 26 local reviewed control-overlay files still match their sealed Git blob identities.

- Geumcheon: source `d380d73a2e7d0f25014bad4c07d9959da4f7265d`, repository tree `491bae1b1405043447dcb6eea7e1be210cf213ad`; [run 38413441347](https://github.com/joseungil-kr/fwith-site-factory/actions/runs/38413441347); build artifact `11823103188`; ZIP SHA-256 `88f214c67d0ac70c8406e487e75e2e9fe678d7852f735dfc5805b30a8f5d9c14`; 879,780 bytes; 19 output files.
- Yeongdeungpo: source `a52b71fac2cbd9befafd5c60b7b4e6250c44ddcd`, repository tree `40ba52989a9c3d04eed138d958e9e9de11099eac`; [run 38413441032](https://github.com/joseungil-kr/fwith-site-factory/actions/runs/38413441032); build artifact `11822773418`; ZIP SHA-256 `1a02a85f842137bf6dfb91b76ba8f8fcbced7fb587461ac9545170f8212ea2af`; 1,209,875 bytes; 24 output files.
- Dongjak: source `bdfb4ae78640a95aa6001581da552a7329fb4775`, repository tree `c87ccd3282fe14c592a87f592437147bca704225`; [run 38413440893](https://github.com/joseungil-kr/fwith-site-factory/actions/runs/38413440893); build artifact `11821699460`; ZIP SHA-256 `ca8de962e5435a33023717ec0fd1afc9323782726556e0443d763f5d8a267fe6`; 878,160 bytes; 19 output files.

All three original ZIPs passed independent CRC, size, SHA-256, duplicate-name, path and symlink checks. Each release manifest exactly binds its source revision, control revision, run ID, repository, branch, source root, production origin, worker identity and every output-file hash. Native source copies match all 210/316/639 source-contract hashes. Full original build logs corroborate both exact checkouts and the exact release-manifest digests, rather than merely reporting a successful build.

The three separate inspection ZIPs were independently matched to fresh API digests and checked against their extracted bytes. Their actual `artifact-check.json` and `http-contract.json` agree with the independently reconstructed output and local controller results. Inspection artifact IDs: `11822203430`, `11822098560`, `11821209934`.

### Actual output, customer-visible parity and tests

- Rehashed all 267 sealed baseline evidence files, including all 153 saved screenshots and all 53 original dist files. Baseline runs are `38318719004`, `38338256404`, `38343055625`.
- All 13 production HTML files preserve their entire body and structural suffix byte-for-byte. All baseline CSS, images, favicon and other unchanged assets remain byte-identical. Added files are exactly the approved public proof plus the two sitemap files per region.
- Parsed every actual HTML page: exact route inventory, one H1, no duplicate IDs, nonempty image alt text, exact revision/canonical/robots metadata, all 130 internal link/fragment references and 77 asset references resolve. Checked CSS asset references and exact sitemap URL sets: 2/3/2 URLs.
- Production home/article routes are indexable. All three thin `/regions/` hubs remain `noindex,follow` and sitemap-excluded. All three 404 documents have no canonical and remain `noindex,nofollow,noarchive`. Generated robots and response-header files match the explicit production contract.
- Each approved public proof has SHA-256 `c40f009f9ed19bfb57c3e66503439b83f5725595cebdbfb9b6a5a41a526cbde1`.
- Independently reran source-native tests and static/mutation QA against copies of the **actual downloaded production output**, without package installation: 250 + 370 + 449 = 1,069 passing Node test executions and 34 + 45 + 54 = 133 passing Python test executions. All three controller artifact checks also passed.
- Independently executed 30 equivalence negative cases, covering nonempty, missing, duplicate or misplaced Naver tags, tags on hubs/404s, arbitrary metadata, customer-body changes, CSS changes and altered public proof. All rejected.
- Independently executed each final production binding through the actual controller: three positive cases passed, and 15 negative cases rejected wrong file hash, source revision, origin, review state or missing binding.

### Explicitly reviewed empty Naver metadata exception

The initial narrow equivalence check correctly rejected an unexpected additional head tag: `<meta name="naver-site-verification" content>`. Direct inspection found the same empty configuration in all three sources, and the active BaseLayout is byte-identical to its immutable baseline. Its existing indexable-only expression emits exactly this empty tag on the seven home/article pages, with none on hubs or 404s.

The reviewed allowance is this exact empty tag at its exact head position on those seven routes, in addition to the originally planned origin/revision/robots and search-artifact changes. Arbitrary metadata and any nonempty verification value remain forbidden. This empty tag establishes **no Naver verification**. No source, customer content, style or interaction change was needed to explain it.

### Visual evidence scope

The existing visual baseline may be reused because the actual production customer bodies, CSS, images and interaction bytes are exactly preserved. All 153 screenshot bytes were independently reverified; three saved 390px detail-top images were newly opened in this review and showed no newly observed blocking defect within that limited sample. The other 150 screenshots were not visually reopened here; their broader original and subsequent independent review records remain the evidence. **No fresh production browser run occurred.**

## Tool-reported observations

Fresh GitHub run/job API records report attempt 1, `issues` event, `main`, exact control SHA, owner actor and triggering actor, successful `build` and `inspect_build`, and skipped `publish` and `finalize_indexnow` for all three runs. Original logs report 76 passing publisher tests per region and completed npm/Astro test/build steps. Astro's final summaries report zero errors and zero warnings, while separate unused-test-import hints and Actions/runtime deprecation notices are present. Actual output and independently repeated checks corroborate the build/inspection results; they do not establish public publication.

## Inference and limitations

[Issue 285](https://github.com/joseungil-kr/fwith-site-factory/issues/285) was directly reread: exact owner, title and immutable source payload, with JSON boolean `build_only:true`; its created and updated times are equal. The association between this particular issue number and these runs is **inferred** from the matching owner, exact payload, title, event, times and skipped publication jobs. Available run API/logs do not expose a direct issue-number binding. Public run-page retrieval was also attempted and returned `Cache miss`. Source/control/run/output identities are directly verified independently of that issue-number association.

All three original npm ci logs report **one high-severity vulnerability**. The retained output does not name its package or advisory, and this review does not identify or clear that unnamed finding. Direct original-lockfile and advisory inspection separately establishes that `http-cache-semantics` 4.2.0 matches the affected range in [GHSA-ch52-4w7c-c8xp](https://github.com/advisories/GHSA-ch52-4w7c-c8xp), which lists no patched version when read on 2026-10-13. That match does not prove it is the unnamed npm finding. The exact deployable inventory has no node_modules, npm package runtime or executable Worker code. This is a static-output certification, **not dependency-security clearance**, and no dependency or security configuration was changed.

Live HTTP, actual unknown-path HTTP 404, hostname/provider binding, IndexNow receipt, search indexing, current external business assertions and fresh browser rendering are not established. The static 404 file's correctness does not prove live HTTP status behavior. These remain later release checks.

## Frozen nine-file binding verdict

The three `production-output-contract.json` files, three `actual-production-build.json` reports and three scoped `test_publish.py` changes were checked byte-for-byte against the final manifest, including Git blob hashes, direct artifact evidence, native QA and explicit limitations. The previously reviewed six binding/report files remain unchanged. No private chat identifiers or executor paths appear in these nine files.

The three test diffs only isolate the existing missing-production-contract negative in a temporary directory, preserving its expected failure assertion after a real contract is present. Runtime publishers, workflows and source contracts are unchanged. An additional independent rerun with the real bindings installed passed 76 tests per region, 228 total. All nine scoped files match their bytes in the proposed integrated main candidate. Other regional additions in that larger integration are outside this review and require their separate owner/reviewer evidence.

Final nine-file manifest SHA-256: `20b0a8c89e94d9d53a6ed1494bec11323c857d72f9f9a2478f3ad469a333bfbb`.

Production binding SHA-256:
- Geumcheon: `acab8433e87d66b2caf57c96ade640e1921338928621fd93f61019c2e108c3d6`
- Yeongdeungpo: `5df6e24410e3d76fdfca114be7c080680cd707d65cd9c1eada86d0b30bc64542`
- Dongjak: `53ca34e8133c3ca1f6691256290c65eb3dab2c47b3bf4da1344c2d12c767fe35`

Evidence-report SHA-256:
- Geumcheon: `02024cd2e088c628f6a2f1248202ab21f122ab1acc5ac60bebc0d9f8dccc03cc`
- Yeongdeungpo: `0761233fc8e02bb7b445b42acfd59224798a0c4b4b2b336568f801444758db39`
- Dongjak: `d2963f06ffcd0d83e4c01c74fafead51977c558c74c1b9b66b967019ebaaa2b1`


Test-isolation file SHA-256:
- Geumcheon: `5b7504efd49fd35f9c50cffaeb0ed1f487dcbd257407a714cbf995b990624fb8`
- Yeongdeungpo: `29e6e60fce7c48d5f6d514effd14aa255b78b236710a118335301550d96eac00`
- Dongjak: `8bfcf7b80527ea71855628cdfe58ea5665b4d752358307522bcf11b2550a25a9`

**The exact actual production output may be bound by these contracts, with the three reviewed test-isolation adjustments.** Before using them, save only the reviewed scoped files, preserve concurrent main work and verify their actual remote commit/tree/content. A later publication build must independently satisfy the immutable output hash contract before any provider operation. Public release remains sequential Geumcheon → Yeongdeungpo → Dongjak with the required live verification and receipts. This verdict does not itself establish that any binding has been saved or any site published.
