"""Narrow Goyang adaptation of manual-release gate; no mutation operations."""
import hashlib, importlib.util, json, os, re, subprocess
from pathlib import Path
CONTROL = Path(__file__).resolve().parents[2]
AUTH = CONTROL / '.github/direct-goyang-copy'
ROOT = 'site-factory/goyang-flower'
BRANCH = 'site-factory-goyang-copy-20261011'
BASELINE = '936cf842b4fc82bc801a142db7196059814f266a'
WORKFLOW = '.github/workflows/goyang-copy-direct-publish.yml'
KEYS = ('contentHash','sourcesHash','catalogHash','catalogFileHash','rendererHash','assetsHash','frozenHash')
spec = importlib.util.spec_from_file_location('manual_gate', CONTROL/'scripts/manual-release-20261007/gate.py')
legacy = importlib.util.module_from_spec(spec); spec.loader.exec_module(legacy)
require, digest, compact, git = legacy.require, legacy.digest, legacy.compact, legacy.git

def load(path):
    require(path.is_file() and not path.is_symlink(), 'missing_or_symlink_evidence')
    return json.loads(path.read_bytes())

def pinned_evidence(relative, expected):
    require(isinstance(relative,str) and relative.startswith('.github/direct-goyang-copy/') and '..' not in Path(relative).parts, 'invalid_evidence_path')
    candidate=CONTROL/relative
    require(all(not (CONTROL/Path(*Path(relative).parts[:i])).is_symlink() for i in range(1,len(Path(relative).parts)+1)), 'evidence_symlink')
    require(digest(candidate.read_bytes())==expected,'evidence_digest_mismatch')
    return load(candidate)

def authority_record(a, revision):
    require(a.get('status')=='APPROVED_EXACT_RELEASE','pending_current_release_authority')
    require(re.fullmatch('[0-9a-f]{40}',revision or '') and a.get('sourceRevision')==revision,'wrong_source_revision')
    require(a.get('sourceBranch')==BRANCH and a.get('sourceRoot')==ROOT and a.get('baselineRevision')==BASELINE,'wrong_source_lineage')
    require(a.get('author')=='/root/integrate_reviewed_legacy_copy' and a.get('reviewer')=='/root' and a['author']!=a['reviewer'],'wrong_independent_identities')
    for key in ('reviewedControlRevision','freshMainRevision'):
        require(re.fullmatch('[0-9a-f]{40}',a.get(key) or ''),'missing_'+key)
    for key in ('deltaSha256','sourceManifestSha256','staticContractSha256','contentReviewSha256'):
        require(re.fullmatch('[0-9a-f]{64}',a.get(key) or ''),'missing_'+key)
    require(set(a.get('sevenBindings',{}))==set(KEYS) and all(re.fullmatch('[0-9a-f]{64}',v or '') for v in a['sevenBindings'].values()),'missing_seven_bindings')
    v=a['visual'];require(v['status']=='DEFERRED_NOT_PASS' and v['pixelQA'] is False and v['viewports']==['desktop','narrow'] and v['sourceManifestSha256']==a['sourceManifestSha256'] and v['staticContractSha256']==a['staticContractSha256'],'wrong_visual_deferral')
    p=a['plan'];require(p.get('status')=='PRESERVED_CURRENT_REVIEWED_SCOPE' and p.get('originalPlannedN') is None and p.get('heldRoutes')==[],'reviewed_scope_or_unknown_original_plan_changed')
    require(p['publicDetailCount']==67 and p['regionalCoverageUnits']==53,'current_reviewed_scope_mismatch')
    require(all(re.fullmatch(r'/[a-z0-9/-]+/',r) and '//' not in r for r in p['heldRoutes']),'unsafe_held_route')
    provider=a['provider'];require(provider.get('status')=='CURRENT_STATE_INDEPENDENTLY_ACCEPTED' and provider.get('reviewer')==a['reviewer'] and provider.get('sourceRevision')==revision and provider.get('controlCodeRevision')==a['reviewedControlRevision'] and re.fullmatch('[0-9a-f]{64}',provider.get('acceptedStateSha256') or ''),'provider_acceptance_pending_or_stale')
    require(a['indexnow'].get('status')=='EXISTING_AUTHORIZED_JOURNAL_VERIFIED' and a['indexnow'].get('receiptIssue')==219 and a['indexnow'].get('siteKey')=='goyang-flower-v2','journal_binding_pending')
    return a

