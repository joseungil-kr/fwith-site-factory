"""Redacted identity of the exact existing Seocho upload. GET transport only.

This observes provider version metadata, not a proof of Git/source asset equality.
The existing provider_readonly account/inventory/collision checks remain unchanged.
"""
import copy
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, build_opener

import provider_readonly as base

Rejected, require = base.Rejected, base.require
HOSTNAME, WORKER = base.HOSTNAME, base.WORKER
TITLE = '[SEOCHO-UPLOADED-IDENTITY-READONLY] 20261014'
SOURCE_SHA = '52741146f4147f64d6804a757f560db0acf0d92c'
PRIOR_RUN_ID = '38532307939'
UUID = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
SOURCES = {'api', 'wrangler', 'dash', 'dashboard', 'terraform', 'unknown', 'pages', 'version_upload', 'deployment'}
HANDLERS = {'fetch', 'scheduled', 'queue', 'email', 'tail', 'trace', 'test', 'alarm',
            'webSocketMessage', 'webSocketClose', 'webSocketError', 'connect'}
BINDINGS = {'assets', 'plain_text', 'secret_text', 'kv_namespace', 'durable_object_namespace',
            'r2_bucket', 'd1', 'service', 'queue', 'analytics_engine', 'hyperdrive', 'ai',
            'browser', 'version_metadata', 'dispatch_namespace', 'send_email', 'mtls_certificate',
            'images', 'workflow', 'vectorize', 'wasm_module', 'text_blob', 'data_blob', 'unsafe',
            'inherit', 'rate_limit', 'secrets_store_secret', 'vpc_service', 'logfwdr'}


def authorize(env, event):
    require(isinstance(event, dict) and isinstance(event.get('issue'), dict), 'invalid_event')
    issue = event['issue']
    require(issue.get('title') == TITLE, 'wrong_issue_title')
    require(isinstance(issue.get('body'), str) and len(issue['body']) < 2048, 'invalid_request_body')
    try:
        body = json.loads(issue['body'])
    except (ValueError, TypeError):
        raise Rejected('invalid_request_json') from None
    require(isinstance(body, dict) and body.get('expected_source_revision') == SOURCE_SHA
            and body.get('prior_upload_run_id') == PRIOR_RUN_ID, 'wrong_source_or_prior_run')
    body = dict(body)
    del body['expected_source_revision'], body['prior_upload_run_id']
    canonical = copy.deepcopy(event)
    canonical['issue']['title'] = base.TITLE
    canonical['issue']['body'] = json.dumps(body)
    revision = base.authorize(env, canonical)
    require(re.fullmatch(r'[1-9][0-9]{0,19}', env.get('GITHUB_RUN_ID', '')) is not None, 'invalid_inspection_run')
    return revision


def result(payload):
    require(isinstance(payload, dict) and payload.get('success') is True
            and payload.get('errors') in (None, []) and isinstance(payload.get('result'), dict),
            'identity_payload_invalid')
    return payload['result']


def timestamp(value):
    require(isinstance(value, str) and re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,9})?(?:Z|[+-]\d{2}:\d{2})', value) is not None,
            'identity_timestamp_invalid')
    try:
        datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError:
        raise Rejected('identity_timestamp_invalid') from None
    return value


def uuid(value):
    require(isinstance(value, str) and re.fullmatch(UUID, value) is not None, 'identity_uuid_invalid')
    return value


def opaque_field(data, key):
    """Fingerprint an optional provider value without assuming a digest encoding.

    SHA256 covers canonical JSON, not script content or deployed asset bytes.
    No original value is returned, including opaque strings or unexpected types.
    """
    if key not in data:
        return {'present': False, 'type': 'absent', 'length': None, 'sha256': None, 'isEmpty': None}
    value = data[key]
    types = {str: 'string', type(None): 'null', bool: 'boolean', int: 'number', float: 'number', list: 'array', dict: 'object'}
    require(type(value) in types, 'opaque_metadata_invalid')
    try:
        encoded = json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode('utf-8')
    except (ValueError, TypeError):
        raise Rejected('opaque_metadata_invalid') from None
    return {'present': True, 'type': types[type(value)], 'length': len(value) if isinstance(value, str) else None,
            'sha256': hashlib.sha256(encoded).hexdigest(), 'isEmpty': value is None or value == ''}


def handlers_field(data):
    value = data.get('handlers')
    identity = opaque_field(data, 'handlers')
    known = None
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        known = sorted({item if item in HANDLERS else 'unrecognized' for item in value})
    return {'present': identity['present'], 'type': identity['type'], 'sha256': identity['sha256'],
            'count': len(value) if isinstance(value, list) else None, 'knownValues': known}


