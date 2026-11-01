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
import socket
import ssl
import subprocess
import time
import zipfile
from urllib.parse import urlsplit
from urllib.error import HTTPError, URLError
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
            allowed |= resource in [f'workers/scripts/{worker}/{suffix}' for suffix in ['deployments', 'settings', 'subdomain']]
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
            result = payload.get('result')
            # All endpoint diagnostics are structure only, never returned values.
            self.record('response_shape', endpoint=resource.split('?', 1)[0],
                        result_type=type(result).__name__, result_fields=sorted(result) if isinstance(result, dict) else [],
                        row_fields=sorted({key for row in result if isinstance(row, dict) for key in row}) if isinstance(result, list) else [],
                        result_count=len(result) if isinstance(result, list) else None,
                        nested_fields={key: sorted(value) for key, value in result.items() if isinstance(value, dict)} if isinstance(result, dict) else {},
                        list_item_fields={key: sorted({field for row in value if isinstance(row, dict) for field in row})
                                          for key, value in result.items() if isinstance(value, list)} if isinstance(result, dict) else {})
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
                    and matches[0].get('service') == worker
                    and matches[0].get('environment') == 'production', 'domain_mapping_drift')
            subdomain = self.get(f'workers/scripts/{worker}/subdomain')['result']
            require(subdomain.get('enabled') is False and subdomain.get('previews_enabled') is False, 'subdomain_exposure_unverified')
            deployments = self.get(f'workers/scripts/{worker}/deployments')['result']['deployments']
            require(isinstance(deployments, list) and bool(deployments), 'deployment_missing')
            latest = deployments[0]  # Official endpoint contract: first is actively serving.
            require(latest.get('strategy') == 'percentage', 'deployment_strategy_unverified')
            versions = latest['versions']
            require(len(versions) == 1 and versions[0]['percentage'] == 100
                    and valid_uuid(versions[0]['version_id']), 'active_version_unverified')
            active = versions[0]['version_id']
            for version_id in set([active, original]):
                version = self.get(f'workers/scripts/{worker}/versions/{version_id}')['result']
                require(version.get('id') == version_id, 'retained_version_unavailable')
            settings = self.get(f'workers/scripts/{worker}/settings')['result']
            state[worker] = dict(version=active, settings=settings, subdomain=subdomain,
                                 domain={key: matches[0][key] for key in ['hostname', 'service', 'environment']})
        return state


def check_state(state, expected_dongjak, baseline=None):
    for worker, expected in [(DONGJAK, expected_dongjak), (GEUMCHEON, G_VERSION)]:
        require(state[worker]['version'] == expected, 'concurrent_version_change')
        require(state[worker]['subdomain'].get('enabled') is False
                and state[worker]['subdomain'].get('previews_enabled') is False, 'subdomain_exposure_unverified')
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


def transport_evidence(error):
    reason = error.reason if isinstance(error, URLError) else error
    category = 'unclassified'
    if isinstance(reason, ssl.SSLCertVerificationError):
        category = 'tls_certificate'
    elif isinstance(reason, ssl.SSLError):
        category = 'tls'
    elif isinstance(reason, socket.gaierror):
        category = 'name_resolution'
    elif isinstance(reason, TimeoutError):
        category = 'timeout'
    elif isinstance(reason, ConnectionError):
        category = 'connection'
    elif isinstance(reason, OSError):
        category = 'os_transport'
    result = dict(transport_category=category, underlying_type=type(reason).__name__)
    for name in ['errno', 'winerror', 'verify_code']:
        value = getattr(reason, name, None)
        if type(value) is int:
            result[name] = value
    return result


def public_snapshot(record=lambda *args, **kwargs: None):
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
            evidence = dict(url='https://' + host + path, status=None, actual_sha256=None,
                            expected_sha256=files.get(path.lstrip('/')), redirect=None)
            if path == '/404' or path.startswith('/__'):
                evidence['expected_sha256'] = files['404.html']
            if path == '/404.html':
                evidence['expected_sha256'] = hashlib.sha256(b'').hexdigest()
            if path == '/robots.txt':
                evidence['expected_sha256'] = None  # Managed prefix is not fixed bytes.
                evidence['expected_original_sha256'] = hashlib.sha256(original_robots).hexdigest()
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
                evidence.update(status=status, actual_sha256=hashlib.sha256(body).hexdigest())
                location = headers.get('location')
                if location:
                    target = urlsplit(location)
                    allowed = target.hostname in HOSTS.values() or (not target.netloc and location.startswith('/'))
                    evidence['redirect'] = (target.scheme + '://' + target.netloc if target.netloc else '') + target.path if allowed and target.path in paths else '[redacted_unexpected_target]'
                if path == '/robots.txt':
                    evidence['original_suffix_matches'] = body.endswith(b'\n\n' + original_robots)
                    evidence['managed_policy_present'] = b'Content-Signal: search=yes,ai-train=no,use=reference' in body
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
            except Exception as error:
                record('public_probe_failed', **evidence, **transport_evidence(error), exception_type=type(error).__name__,
                       reason=str(error) if isinstance(error, Stop) else 'transport_or_response_error')
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


