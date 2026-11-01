"""One-shot Dongjak executor. Explicit arming required; no domain writes or retries.

Provider exception bodies, subprocess output and credential values are never logged.
Manual/dashboard publishers must be excluded: API GET + deploy is not atomic CAS.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time
import zipfile
from urllib.error import HTTPError
from urllib.request import Request, HTTPRedirectHandler, build_opener

from prepare_stage1 import CONFIG, ROOT, ROUTER_SHA, ZIP_SHA
from recovery_plan import DONGJAK, GEUMCHEON, D_VERSION, G_VERSION, valid_uuid

HOSTS = {DONGJAK: 'seoul-dongjak.fwith.kr', GEUMCHEON: 'seoul-geumcheon.fwith.kr'}
ORIGINALS = {DONGJAK: D_VERSION, GEUMCHEON: G_VERSION}


class Stop(Exception):
    pass


def require(condition, code):
    if not condition:
        raise Stop(code)


def single_page_domains(payload):
    """Domains.list is SyncSinglePage in Cloudflare's SDK, not a V4Page API.

    No page/per_page request parameters. Optional metadata must not contradict
    completeness; any advertised continuation, truncation or unknown metadata stops.
    """
    require(payload.get('success') is True and payload.get('errors') in (None, []), 'domain_response_failed')
    rows = payload.get('result')
    require(isinstance(rows, list) and all(isinstance(row, dict) for row in rows), 'domain_rows_invalid')
    require(not any(key in payload for key in ['cursor', 'cursors', 'next', 'next_page', 'has_more', 'links']), 'domain_continuation_unverified')
    info = payload.get('result_info', {})
    require(isinstance(info, dict) and set(info) <= {'page', 'per_page', 'count', 'total_count', 'total_pages'}, 'domain_metadata_unverified')
    require(all(type(value) is int and value >= 0 for value in info.values()), 'domain_metadata_invalid')
    for key in ['count', 'total_count']:
        require(key not in info or info[key] == len(rows), 'domain_inventory_incomplete')
    require(info.get('page', 1) == 1 and info.get('total_pages', 1) == 1
            and info.get('per_page', len(rows)) >= len(rows), 'domain_inventory_incomplete')
    ids = [row.get('id') for row in rows]
    require(all(isinstance(value, str) and value for value in ids) and len(set(ids)) == len(ids), 'domain_identity_invalid')
    require(all(isinstance(row.get(key), str) and row[key] for row in rows for key in ['hostname', 'service']), 'domain_identity_invalid')
    return rows


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class Provider:
    def __init__(self, record=lambda *args, **kwargs: None):
        self.record = record
        self.account = os.environ.get('CLOUDFLARE_ACCOUNT_ID', '')
        self.token = os.environ.get('CLOUDFLARE_API_TOKEN', '')
        require(bool(re.fullmatch('[a-f0-9]{32}', self.account)) and bool(self.token), 'existing_credentials_unavailable')
        self.opener = build_opener(NoRedirect())

    def get(self, resource):
        allowed = resource == 'workers/domains'
        for worker in ORIGINALS:
            allowed |= resource in [f'workers/domains?hostname={HOSTS[worker]}', f'workers/domains?service={worker}']
            allowed |= resource in [f'workers/scripts/{worker}/deployments', f'workers/scripts/{worker}/settings']
            allowed |= bool(re.fullmatch(f'workers/scripts/{worker}/versions/[a-f0-9-]{{36}}', resource))
        require(allowed, 'get_path_not_allowed')
        request = Request(f'https://api.cloudflare.com/client/v4/accounts/{self.account}/{resource}',
                          headers={'Authorization': 'Bearer ' + self.token}, method='GET')
        try:
            remaining = getattr(self, 'deadline', time.monotonic() + 60) - time.monotonic()
            require(remaining > 0, 'provider_snapshot_timeout')
            with self.opener.open(request, timeout=min(10, remaining)) as response:
                payload = json.loads(response.read(4 * 1024 * 1024))
            require(payload.get('success') is True, 'provider_get_failed')
            if resource.startswith('workers/domains'):
                info = payload.get('result_info')
                # Structural diagnostics only: no account, token, domain records
                # or unknown response values can enter the retained report.
                self.record('domain_response_shape', query=resource.split('?', 1)[-1].split('=', 1)[0] if '?' in resource else 'all',
                            top_fields=sorted(payload), result_type=type(payload.get('result')).__name__,
                            result_count=len(payload['result']) if isinstance(payload.get('result'), list) else None,
                            info_type=type(info).__name__, info_fields=sorted(info) if isinstance(info, dict) else [],
                            pagination={key: value for key, value in (info.items() if isinstance(info, dict) else [])
                                        if key in ['page', 'per_page', 'count', 'total_count', 'total_pages'] and type(value) is int})
            return payload
        except Exception:
            raise Stop('provider_get_failed') from None

    def snapshot(self):
        self.deadline = time.monotonic() + 60
        domains = single_page_domains(self.get('workers/domains'))
        # Reconcile documented exact filters, detecting missing target rows,
        # ignored filters, extra aliases for a Worker and changing inventories.
        for worker, host in HOSTS.items():
            for key, value in [('hostname', host), ('service', worker)]:
                filtered = single_page_domains(self.get(f'workers/domains?{key}={value}'))
                require(all(row[key] == value for row in filtered), 'domain_filter_ignored')
                expected = {row['id']: row for row in domains if row[key] == value}
                require({row['id']: row for row in filtered} == expected, 'domain_filter_disagreement')
        state = {}
        for worker, original in ORIGINALS.items():
            host = HOSTS[worker]
            matches = [r for r in domains if r.get('hostname') == host or r.get('service') == worker]
            require(len(matches) == 1 and matches[0].get('hostname') == host
                    and matches[0].get('service') == worker and matches[0].get('enabled') is True
                    and matches[0].get('previews_enabled') is False, 'domain_mapping_drift')
            deployments = self.get(f'workers/scripts/{worker}/deployments')['result']['deployments']
            require(bool(deployments), 'deployment_missing')
            latest = max(deployments, key=lambda row: row['created_on'])
            versions = latest['versions']
            require(len(versions) == 1 and versions[0]['percentage'] == 100
                    and valid_uuid(versions[0]['version_id']), 'active_version_unverified')
            active = versions[0]['version_id']
            for version_id in set([active, original]):
                version = self.get(f'workers/scripts/{worker}/versions/{version_id}')['result']
                require(version.get('id') == version_id, 'retained_version_unavailable')
            settings = self.get(f'workers/scripts/{worker}/settings')['result']
            state[worker] = dict(version=active, settings=settings)
        return state


def check_state(state, expected_dongjak, baseline=None):
    for worker, expected in [(DONGJAK, expected_dongjak), (GEUMCHEON, G_VERSION)]:
        require(state[worker]['version'] == expected, 'concurrent_version_change')
        settings = state[worker]['settings']
        require(settings.get('compatibility_date') == '2026-10-09'
                and settings.get('compatibility_flags') == [] and settings.get('logpush') is False
                and settings.get('usage_model') == 'standard' and settings.get('placement', {}) == {}, 'settings_drift')
        bindings = settings.get('bindings')
        if worker == DONGJAK and expected_dongjak != D_VERSION:
            require(bindings == [{'name': 'ASSETS', 'type': 'assets'}], 'unexpected_pilot_bindings')
        else:
            require(bindings == [], 'unexpected_original_bindings')
        if baseline is not None:
            # Full returned settings must remain stable except the one intended binding.
            before = dict(baseline[worker]['settings'])
            after = dict(settings)
            before.pop('bindings', None)
            after.pop('bindings', None)
            require(before == after, 'nonbinding_settings_changed')


def verify_bundle(bundle):
    require(json.loads((bundle / 'wrangler.stage1.json').read_text()) == CONFIG, 'config_mismatch')
    require(hashlib.sha256((bundle / 'router.mjs').read_bytes()).hexdigest() == ROUTER_SHA, 'router_mismatch')
    expected = {}
    for region in ['dongjak', 'geumcheon']:
        contract = json.loads((ROOT / f'scripts/direct-seoul-{region}/production-output-contract.json').read_text())
        for name, sha in contract['files'].items():
            if name != '_headers':
                expected[f'__regional/{region}/{name}'] = sha
    archive = ROOT / 'docs/regional-worker-integration/artifacts/pilot-local-bundle.zip'
    require(hashlib.sha256(archive.read_bytes()).hexdigest() == ZIP_SHA, 'reviewed_zip_mismatch')
    with zipfile.ZipFile(archive) as z:
        inventory = json.loads(z.read('inventory.json'))
    header = [r for r in inventory['files'] if r['path'] == '_headers']
    require(len(header) == 1, 'headers_inventory_missing')
    expected['_headers'] = header[0]['sha256']
    paths = list((bundle / 'assets').rglob('*'))
    require(not any(p.is_symlink() for p in paths), 'symlink_refused')
    actual = {p.relative_to(bundle / 'assets').as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in paths if p.is_file()}
    require(actual == expected and len(actual) == 37, 'asset_inventory_mismatch')


def public_snapshot():
    opener = build_opener(NoRedirect())
    result = {}
    deadline = time.monotonic() + 120
    selected = ['content-type', 'cache-control', 'location', 'x-robots-tag', 'x-content-type-options', 'x-frame-options', 'referrer-policy']
    for worker, host in HOSTS.items():
        region = 'dongjak' if worker == DONGJAK else 'geumcheon'
        files = json.loads((ROOT / f'scripts/direct-seoul-{region}/production-output-contract.json').read_text())['files']
        with zipfile.ZipFile(ROOT / 'docs/regional-worker-integration/artifacts/pilot-local-bundle.zip') as archive:
            original_robots = archive.read(f'assets/__regional/{region}/robots.txt')
        paths = ['/' + name for name in files if name != '_headers']
        paths += ['/', '/404', '/__stage1_missing_20261101__', '/regions',
                  '/__regional/dongjak/index.html', '/__regional/geumcheon/index.html']
        for path in paths:
            try:
                try:
                    require(time.monotonic() < deadline, 'public_probe_timeout')
                    response = opener.open('https://' + host + path, timeout=10)
                except HTTPError as error:
                    response = error
                with response:
                    body = response.read(2 * 1024 * 1024)
                    status = response.code
                    headers = {key: response.headers.get(key) for key in selected}
                require(status in [200, 307, 308, 404], 'public_response_unverified')
                if path == '/404.html':
                    require(status == 307 and headers['location'] == '/404' and body == b'', '404_redirect_mismatch')
                if path == '/404':
                    require(status == 200 and hashlib.sha256(body).hexdigest() == files['404.html'], 'canonical_404_mismatch')
                if path.startswith('/__'):
                    require(status == 404 and hashlib.sha256(body).hexdigest() == files['404.html'], 'missing_or_namespace_mismatch')
                if path == '/robots.txt':
                    require(status == 200 and b'Content-Signal: search=yes,ai-train=no,use=reference' in body
                            and body.endswith(b'\n\n' + original_robots), 'robots_policy_missing')
                if status == 200 and path.lstrip('/') in files and path != '/robots.txt':
                    require(hashlib.sha256(body).hexdigest() == files[path.lstrip('/')], 'public_asset_mismatch')
                result[host + path] = dict(status=status, headers=headers, sha256=hashlib.sha256(body).hexdigest())
            except Exception:
                raise Stop('public_verification_failed') from None
    return result


class Wrangler:
    def __init__(self, cli, bundle):
        self.cli, self.bundle = cli.resolve(), bundle.resolve()
        require(json.loads((self.cli.parent.parent / 'package.json').read_text())['version'] == '4.148.0', 'wrangler_version_mismatch')
        self.called = set()

    def run(self, operation):
        require(operation in ['deploy', 'rollback'] and operation not in self.called, 'mutation_retry_refused')
        self.called.add(operation)
        verify_bundle(self.bundle)
        args = ['node', str(self.cli), operation]
        if operation == 'rollback':
            args += [D_VERSION, '--name', DONGJAK]
        args += ['--config', str(self.bundle / 'wrangler.stage1.json')]
        env = {k: v for k, v in os.environ.items() if k not in ['CLOUDFLARE_API_KEY', 'CLOUDFLARE_EMAIL']}
        env.update(WRANGLER_SEND_METRICS='false', WRANGLER_LOG_SANITIZE='true', CI='true')
        try:
            proc = subprocess.run(args, cwd=self.bundle, env=env, capture_output=True, text=True, timeout=180)
            ids = re.findall(r'Current Version ID:\s*([a-f0-9-]{36})', proc.stdout)
            pilot = ids[0] if len(set(ids)) == 1 and ids and valid_uuid(ids[0]) else None
            return {'ok': proc.returncode == 0, 'uuid': pilot}
        except Exception:
            return {'ok': False, 'uuid': None}


def execute(provider, runner, probe, record):
    """Injectable state machine; one deploy maximum, one guarded rollback maximum."""
    original = provider.snapshot()
    check_state(original, D_VERSION)
    baseline = probe()
    check_state(provider.snapshot(), D_VERSION, original)  # last read before mutation
    record('deploy_started')
    outcome = runner.run('deploy')
    pilot = outcome.get('uuid')
    if not valid_uuid(pilot) or pilot == D_VERSION:
        # Reconcile read-only even if failed process may have deployed; never infer ownership.
        try:
            provider.snapshot()
            record('uncertain_deploy_readback_obtained')
        except Exception:
            record('uncertain_deploy_readback_failed')
        raise Stop('deploy_uuid_uncertain_no_retry_or_rollback')
    record('pilot_recorded', pilot_uuid=pilot)
    postdeploy = None
    try:
        postdeploy = provider.snapshot()
        check_state(postdeploy, pilot, original)
        require(outcome['ok'], 'deploy_reported_failure_with_known_uuid')
        require(probe() == baseline, 'postdeploy_public_difference')
        check_state(provider.snapshot(), pilot, original)
        record('pilot_verified', pilot_uuid=pilot)
        return 'pilot_verified'
    except Exception:
        record('postdeploy_failed')
        # A fresh read must prove ownership before ANY rollback; conflicts remain untouched.
        current = provider.snapshot()
        require(current[DONGJAK]['version'] == pilot and current[GEUMCHEON]['version'] == G_VERSION, 'rollback_conflict_stop')
        require(postdeploy is not None and postdeploy[DONGJAK]['version'] == pilot,
                'rollback_postdeploy_baseline_unavailable')
        # Geumcheon was never modified by this deployment. Dongjak may have an
        # initial deployment error, but further settings drift is not ours to undo.
        require(postdeploy[GEUMCHEON] == original[GEUMCHEON]
                and current[GEUMCHEON] == original[GEUMCHEON], 'rollback_geumcheon_settings_drift')
        require(current[DONGJAK] == postdeploy[DONGJAK], 'rollback_dongjak_settings_drift')
        record('rollback_started', pilot_uuid=pilot)
        restored = runner.run('rollback')
        check_state(provider.snapshot(), D_VERSION, original)
        require(probe() == baseline, 'rollback_public_difference')
        record('rollback_verified', command_success=restored['ok'])
        return 'rolled_back'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute-reviewed-stage1', action='store_true')
    parser.add_argument('--bundle', type=Path, required=True)
    parser.add_argument('--wrangler', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--remaining-requests', type=int, required=True)
    parser.add_argument('--usage-observed-at', required=True)
    args = parser.parse_args()
    report = {'events': [], 'status': 'not_started'}
    def record(event, **fields):
        report['events'].append(dict(event=event, utc=datetime.now(timezone.utc).isoformat(), **fields))
        args.report.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    try:
        require(args.execute_reviewed_stage1 and os.environ.get('GITHUB_ACTIONS') == 'true'
                and os.environ.get('GITHUB_REPOSITORY') == 'joseungil-kr/fwith-site-factory'
                and os.environ.get('GITHUB_RUN_ATTEMPT') == '1', 'execution_not_armed')
        observed = datetime.fromisoformat(args.usage_observed_at.replace('Z', '+00:00'))
        age = (datetime.now(timezone.utc) - observed).total_seconds()
        require(0 <= age <= 900 and 20000 <= args.remaining_requests <= 100000, 'capacity_observation_stale_or_low')
        verify_bundle(args.bundle)
        report['status'] = execute(Provider(record), Wrangler(args.wrangler, args.bundle), public_snapshot, record)
    except Stop as error:
        report['status'] = 'stopped'
        report['reason'] = str(error)  # only our fixed codes, never provider bodies
    except Exception:
        report['status'] = 'stopped'
        report['reason'] = 'unexpected_error_redacted'
    record('finished')
    print(json.dumps({'status': report['status']}))
    return 0 if report['status'] == 'pilot_verified' else 1


if __name__ == '__main__':
    raise SystemExit(main())