def canonical_sha256(value):
    try:
        encoded = json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode('utf-8')
    except (ValueError, TypeError):
        raise Rejected('canonical_metadata_invalid') from None
    return hashlib.sha256(encoded).hexdigest()


def selected(data, fields):
    require(isinstance(data, dict), 'identity_object_invalid')
    out = {}
    for key in fields:
        if key == 'etag':
            out[key] = opaque_field(data, key)
            continue
        if key == 'handlers':
            out[key] = handlers_field(data)
            continue
        if key not in data:
            continue
        value = data[key]
        if key in {'created_on', 'modified_on'}:
            out[key] = timestamp(value)
        elif key == 'has_assets':
            require(type(value) is bool, 'identity_boolean_invalid')
            out[key] = value
        elif key in {'source', 'last_deployed_from'}:
            if value is None:
                out[key] = None
            elif isinstance(value, str):
                out[key] = value if value in SOURCES else 'unrecognized'
            else:
                out[key] = {'unrecognizedValue': opaque_field(data, key)}
    return out


def active_deployment(payload):
    value = result(payload)
    rows = value.get('deployments')
    require(isinstance(rows, list) and len(rows) == 1 and isinstance(rows[0], dict), 'active_deployment_ambiguous')
    info = payload.get('result_info')
    if info is not None:
        require(isinstance(info, dict), 'deployment_pagination_invalid')
        for key in ['page', 'per_page', 'count', 'total_count', 'total_pages']:
            if key in info:
                require(type(info[key]) is int and info[key] >= 0, 'deployment_pagination_invalid')
        require(info.get('page', 1) == 1 and info.get('per_page', 1) == 1 and info.get('count', 1) == 1
                and info.get('total_count', 1) >= 1 and info.get('total_pages', 1) >= 1, 'deployment_pagination_invalid')
    row = rows[0]
    require(row.get('strategy') == 'percentage', 'deployment_strategy_invalid')
    versions = row.get('versions')
    require(isinstance(versions, list) and len(versions) == 1 and isinstance(versions[0], dict), 'active_version_ambiguous')
    version = versions[0]
    require(type(version.get('percentage')) in (int, float) and version['percentage'] == 100, 'active_version_not_full_traffic')
    out = {'id': uuid(row.get('id')), 'created_on': timestamp(row.get('created_on')),
           'strategy': 'percentage', 'versions': [{'version_id': uuid(version.get('version_id')), 'percentage': 100}]}
    out.update(selected(row, ['source']))
    return out


def binding_types(value):
    if value is None:
        return []
    require(isinstance(value, (list, dict)), 'bindings_shape_invalid')
    rows = list(value.values()) if isinstance(value, dict) else value
    require(len(rows) <= 256 and all(isinstance(row, dict) and isinstance(row.get('type'), str) for row in rows), 'bindings_shape_invalid')
    return sorted({row['type'] if row['type'] in BINDINGS else 'unrecognized' for row in rows})


def assets(value):
    out = {'present': value is not None, 'type': 'null' if value is None else 'object',
           'configuration': {}, 'hashes': {}, 'allowedFieldTypes': {}, 'omittedFieldCount': 0}
    if value is None:
        return out
    require(isinstance(value, dict), 'assets_shape_invalid')
    config = value.get('config', value.get('configuration', {}))
    require(isinstance(config, dict), 'assets_configuration_invalid')
    allowed = {'html_handling': {'auto-trailing-slash', 'force-trailing-slash', 'drop-trailing-slash', 'none'},
               'not_found_handling': {'none', '404-page', 'single-page-application'}}
    for key in ['hash', 'etag']:
        if key in value:
            out['hashes'][key] = opaque_field(value, key)
            out['allowedFieldTypes'][key] = out['hashes'][key]['type']
    for key in ['config', 'configuration']:
        if key in value:
            out['allowedFieldTypes'][key] = type(value[key]).__name__
    for key, options in allowed.items():
        if key in config:
            require(isinstance(config[key], str) and config[key] in options, 'assets_configuration_invalid')
            out['configuration'][key] = config[key]
    if 'run_worker_first' in config:
        # A path list is intentionally not emitted; only its type is retained.
        val = config['run_worker_first']
        require(type(val) is bool or (isinstance(val, list) and all(isinstance(x, str) for x in val)), 'assets_configuration_invalid')
        out['allowedFieldTypes']['config.run_worker_first'] = 'boolean' if type(val) is bool else 'array'
        if type(val) is bool:
            out['configuration']['run_worker_first'] = val
    out['omittedFieldCount'] = len(set(value) - {'hash', 'etag', 'config', 'configuration'}) + len(set(config) - set(allowed) - {'run_worker_first'})
    return out


