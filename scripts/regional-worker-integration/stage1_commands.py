"""Prepare fixed stage-1 command argv; never execute a provider command.

Readback must be refreshed by the authorized executor immediately before use.
Wrangler has no compare-and-swap deployment guard: serialize publishers and
recheck active UUID immediately before execution; this plan cannot close that race.
"""
import argparse
import json
from pathlib import Path
from recovery_plan import DONGJAK, GEUMCHEON, D_VERSION, G_VERSION, valid_uuid

WRANGLER_VERSION = '4.148.0'
ROOT = Path(__file__).resolve().parents[2]
WRANGLER = ROOT.parent / 'build-tools/node_modules/wrangler/bin/wrangler.js'
CONFIG = ROOT.parent / 'regional-pilot-bundle/wrangler.stage1.json'


def prepare(state, operation):
    if state.get('fresh_readback') is not True:
        raise ValueError('fresh readback required')
    if (state.get('dongjak_service') != DONGJAK or state.get('geumcheon_service') != GEUMCHEON
            or state.get('geumcheon_version') != G_VERSION
            or state.get('dongjak_percentage') != 100 or state.get('geumcheon_percentage') != 100):
        raise ValueError('stage 1 requires both original mappings and single-version deployments')
    current = state.get('dongjak_version')
    if operation == 'deploy':
        if current != D_VERSION:
            raise ValueError('deploy precondition conflicts with expected original UUID')
        return ['node', str(WRANGLER), 'deploy', '--config', str(CONFIG)]
    pilot = state.get('expected_pilot_uuid')
    if not valid_uuid(pilot) or pilot == D_VERSION or current != pilot:
        raise ValueError('rollback requires exact recorded post-deployment pilot UUID')
    return ['node', str(WRANGLER), 'rollback', D_VERSION, '--name', DONGJAK, '--config', str(CONFIG)]


def check_local_configuration():
    package = json.loads((WRANGLER.parent.parent / 'package.json').read_text())
    if package['version'] != WRANGLER_VERSION:
        raise ValueError('pinned Wrangler version mismatch')
    config = json.loads(CONFIG.read_text())
    if (config.get('name') != DONGJAK or config.get('routes') or config.get('route')
            or config.get('workers_dev') is not False or config.get('preview_urls') is not False
            or config.get('compatibility_date') != '2026-10-09'
            or config.get('assets', {}).get('run_worker_first') is not True):
        raise ValueError('production configuration violates stage-1 scope')
    return config


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=['deploy', 'rollback'])
    parser.add_argument('state')
    args = parser.parse_args()
    check_local_configuration()
    argv = prepare(json.loads(Path(args.state).read_text()), args.operation)
    print(json.dumps({'executed': False, 'argv': argv,
                      'required': 'parent approval, serialized publisher, immediate live readback and post-action UUID/100% verification'}, indent=2))
