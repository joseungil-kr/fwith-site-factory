"""Create a local-only bundle from exact retained production-output contracts."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[2]
PILOT = {
    'dongjak': '2935ac394dd63e81c443995a66fab46981f652bf',
    'geumcheon': '673ff52bb8f21f58bb104b447f3f105fd1a52a98',
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def package(sources, output):
    if set(sources) != set(PILOT):
        raise ValueError('exact_two_regions_required')
    if output.exists():
        raise ValueError('output_must_be_new')
    verified = {}
    for region, source in sources.items():
        contract = json.loads((ROOT / f'scripts/direct-seoul-{region}/production-output-contract.json').read_text(encoding='utf-8'))
        if contract['sourceRevision'] != PILOT[region]:
            raise ValueError('retained_contract_revision_mismatch')
        nodes = list(source.rglob('*'))
        if any(p.is_symlink() or not (p.is_file() or p.is_dir()) for p in [source, *source.parents, *nodes]):
            raise ValueError('unsafe_source_node')
        observed = {p.relative_to(source).as_posix(): digest(p) for p in nodes if p.is_file()}
        if observed != contract['files']:
            raise ValueError('built_bytes_differ_from_retained_contract: ' + region)
        verified[region] = observed
    output.mkdir(parents=True)
    assets = output / 'assets'
    headers = []
    inventory = []
    for region, files in verified.items():
        for relative, sha in files.items():
            source = sources[region] / relative
            if relative == '_headers':
                lines = source.read_text(encoding='utf-8').splitlines()
                # Pilot contracts use one global rule. Fail closed on unsupported syntax.
                if not lines or lines[0] != '/*' or any(line and not line.startswith('  ') for line in lines[1:]):
                    raise ValueError('unsupported_header_rules')
                headers.extend([f'/__regional/{region}/*', *lines[1:]])
                continue
            target = assets / '__regional' / region / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            assert digest(target) == sha
            inventory.append(dict(path=target.relative_to(assets).as_posix(), bytes=target.stat().st_size, sha256=sha))
    header_file = assets / '_headers'
    header_file.write_text('\n'.join(headers) + '\n', encoding='utf-8', newline='\n')
    inventory.append(dict(path='_headers', bytes=header_file.stat().st_size, sha256=digest(header_file)))
    if len(inventory) > 20000 or max(row['bytes'] for row in inventory) > 25 * 1024 * 1024:
        raise ValueError('asset_limits_exceeded')
    shutil.copyfile(Path(__file__).with_name('router.mjs'), output / 'router.mjs')
    config = dict(name='regional-integration-local', main='router.mjs', compatibility_date='2026-10-09',
                  workers_dev=False, assets=dict(directory='./assets', binding='ASSETS', run_worker_first=True,
                                                html_handling='auto-trailing-slash', not_found_handling='404-page'))
    (output / 'wrangler.local.json').write_text(json.dumps(config, indent=2) + '\n', encoding='utf-8')
    report = dict(status='local_bundle_not_live_backup', sourceRevisions=PILOT,
                  sourceFiles={key: len(value) for key, value in verified.items()},
                  packageFileCount=len(inventory), uploadableAssetCount=len(inventory)-1,
                  configurationFiles=['_headers'], maxAssetBytes=max(row['bytes'] for row in inventory),
                  totalAssetBytes=sum(row['bytes'] for row in inventory), files=sorted(inventory, key=lambda row: row['path']),
                  liveVersionVerified=False, rollbackVerified=False)
    (output / 'inventory.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--dongjak', type=Path, required=True)
    parser.add_argument('--geumcheon', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = package({region: getattr(args, region) for region in PILOT}, args.output)
    print(json.dumps({key: value for key, value in report.items() if key != 'files'}))
