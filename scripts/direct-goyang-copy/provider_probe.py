"""Observe one existing Goyang provider target; never approve or publish it."""
import argparse, datetime, hashlib, importlib, json, os, re, subprocess, sys
from pathlib import Path
from urllib.error import HTTPError

CONTROL=Path(__file__).resolve().parents[2]
REPOSITORY='joseungil-kr/fwith-site-factory'
HOSTNAME='goyang.fwith.kr'
ORIGIN='https://'+HOSTNAME
WORKER='goyang-flower-guide-qa'
SITE_KEY='goyang-flower-v2'
SOURCE_BRANCH='site-factory-goyang-copy-20261011'
SOURCE_ROOT='site-factory/goyang-flower'
MANIFEST='.github/direct-goyang-copy/source-release-manifest.root.json'
MANIFEST_SHA256='7392c4f97a15fa9d7f2aeb6d8fcd6483c9a02f33791718d6245a8830fc0b7bcb'
WORKFLOW='.github/workflows/goyang-copy-direct-publish.yml'
CODE_FILES=(WORKFLOW,MANIFEST,'scripts/direct-goyang-copy/provider_probe.py','scripts/direct-goyang-copy/test_publish.py',
    'scripts/direct-goyang-copy/publish.py','scripts/direct-goyang-copy/guard.py',
    'scripts/manual-release-20261007/gate.py','scripts/manual-release-20261007/provider_check.py')

def require(value,code):
    if not value:raise ValueError(code)
def sha(data):return hashlib.sha256(data).hexdigest()
def compact(value):return json.dumps(value,sort_keys=True,separators=(',',':')).encode()
def git(*args):return subprocess.check_output(['git','-C',str(CONTROL),*args],stderr=subprocess.DEVNULL)

def current_refs(control_revision,source_revision):
    rows=git('ls-remote','--heads','origin','refs/heads/main','refs/heads/'+SOURCE_BRANCH).decode().splitlines()
    parsed=[row.split() for row in rows]
    require(len(parsed)==2 and all(len(row)==2 for row in parsed),'probe_refs_missing_or_ambiguous')
    refs={row[1]:row[0] for row in parsed}
    require(refs=={'refs/heads/main':control_revision,'refs/heads/'+SOURCE_BRANCH:source_revision},'probe_main_or_source_moved')

def verify_source_identity(source_revision):
    raw=(CONTROL/MANIFEST).read_bytes()
    require(sha(raw)==MANIFEST_SHA256,'probe_source_manifest_drift')
    manifest=json.loads(raw);require(manifest['fileCount']==182 and len(manifest['files'])==182,'probe_source_manifest_scope')
    expected={SOURCE_ROOT+'/'+row['path']:row for row in manifest['files']}
    require(len(expected)==182 and all(not row['path'].startswith('/') and '..' not in Path(row['path']).parts for row in manifest['files']),'probe_source_manifest_paths')
    actual={}
    for row in git('ls-tree','-rz',source_revision,'--',SOURCE_ROOT).split(b'\0'):
        if not row:continue
        metadata,path=row.split(b'\t');mode,kind,blob=metadata.split();name=path.decode()
        require(kind==b'blob' and mode in (b'100644',b'100755'),'probe_nonregular_source_blob')
        require(name not in actual,'probe_duplicate_source_path');actual[name]=blob.decode()
    require(set(actual)==set(expected),'probe_source_file_set_mismatch')
    for name,blob in actual.items():
        entry=expected[name];require(blob==entry['gitBlob'],'probe_source_gitblob_mismatch')
        data=git('cat-file','blob',blob)
        require(len(data)==entry['bytes'] and sha(data)==entry['sha256'],'probe_source_bytes_mismatch')
    return dict(sourceManifestSha256=MANIFEST_SHA256,sourceFilesVerified=182,sourceIdentity='EXACT_GIT_BLOBS_ONLY_NOT_PUBLICATION_APPROVAL')

def trusted_control():
    require(os.environ.get('GITHUB_REPOSITORY')==REPOSITORY and os.environ.get('GITHUB_REF')=='refs/heads/main' and os.environ.get('GITHUB_EVENT_NAME')=='workflow_dispatch','wrong_probe_dispatch_context')
    revision=os.environ.get('GITHUB_SHA','');source_revision=os.environ.get('EXPECTED_REVISION','');run=os.environ.get('GITHUB_RUN_ID','');actor=os.environ.get('GITHUB_ACTOR','')
    require(re.fullmatch('[0-9a-f]{40}',revision) and re.fullmatch('[1-9][0-9]*',run) and re.fullmatch('[A-Za-z0-9_-]{1,100}',actor),'invalid_probe_run_identity')
    require(re.fullmatch('[0-9a-f]{40}',source_revision),'probe_full_source_sha_required')
    require(os.environ.get('GITHUB_RUN_ATTEMPT')=='1','probe_requires_first_attempt')
    require(git('rev-parse','HEAD').decode().strip()==revision,'wrong_probe_control_revision')
    current_refs(revision,source_revision)
    bindings={}
    for relative in CODE_FILES:
        path=CONTROL/relative
        require(all(not (CONTROL/Path(*Path(relative).parts[:i])).is_symlink() for i in range(1,len(Path(relative).parts)+1)),'probe_code_symlink')
        require(path.is_file(),'probe_code_missing')
        metadata=git('ls-tree',revision,'--',relative).decode().strip().split()
        require(len(metadata)==4 and metadata[0]=='100644' and metadata[1]=='blob' and metadata[3]==relative,'probe_code_nonregular')
        raw=path.read_bytes();require(raw==git('show',revision+':'+relative),'probe_code_worktree_drift')
        bindings[relative]={'sha256':sha(raw),'gitBlob':metadata[2]}
    source_identity=verify_source_identity(source_revision)
    return dict(**source_identity,repository=REPOSITORY,controlRevision=revision,sourceBranch=SOURCE_BRANCH,sourceRevision=source_revision,runId=run,runAttempt=1,actor=actor,
        runUrl='https://github.com/'+REPOSITORY+'/actions/runs/'+run,trustedCode=bindings)

