# Yangcheon candidate control verification

Status: candidate configured; publication pending independent source/plan/control review. No external issue, push or deployment was performed.

The workflow retains exact-source dispatch and adds the existing Dobong owner-only issues/opened adapter. An issue must have title `[REGIONAL-COPY-DEPLOY] batch`; actor and issue author must both be `joseungil-kr`; repository and main branch remain fixed. All seven source revision selections use `fromJSON(github.event.issue.body).revisions['seoul-yangcheon']`. Exact 40-character source SHA, branch-head equality, ancestry, first-run restriction and pre-publication branch recheck remain intact.

Candidate article slugs:
- mok-dong-loftgarden344-wedding-wreath
- sinjeong-dong-yangcheon-culture-performance-wreath
- sinwol-dong-mediheal-funeral-wreath

Together with home and regional directory these yield five sitemap routes and five normal HTML routes, plus a genuine noindex 404. They are candidate controls, not proof of editorial approval or a live release.

## Receipt journal

RECEIPT_ISSUE=266 reuses the established multi-region journal after parent authorization. Repository code inspection found many existing regional publishers already use this issue. The unchanged engine's `Journal.records` reads repository-wide bot-authored issue comments, while writes go to the configured issue. A separate issue does not change record lookup or idempotency isolation.

The exact fingerprint includes siteKey, origin, source revision, endpoint, exact URL-set digest and count, and ownership-key digest. A new offline test exercises the real finalizer with one shared journal and two different regions: two distinct fingerprints cause exactly two submissions; the third invocation for the first region returns its exact existing receipt with no third submission. Existing uncertain-result, 403-diagnosis, revision-isolation and source-drift guards remain tested.

## Execution evidence

`python3 scripts/direct-seoul-yangcheon/test_publish.py -v`: 43 tests passed, zero skipped. `python3 -m py_compile scripts/direct-seoul-yangcheon/{publish.py,test_publish.py}` passed.

SHA-256 at this verification:
- publish.py: 123131b2779c1cd36cf870df860469827198ea19897c50f74492bed9841d9963
- test_publish.py: adada191afd6514a4483ed1961db75532775995e59d5613f59fdcbe9444edb2a
- workflow: f39039f0c51605393af0166a135db817b3013e4ef56e21b1d6bce5c8433045af

Offline tests do not establish remote issue state/access, current provider state, a GitHub Actions run, public HTTP content or IndexNow receipt for Yangcheon. Those remain publication-stage gates. No provider secrets or permissions were changed. The runtime skeleton regeneration note predates this candidate configuration; its unset control-plan/receipt statements are superseded by this report.