def control(revision, check_remote=True):
    a=authority_record(load(AUTH/'authority.json'),revision)
    require(os.environ.get('GITHUB_REPOSITORY')=='joseungil-kr/fwith-site-factory' and os.environ.get('GITHUB_REF')=='refs/heads/main' and os.environ.get('GITHUB_EVENT_NAME')=='workflow_dispatch' and os.environ.get('GITHUB_RUN_ATTEMPT')=='1','wrong_dispatch_context')
    actual=git(CONTROL,'rev-parse','HEAD').decode().strip()
    require(actual==os.environ.get('GITHUB_SHA') and re.fullmatch('[0-9a-f]{40}',actual),'wrong_runtime_control_revision')
    require((AUTH/'authority.json').read_bytes()==git(CONTROL,'show',actual+':.github/direct-goyang-copy/authority.json'),'authority_worktree_differs_from_runtime_blob')
    if check_remote:
        remote=git(CONTROL,'ls-remote','--heads','origin','refs/heads/main').decode().split()
        require(len(remote)==2 and remote[0]==actual,'trusted_main_moved')
        source_head=git(CONTROL,'ls-remote','--heads','origin','refs/heads/'+BRANCH).decode().split()
        require(len(source_head)==2 and source_head[0]==revision,'source_head_moved')
    require(a['controlFiles'] and WORKFLOW in a['controlFiles'],'missing_control_files')
    static_inputs={'.github/direct-goyang-copy/'+n for n in ('policy.json','baseline-bindings.json','wrangler.staging.jsonc','source-release-manifest.root.json','reviewed-static-contract.json')}
    required=static_inputs | {WORKFLOW, *[str(f.relative_to(CONTROL)) for f in (CONTROL/'scripts/direct-goyang-copy').glob('*.py')], *['scripts/manual-release-20261007/'+n for n in ('gate.py','provider_check.py','write_assets_only_config.py','verify_http.py')], 'site-factory/engine/indexnow_finalize.py'}
    require(required<=set(a['controlFiles']),'incomplete_trusted_control_binding')
    for name,h in a['controlFiles'].items():
        require(not name.startswith('/') and '..' not in Path(name).parts,'unsafe_control_path')
        f=CONTROL/name;require(f.is_file() and not f.is_symlink() and digest(f.read_bytes())==h,'control_worktree_drift')
        require(digest(git(CONTROL,'show',a['reviewedControlRevision']+':'+name))==h,'unreviewed_control_code')
        require(digest(git(CONTROL,'show',actual+':'+name))==h,'runtime_control_blob_drift')
    authority_files=legacy.tracked_files(CONTROL,'.github/direct-goyang-copy',actual)
    require(set(authority_files)==set(a.get('authorityFiles',{})) | {'.github/direct-goyang-copy/authority.json'},'incomplete_authority_file_binding')
    require({k:v for k,v in authority_files.items() if k!='.github/direct-goyang-copy/authority.json'}==a['authorityFiles'],'authority_blob_manifest_mismatch')
    require({str(f.relative_to(CONTROL)) for f in AUTH.rglob('*') if f.is_file()}==set(authority_files),'untracked_authority_file')
    legacy.worktree(CONTROL,authority_files,'.github/direct-goyang-copy',actual,False)
    manifest=load(AUTH/'source-release-manifest.root.json');contract=load(AUTH/'reviewed-static-contract.json')
    require(digest((AUTH/'source-release-manifest.root.json').read_bytes())==a['sourceManifestSha256'],'source_manifest_drift')
    require(digest((AUTH/'reviewed-static-contract.json').read_bytes())==a['staticContractSha256'],'static_contract_drift')
    require(contract['sourceManifestSha256']==a['sourceManifestSha256'],'contract_source_binding')
    config_entry=next(r for r in manifest['files'] if r['path']=='wrangler.staging.jsonc')
    require(digest((AUTH/'wrangler.staging.jsonc').read_bytes())==config_entry['sha256'],'trusted_upload_source_config_drift')
    baseline_manifest=load(AUTH/'baseline-bindings.json')
    require(baseline_manifest['sourceRevision']==BASELINE and digest((AUTH/'baseline-bindings.json').read_bytes())=='996a842ca2c3bf5f29ed8e8c2ed12151b12d77ba8ed7ad60d86c0ff98aa49857','original_baseline_manifest_drift')
    for key in ('provider',):
        evidence=pinned_evidence(a[key]['evidenceFile'],a[key]['evidenceSha256'])
        require(evidence['sourceRevision']==revision and evidence['reviewer']==a['reviewer'],'stale_independent_'+key)
        if key=='provider':require(evidence['acceptedStateSha256']==a[key]['acceptedStateSha256'] and evidence['controlCodeRevision']==a['reviewedControlRevision'],'provider_receipt_binding')
    v=pinned_evidence(a['visual']['authorizationEvidenceFile'],a['visual']['authorizationEvidenceSha256'])
    require(v['status']=='DEFERRED_NOT_PASS' and v['sourceManifestSha256']==a['sourceManifestSha256'] and v['staticContractSha256']==a['staticContractSha256'] and v['viewports']==['desktop','narrow'],'deferral_authorization_mismatch')
    return a,dict(authorityRevision=actual,authoritySha256=digest((AUTH/'authority.json').read_bytes()),reviewedControlRevision=a['reviewedControlRevision'],sourceRevision=revision)

