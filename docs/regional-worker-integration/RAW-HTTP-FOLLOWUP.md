# Raw HTTP follow-up — verified local evidence

This supersedes the missing Geumcheon Location/robots-cause statements in LIVE-DIFFERENCE-REVIEW.md. No public request, provider mutation or browser access was performed for this follow-up. At 05:46 UTC the user approved publishing the two regions’ version IDs, non-sensitive settings, hashes and comparisons to the designated repository branch, excluding secrets, personal information and environment values. Upload status is reported separately after readback.

Source: parent-supplied files in the helper evidence folder `regional-worker-evidence-20261101/`. Original file/body SHA-256 and selected non-telemetry response headers are recorded in `raw-http-analysis.json`. Raw Report-To URLs and CF telemetry identifiers are not copied into this report.

| Observation | Dongjak | Geumcheon |
| --- | --- | --- |
| Helper checked-at UTC | 2026-11-01T05:39:53.3855543Z | 2026-11-01T05:39:55.3819116Z |
| `/404.html` response Date UTC | 05:39:53 | 05:39:55 |
| `/404.html` first hop | 307, Location `/404`, empty body | 307, Location `/404`, empty body |
| robots response Date UTC | 05:39:55 | 05:39:56 |
| robots status/type/length | 200, text/plain UTF-8, 2757 bytes | 200, text/plain UTF-8, 2759 bytes |
| Saved robots hash agrees with prior helper comparison | Yes | Yes |
| Original robots suffix byte-exact | Yes | Yes |

Both saved robots bodies consist exactly of the same **2,674-byte managed prefix**, two LF separators (`0a0a`), and the corresponding original robots file. Prefix SHA-256: `74cfd1bcd1dede6d233fe5b6005c0f13a339ec087363379a35f5f9d57ed5e42b`. This comparison does not strip comments, reorder directives or normalize whitespace. Missing/duplicate markers, changed sitemap, added rules and altered separators are tested as failures.

The observed prefix contains `Content-Signal: search=yes,ai-train=no,use=reference` and named crawler restrictions. Each untouched origin suffix contains its own Allow rule and sitemap URL. Thus Geumcheon's captured difference is now explained by the same managed prefix as Dongjak. **The direct public-file hash result is still 16/18 per site**: explanation of different bytes is not an 18/18 byte-equality verdict.

Preservation policy remains: keep source robots unchanged, preserve Cloudflare's current policy configuration, neither strip nor hardcode the managed block, and verify that the edge transformation remains applied after any eventually approved worker-first change. Current raw evidence does not prove future edge behavior. No policy settings were changed.

The 404 tests distinguish platform URL canonicalization from missing-resource handling. `/404.html` canonically redirects to `/404`; the local canonical `/404` is a directly requested document (200 with the retained 404.html bytes), while an actually missing path returns 404 with those same branded/noindex bytes. Both original static-only baselines and the integrated local router are compared. No internal namespace appears in Location. The public final `/404` response and a public missing-path response are still not included in the supplied capture, so local results are not promoted to a live final-chain assertion.

Independent raw-evidence tests: 3/3. Updated real local workerd checks include `/404` and explicit document-versus-missing status checks; 123/123 passed; see `local-http-results.json`. Existing router runtime and candidate ZIPs are unchanged. Active-UUID/source binding, full configuration restoration, request growth and post-integration edge policy remain release gates. Production deployment remains pending independent review. Local test storage was isolated per server after a SQLite lock; the successful run used the isolated storage.
