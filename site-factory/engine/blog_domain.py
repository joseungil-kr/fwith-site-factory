#!/usr/bin/env python3
"""Fixed, fail-closed noindex blog custom-domain adapter.

This module deliberately accepts no hostname, Worker, account, or route input.
It reuses the reviewed native Custom Domains preflight/attach implementation;
callers must provide credentials only through the existing environment variables.
"""
import argparse
import json
import os
from pathlib import Path
import re
from urllib.error import HTTPError
from urllib.request import Request, build_opener

import bucheon_domain_attach as native
from goyang_domain import NoRedirect, PreflightError, single_page

SITE_KEY = "blog-fwith"
HOSTNAME = "blog.fwith.kr"
ZONE_NAME = "fwith.kr"
WORKER = "blog-fwith-prod-disabled"
ACCOUNT_ID_RE = re.compile(r"[0-9a-fA-F]{32}")


def validate_registry(registry: Path) -> dict:
    registry = Path(registry)
    site = json.loads(registry.read_text(encoding="utf-8"))["sites"].get(SITE_KEY)
    expected = {
        "repo": "joseungil-kr/fwith-site-factory",
        "branch": "site-factory-blog-fwith",
        "root": "site-factory/blog-fwith",
        "siteUrl": "https://" + HOSTNAME,
        "worker": WORKER,
        "wranglerConfig": "wrangler.jsonc",
        "launchMode": "staging",
        "productionEnabled": False,
        "growthPaused": True,
        "autoDeploySnapshots": False,
        "stagingBuildIsolation": False,
        "stagingWorker": "blog-fwith-guide-qa",
        "stagingUrl": "https://blog-fwith-guide-qa.joseungil.workers.dev",
    }
    if not isinstance(site, dict) or any(site.get(key) != value for key, value in expected.items()):
        raise ValueError("blog_registry_identity_mismatch")
    return site


def _with_fixed_identity(callback, *args):
    original = native.HOSTNAME, native.ZONE_NAME, native.WORKER
    try:
        native.HOSTNAME, native.ZONE_NAME, native.WORKER = HOSTNAME, ZONE_NAME, WORKER
        return callback(*args)
    finally:
        native.HOSTNAME, native.ZONE_NAME, native.WORKER = original


def _validate_account_id(account_id):
    if not isinstance(account_id, str) or not ACCOUNT_ID_RE.fullmatch(account_id):
        raise PreflightError("invalid_account_configuration")


def preflight(transport, account_id, diagnostics=None):
    """GET-only inventory; unknown DNS state is never treated as absent."""
    _validate_account_id(account_id)
    return _with_fixed_identity(native.preflight, transport, account_id, diagnostics)


def attach(transport, account_id):
    """One native PUT with all Wrangler override controls disabled; never retries."""
    _validate_account_id(account_id)
    return _with_fixed_identity(native.attach, transport, account_id)


def get_binding(transport, account_id):
    """Read one complete domains inventory; DNS remains unobserved."""
    _validate_account_id(account_id)
    path = "/accounts/" + account_id + "/workers/domains"
    try:
        payload = transport("GET", path)
    except HTTPError as error:
        raise PreflightError("domain_inventory_http_error", error.code) from None
    except Exception:
        raise PreflightError("domain_inventory_request_failed") from None
    if not (getattr(transport, "last_http_status", None) == 200 and isinstance(payload, dict)
            and payload.get("success") is True and payload.get("errors") in ([], None)
            and isinstance(payload.get("result"), list)):
        raise PreflightError("domain_inventory_unverified")
    try:
        rows = single_page(lambda method, requested: payload if method == "GET" and requested == path else (_ for _ in ()).throw(ValueError()), path)
    except PreflightError:
        raise PreflightError("domain_inventory_unverified") from None
    matches = [row for row in rows if isinstance(row, dict) and isinstance(row.get("hostname"), str) and row["hostname"].lower() == HOSTNAME]
    if len(matches) != 1 or matches[0].get("service") != WORKER:
        raise PreflightError("blog_binding_mismatch")
    return {"hostname": HOSTNAME, "worker": WORKER, "dnsState": "not_observed"}


def _readback_transport(token, account_id):
    expected = "/accounts/" + account_id + "/workers/domains"
    opener = build_opener(NoRedirect())
    def transport(method, path, body=None):
        if method != "GET" or body is not None or path != expected:
            raise RuntimeError("readback_operation_not_allowed")
        request = Request("https://api.cloudflare.com/client/v4" + path, method="GET",
                          headers={"Authorization": "Bearer " + token, "Accept": "application/json"})
        transport.last_http_status = None
        with opener.open(request, timeout=20) as response:
            transport.last_http_status = response.status
            response_body = response.read(1024 * 1024 + 1)
        if len(response_body) > 1024 * 1024:
            raise RuntimeError("response_limit")
        return json.loads(response_body)
    transport.last_http_status = None
    return transport


def _write_report(path, report):
    Path(path).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--mode", choices=("preflight", "attach", "readback"), required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args(argv)
    report, exit_code = {"mode": args.mode, "mutationsPerformed": False, "mutationStatus": "not_attempted", "state": "blocked"}, 1
    try:
        validate_registry(args.registry)
        account_id = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "")
        _validate_account_id(account_id)
        if args.mode == "readback":
            token = os.environ.get("CLOUDFLARE_API_TOKEN", "")
            if not token:
                raise PreflightError("missing_credentials")
            report.update(state="binding_verified", **get_binding(_readback_transport(token, account_id), account_id))
            exit_code = 0
        else:
            native_args = ["--preflight"] if args.mode == "preflight" else []
            if args.mode == "preflight":
                native_report = args.report.with_name(args.report.stem + "-native.json")
                native_args += ["--report", str(native_report)]
                report["nativeReport"] = str(native_report)
            native_code = _with_fixed_identity(native.main, native_args)
            report.update(state="native_" + args.mode + ("_succeeded" if native_code == 0 else "_blocked"),
                          mutationsPerformed=(True if args.mode == "attach" and native_code == 0 else None if args.mode == "attach" else False),
                          mutationStatus=("accepted" if args.mode == "attach" and native_code == 0
                                          else "unknown" if args.mode == "attach" else "not_attempted"))
            exit_code = int(native_code != 0)
    except PreflightError as error:
        report["code"] = error.code
        if error.status is not None:
            report["httpStatus"] = error.status
    except (OSError, ValueError, KeyError, json.JSONDecodeError):
        report["code"] = "configuration_unverified"
    try:
        _write_report(args.report, report)
    except OSError:
        return 1
    print(json.dumps(report, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
