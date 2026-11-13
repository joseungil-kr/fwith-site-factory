# Baekse public smoke diagnostics: staged, not activated

The production release and application are unchanged by this directory. Run local synthetic tests with:
```sh
cd scripts/diagnostics/baekse
python -m unittest -v test_smoke_diagnostic.py
```
Six synthetic tests cover all paths, exact failure path, immediate stop on 403, no error-body read, exception sanitization, no redirects, invalid phase and body-size limit. No live network is used.

## Diagnostic gap in release 43449803639
The actual 403 traceback identifies the asset loop, but not which of its four URLs failed. There was no public baseline check before activation and no CF-Ray or response classification retained. Do not label this an application failure or edge failure without additional evidence.

## Proposed baseline workflow, not an executable workflow
A future independent **manual-only** read-only workflow may:
- Use permissions contents:read; no secrets, Cloudflare token, environment access, deployment commands or production writes.
- Checkout a reviewed immutable revision, use Python 3.12, run these synthetic tests first.
- Only after the denied access path has a legitimate resolution and explicit scope is confirmed, invoke observe('baseline') once, with no retry or fallback.
- Record UTC time, immutable revision, phase, known public path, status, allowlisted headers and success hash. No credentials, queries, cookies, order data, response body or error string.
- Stop immediately at any failure. Diagnostic failure never activates, rolls back or changes security settings.
- A 403 remains a failed baseline, not a successful verification and not a reason to spoof browser headers, change IP/proxy, use another host, or disable security.

No such network workflow has been added or triggered. Historical Cloudflare events and already-permitted normal-browser observations should be used first to identify the rejection. The previously rejected CI request must not be repeated just because a new helper exists.

## Future release integration
Once a legitimate baseline verification method works, require baseline validation **before** upload/activation. Check baseline assets against baseline hashes, not candidate hashes. Retain the candidate post-activation pinned-source hashes, noindex/no-store and anonymous session401 assertions and guarded rollback. This diagnostic helper cannot replace those correctness assertions. No changes to the production release workflow are included here.
