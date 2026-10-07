#!/usr/bin/env python3
"""Retain submission-started evidence and never automatically repeat an uncertain POST."""
import datetime
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def main():
    urls_file = Path('indexnow-urls.json')
    urls = json.loads(urls_file.read_text())
    if len(urls) != 18 or len(set(urls)) != 18:
        raise SystemExit('Expected exactly 18 unique approved IndexNow URLs')
    if any(not url.startswith('https://yongin.fwith.kr/') for url in urls):
        raise SystemExit('Unexpected IndexNow URL host')
    if os.environ.get('GITHUB_RUN_ATTEMPT') != '1':
        raise SystemExit('IndexNow is not retried automatically. Review the prior run receipt first.')
    key = os.environ['INDEXNOW_KEY']
    if not key:
        raise SystemExit('INDEXNOW_KEY is required')
    redact = lambda text: text.replace(key, '[REDACTED_INDEXNOW_KEY]')
    key_sha256 = hashlib.sha256(key.encode()).hexdigest()
    fingerprint_input = {'origin': 'https://yongin.fwith.kr', 'sourceRevision': os.environ['GITHUB_SHA'], 'endpoint': os.environ['INDEXNOW_ENDPOINT'], 'keySha256': key_sha256, 'urls': sorted(urls)}
    fingerprint = hashlib.sha256(json.dumps(fingerprint_input, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    receipt_path = Path('indexnow-submission-receipt.json')
    receipt = {'schemaVersion': 1, 'state': 'started-do-not-retry-if-terminal-receipt-missing',
               'startedAt': now(), 'sourceRevision': os.environ['GITHUB_SHA'],
               'runId': os.environ['GITHUB_RUN_ID'], 'runAttempt': os.environ['GITHUB_RUN_ATTEMPT'],
               'endpoint': os.environ['INDEXNOW_ENDPOINT'], 'origin': 'https://yongin.fwith.kr', 'urlCount': len(urls),
               'keySha256': key_sha256, 'fingerprint': fingerprint,
               'urlsSha256': hashlib.sha256(urls_file.read_bytes()).hexdigest(),
               'automaticRetryAllowed': False}
    # This file is created before launching the existing native submit helper.
    with receipt_path.open('x') as output:
        output.write(json.dumps(receipt, indent=2) + '\n')
        output.flush()
        os.fsync(output.fileno())
    output_lines = []
    try:
        with Path('indexnow-receipt.log').open('x') as log:
            process = subprocess.Popen(['node', 'scripts/submit_indexnow.mjs'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            for line in process.stdout:
                line = redact(line)
                output_lines.append(line)
                log.write(line)
                log.flush()
                print(line, end='', flush=True)
            result = process.wait()
        accepted = re.findall(r'IndexNow accepted (\d+) URL\(s\): HTTP (200|202)', ''.join(output_lines))
        if result == 0 and len(accepted) == 1 and accepted[0][0] == '18':
            status = int(accepted[0][1])
            receipt.update(state='accepted' if status == 200 else 'received-key-validation-pending', httpStatus=status)
        else:
            receipt.update(state='failed-or-unknown-do-not-retry', exitCode=result)
            result = result or 1
    except Exception as error:
        receipt.update(state='failed-or-unknown-do-not-retry', error=redact(str(error)))
        result = 1
    receipt['finishedAt'] = now()
    receipt_path.write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt))
    raise SystemExit(result)


if __name__ == '__main__':
    main()
