"""Offline comparison of helper receipts, retained ZIPs and prior local HTTP evidence."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'docs/regional-worker-integration/live-differences'
EMPTY_SHA = hashlib.sha256(b'').hexdigest()


def classify(path, status, actual_sha, retained_sha):
    if status == '200' and actual_sha == retained_sha:
        return 'exact_public_body_match'
    if path == '/404.html' and status == '307' and actual_sha == EMPTY_SHA:
        return 'redirect_response_not_file_body; location_and_target_require_separate_evidence'
    if path == '/robots.txt' and status == '200':
        return 'robots_difference_requires_raw_body_and_policy_comparison'
    return 'unexplained_difference_blocks_cutover'


def main(evidence):
    OUT.mkdir(exist_ok=True)
    provenance = []
    for name in ['release-comparison.json', 'usage-and-restore-limitations.json',
                 *[f'{region}-result/release/{file}' for region in ['dongjak', 'geumcheon']
                   for file in ['release.json', 'wrangler.publish.json']]]:
        raw = (evidence / name).read_bytes()
        value = json.loads(raw.decode('utf-8-sig'))
        target = name.replace('/', '--')
        (OUT / target).write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8', newline='\n')
        provenance.append(dict(sourceRelativePath=name, savedFile=target, originalSha256=hashlib.sha256(raw).hexdigest()))
    current = json.loads((evidence / 'release-comparison.json').read_text(encoding='utf-8-sig'))
    local = json.loads((OUT.parent / 'local-http-results.json').read_text(encoding='utf-8-sig'))
    results = []
    for row in current:
        region = row['city']
        receipt = json.loads((evidence / f'{region}-result/release/release.json').read_text(encoding='utf-8-sig'))
        with zipfile.ZipFile(OUT.parent / f'artifacts/{region}-retained-build.zip') as archive:
            retained = {name: hashlib.sha256(archive.read(name)).hexdigest() for name in archive.namelist()}
        if retained != receipt['files'] or receipt['revision'] != row['release_source_sha']:
            raise ValueError('retained_receipt_mismatch: ' + region)
        comparisons = []
        for item in row['live_files']:
            origin = receipt['origin']
            if not item['url'].startswith(origin + '/'):
                raise ValueError('foreign_origin')
            path = item['url'][len(origin):]
            file = 'index.html' if path == '/' else path.lstrip('/') + ('index.html' if path.endswith('/') else '')
            comparisons.append(dict(path=path, liveStatus=item['status'], liveSha256=item['sha256'],
                retainedSha256=retained[file], classification=classify(path, item['status'], item['sha256'], retained[file])))
        matches = sum(item['classification'] == 'exact_public_body_match' for item in comparisons)
        if matches != row['live_hash_matches']:
            raise ValueError('helper_match_count_inconsistent')
        local_redirect = next(item for item in local['results'] if item.get('region') == region and item.get('path') == '/404.html')
        results.append(dict(region=region, sourceRevision=receipt['revision'], releaseRun=receipt['runId'],
            retainedReceiptFiles=len(retained), retainedReceiptAllHashesMatch=True,
            publicBodyMatches=matches, publiclyRequestedFiles=len(comparisons),
            local404Redirect=local_redirect, comparisons=comparisons,
            live404LocationEvidence='/404 reported by helper' if region == 'dongjak' else 'not supplied',
            robotsEvidence='Managed prefix observed by helper; exact raw body absent' if region == 'dongjak' else 'raw body/cause not inspected',
            activeUUIDToSourceDirectMapping=False, currentProviderFullConfigExported=False))
    report = dict(scope='offline reconciliation; no network requests or provider writes',
                  provenance=provenance, sites=results, cutoverApproved=False)
    (OUT / 'reconciled.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps([dict(region=r['region'], retainedFiles=r['retainedReceiptFiles'], matches=r['publicBodyMatches'],
                           publicFiles=r['publiclyRequestedFiles']) for r in results]))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('evidence', type=Path)
    main(parser.parse_args().evidence)
