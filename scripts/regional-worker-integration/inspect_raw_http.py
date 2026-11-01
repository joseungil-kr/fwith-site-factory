"""Read helper-captured HTTP files offline; retain hashes, not telemetry URLs."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BEGIN = b'# BEGIN Cloudflare Managed content'
END = b'# END Cloudflare Managed Content'


def split_managed(live, original):
    if live.count(BEGIN) != 1 or live.count(END) != 1 or live.index(BEGIN) >= live.index(END):
        raise ValueError('managed_markers_not_unique_and_ordered')
    boundary = live.index(END) + len(END)
    # Exactly the two observed LF separators; no comment or whitespace normalization.
    if live[boundary:] != b'\n\n' + original:
        raise ValueError('original_suffix_changed')
    return live[:boundary]


def main(evidence):
    comparisons = json.loads((evidence / 'release-comparison.json').read_text(encoding='utf-8-sig'))
    rows = []
    prefixes = []
    for region in ['dongjak', 'geumcheon']:
        original = (ROOT.parent / f'build-{region}/dist/robots.txt').read_bytes()
        live = (evidence / f'{region}-robots.txt').read_bytes()
        prefix = split_managed(live, original)
        prefixes.append(prefix)
        sha = hashlib.sha256(live).hexdigest()
        expected = next(item['sha256'] for row in comparisons if row['city'] == region
                        for item in row['live_files'] if item['url'].endswith('/robots.txt'))
        if sha != expected:
            raise ValueError('captured_body_hash_disagrees_with_helper_comparison')
        records = {}
        for kind in ['404', 'robots']:
            source = evidence / f'{region}-{kind}-headers.txt'
            raw = source.read_bytes()
            lines = raw.decode('utf-8-sig').splitlines()
            headers = {key.lower(): value.strip() for line in lines[1:] if ':' in line
                       for key, value in [line.split(':', 1)]}
            keys = ['date', 'location', 'content-type', 'content-length', 'cf-cache-status',
                    'x-content-type-options', 'x-frame-options', 'referrer-policy']
            records[kind] = dict(statusLine=lines[0], headers={key: headers[key] for key in keys if key in headers},
                                 sourceFile=source.name, sourceSha256=hashlib.sha256(raw).hexdigest())
        body404 = (evidence / f'{region}-404-body.txt').read_bytes()
        if records['404']['statusLine'] != 'HTTP/1.1 307 Temporary Redirect' or records['404']['headers']['location'] != '/404' or body404:
            raise ValueError('unexpected_404_first_hop')
        rows.append(dict(region=region, helperCheckedAt=(evidence / f'{region}-http-checked-at.txt').read_text().strip(),
            responses=records, robotsRawSha256=sha, robotsRawBytes=len(live),
            managedPrefixSha256=hashlib.sha256(prefix).hexdigest(), managedPrefixBytes=len(prefix),
            originalSuffixByteExact=True, separatorHex='0a0a', originalSuffixSha256=hashlib.sha256(original).hexdigest(),
            contentSignalLines=[line for line in prefix.decode().splitlines() if line.lower().startswith('content-signal:')],
            public404FinalTargetVerified=False, postIntegrationEdgeTransformationVerified=False))
    report = dict(scope='offline raw helper evidence; no new public requests',
                  commonManagedPrefixByteExact=prefixes[0] == prefixes[1], sites=rows,
                  directPublicFileHashMatches='16/18 per site remains unchanged; semantic explanation is not byte equality')
    output = ROOT / 'docs/regional-worker-integration/raw-http-analysis.json'
    output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(dict(commonPrefix=report['commonManagedPrefixByteExact'], suffixMatches=[row['originalSuffixByteExact'] for row in rows])))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('evidence', type=Path)
    main(parser.parse_args().evidence)
