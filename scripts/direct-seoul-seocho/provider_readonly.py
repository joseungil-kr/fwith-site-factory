"""Exact Seocho inventory, using existing credentials and three GET endpoints only.

No DNS/route/script-content/token-identity reads; no mutation transport exists.
The result never asserts DNS ownership or grants permission to attach a hostname.
"""
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import HTTPRedirectHandler, Request, build_opener

REPOSITORY = 'joseungil-kr/fwith-site-factory'
OWNER = 'joseungil-kr'
HOSTNAME = 'seoul-seocho.fwith.kr'
WORKER = 'seoul-seocho-flower-guide'
TITLE = '[SEOCHO-PROVIDER-READONLY] 20261014'
LIMIT = 1024 * 1024


class Rejected(Exception):
    pass


def require(value, code):
    if not value:
        raise Rejected(code)


def authorize(env, event):
    require(env.get('GITHUB_REPOSITORY') == REPOSITORY and env.get('GITHUB_REF') == 'refs/heads/main', 'wrong_repository_or_ref')
    require(env.get('GITHUB_ACTOR') == OWNER and env.get('GITHUB_RUN_ATTEMPT') == '1', 'wrong_actor_or_rerun')
    require(env.get('GITHUB_EVENT_NAME') == 'issues' and event.get('action') == 'opened', 'wrong_event')
    repository = event.get('repository', {})
    require(repository.get('full_name') == REPOSITORY and repository.get('owner', {}).get('login') == OWNER
            and repository.get('owner', {}).get('type') == 'User', 'wrong_repository_owner')
    issue = event.get('issue', {})
    require(issue.get('title') == TITLE and issue.get('user', {}).get('login') == OWNER, 'wrong_issue_owner_or_title')
    require(isinstance(issue.get('body'), str) and len(issue['body']) < 2048, 'invalid_request_body')
    try:
        body = json.loads(issue['body'])
    except (ValueError, TypeError):
        raise Rejected('invalid_request_json') from None
    revision = env.get('GITHUB_SHA', '')
    require(re.fullmatch(r'[0-9a-f]{40}', revision) is not None, 'invalid_control_revision')
    require(isinstance(body, dict) and type(body.get('schemaVersion')) is int and body.get('read_only') is True,
            'request_types_invalid')
    require(body == {'schemaVersion': 1, 'expected_control_revision': revision,
                     'hostname': HOSTNAME, 'worker': WORKER, 'read_only': True}, 'request_contract_mismatch')
    return revision


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise Rejected('provider_redirect_forbidden')


def make_transport(account, token, statuses):
    require(re.fullmatch(r'[0-9a-fA-F]{32}', account or '') is not None, 'invalid_account_configuration')
    require(isinstance(token, str) and token and token == token.strip() and '\r' not in token and '\n' not in token,
            'invalid_token_configuration')
    prefix = '/accounts/' + account
    allowed = {prefix: 'account', prefix + '/workers/scripts': 'scripts', prefix + '/workers/domains': 'domains'}
    opener = build_opener(NoRedirect())

    def transport(method, path, body=None):
        require(method == 'GET' and path in allowed and body is None, 'provider_operation_forbidden')
        name = allowed[path]
        request = Request('https://api.cloudflare.com/client/v4' + path, method='GET',
                          headers={'Authorization': 'Bearer ' + token, 'Accept': 'application/json'})
        try:
            with opener.open(request, timeout=20) as response:
                statuses[name] = response.status
                require(response.status == 200, 'provider_http_unverified')
                raw = response.read(LIMIT + 1)
        except HTTPError as error:
            statuses[name] = error.code
            error.close()
            raise Rejected('provider_http_unverified') from None
        except Rejected:
            raise
        except Exception:
            raise Rejected('provider_transport_unverified') from None
        require(len(raw) <= LIMIT, 'provider_response_limit')
        try:
            value = json.loads(raw)
        except (ValueError, TypeError):
            raise Rejected('provider_json_invalid') from None
        require(isinstance(value, dict) and value.get('success') is True and value.get('errors') in (None, []),
                'provider_payload_unverified')
        return value
    return transport


