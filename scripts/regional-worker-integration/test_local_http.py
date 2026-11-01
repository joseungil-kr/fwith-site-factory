"""Compare running local workerd bundle :8787 with assets-only :8788/:8789."""
import hashlib
import http.client
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / 'docs/regional-worker-integration/local-http-results.json'
HEADERS = ['content-type', 'cache-control', 'etag', 'x-robots-tag', 'x-content-type-options',
           'x-frame-options', 'referrer-policy', 'location']


def get(port, host, path, method='GET', headers=None):
    connection = http.client.HTTPConnection('127.0.0.1', port, timeout=15)
    connection.request(method, path, headers={'Host': host, **(headers or {})})
    response = connection.getresponse()
    body = response.read()
    result = dict(status=response.status, headers={key: response.getheader(key) for key in HEADERS},
                  bytes=len(body), sha256=hashlib.sha256(body).hexdigest())
    connection.close()
    return result


results = []
def equivalent(baseline, candidate):
    # ETags are opaque per-deployment validators; test each server's 304 separately.
    def normalized(value):
        return {**value, 'headers': {key: header for key, header in value['headers'].items() if key != 'etag'}}
    return normalized(baseline) == normalized(candidate) and bool(baseline['headers']['etag']) == bool(candidate['headers']['etag'])


for i, region in enumerate(['dongjak', 'geumcheon']):
    host = f'seoul-{region}.fwith.kr'
    contract = json.loads((ROOT / f'scripts/direct-seoul-{region}/production-output-contract.json').read_text())
    paths = ['/' + key for key in contract['files'] if key != '_headers']
    paths += ['/', '/regions/', '/regions', '/404', '/missing', '/__regional/dongjak/index.html',
              '/__regional/geumcheon/index.html', '/regions/other-region/',
              f'/regions/{region}-funeral-wreath', f'/regions/{region}-funeral-wreath/?v=1']
    for repeat in range(2):
        for path in paths:
            baseline = get(8788+i, host, path)
            candidate = get(8787, host, path)
            results.append(dict(region=region, path=path, repeat=repeat,
                                equal=equivalent(baseline, candidate), baseline=baseline, candidate=candidate))
    for path, status in [('/404', 200), ('/missing', 404)]:
        candidate = get(8787, host, path)
        results.append(dict(region=region, test='404-body-versus-status', path=path,
            equal=candidate['status'] == status and candidate['sha256'] == contract['files']['404.html'], candidate=candidate))
    for method in ['HEAD', 'GET']:
        baseline = get(8788+i, host, '/', method, {} if method == 'HEAD' else {'If-None-Match': get(8788+i, host, '/')['headers']['etag']})
        candidate = get(8787, host, '/', method, {} if method == 'HEAD' else {'If-None-Match': get(8787, host, '/')['headers']['etag']})
        results.append(dict(region=region, path='/', method=method, equal=equivalent(baseline, candidate),
                            baseline=baseline, candidate=candidate))
    old_tag = get(8788+i, host, '/')['headers']['etag']
    revalidated = get(8787, host, '/', headers={'If-None-Match': old_tag})
    current = get(8787, host, '/')
    results.append(dict(region=region, test='old-validator-safe-full-response',
                        equal=revalidated['status'] == 200 and revalidated['sha256'] == current['sha256'], candidate=revalidated))
unknown = get(8787, 'unlisted.fwith.kr', '/')
results.append(dict(test='unknown-host', equal=unknown['status'] == 404, candidate=unknown))
report = dict(scope='local workerd only; no production or edge-cache verification',
              validatorNote='Opaque ETag values may change on migration; own-validator 304 and old-validator full bytes checked.',
              checks=len(results), failures=sum(not row['equal'] for row in results), results=results)
REPORT.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps({key: value for key, value in report.items() if key != 'results'}))
for row in [row for row in results if not row['equal']][:5]:
    if not row['equal']:
        print(json.dumps(row))
raise SystemExit(bool(report['failures']))
