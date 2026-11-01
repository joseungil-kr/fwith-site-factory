"""Offline, portable preparation from the reviewed repository artifact. No credentials."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import zipfile

ROOT = Path(__file__).resolve().parents[2]
ZIP_SHA = 'da8817cc8b501a4728e838f415447735e9932e9256b48c1df7a7504ac0ee9cb9'
ROUTER_SHA = 'df119c463b2a1c0a25a4323b8ec4575c6c386d1f539d95e3efb48569219538f1'
CONFIG = {
    'name': 'seoul-dongjak-flower-guide', 'main': 'router.mjs',
    'compatibility_date': '2026-10-09', 'workers_dev': False,
    'assets': {'directory': './assets', 'binding': 'ASSETS', 'run_worker_first': True,
               'html_handling': 'auto-trailing-slash', 'not_found_handling': '404-page'},
    'preview_urls': False, 'compatibility_flags': [], 'logpush': False,
    'observability': {'enabled': False},
}


def prepare(output):
    if output.exists():
        raise ValueError('output must be new')
    archive = ROOT / 'docs/regional-worker-integration/artifacts/pilot-local-bundle.zip'
    if hashlib.sha256(archive.read_bytes()).hexdigest() != ZIP_SHA:
        raise ValueError('reviewed ZIP mismatch')
    with zipfile.ZipFile(archive) as z:
        names = z.namelist()
        if len(names) != len(set(names)) or any(PurePosixPath(n).is_absolute() or '..' in PurePosixPath(n).parts or '\\' in n for n in names):
            raise ValueError('unsafe archive names')
        inventory = json.loads(z.read('inventory.json'))
        rows = inventory['files']
        if len(rows) != 37 or inventory['uploadableAssetCount'] != 36:
            raise ValueError('unexpected asset count')
        expected = {'assets/' + r['path'] for r in rows} | {'router.mjs', 'inventory.json', 'wrangler.local.json'}
        if set(names) != expected:
            raise ValueError('unexpected archive inventory')
        for row in rows:
            data = z.read('assets/' + row['path'])
            if len(data) != row['bytes'] or hashlib.sha256(data).hexdigest() != row['sha256']:
                raise ValueError('asset contract mismatch')
        if hashlib.sha256(z.read('router.mjs')).hexdigest() != ROUTER_SHA:
            raise ValueError('router mismatch')
        output.mkdir(parents=True)
        for name in names:
            if name == 'wrangler.local.json':
                continue
            target = output / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(z.read(name))
    config = output / 'wrangler.stage1.json'
    config.write_text(json.dumps(CONFIG, indent=2) + '\n', encoding='utf-8', newline='\n')
    return {'config_sha256': hashlib.sha256(config.read_bytes()).hexdigest(),
            'router_sha256': ROUTER_SHA, 'uploadable_assets': 36, 'files_in_assets': 37}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    print(json.dumps(prepare(parser.parse_args().output)))
