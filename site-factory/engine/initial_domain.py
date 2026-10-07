#!/usr/bin/env python3
"""Read-only target inventory using the existing fail-closed domain adapter."""
import argparse
import json
from pathlib import Path

import bucheon_domain_attach as adapter
from provision_goyang import INITIAL_REGIONS, INITIAL_SOURCE_PROFILES, target_contract


def inspect_initial(site_key, report):
    if site_key not in INITIAL_REGIONS or site_key not in INITIAL_SOURCE_PROFILES:
        raise ValueError('Initial domain identity is not reviewed')
    target = target_contract(site_key)
    original = adapter.HOSTNAME, adapter.WORKER
    try:
        # Single invocation, explicit code-pinned identity. Arbitrary input never
        # supplies a hostname, account, endpoint or Worker name.
        adapter.HOSTNAME = target['siteUrl'].removeprefix('https://')
        adapter.WORKER = target['productionWorker']
        status = adapter.main(['--preflight', '--report', str(report)])
    finally:
        adapter.HOSTNAME, adapter.WORKER = original
    if report.is_file():
        value = json.loads(report.read_text())
        value['siteKey'] = site_key
        value['state'] = 'initial_target_absent_verified' if status == 0 else 'initial_target_blocked'
        report.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    return status


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--site-key', required=True, choices=sorted(INITIAL_REGIONS))
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--attach', action='store_true')
    parser.add_argument('--registry', type=Path)
    parser.add_argument('--revision')
    args = parser.parse_args(argv)
    if args.attach:
        from whole_initial import resolve
        if args.registry is None or not args.revision:
            raise ValueError('Exact independently reviewed production revision is required')
        site = json.loads(args.registry.read_text())['sites'][args.site_key]
        config = site['initialDeployment']
        if config.get('siteKey') != args.site_key:
            raise ValueError('Initial domain identity mismatch')
        resolve(site, site['repo'], args.revision, config['launchKey'], config['scopeKey'])
        target = target_contract(args.site_key)
        original = adapter.HOSTNAME, adapter.WORKER
        try:
            adapter.HOSTNAME = target['siteUrl'].removeprefix('https://')
            adapter.WORKER = target['productionWorker']
            status = adapter.main(['--report', str(args.report)])
        finally:
            adapter.HOSTNAME, adapter.WORKER = original
        args.report.write_text(json.dumps({'state': 'initial_domain_request_accepted' if status == 0 else 'initial_domain_attach_failed_or_uncertain',
            'siteKey': args.site_key, 'hostname': target['siteUrl'].removeprefix('https://'),
            'worker': target['productionWorker'], 'liveVerified': False,
            'requiresInspectionBeforeRetry': status != 0}, indent=2) + '\n')
        return status
    return inspect_initial(args.site_key, args.report)


if __name__ == '__main__':
    raise SystemExit(main())