def nonsecret_state(state):
    # Do not redact into a different digest. Unexpected/free-text values block
    # before any state is serialized; successful receipts retain exact normalized bytes.
    require(set(state)=={'worker','settings','workersDev','domains','legacyRoutes','scope'} and state['worker']==WORKER,'probe_state_shape')
    settings=state['settings']
    require(set(settings)=={'bindings','compatibility_date','compatibility_flags','logpush','placement','tags','tail_consumers','usage_model'},'probe_nonpublic_setting_shape')
    require(settings['bindings']==[] and settings['compatibility_flags']==[] and settings['placement']=={} and settings['tags']==[] and settings['tail_consumers']==[],'probe_free_text_settings_blocked')
    require(type(settings['logpush']) is bool and settings['usage_model'] in ('standard','bundled','unbound'),'probe_setting_value_blocked')
    date=settings['compatibility_date'];require(isinstance(date,str) and re.fullmatch(r'20[0-9]{2}-[0-9]{2}-[0-9]{2}',date),'probe_date_value_blocked')
    datetime.date.fromisoformat(date)
    require(set(state['workersDev'])=={'enabled','previews_enabled'} and all(type(v) is bool for v in state['workersDev'].values()),'probe_exposure_value_blocked')
    domains=state['domains'];require(isinstance(domains,list) and len(domains)==1,'probe_domain_scope_blocked')
    for row in domains:
        require(set(row)=={'id','hostname','service','environment','zone_id','zone_name','enabled','previews_enabled'},'probe_domain_shape_blocked')
        require(row['hostname']==HOSTNAME and row['service']==WORKER and row['environment'] in (None,'production') and row['zone_name'] in (None,'fwith.kr'),'probe_domain_identity_blocked')
        require(isinstance(row['zone_id'],str) and re.fullmatch('[0-9a-fA-F]{32}',row['zone_id']),'probe_zone_identifier_blocked')
        require(isinstance(row['id'],str) and re.fullmatch(r'(?:[0-9a-fA-F]{32}|[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12})',row['id']),'probe_domain_identifier_blocked')
        require(all(row[k] is None or type(row[k]) is bool for k in ('enabled','previews_enabled')),'probe_domain_flag_blocked')
    require(state['legacyRoutes']=={'state':'not_read_not_modified','requiresAssetsOnlyConfig':True} and state['scope']=='fixed-worker-and-existing-fwith.kr-domains','probe_inventory_scope_blocked')
    return state

def observe():
    context=trusted_control()
    # Import only after exact current-main code bytes are checked. The publication
    # authority is deliberately neither read nor accepted by this observation path.
    publisher=importlib.import_module('publish')
    require(publisher.REPOSITORY==REPOSITORY and publisher.HOSTNAME==HOSTNAME and publisher.WORKER==WORKER,'probe_fixed_target_drift')
    account,get=publisher.provider_transport()
    state=publisher.inspect_existing(account,get,{'worker':WORKER,'productionOrigin':ORIGIN})
    nonsecret_state(state)
    current_refs(context['controlRevision'],context['sourceRevision'])
    return dict(schemaVersion=1,status='OBSERVED_NOT_APPROVED',**context,siteKey=SITE_KEY,hostname=HOSTNAME,worker=WORKER,
        observedAt=datetime.datetime.now(datetime.timezone.utc).isoformat(),accountIdSha256=sha(account.encode()),
        providerState=state,providerStateSha256=sha(compact(state)),providerOperations='GET_ONLY',providerMutationsPerformed=False,
        releaseAuthority='NOT_GRANTED',providerApproval='NOT_GRANTED',publication='NOT_ATTEMPTED',
        legacyRoutes='not_read_not_modified',limitations=['Observation only; an independent reviewer must assess the exact state.',
        'No source build, release tuple, public-byte validation, IndexNow, GSC or visual verification was performed.'])

def safe_error(error):
    if isinstance(error,HTTPError):return 'provider_http_'+str(error.code)
    if type(error) is ValueError and re.fullmatch('[A-Za-z0-9_]+',str(error)):return str(error)
    return type(error).__name__

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--report',type=Path,required=True);args=parser.parse_args()
    # A fixed workflow output filename avoids credential-bearing writes to arbitrary paths.
    require(args.report==Path('provider-observation.json') and not args.report.exists(),'invalid_probe_report_path')
    try:result=observe();code=0
    except Exception as error:
        result=dict(schemaVersion=1,status='BLOCKED_NOT_APPROVED',code=safe_error(error),hostname=HOSTNAME,worker=WORKER,
            providerMutationsPerformed=False,providerApproval='NOT_GRANTED',releaseAuthority='NOT_GRANTED',publication='NOT_ATTEMPTED');code=1
    args.report.write_text(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('providerState','trustedCode')},sort_keys=True));return code
if __name__=='__main__':raise SystemExit(main())
