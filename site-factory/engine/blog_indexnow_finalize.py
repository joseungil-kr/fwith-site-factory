#!/usr/bin/env python3
"""Submit a verified blog release without opening generic production gates.

The registry's separate blog indexing opt-in is required. Existing deployment,
Cloudflare credentials, generic production gates, and IndexNow transport/journal
behavior are not changed. This adapter never generates or publishes ownership.
"""
import argparse
import json
from pathlib import Path
import re

from blog_domain import validate_registry
from indexnow_finalize import Journal, finalize, request, require, verify_public

SITE_KEY = 'blog-fwith'


def approved_site(registry):
    """Validate the unchanged fixed blog identity and explicit indexing opt-in."""
    site = validate_registry(Path(registry))
    require(site.get('blogIndexnowEnabled') is True, 'blog_indexnow_not_approved')
    key = site.get('indexnowKey', '')
    require(re.fullmatch(r'[A-Za-z0-9-]{8,128}', key or ''), 'ownership_key_not_configured')
    sites = json.loads(Path(registry).read_text())['sites']
    require(not any(other.get('indexnowKey') == key for name, other in sites.items()
                    if name != SITE_KEY), 'blog_ownership_key_reused_from_other_site')
    return dict(site, siteKey=SITE_KEY)


def resolved_target(registry, revision):
    site = approved_site(registry)
    require(re.fullmatch(r'[0-9a-f]{40}', revision or ''), 'full_revision_required')
    return {'site_key': SITE_KEY, 'revision': revision, 'branch': site['branch'],
            'root': site['root'], 'site_url': site['siteUrl']}


def effective_site(registry, revision, root):
    site = approved_site(registry)
    require(re.fullmatch(r'[0-9a-f]{40}', revision or ''), 'full_revision_required')
    dist = Path(root) / 'dist'
    proof = dist / (site['indexnowKey'] + '.txt')
    require(proof.is_file() and not proof.is_symlink(), 'blog_built_ownership_file_missing')
    require(proof.read_bytes() == (site['indexnowKey'] + '\n').encode(),
            'blog_built_ownership_file_mismatch')
    # The shared verifier represents publication with generic flags. Only this
    # in-memory copy maps the explicit blog indexing grant to that interface;
    # validate_registry above requires the actual generic gates to stay closed.
    return dict(site, productionEnabled=True, launchMode='live')


def verify(registry, revision, root, transport=request):
    site = effective_site(registry, revision, root)
    urls = verify_public(site, revision, root, lambda url: transport('GET', url))
    return {'siteKey': SITE_KEY, 'revision': revision, 'origin': site['siteUrl'],
            'state': 'blog_public_indexnow_ready', 'urlCount': len(urls),
            'searchIndexing': 'not_verified'}


def submit(registry, revision, root, journal, transport=request, run_url='', sleep=None):
    site = effective_site(registry, revision, root)
    kwargs = dict(transport=transport, run_url=run_url)
    if sleep is not None:
        kwargs['sleep'] = sleep
    result = finalize(site, revision, root, journal, **kwargs)
    result.update(pipelineState='live_verified_indexnow_received', searchIndexing='not_verified')
    return result


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode', choices=['verify', 'submit'])
    p.add_argument('--registry', type=Path, required=True)
    p.add_argument('--revision', required=True)
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    p.add_argument('--receipt-issue', type=int)
    p.add_argument('--run-url', default='')
    args = p.parse_args(argv)
    try:
        if args.mode == 'verify':
            result = verify(args.registry, args.revision, args.root)
        else:
            site = approved_site(args.registry)
            journal = Journal(site['repo'], args.receipt_issue)
            result = submit(args.registry, args.revision, args.root, journal, run_url=args.run_url)
        ok = True
    except Exception as error:
        safe = str(error) if type(error) is ValueError and re.fullmatch(r'[a-z0-9_]+', str(error)) else type(error).__name__
        result = {'pipelineState': 'indexnow_blocked_or_failed', 'siteKey': SITE_KEY,
                  'revision': args.revision, 'reason': safe, 'searchIndexing': 'not_verified'}
        ok = False
    args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'urls'}, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
