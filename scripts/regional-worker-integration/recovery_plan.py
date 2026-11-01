"""Offline recovery planner. Never performs provider mutations or runs commands.

Generate one next action from fresh readback; do not queue the entire recovery.
Custom Domain API payload must be supplied from private preflight evidence.
"""
import argparse
import json
from uuid import UUID

DONGJAK = 'seoul-dongjak-flower-guide'
GEUMCHEON = 'seoul-geumcheon-flower-guide'
D_VERSION = '3720873d-5c57-4c0f-a25c-80dba048ddd1'
G_VERSION = 'c3d0ea60-ca39-47b6-a119-e692d66a1658'


def valid_uuid(value):
    try:
        return isinstance(value, str) and str(UUID(value)) == value
    except (ValueError, TypeError, AttributeError):
        return False


def next_action(state):
    if state.get('fresh_readback') is not True:
        return {'action': 'STOP', 'reason': 'Fresh domain and deployment readback required; unknown outcomes cannot be retried blindly.'}
    current = state.get('dongjak_version')
    pilot = state.get('expected_pilot_uuid')
    if not valid_uuid(current) or (current != D_VERSION and (not valid_uuid(pilot) or pilot == D_VERSION or current != pilot)):
        return {'action': 'STOP', 'reason': 'Unknown or conflicting active UUID; require original or exact recorded pilot UUID.'}
    if state.get('dongjak_percentage') != 100 or state.get('geumcheon_percentage') != 100:
        return {'action': 'STOP', 'reason': 'Expected single-version deployment at 100%; split or unknown traffic state.'}
    if state.get('dongjak_service') != DONGJAK:
        return {'action': 'STOP', 'reason': 'Unexpected Dongjak hostname ownership.'}
    if state.get('geumcheon_version') != G_VERSION:
        return {'action': 'STOP', 'reason': 'Original Geumcheon Worker drifted; resolve before reattaching traffic.'}
    owner = state.get('geumcheon_service')
    if owner == DONGJAK:
        return {'action': 'RESTORE_GEUMCHEON_DOMAIN', 'hostname': 'seoul-geumcheon.fwith.kr',
                'service': GEUMCHEON, 'then': 'Read back binding and verify Geumcheon public content. Do not roll Dongjak back yet.'}
    if owner != GEUMCHEON or state.get('dongjak_service') != DONGJAK:
        return {'action': 'STOP', 'reason': 'Unexpected hostname ownership; do not overwrite unknown state.'}
    if state.get('geumcheon_public_verified') is not True:
        return {'action': 'VERIFY_GEUMCHEON', 'reason': 'Original service binding alone does not prove public recovery.'}
    if state.get('dongjak_version') != D_VERSION:
        return {'action': 'ROLLBACK_DONGJAK', 'argv': ['wrangler', 'rollback', D_VERSION, '--name', DONGJAK],
                'then': 'Read back exact UUID at 100% and verify public responses and settings.'}
    return {'action': 'VERIFY_FINAL', 'reason': 'Confirm both UUIDs at 100%, mappings, public content and settings; no mutation needed.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('state', help='Local JSON with fresh readback; excludes credentials')
    args = parser.parse_args()
    with open(args.state, encoding='utf-8') as stream:
        print(json.dumps(next_action(json.load(stream)), indent=2))