def make_transport(account, token, statuses):
    require(re.fullmatch(r'[0-9a-fA-F]{32}', account or '') is not None, 'invalid_account_configuration')
    require(isinstance(token, str) and token and token == token.strip() and '\r' not in token and '\n' not in token,
            'invalid_token_configuration')
    prefix = '/accounts/' + account
    worker = prefix + '/workers/scripts/' + WORKER
    deployment_path = worker + '/deployments?page=1&per_page=1'
    allowed = {prefix: 'account', prefix + '/workers/scripts': 'scripts', prefix + '/workers/domains': 'domains',
               deployment_path: 'deployments', worker + '/settings': 'settings', worker + '/subdomain': 'subdomain'}
    opener = build_opener(base.NoRedirect())

    def transport(method, path, body=None):
        require(method == 'GET' and path in allowed and body is None, 'provider_operation_forbidden')
        name = allowed[path]
        request = Request('https://api.cloudflare.com/client/v4' + path, method='GET',
                          headers={'Authorization': 'Bearer ' + token, 'Accept': 'application/json'})
        try:
            with opener.open(request, timeout=20) as response:
                statuses[name] = response.status
                require(response.status == 200, 'provider_http_unverified')
                raw = response.read(base.LIMIT + 1)
        except HTTPError as error:
            statuses[name] = error.code
            error.close()
            raise Rejected('provider_http_unverified') from None
        except Rejected:
            raise
        except Exception:
            raise Rejected('provider_transport_unverified') from None
        require(len(raw) <= base.LIMIT, 'provider_response_limit')
        try:
            value = json.loads(raw)
        except (ValueError, TypeError):
            raise Rejected('provider_json_invalid') from None
        require(isinstance(value, dict) and value.get('success') is True and value.get('errors') in (None, []), 'provider_payload_unverified')
        if path == deployment_path:
            deployment = active_deployment(value)
            # The only version GET is derived from this exact script's validated active deployment.
            for old in [p for p in allowed if allowed[p] == 'version']:
                del allowed[old]
            allowed[worker + '/versions/' + deployment['versions'][0]['version_id']] = 'version'
        return value
    return transport


def inspect(account, transport, report=None):
    report = {} if report is None else report
    script_rows = []
    domain_rows = []
    def capture(method, path, body=None):
        payload = transport(method, path, body)
        if path == '/accounts/' + account + '/workers/scripts':
            script_rows.extend(base.single_page(payload))
        if path == '/accounts/' + account + '/workers/domains':
            domain_rows.extend(base.single_page(payload))
        return payload
    inventory = base.inspect(account, capture)
    report.update({**inventory, 'state': 'uploaded_worker_identity_partial',
                   'uploadedContentMatchesExpectedSource': False, 'publicHTTPVerified': False,
                   'identityLimitation': 'Provider version metadata does not establish Git revision or exact deployed asset bytes.'})
    require(inventory['workerExists'], 'uploaded_worker_absent')
    raw_script = next(row for row in script_rows if row['id'] == WORKER)
    script = {'id': WORKER}
    report['script'] = script
    # Optional inventory metadata must not prevent the independent exact GETs.
    for field in ['etag', 'created_on', 'modified_on', 'has_assets', 'last_deployed_from']:
        try:
            script.update(selected(raw_script, [field]))
        except Rejected as error:
            report.setdefault('scriptMetadataErrors', {})[field] = str(error)
    exact_domains = [row for row in domain_rows if row['hostname'].lower() == HOSTNAME and row['service'] == WORKER]
    if exact_domains:
        row = exact_domains[0]
        # Missing optional provider fields are recorded as missing, never promoted to observed facts.
        fields = ['environment', 'zone_name', 'enabled', 'previews_enabled']
        report['hostnameBindingDetails'] = {'hostname': HOSTNAME, 'service': WORKER,
            'observedFields': {key: row[key] for key in fields if key in row},
            'allOptionalFieldsPresent': all(key in row for key in fields)}
    worker_path = '/accounts/' + account + '/workers/scripts/' + WORKER
    errors = {}
    # Independent GETs first: assets-only/unsupported version reads still retain useful observations.
    try:
        raw_settings = result(transport('GET', worker_path + '/settings'))
        report['rawSettingsSha256'] = canonical_sha256(raw_settings)
        report['settings'] = {'assets': assets(raw_settings.get('assets')), 'bindingTypes': binding_types(raw_settings.get('bindings'))}
    except Rejected as error:
        errors['settings'] = str(error)
    try:
        raw_subdomain = result(transport('GET', worker_path + '/subdomain'))
        require(type(raw_subdomain.get('enabled')) is bool and type(raw_subdomain.get('previews_enabled')) is bool, 'subdomain_shape_invalid')
        report['subdomain'] = {key: raw_subdomain[key] for key in ['enabled', 'previews_enabled']}
    except Rejected as error:
        errors['subdomain'] = str(error)
    try:
        deployment = active_deployment(transport('GET', worker_path + '/deployments?page=1&per_page=1'))
        report['deployment'] = deployment
    except Rejected as error:
        errors['deployments'] = str(error)
        report['inspectionErrors'] = errors
        raise Rejected('uploaded_identity_incomplete') from None
    version_id = deployment['versions'][0]['version_id']
    try:
        raw_version = result(transport('GET', worker_path + '/versions/' + version_id))
        report['rawVersionSha256'] = canonical_sha256(raw_version)
        inspect_version(raw_version, version_id, script, report)
    except Rejected as error:
        errors['version'] = str(error)
    if errors:
        report['inspectionErrors'] = errors
        raise Rejected('uploaded_identity_incomplete') from None
    report['state'] = 'uploaded_worker_identity_observed'
    return report


