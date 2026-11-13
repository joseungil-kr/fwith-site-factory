"""Local proposal only. One pass, no retries, no deployment or authentication.

Run only after authorization for the specific read-only observation. An existing
denial must not be retried by using this helper. Never substitute diagnostics
for the production hash/header assertions in the release gate.
"""
import hashlib
import json
import urllib.error
import urllib.request

BASE = 'https://order.baeksefood.com'
PATHS = ('/', '/app.js', '/buyer.js', '/request/')
HEADERS = ('server', 'cf-ray', 'cf-mitigated', 'content-type')

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Do not follow an unexpected destination or transmit any URL query.
        return None

def _headers(headers):
    # Only diagnostic headers: never Cookie, Authorization or Set-Cookie.
    return {key: str(headers.get(key))[:256] for key in HEADERS if headers.get(key)}

def observe(phase, opener=None, emit=print):
    if phase not in ('baseline', 'candidate'):
        raise ValueError('phase must be baseline or candidate')
    opener = opener or urllib.request.build_opener(NoRedirect()).open
    results = []
    for path in PATHS:
        emit(json.dumps({'phase': phase, 'path': path, 'event': 'request'}, sort_keys=True))
        try:
            # No UA impersonation, cookies, auth headers, proxy or retry fallback.
            with opener(BASE + path, timeout=30) as response:
                status = response.status
                data = response.read(2 * 1024 * 1024 + 1)
                row = {'phase': phase, 'path': path, 'status': status,
                       'headers': _headers(response.headers)}
                if len(data) > 2 * 1024 * 1024:
                    row['error'] = 'response_too_large'
                elif status == 200:
                    row['sha256'] = hashlib.sha256(data).hexdigest()
                    row['bytes'] = len(data)
        except urllib.error.HTTPError as exc:
            row = {'phase': phase, 'path': path, 'status': exc.code,
                   'headers': _headers(exc.headers)}
            # Error bodies may include IPs, request context or challenge tokens.
            # Do not read/log/hash them; close immediately and stop this pass.
            exc.close()
        except Exception as exc:
            # Never print repr/str(exc), since URLs might carry sensitive data.
            row = {'phase': phase, 'path': path, 'error': type(exc).__name__}
        results.append(row)
        emit(json.dumps(row, sort_keys=True))
        if row.get('status') != 200 or 'error' in row:
            break
    passed = len(results) == len(PATHS) and all(r.get('status') == 200 and 'error' not in r for r in results)
    return {'phase': phase, 'http_observation_passed': passed, 'results': results}

if __name__ == '__main__':
    raise SystemExit('Import observe() only for an explicitly authorized observation; no network is run by default.')