def single_page(payload):
    require(isinstance(payload, dict) and payload.get('success') is True and payload.get('errors') in (None, []),
            'inventory_payload_invalid')
    rows, info = payload.get('result'), payload.get('result_info', {})
    require(isinstance(rows, list) and all(isinstance(row, dict) for row in rows) and isinstance(info, dict), 'inventory_shape_invalid')
    defaults = {'page': 1, 'total_pages': 1 if rows else 0, 'count': len(rows), 'total_count': len(rows), 'per_page': len(rows)}
    for key, default in defaults.items():
        value = info.get(key, default)
        require(type(value) is int and value >= 0, 'inventory_pagination_invalid')
    require(info.get('page', 1) == 1 and info.get('total_pages', 1) in ({0, 1} if not rows else {1})
            and info.get('count', len(rows)) == len(rows) and info.get('total_count', len(rows)) == len(rows)
            and info.get('per_page', len(rows)) >= len(rows), 'inventory_incomplete')
    return rows


def inspect(account, transport):
    prefix = '/accounts/' + account
    response = transport('GET', prefix)
    require(isinstance(response, dict) and response.get('success') is True and response.get('errors') in (None, [])
            and isinstance(response.get('result'), dict) and response['result'].get('id') == account,
            'account_identity_unverified')
    scripts = single_page(transport('GET', prefix + '/workers/scripts'))
    names = [row.get('id') for row in scripts]
    require(all(isinstance(name, str) and name for name in names) and len(names) == len(set(names)), 'script_inventory_invalid')
    domains = single_page(transport('GET', prefix + '/workers/domains'))
    require(all(isinstance(row.get('hostname'), str) and row['hostname'] and isinstance(row.get('service'), str)
                and row['service'] for row in domains), 'domain_inventory_invalid')
    matches = [row for row in domains if row['hostname'].lower() == HOSTNAME or row['service'] == WORKER]
    exact = len(matches) == 1 and matches[0]['hostname'].lower() == HOSTNAME and matches[0]['service'] == WORKER
    require(not matches or exact, 'hostname_or_worker_collision')
    exists = WORKER in names
    require(not exact or exists, 'binding_without_worker')
    if exact:
        row = matches[0]
        require(row.get('environment', 'production') == 'production' and row.get('zone_name', 'fwith.kr') == 'fwith.kr'
                and row.get('enabled', True) is True and row.get('previews_enabled', False) is False, 'binding_configuration_mismatch')
    return {'state': 'exact_binding_observed' if exact else 'worker_present_unbound' if exists else 'target_absent_observed',
            'accountVerified': True, 'workerExists': exists, 'hostnameBindingExists': exact,
            'hostname': HOSTNAME, 'worker': WORKER, 'dnsOwnershipVerified': False,
            'publicationAuthorizedByThisReport': False, 'mutationsPerformed': False}


def main():
    report = {'state': 'unknown', 'hostname': HOSTNAME, 'worker': WORKER, 'mutationsPerformed': False,
              'dnsOwnershipVerified': False, 'publicationAuthorizedByThisReport': False, 'httpStatus': {}}
    mode = sys.argv[1] if len(sys.argv) == 2 else ''
    try:
        require(mode in {'authorize', 'inspect'}, 'invalid_mode')
        event = json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text(encoding='utf-8'))
        report['controlRevision'] = authorize(os.environ, event)
        if mode == 'inspect':
            account = os.environ.get('CLOUDFLARE_ACCOUNT_ID', '')
            transport = make_transport(account, os.environ.get('CLOUDFLARE_API_TOKEN', ''), report['httpStatus'])
            report.update(inspect(account, transport))
        else:
            print('Exact owner/main/first-attempt read-only request authorized')
            return 0
    except Rejected as error:
        report['errorCode'] = str(error)
    except Exception:
        report['errorCode'] = 'read_only_inspection_unverified'
    report['checkedAtUTC'] = datetime.now(timezone.utc).isoformat()
    Path('seoul-seocho-provider-readonly.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, sort_keys=True))
    return 1 if 'errorCode' in report else 0


if __name__ == '__main__':
    raise SystemExit(main())