def inspect_version(raw_version, version_id, script, report=None):
    require(raw_version.get('id') == version_id and type(raw_version.get('number')) is int and raw_version['number'] >= 1, 'version_identity_mismatch')
    version = {'id': version_id, 'number': raw_version['number'], 'metadata': {}}
    if report is not None:
        report['version'] = version
    metadata = raw_version.get('metadata')
    require(isinstance(metadata, dict), 'version_metadata_invalid')
    # Creation time is required provenance; preserve it before optional fields.
    version['metadata']['created_on'] = timestamp(metadata.get('created_on'))
    resources = raw_version.get('resources')
    require(isinstance(resources, dict), 'version_resources_invalid')
    raw_script = resources.get('script')
    require(raw_script is None or isinstance(raw_script, dict), 'version_resources_invalid')
    version['script'] = {}
    version['scriptRepresentation'] = opaque_field(resources, 'script')
    for target, data, fields in [(version['metadata'], metadata, ['modified_on', 'source']),
                                 (version['script'], raw_script or {}, ['etag', 'handlers', 'last_deployed_from'])]:
        for field in fields:
            try:
                if field == 'modified_on' and field in data and data[field] is None:
                    target[field] = None
                else:
                    target.update(selected(data, [field]))
            except Rejected as error:
                version.setdefault('optionalMetadataErrors', {})[field] = str(error)
    version['assets'] = assets(resources.get('assets'))
    version['bindingTypes'] = binding_types(resources.get('bindings'))
    return version


def main():
    report = {'schemaVersion': 1, 'state': 'unknown', 'hostname': HOSTNAME, 'worker': WORKER,
              'mutationsPerformed': False, 'publicationAuthorizedByThisReport': False,
              'dnsOwnershipVerified': False, 'publicHTTPVerified': False,
              'uploadedContentMatchesExpectedSource': False, 'httpStatus': {}}
    try:
        mode = sys.argv[1] if len(sys.argv) == 2 else ''
        require(mode in {'authorize', 'inspect'}, 'invalid_mode')
        event = json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text(encoding='utf-8'))
        report['controlRevision'] = authorize(os.environ, event)
        report['inspectionRunId'] = os.environ['GITHUB_RUN_ID']
        report['inspectionRunAttempt'] = 1
        report['expectedSourceRevision'] = SOURCE_SHA
        report['priorUploadContext'] = {'runId': PRIOR_RUN_ID, 'startedAtUTC': '2026-10-14T08:02:23Z',
                                      'endedAtUTC': '2026-10-14T08:02:36Z', 'identityMatchEstablished': False}
        if mode == 'authorize':
            print('Exact owner/main/first-attempt uploaded identity read-only request authorized')
            return 0
        account = os.environ.get('CLOUDFLARE_ACCOUNT_ID', '')
        transport = make_transport(account, os.environ.get('CLOUDFLARE_API_TOKEN', ''), report['httpStatus'])
        inspect(account, transport, report)
    except Rejected as error:
        report['errorCode'] = str(error)
    except Exception:
        report['errorCode'] = 'uploaded_identity_unverified'
    report['checkedAtUTC'] = datetime.now(timezone.utc).isoformat()
    Path('seoul-seocho-uploaded-identity.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, sort_keys=True))
    return 1 if 'errorCode' in report else 0


if __name__ == '__main__':
    raise SystemExit(main())
