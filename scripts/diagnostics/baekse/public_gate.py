"""One-pass public correctness gate; no authentication, writes, retry or fallback."""
import hashlib
import json
import pathlib
import re
import sys
import urllib.error
import urllib.request

BASE = 'https://order.baeksefood.com'
ASSETS = {'/':'index.html','/app.js':'app.js','/buyer.js':'buyer.js','/request/':'request/index.html'}
LIMIT = 2 * 1024 * 1024

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None

def diagnostic_headers(h):
    result = {}
    ray = h.get('CF-Ray', '')
    if re.fullmatch(r'[a-fA-F0-9]{8,32}(?:-[A-Z]{3})?', ray):
        result['cf-ray'] = ray
    for key, values in {'server': ('cloudflare','nginx'), 'cf-mitigated': ('challenge',)}.items():
        value = h.get(key, '')
        if value in values:
            result[key] = value
    return result

def gate(phase, source, opener=None, emit=print):
    if phase not in ('baseline', 'candidate'):
        raise ValueError('invalid phase')
    expected = {path: hashlib.sha256((pathlib.Path(source)/local).read_bytes()).hexdigest() for path, local in ASSETS.items()}
    opener = opener or urllib.request.build_opener(NoRedirect()).open
    for path in (*ASSETS, '/api/session'):
        row = {'phase':phase,'path':path}
        emit(json.dumps({**row, 'event':'request'}, sort_keys=True))
        try:
            with opener(BASE+path,timeout=30) as response:
                row.update(status=response.status,headers=diagnostic_headers(response.headers))
                if path == '/api/session':
                    row['error'] = 'anonymous_session_must_be_401'
                elif response.status != 200:
                    row['error'] = 'asset_status_not_200'
                else:
                    data = response.read(LIMIT+1)
                    if len(data)>LIMIT:
                        row['error']='asset_too_large'
                    else:
                        row['sha256']=hashlib.sha256(data).hexdigest()
                        if row['sha256']!=expected[path]:row['error']='asset_hash_mismatch'
                        elif 'noindex' not in response.headers.get('X-Robots-Tag',''):row['error']='missing_noindex'
                        elif 'no-store' not in response.headers.get('Cache-Control',''):row['error']='missing_no_store'
        except urllib.error.HTTPError as exc:
            row.update(status=exc.code,headers=diagnostic_headers(exc.headers))
            if path != '/api/session' or exc.code != 401:
                row['error']='unexpected_http_status'
            exc.close() # Do not read or emit error bodies.
        except Exception as exc:
            row['error']=type(exc).__name__ # No exception message or URL query.
        emit(json.dumps(row,sort_keys=True))
        if 'error' in row:return False
    emit(json.dumps({'phase':phase,'result':'PUBLIC_CORRECTNESS_GATE_PASS','requests':5},sort_keys=True))
    return True

if __name__=='__main__':
    if len(sys.argv)!=3:raise SystemExit('usage: public_gate.py baseline|candidate pinned-public-directory')
    try:
        passed=gate(sys.argv[1],sys.argv[2])
    except Exception as exc:
        print(json.dumps({'error':type(exc).__name__}))
        passed=False
    raise SystemExit(0 if passed else 1)