def diagnose_readonly(provider, record):
    """Collect all allowlisted schema evidence even if one endpoint is unavailable.

    No Wrangler, subprocess or public probe; check the collected GET snapshot only.
    """
    cache = {}
    paths = ['workers/domains']
    for worker, host in HOSTS.items():
        paths += [f'workers/domains?hostname={host}', f'workers/domains?service={worker}']
        paths += [f'workers/scripts/{worker}/{suffix}' for suffix in ['deployments', 'settings', 'subdomain']]
        paths += [f'workers/scripts/{worker}/versions/{ORIGINALS[worker]}']
    for path in paths:
        try:
            cache[path] = provider.get(path)
            if path.endswith('/deployments'):
                worker = path.split('/')[2]
                rows = cache[path]['result']['deployments']
                for entry in rows[0]['versions'] if rows else []:
                    version = entry.get('version_id')
                    if valid_uuid(version) and version != ORIGINALS[worker]:
                        extra = f'workers/scripts/{worker}/versions/{version}'
                        cache[extra] = provider.get(extra)
        except Exception:
            record('diagnostic_get_failed', endpoint=path.split('?', 1)[0])
    cached_provider = object.__new__(Provider)
    cached_provider.get = lambda path: cache[path]
    try:
        snapshot = cached_provider.snapshot()
        check_state(snapshot, D_VERSION)
        record('diagnostic_snapshot_verified')
        return 'diagnostic_verified'
    except Stop as error:
        record('diagnostic_snapshot_stopped', reason=str(error))
    except Exception:
        record('diagnostic_snapshot_stopped', reason='missing_or_unexpected_schema')
    return 'diagnostic_stopped'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--execute-reviewed-stage1', action='store_true')
    mode.add_argument('--diagnose-readonly', action='store_true')
    mode.add_argument('--public-preflight-readonly', action='store_true')
    parser.add_argument('--bundle', type=Path)
    parser.add_argument('--wrangler', type=Path)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--remaining-requests', type=int)
    parser.add_argument('--usage-observed-at')
    args = parser.parse_args()
    report = {'events': [], 'status': 'not_started'}
    def record(event, **fields):
        report['events'].append(dict(event=event, utc=datetime.now(timezone.utc).isoformat(), **fields))
        args.report.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    try:
        if args.public_preflight_readonly:
            public_snapshot(record)
            report['status'] = 'public_preflight_verified'
            record('finished')
            return 0
        require((args.execute_reviewed_stage1 or args.diagnose_readonly) and os.environ.get('GITHUB_ACTIONS') == 'true'
                and os.environ.get('GITHUB_REPOSITORY') == 'joseungil-kr/fwith-site-factory'
                and os.environ.get('GITHUB_RUN_ATTEMPT') == '1', 'execution_not_armed')
        if args.diagnose_readonly:
            report['status'] = diagnose_readonly(Provider(record), record)
        else:
            require(args.bundle is not None and args.wrangler is not None and args.usage_observed_at is not None
                    and args.remaining_requests is not None, 'execution_inputs_missing')
            observed = datetime.fromisoformat(args.usage_observed_at.replace('Z', '+00:00'))
            age = (datetime.now(timezone.utc) - observed).total_seconds()
            require(0 <= age <= 900 and 20000 <= args.remaining_requests <= 100000, 'capacity_observation_stale_or_low')
            verify_bundle(args.bundle)
            report['status'] = execute(Provider(record), Wrangler(args.wrangler, args.bundle), lambda: public_snapshot(record), record)
    except Stop as error:
        report['status'] = 'stopped'
        report['reason'] = str(error)  # only our fixed codes, never provider bodies
    except Exception:
        report['status'] = 'stopped'
        report['reason'] = 'unexpected_error_redacted'
    record('finished')
    print(json.dumps({'status': report['status']}))
    return 0 if report['status'] in ['pilot_verified', 'diagnostic_verified'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
