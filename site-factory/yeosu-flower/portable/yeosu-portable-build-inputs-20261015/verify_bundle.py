#!/usr/bin/env python3
"""Read-only exact package/source/output check; no dependencies, network or writes."""
import argparse
import hashlib
import json
import re
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parent
CANDIDATE = ROOT / 'yeosu-local-implementation-20261015/candidate'
SHA = lambda data: hashlib.sha256(data).hexdigest()


def file_record(root, path):
    if not isinstance(path, str) or not path or '\\' in path:
        raise AssertionError('Invalid manifest path')
    rel = PurePosixPath(path)
    if rel.is_absolute() or '..' in rel.parts or rel.as_posix() != path:
        raise AssertionError(f'Unsafe or noncanonical manifest path: {path}')
    for index in range(1, len(rel.parts) + 1):
        if root.joinpath(*rel.parts[:index]).is_symlink():
            raise AssertionError(f'Symlink in bundled path: {path}')
    target = root / path
    if target.is_symlink() or not target.is_file():
        raise AssertionError(f'Missing or non-regular bundled file: {path}')
    raw = target.read_bytes()
    return {'path': path, 'bytes': len(raw), 'sha256': SHA(raw)}


def check_manifest(root, manifest):
    paths = [item['path'] for item in manifest['files']]
    if paths != sorted(set(paths)):
        raise AssertionError('Manifest paths must be sorted and unique')
    for item in manifest['files']:
        if set(item) != {'path', 'bytes', 'sha256'} or type(item['bytes']) is not int or item['bytes'] < 0 or not re.fullmatch(r'[0-9a-f]{64}', item['sha256']):
            raise AssertionError('Invalid manifest record')
    actual = [file_record(root, item['path']) for item in manifest['files']]
    if actual != manifest['files']:
        raise AssertionError('Manifest file bytes differ')
    tree_hash = SHA(''.join(f"{item['sha256']}  {item['path']}\n" for item in actual).encode())
    if tree_hash != manifest['treeSHA256']:
        raise AssertionError('Tree digest differs')
    return {'files': len(actual), 'treeSHA256': tree_hash}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--built-output', action='store_true')
    args = parser.parse_args()
    manifest_record = file_record(ROOT, 'MANIFEST.json')
    file_record(ROOT, 'SHA256SUMS')
    manifest = json.loads((ROOT / 'MANIFEST.json').read_text())
    result = {'bundle': check_manifest(ROOT, manifest)}
    expected = {item['path'] for item in manifest['files']} | {'MANIFEST.json', 'SHA256SUMS'}
    # Only dependency and standard build products may appear after running build/test.
    generated = ('yeosu-local-implementation-20261015/candidate/node_modules/',
                 'yeosu-local-implementation-20261015/candidate/.astro/',
                 'yeosu-local-implementation-20261015/candidate/dist/',
                 'yeosu-local-implementation-20261015/candidate/scripts/__pycache__/')
    for target in ROOT.rglob('*'):
        rel = target.relative_to(ROOT).as_posix()
        if target.is_file() or target.is_symlink():
            if rel not in expected and not rel.startswith(generated) and rel not in (
                'yeosu-local-implementation-20261015/candidate/evidence/static-qa.json',
                'yeosu-local-implementation-20261015/candidate/node_modules',
            ):
                raise AssertionError(f'Unexpected file: {rel}')
    sums = sorted([*manifest['files'], manifest_record], key=lambda item: item['path'])
    expected_sums = ''.join(f"{item['sha256']}  {item['path']}\n" for item in sums)
    if (ROOT / 'SHA256SUMS').read_text() != expected_sums:
        raise AssertionError('SHA256SUMS must exactly cover the payload and MANIFEST.json, once each')
    result['source'] = check_manifest(CANDIDATE, json.loads((ROOT / 'reference/prior-source-manifest.json').read_text()))
    if args.built_output:
        output = json.loads((ROOT / 'reference/prior-output-manifest.json').read_text())
        expected_output = {item['path'] for item in output['files']}
        actual_output = {path.relative_to(CANDIDATE / 'dist').as_posix() for path in (CANDIDATE / 'dist').rglob('*') if path.is_file() or path.is_symlink()}
        if actual_output != expected_output:
            raise AssertionError('Output file set differs')
        result['output'] = check_manifest(CANDIDATE / 'dist', output)
    print(json.dumps({'status': 'EXACT_BYTES_VERIFIED', **result}, indent=2))


if __name__ == '__main__':
    main()
