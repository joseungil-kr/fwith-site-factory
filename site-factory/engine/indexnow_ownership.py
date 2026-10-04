#!/usr/bin/env python3
"""Strict one-file ownership amendment of an already approved public source."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
from indexnow_finalize import require, request, verify_public


def amendment(site, revision):
    value = site.get('indexnowOwnership', {})
    key = site.get('indexnowKey', '')
    require(isinstance(value, dict) and value.get('approved') is True, 'ownership_amendment_not_approved')
    require(re.fullmatch(r'[a-zA-Z0-9-]{8,128}', key or ''), 'ownership_key_not_configured')
    require(value.get('keySha256') == hashlib.sha256(key.encode()).hexdigest(), 'ownership_key_digest_mismatch')
    require(value.get('revision') == revision and site.get('approvedRevision') == revision, 'ownership_revision_mismatch')
    require(re.fullmatch(r'[0-9a-f]{40}', value.get('previousRevision', '')), 'ownership_previous_revision_missing')
    require(value.get('origin') == site['siteUrl'] and value.get('path') == site['root'] + '/public/' + key + '.txt',
            'ownership_target_mismatch')
    return value


def key_allowed(site):
    key = site.get('indexnowKey', '')
    if key == '':
        return True
    value = site.get('indexnowOwnership', {})
    return (isinstance(value, dict) and value.get('approved') is True
        and re.fullmatch(r'[A-Za-z0-9-]{8,128}', key or '') is not None
        and value.get('keySha256') == hashlib.sha256(key.encode()).hexdigest()
        and value.get('origin') == site['siteUrl']
        and value.get('path') == site['root'] + '/public/' + key + '.txt'
        and re.fullmatch(r'[0-9a-f]{40}', value.get('revision', '')) is not None
        and re.fullmatch(r'[0-9a-f]{40}', value.get('previousRevision', '')) is not None)


def verify_source(site, revision, workspace):
    value = amendment(site, revision)
    def git(*args):
        return subprocess.check_output(['git', '-C', str(workspace), *args])
    require(git('rev-parse', 'HEAD').decode().strip() == revision, 'ownership_checkout_mismatch')
    old = value['previousRevision']
    # Compare the WHOLE repository, not just the site root. No hidden config,
    # route, content, credentials, or symlink changes can enter this amendment.
    changed = git('diff', '--name-status', '--no-renames', old, revision).decode().splitlines()
    require(changed == ['A\t' + value['path']], 'ownership_not_exact_one_file_addition')
    mode = git('ls-tree', revision, '--', value['path']).decode().split()[0]
    require(mode == '100644', 'ownership_file_not_regular')
    require(git('show', revision + ':' + value['path']) == (site['indexnowKey'] + '\n').encode(), 'ownership_file_content_mismatch')
    return {'state': 'ownership_source_verified', 'previousRevision': old, 'revision': revision,
            'origin': site['siteUrl'], 'keySha256': value['keySha256']}


def compare_artifacts(site, old_root, new_root):
    value = amendment(site, site['approvedRevision'])
    old, new = Path(old_root)/'dist', Path(new_root)/'dist'
    old_files = {p.relative_to(old).as_posix():p for p in old.rglob('*') if p.is_file()}
    new_files = {p.relative_to(new).as_posix():p for p in new.rglob('*') if p.is_file()}
    key_file = site['indexnowKey'] + '.txt'
    require(set(new_files) - set(old_files) == {key_file} and not set(old_files) - set(new_files), 'ownership_build_scope_changed')
    for name, path in old_files.items():
        previous = path.read_bytes()
        # The only expected rendered-content delta is the full revision meta.
        if name.endswith('.html'):
            previous = previous.replace(('content="'+value['previousRevision']+'"').encode(),
                                        ('content="'+value['revision']+'"').encode())
        require(previous == new_files[name].read_bytes(), 'ownership_build_content_changed')
    require(new_files[key_file].read_text() == site['indexnowKey']+'\n', 'ownership_build_key_mismatch')
    return {'state':'ownership_artifacts_verified','preservedFiles':len(old_files),'addedFiles':1}


def verify_old_live(site, root):
    value = amendment(site, site['approvedRevision'])
    # Ownership proof does not exist yet; all current public content still must
    # be checked against the original exact source before the key-only deploy.
    original = dict(site, indexnowKey='')
    urls = verify_public(original, value['previousRevision'], root,
                         lambda url:request('GET',url), require_ownership=False)
    return {'state':'ownership_previous_public_verified','urlCount':len(urls),'revision':value['previousRevision']}


def binding(site):
    account, token = os.environ.get('CLOUDFLARE_ACCOUNT_ID',''), os.environ.get('CLOUDFLARE_API_TOKEN','')
    require(re.fullmatch(r'[0-9a-fA-F]{32}',account) and token, 'cloudflare_binding_read_unavailable')
    req=Request(f'https://api.cloudflare.com/client/v4/accounts/{account}/workers/domains',
                headers={'Authorization':'Bearer '+token})
    with urlopen(req,timeout=30) as response:
        require(response.status==200,'binding_read_not_http200')
        data=json.load(response)
    require(data.get('success') is True and not data.get('errors') and isinstance(data.get('result'),list), 'binding_read_incomplete')
    rows=data['result']; info=data.get('result_info') or {}
    require(info.get('total_count',len(rows))==len(rows) and info.get('total_pages',1)<=1,'binding_inventory_truncated')
    hostname=urlsplit(site['siteUrl']).hostname
    worker=site.get('coverageDeployment',{}).get('worker',site['worker'])
    found=[r for r in rows if r.get('hostname')==hostname]
    require(len(found)==1 and found[0].get('service')==worker and found[0].get('environment') in ('production',None), 'existing_binding_identity_mismatch')
    return {'state':'existing_binding_verified','hostname':hostname,'worker':worker,'bindingId':found[0].get('id')}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('phase',choices=['source','artifacts','old-live','binding'])
    p.add_argument('--registry',type=Path,required=True);p.add_argument('--site-key',required=True)
    p.add_argument('--workspace',type=Path);p.add_argument('--root',type=Path);p.add_argument('--old-root',type=Path)
    p.add_argument('--report',type=Path,required=True);args=p.parse_args()
    try:
        site=json.loads(args.registry.read_text())['sites'][args.site_key]
        if args.phase=='source':result=verify_source(site,site['approvedRevision'],args.workspace)
        elif args.phase=='artifacts':result=compare_artifacts(site,args.old_root,args.root)
        elif args.phase=='old-live':result=verify_old_live(site,args.old_root)
        else:result=binding(site)
        ok=True
    except Exception as error:
        safe=str(error) if type(error) is ValueError and re.fullmatch('[a-z0-9_]+',str(error)) else type(error).__name__
        result={'state':'ownership_amendment_blocked','reason':safe};ok=False
    args.report.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
    return 0 if ok else 1

if __name__=='__main__':raise SystemExit(main())
