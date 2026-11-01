"""One GET per candidate, no retries, redirects or provider mutations."""
import hashlib
import json
from pathlib import Path
import re
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


results = []
for region in ('seoul-dongjak', 'seoul-geumcheon'):
    url = f'https://{region}.fwith.kr/'
    row = dict(url=url)
    try:
        with build_opener(NoRedirect()).open(Request(url), timeout=25) as response:
            body = response.read(2 * 1024 * 1024 + 1)
            if len(body) > 2 * 1024 * 1024:
                raise ValueError('response_too_large')
            text = body.decode('utf-8')
            row.update(status=response.status, bytes=len(body), sha256=hashlib.sha256(body).hexdigest(),
                       headers=dict(response.headers),
                       revisionMeta=re.findall(r'<meta[^>]+(?:site-factory-revision)[^>]*>', text))
    except HTTPError as error:
        row.update(status=error.code, state='http_error_not_retried')
    except (URLError, ValueError) as error:
        row.update(state='unverified', reason=str(error))
    results.append(row)
path = Path(__file__).resolve().parents[2] / 'docs/regional-worker-integration/live-home-probe.json'
path.write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(results, ensure_ascii=False))