def source(checkout,revision,after=False):
    a,tuple_=control(revision);require(git(checkout,'rev-parse','HEAD').decode().strip()==revision,'source_checkout_mismatch')
    p=load(AUTH/'policy.json');p['branch']=BRANCH
    legacy.lineage(checkout,p,dict(a,revision=revision),'production')
    parents=git(checkout,'show','-s','--format=%P',revision).decode().strip().split()
    require(parents==[a['freshMainRevision'],BASELINE],'source_requires_reviewed_two_parent_merge')
    for rev in (a['freshMainRevision'],BASELINE):
        subprocess.run(['git','-C',str(checkout),'merge-base','--is-ancestor',rev,revision],check=True)
    changed=git(checkout,'diff','--name-only',a['freshMainRevision'],revision).decode().splitlines()
    require(changed and all(n.startswith(ROOT+'/') for n in changed),'source_tree_outside_fixed_root_changed')
    expected={ROOT+'/'+r['path']:r['sha256'] for r in load(AUTH/'source-release-manifest.root.json')['files']}
    require(legacy.tracked_files(checkout,ROOT,revision)==expected,'full_source_blob_manifest_mismatch')
    expected_base={ROOT+'/'+r['path']:r['sha256'] for r in load(AUTH/'baseline-bindings.json')['files']}
    require(legacy.tracked_files(checkout,ROOT,BASELINE)==expected_base,'original_baseline_blob_manifest_mismatch')
    workflows=legacy.tracked_files(checkout,'.github/workflows',revision)
    require(workflows==a['sourceWorkflowFiles'] and workflows==legacy.tracked_files(checkout,'.github/workflows',a['freshMainRevision']),'isolated_source_workflow_tree_mismatch')
    legacy.worktree(checkout,expected,ROOT,revision,after,'revision')
    generated={'node_modules','.astro','dist'} if after else set()
    for f in (checkout/ROOT).rglob('*'):
        if not (set(f.relative_to(checkout/ROOT).parts)&generated):require(not f.is_symlink(),'source_symlink_path')
    actual={str(f.relative_to(checkout)) for f in (checkout/ROOT).rglob('*') if f.is_file() and not (set(f.relative_to(checkout/ROOT).parts)&generated)}
    require(actual==set(expected),'extra_or_missing_source_file')
    review_path=checkout/ROOT/'src/data/manual-review/goyang-customer-copy-review-20261011.json'
    require(digest(review_path.read_bytes())==a['contentReviewSha256'],'content_review_drift')
    review=load(review_path)
    require(review['status']=='approved' and review['writerId']==a['author'] and review['reviewerId']==a['reviewer'] and review['visualQa']=='DEFERRED_NOT_PASS' and review['publicComplete'] is False,'wrong_content_review')
    require({k:review[k] for k in KEYS}==a['sevenBindings'],'seven_binding_drift')
    ledger=load(checkout/ROOT/'src/data/customer-copy-revision-20261011.json')
    require(ledger['scope']['originalPlannedN'] is None and ledger['scope']['heldRoutes']==[] and ledger['scope']['originalPublicArticles']==67 and len(ledger['articles'])==67,'reviewed_ledger_scope_changed')
    require(len(load(checkout/ROOT/'src/data/region-coverage.json')['units'])==53,'regional_coverage_changed')
    return dict(state='source_after_verified' if after else 'source_before_verified',**tuple_)
