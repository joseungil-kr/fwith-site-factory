"""Offline regressions adapted from direct Uijeongbu; fixtures are NOT authority."""
import copy, importlib.util, json, os, re, shutil, stat, sys, tempfile, unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
from urllib.error import HTTPError
from email.message import Message
import guard
import publish as pub
ROOT=Path(__file__).resolve().parents[2]
REV='1'*40;ACCOUNT='2'*32

def approved_fixture():
    a=copy.deepcopy(guard.load(pub.AUTH/'authority.json'))
    a.update(status='APPROVED_EXACT_RELEASE',sourceRevision=REV,reviewedControlRevision='2'*40,freshMainRevision='3'*40,deltaSha256='4'*64)
    a['provider'].update(status='CURRENT_STATE_INDEPENDENTLY_ACCEPTED',reviewer='/root',sourceRevision=REV,controlCodeRevision='2'*40,acceptedStateSha256='5'*64)
    a['indexnow'].update(status='EXISTING_AUTHORIZED_JOURNAL_VERIFIED',receiptIssue=219)
    return a

def state_fixture():
    return dict(worker=pub.WORKER,settings={'bindings':[],'compatibility_date':'2026-09-29','compatibility_flags':[],'logpush':False,'placement':{},'tags':[],'tail_consumers':[],'usage_model':'standard'},workersDev={'enabled':True,'previews_enabled':True},domains=[domain_fixture()],legacyRoutes={'state':'not_read_not_modified','requiresAssetsOnlyConfig':True},scope='fixed-worker-and-existing-fwith.kr-domains')

def domain_fixture():
    return dict(id='fixed-domain-id',hostname=pub.HOSTNAME,service=pub.WORKER,environment=None,zone_id='zone',zone_name='fwith.kr',enabled=None,previews_enabled=None)

class Provider:
    def __init__(self):self.state=state_fixture();self.domains=[domain_fixture()];self.names=[pub.WORKER];self.calls=[]
    def __call__(self,path):
        self.calls.append(path)
        if '/workers/scripts?' in path:v=[{'id':n} for n in self.names]
        elif '/workers/domains?' in path:v=self.domains
        elif path.endswith('/settings'):v=self.state['settings']
        elif path.endswith('/subdomain'):v=self.state['workersDev']
        else:v={'id':ACCOUNT}
        return {'success':True,'result':v}

class GuardTests(unittest.TestCase):
    def test_proposal_is_pending_not_fabricated_authority(self):
        a=approved_fixture();a['status']='PENDING_ROOT_RELEASE_AND_PROVIDER_REVIEW'
        with self.assertRaisesRegex(ValueError,'pending_current_release_authority'):guard.authority_record(a,REV)
    def test_persisted_authority_supports_pending_or_actual_approved_schema(self):
        a=guard.load(pub.AUTH/'authority.json')
        self.assertIn(a['status'],('PENDING_ROOT_RELEASE_AND_PROVIDER_REVIEW','APPROVED_EXACT_RELEASE'))
        if a['status']=='APPROVED_EXACT_RELEASE':guard.authority_record(a,a['sourceRevision'])
    def test_runtime_authority_blob_mismatch_blocks(self):
        a=approved_fixture();env={'GITHUB_REPOSITORY':pub.REPOSITORY,'GITHUB_REF':'refs/heads/main','GITHUB_EVENT_NAME':'workflow_dispatch','GITHUB_RUN_ATTEMPT':'1','GITHUB_SHA':'a'*40}
        with patch.dict(os.environ,env),patch.object(guard,'load',return_value=a),patch.object(guard,'git',side_effect=[('a'*40+'\n').encode(),b'tampered authority']):
            with self.assertRaisesRegex(ValueError,'authority_worktree_differs_from_runtime_blob'):guard.control(REV)
    def test_missing_config_in_control_minimum_blocks(self):
        a=approved_fixture();a['controlFiles']={guard.WORKFLOW:'5'*64};env={'GITHUB_REPOSITORY':pub.REPOSITORY,'GITHUB_REF':'refs/heads/main','GITHUB_EVENT_NAME':'workflow_dispatch','GITHUB_RUN_ATTEMPT':'1','GITHUB_SHA':'a'*40}
        with patch.dict(os.environ,env),patch.object(guard,'load',return_value=a),patch.object(guard,'git',side_effect=[('a'*40+'\n').encode(),(pub.AUTH/'authority.json').read_bytes(),('a'*40+' refs/heads/main\n').encode(),(REV+' refs/heads/source\n').encode()]):
            with self.assertRaisesRegex(ValueError,'incomplete_trusted_control_binding'):guard.control(REV)
    def test_synthetic_complete_tuple_accepts_null_original_plan(self):
        a=approved_fixture();self.assertEqual(guard.authority_record(a,REV),a);self.assertIsNone(a['plan']['originalPlannedN'])
    def test_source_control_baseline_independence_binding_negatives(self):
        cases=[('sourceRevision','0'*40),('reviewedControlRevision',None),('freshMainRevision','abc'),('baselineRevision','0'*40),('sourceBranch','site-factory-goyang-v2'),('author','/root'),('reviewer','writer'),('deltaSha256',None),('sevenBindings',{})]
        for key,value in cases:
            with self.subTest(key=key):
                a=approved_fixture();a[key]=value
                with self.assertRaises(ValueError):guard.authority_record(a,REV)
    def test_provider_pending_stale_or_self_reviewed_blocks(self):
        for key,value in [('status','passed'),('reviewer','/root/integrate_reviewed_legacy_copy'),('sourceRevision','0'*40),('controlCodeRevision','0'*40),('acceptedStateSha256',None)]:
            with self.subTest(key=key):
                a=approved_fixture();a['provider'][key]=value
                with self.assertRaises(ValueError):guard.authority_record(a,REV)
    def test_pixel_pass_missing_viewport_or_stale_binding_blocks(self):
        for key,value in [('status','PASS'),('pixelQA',True),('viewports',['desktop']),('staticContractSha256','0'*64)]:
            with self.subTest(key=key):
                a=approved_fixture();a['visual'][key]=value
                with self.assertRaises(ValueError):guard.authority_record(a,REV)
    def test_invented_original_count_or_removed_current_scope_blocks(self):
        for key,value in [('originalPlannedN',83),('heldRoutes',['/fiction/']),('publicDetailCount',54),('regionalCoverageUnits',52)]:
            with self.subTest(key=key):
                a=approved_fixture();a['plan'][key]=value
                with self.assertRaises(ValueError):guard.authority_record(a,REV)
    def test_remote_source_head_or_wrong_delta_block(self):
        p={'branch':guard.BRANCH,'root':guard.ROOT};a=dict(approved_fixture(),revision=REV)
        with patch.object(guard.legacy,'git',return_value=b'0000000000000000000000000000000000000000 refs/heads/x\n'):
            with self.assertRaisesRegex(ValueError,'Remote branch'):guard.legacy.lineage(Path('/fixture'),p,a,'production')
        with patch.object(guard.legacy,'git',side_effect=[(REV+' refs/heads/x\n').encode(),b'wrong delta']),patch.object(guard.legacy.subprocess,'run'):
            with self.assertRaisesRegex(ValueError,'Unreviewed baseline delta'):guard.legacy.lineage(Path('/fixture'),p,a,'production')
    def test_wrong_runtime_control_and_main_cas_fail_before_evidence(self):
        a=approved_fixture();env={'GITHUB_REPOSITORY':pub.REPOSITORY,'GITHUB_REF':'refs/heads/main','GITHUB_EVENT_NAME':'workflow_dispatch','GITHUB_RUN_ATTEMPT':'1','GITHUB_SHA':'a'*40}
        with patch.dict(os.environ,env),patch.object(guard,'load',return_value=a),patch.object(guard,'git',return_value=b'bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb\n'):
            with self.assertRaisesRegex(ValueError,'wrong_runtime_control_revision'):guard.control(REV)
        with patch.dict(os.environ,env),patch.object(guard,'load',return_value=a),patch.object(guard,'git',side_effect=[('a'*40+'\n').encode(),(pub.AUTH/'authority.json').read_bytes(),('b'*40+' refs/heads/main\n').encode()]):
            with self.assertRaisesRegex(ValueError,'trusted_main_moved'):guard.control(REV)
    def test_source_worktree_only_generated_revision_may_change(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);f=p/guard.ROOT/'src/data/build-revision.json';f.parent.mkdir(parents=True);f.write_text('{"revision":"old"}');files={str(f.relative_to(p)):pub.sha(f.read_bytes())}
            guard.legacy.worktree(p,files,guard.ROOT,REV,False)
            f.write_text(json.dumps({'revision':REV}));guard.legacy.worktree(p,files,guard.ROOT,REV,True)
            f.write_text(json.dumps({'revision':'wrong'}))
            with self.assertRaises(ValueError):guard.legacy.worktree(p,files,guard.ROOT,REV,True)
    def test_evidence_authority_digest_cannot_be_changed(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);f=p/'.github/direct-goyang-copy/review.json';f.parent.mkdir(parents=True);f.write_text('{}');h=pub.sha(f.read_bytes())
            with patch.object(guard,'CONTROL',p):
                self.assertEqual(guard.pinned_evidence(str(f.relative_to(p)),h),{})
                f.write_text('{"changed":true}')
                with self.assertRaisesRegex(ValueError,'evidence_digest_mismatch'):guard.pinned_evidence(str(f.relative_to(p)),h)

class ProviderTests(unittest.TestCase):
    def setUp(self):self.a=approved_fixture();self.a['provider']['acceptedStateSha256']=pub.sha(guard.compact(state_fixture()));self.p=pub.provider_policy(self.a)
    def test_provider_pre_post_lifecycle_and_unchanged_state(self):
        old=Path.cwd()
        with tempfile.TemporaryDirectory() as t:
            try:
                os.chdir(t);Path('release').mkdir();provider=Provider()
                with patch.object(guard,'control',return_value=(self.a,{})) as control,patch.object(pub,'provider_transport',return_value=(ACCOUNT,provider)),patch.dict(os.environ,{'REVISION':REV}):
                    self.assertEqual(pub.provider('before')['state'],'provider_unchanged')
                    self.assertEqual(pub.provider('after')['state'],'provider_unchanged')
                    self.assertEqual(control.call_args.kwargs,{'check_remote':False})
                    provider.state['workersDev']['previews_enabled']=False
                    with self.assertRaisesRegex(ValueError,'provider_state_differs'):pub.provider('after')
                    self.assertFalse(json.loads(Path('provider-observed-after.json').read_text())['workersDev']['previews_enabled'])
            finally:os.chdir(old)
    def test_existing_exact_binding_is_get_only(self):
        provider=Provider();state=pub.inspect_existing(ACCOUNT,provider,self.p);self.assertEqual(state,state_fixture());self.assertTrue(all('/workers/routes' not in p for p in provider.calls))
    def test_absent_worker_misbound_host_duplicate_and_unbound_block(self):
        for change in ('absent','unbound','wrong','duplicate'):
            with self.subTest(change=change):
                p=Provider()
                if change=='absent':p.names=[]
                elif change=='unbound':p.domains=[]
                elif change=='wrong':p.domains[0]['service']='foreign'
                else:p.domains*=2
                with self.assertRaises(ValueError):pub.inspect_existing(ACCOUNT,p,self.p)
    def test_settings_bindings_shape_and_nondefault_fail(self):
        for change in ('bindings','unknown','nondefault'):
            with self.subTest(change=change):
                p=Provider()
                if change=='bindings':p.state['settings']['bindings']=[{'type':'secret_text','name':'redacted'}]
                elif change=='unknown':p.state['settings']['unreviewed']=True
                else:p.state['settings']['usage_model']='bundled'
                if change!='nondefault':
                    with self.assertRaises(ValueError):pub.inspect_existing(ACCOUNT,p,self.p)
                else:
                    state=pub.inspect_existing(ACCOUNT,p,self.p);self.p['providerBaselineSha256']['production']=pub.sha(guard.compact(state))
                    with self.assertRaisesRegex(ValueError,'Nondefault'):pub.helper('write_assets_only_config').configuration(self.p,'production',guard.load(pub.AUTH/'wrangler.staging.jsonc'),state)
    def test_assets_only_config_retains_exposure_no_routes_or_main(self):
        c=pub.helper('write_assets_only_config').configuration(self.p,'production',guard.load(pub.AUTH/'wrangler.staging.jsonc'),state_fixture())
        self.assertIs(c['workers_dev'],True);self.assertIs(c['preview_urls'],True);self.assertFalse({'main','routes','route','bindings','triggers'}&set(c));self.assertEqual(c['name'],pub.WORKER)
    def test_foreign_route_new_capability_or_exposure_change_block(self):
        for key,value in [('routes',[{'pattern':'foreign.fwith.kr','custom_domain':True}]),('main','worker.js'),('workers_dev',False)]:
            source=guard.load(pub.AUTH/'wrangler.staging.jsonc');source[key]=value
            with self.assertRaises(ValueError):pub.helper('write_assets_only_config').configuration(self.p,'production',source,state_fixture())
    def test_changed_preview_settings_or_domain_receipt_blocks(self):
        for change in ('preview','settings','domain'):
            state=state_fixture()
            if change=='preview':state['workersDev']['previews_enabled']=False
            elif change=='settings':state['settings']['logpush']=True
            else:state['domains'][0]['id']='different'
            with self.assertRaisesRegex(ValueError,'Unreviewed live receipt'):pub.helper('write_assets_only_config').configuration(self.p,'production',guard.load(pub.AUTH/'wrangler.staging.jsonc'),state)
    def test_provider_denial_and_legacy_route_call_fail_without_retry(self):
        env={'CLOUDFLARE_ACCOUNT_ID':ACCOUNT,'CLOUDFLARE_API_TOKEN':'fixture-not-real'}
        with patch.dict(os.environ,env),patch.object(pub,'build_opener') as build:
            opener=build.return_value;opener.open.side_effect=HTTPError('https://api.cloudflare.com',403,'Forbidden',{},None)
            account,get=pub.provider_transport()
            with self.assertRaises(HTTPError):get('/accounts/'+ACCOUNT)
            self.assertEqual(opener.open.call_count,1)
            with self.assertRaisesRegex(ValueError,'provider_operation_forbidden'):get('/zones/any/workers/routes')
            self.assertEqual(opener.open.call_count,1)

class ArtifactTests(unittest.TestCase):
    def test_local_url_and_duplicate_metadata_negatives_reused(self):
        for url in ('http://goyang.fwith.kr/','https://other.example/','https://goyang.fwith.kr/a/../b/','https://goyang.fwith.kr/a/?q=1'):
            with self.assertRaises(ValueError):pub.local_path(url)
        with self.assertRaisesRegex(ValueError,'duplicate_metadata'):pub.Page('<meta name="robots" content="index"><meta name="robots" content="noindex">')
    def test_symlink_executable_hidden_redirect_configs_block(self):
        for case in ('symlink','executable','hidden','worker','config'):
            with tempfile.TemporaryDirectory() as t:
                p=Path(t);f=p/'test';f.write_text('x')
                if case=='symlink':(p/'link').symlink_to(f)
                elif case=='executable':f.chmod(0o755)
                elif case=='hidden':(p/'.x').write_text('x')
                elif case=='worker':(p/'_worker.js').write_text('x')
                else:(p/'wrangler.json').write_text('{}')
                with self.assertRaises(ValueError):pub.inventory(p)
    def test_release_redirect_config_blocked(self):
        old=Path.cwd()
        with tempfile.TemporaryDirectory() as t:
            try:
                os.chdir(t);Path('release').mkdir();Path('.wrangler/deploy').mkdir(parents=True);Path('.wrangler/deploy/config.json').write_text('{}')
                with self.assertRaisesRegex(ValueError,'wrangler_config_redirect'):pub.no_redirect_config()
            finally:os.chdir(old)
    def test_http_denials_and_redirects_block(self):
        http=pub.helper('verify_http')
        for status in (401,403,429,301,302):
            response=MagicMock(status=status,url=pub.ORIGIN+'/')
            with self.assertRaises(AssertionError):http.assert_response_status(response,pub.ORIGIN+'/','/',200)
    def test_wrong_digest_or_run_identity_blocks_before_static(self):
        old=Path.cwd();a=approved_fixture();authority={'exact':'tuple'}
        with tempfile.TemporaryDirectory() as t:
            try:
                os.chdir(t);Path('release/dist').mkdir(parents=True);Path('release/release.json').write_text('{}')
                with patch.object(guard,'control',return_value=(a,authority)),patch.dict(os.environ,{'REVISION':REV,'RELEASE_SHA256':'0'*64}):
                    with self.assertRaisesRegex(ValueError,'manifest_digest_mismatch'):pub.artifact()
                with patch.object(guard,'control',return_value=(a,authority)),patch.object(pub,'inventory',return_value={}),patch.dict(os.environ,{'REVISION':REV,'GITHUB_SHA':'2'*40,'GITHUB_RUN_ID':'123','RELEASE_SHA256':pub.sha(b'{}')}):
                    with self.assertRaisesRegex(ValueError,'artifact_identity_or_digest_mismatch'):pub.artifact()
            finally:os.chdir(old)
    @unittest.skipUnless(os.environ.get('GOYANG_REVIEWED_DIST'),'External reviewed artifact fixture is supplied for offline proposal review only')
    def test_exact_reviewed_artifact_positive_and_byte_drift_negatives(self):
        reference=Path(os.environ['GOYANG_REVIEWED_DIST']);contract=guard.load(pub.AUTH/'reviewed-static-contract.json');rev=contract['referenceRevision']
        self.assertEqual(len(pub.check_static(reference,contract,rev,[])['files']),94)
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)/'dist';shutil.copytree(reference,root)
            for name in ['index.html','funeral/ilsan-paik-funeral-wreath/index.html','sitemap-0.xml','robots.txt','404.html','images/products/funeral-basic.webp']:
                f=root/name
                if not f.exists():continue
                saved=f.read_bytes();f.write_bytes(saved+b'changed')
                with self.subTest(path=name):
                    with self.assertRaises(ValueError):pub.check_static(root,contract,rev,[])
                f.write_bytes(saved)
            with self.assertRaises(ValueError):pub.check_static(root,contract,'0'*40,[])
            with self.assertRaisesRegex(ValueError,'held_route_built'):pub.check_static(root,contract,rev,['/funeral/ilsan-paik-funeral-wreath/'])
            for f in root.rglob('*.html'):f.write_bytes(f.read_bytes().replace(rev.encode(),REV.encode()))
            self.assertEqual(len(pub.check_static(root,contract,REV,[])['pages']),74)
            (root/'extra.txt').write_text('extra')
            with self.assertRaises(ValueError):pub.check_static(root,contract,REV,[])
    def test_workflow_fixed_dispatch_no_target_code_in_publisher(self):
        w=(ROOT/guard.WORKFLOW).read_text();build,publish=w.split('  build:\n',1)[1].split('  publish:\n',1);final=publish.split('  finalize_indexnow:\n',1)[1]
        self.assertIn('  workflow_dispatch:',w)
        for x in ('  push:','  schedule:','  workflow_run:','  pull_request:'):self.assertNotIn(x,w.split('permissions:',1)[0])
        self.assertIn("github.ref == 'refs/heads/main'",w);self.assertIn("ref: 'heads/"+guard.BRANCH+"'",w)
        self.assertNotIn('secrets.',build);self.assertNotIn('MANUAL_PREVIEW',w)
        for x in ('npm ci','npm test','npm run build','npm run qa'):self.assertIn(x,build);self.assertNotIn(x,publish)
        for x in ('CLOUDFLARE','secrets.','wrangler@','provider-before','provider-after'):self.assertNotIn(x,final)
        self.assertIn('group: goyang-reviewed-manual-release',w);self.assertEqual(w.count('group: site-staging-${{ github.repository }}'),3)
        self.assertIn('wrangler@4.147.0',publish);self.assertIn('a.digest',publish);self.assertIn('a.workflow_run?.id',publish)
        self.assertNotIn('publish.py attach',w);self.assertNotIn('domain_attach',Path(pub.__file__).read_text());self.assertNotIn('GSC',w)
        self.assertIn("steps.deploy.outcome == 'failure'",publish);self.assertIn('cancel-in-progress: false',w)
        self.assertEqual(set(re.findall(r'secrets[.]([A-Z_]+)',w)),{'CLOUDFLARE_API_TOKEN','CLOUDFLARE_ACCOUNT_ID'})
    def test_diagnostic_http_does_not_require_remote_ref_cas(self):
        old=Path.cwd();a=approved_fixture();c={'files':{'404.html':pub.sha(b'404body')},'heldRoutes':[]}
        with tempfile.TemporaryDirectory() as t:
            try:
                os.chdir(t);Path('release/dist').mkdir(parents=True);Path('release/release.json').write_text('{}');pub.save('http-contract.json',c)
                response=MagicMock();response.__enter__.return_value=response;response.status=404;response.url=pub.ORIGIN+'/__goyang_release_missing_'+REV+'__/';response.headers={};response.read.return_value=b'404body'
                http=pub.helper('verify_http')
                with patch.object(guard,'control',return_value=(a,{})) as control,patch.object(pub,'check_static',return_value=c),patch.object(pub,'helper',return_value=http),patch.object(http,'request_response',return_value=response),patch.dict(os.environ,{'REVISION':REV,'GITHUB_SHA':'2'*40}):
                    self.assertEqual(pub.public_http()['state'],'public_release_verified')
                    control.assert_called_once_with(REV,check_remote=False)
            finally:os.chdir(old)
    def test_indexnow_rejects_stale_public_receipt_before_network(self):
        old=Path.cwd()
        with tempfile.TemporaryDirectory() as t:
            try:
                os.chdir(t);pub.save('public-http.json',{'state':'public_release_verified','revision':'0'*40})
                with patch.object(guard,'control',return_value=(approved_fixture(),{})),patch.dict(os.environ,{'REVISION':REV}),patch.object(pub,'helpers') as helpers:
                    with self.assertRaisesRegex(ValueError,'public_receipt_missing_or_stale'):pub.indexnow()
                    helpers.assert_not_called()
            finally:os.chdir(old)
    def test_wrapper_has_no_attach_dispatch_or_beacon_content_rewriting(self):
        text=Path(pub.__file__).read_text();self.assertNotIn("method='PUT'",text);self.assertNotIn('strip_one_cf_beacon',text);self.assertNotIn("'attach'",text)
        self.assertIn('Journal(REPOSITORY,',text);self.assertIn("siteKey='goyang-flower-v2'",text)

class JournalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pub.helpers();import indexnow_finalize
        cls.engine=indexnow_finalize
    def test_fixed_journal_and_reference_finalizer_bytes(self):
        self.assertEqual(pub.RECEIPT_ISSUE,219)
        self.assertEqual(self.engine.Journal(pub.REPOSITORY,219).path,'repos/joseungil-kr/fwith-site-factory/issues/219/comments')
        self.assertEqual(pub.sha(Path(self.engine.__file__).read_bytes()),'55f5274d3fcc713e82fd8ce18e280447e68e9e460bc1ff3f9bf5cc683834935f')
    def test_new_source_and_urlset_do_not_reuse_historical_received(self):
        engine=self.engine;site={'siteKey':'goyang-flower-v2','siteUrl':pub.ORIGIN,'indexnowKey':'fixtureproof123'};urls=[pub.ORIGIN+'/',pub.ORIGIN+'/new/']
        journal=MagicMock();journal.records.return_value=[{'fingerprint':'historical-fingerprint','state':'received','httpStatus':200}]
        transport=MagicMock(return_value=(200,'',{}))
        with patch.object(engine,'verify_public',return_value=urls):result=engine.finalize(site,REV,Path('/unused'),journal,transport=transport)
        self.assertEqual(result['state'],'received');transport.assert_called_once();self.assertEqual(journal.write.call_args_list[0].args[0]['state'],'started');self.assertEqual(result['revision'],REV)
        journal.records.return_value=[result];transport.reset_mock()
        with patch.object(engine,'verify_public',return_value=urls):again=engine.finalize(site,REV,Path('/unused'),journal,transport=transport)
        self.assertEqual(again['state'],'already_received');transport.assert_not_called()
        journal.records.return_value=[dict(result,state='started')]
        with patch.object(engine,'verify_public',return_value=urls):
            with self.assertRaisesRegex(ValueError,'prior_submission_outcome_uncertain'):engine.finalize(site,REV,Path('/unused'),journal,transport=transport)
        transport.assert_not_called()
    def test_observer_scope_and_ownership_redaction_reused(self):
        old=Path.cwd()
        with tempfile.TemporaryDirectory() as t:
            try:
                os.chdir(t)
                with patch.object(self.engine,'request',return_value=(200,'fixtureproof123',{})) as request:
                    pub.observed_indexnow_request('GET',pub.ORIGIN+'/fixtureproof123.txt')
                    self.assertNotIn('fixtureproof123',Path('indexnow-http-observations.json').read_text())
                    with self.assertRaisesRegex(ValueError,'indexnow_observation_scope_mismatch'):pub.observed_indexnow_request('POST',pub.ORIGIN+'/')
                    self.assertEqual(request.call_count,1)
            finally:os.chdir(old)


import provider_probe as probe
publish=pub
CODE='c'*40;SOURCE='a'*40;ACCOUNT='2'*32

def context():return dict(repository=probe.REPOSITORY,controlRevision=CODE,sourceBranch=probe.SOURCE_BRANCH,sourceRevision=SOURCE,runId='123',runAttempt=1,actor='owner',runUrl='https://github.com/'+probe.REPOSITORY+'/actions/runs/123',trustedCode={'fixture':'unit-only'})
def env():return dict(GITHUB_REPOSITORY=probe.REPOSITORY,GITHUB_REF='refs/heads/main',GITHUB_EVENT_NAME='workflow_dispatch',GITHUB_SHA=CODE,EXPECTED_REVISION=SOURCE,GITHUB_RUN_ID='123',GITHUB_RUN_ATTEMPT='1',GITHUB_ACTOR='owner')
def domain(host=probe.HOSTNAME,worker=probe.WORKER):return dict(id='d'*32,hostname=host,service=worker,environment=None,zone_id='e'*32,zone_name='fwith.kr',enabled=None,previews_enabled=None)
class ProbeProvider:
    def __init__(self):
        self.calls=[];self.names=[probe.WORKER,'unrelated-private-worker'];self.domains=[domain(),domain('unrelated-private.example','unrelated-private-worker')]
        self.settings={'bindings':[],'compatibility_date':'2026-09-29','compatibility_flags':[],'logpush':False,'placement':{},'tags':[],'tail_consumers':[],'usage_model':'standard'}
        self.subdomain={'enabled':True,'previews_enabled':True}
    def __call__(self,path):
        self.calls.append(path)
        if path.endswith('/settings'):result=self.settings
        elif path.endswith('/subdomain'):result=self.subdomain
        elif '/workers/scripts?' in path:result=[{'id':name} for name in self.names]
        elif '/workers/domains?' in path:result=self.domains
        else:result={'id':ACCOUNT}
        return {'success':True,'result':result}

class ProbeTests(unittest.TestCase):
    def test_exact_source_code_main_and_filtered_observed_receipt(self):
        provider=ProbeProvider()
        with patch.object(probe,'trusted_control',return_value=context()),patch.object(probe,'current_refs') as refs,patch.object(publish,'provider_transport',return_value=(ACCOUNT,provider)),patch.object(publish.guard,'control',side_effect=AssertionError('Publication authority must not be read')):
            receipt=probe.observe()
        self.assertEqual(receipt['status'],'OBSERVED_NOT_APPROVED');self.assertEqual(receipt['sourceRevision'],SOURCE);self.assertEqual(receipt['controlRevision'],CODE)
        self.assertEqual(receipt['providerStateSha256'],probe.sha(probe.compact(receipt['providerState'])))
        self.assertEqual(receipt['providerApproval'],'NOT_GRANTED');self.assertFalse(receipt['providerMutationsPerformed']);refs.assert_called_once_with(CODE,SOURCE)
        encoded=json.dumps(receipt);self.assertNotIn('unrelated-private',encoded);self.assertNotIn(ACCOUNT,encoded)
        self.assertTrue(all('/workers/routes' not in p for p in provider.calls))
    def test_absent_host_wrong_worker_or_duplicate_domains_block(self):
        for mode in ('absent-worker','absent-host','misbound','duplicate'):
            p=ProbeProvider()
            if mode=='absent-worker':p.names=[]
            elif mode=='absent-host':p.domains=[]
            elif mode=='misbound':p.domains=[domain(worker='foreign')]
            else:p.domains=[domain(),domain()]
            with self.subTest(mode=mode),patch.object(probe,'trusted_control',return_value=context()),patch.object(publish,'provider_transport',return_value=(ACCOUNT,p)):
                with self.assertRaises(ValueError):probe.observe()
    def test_secret_bindings_unknown_settings_and_incomplete_exposure_block(self):
        for mode in ('secret','unknown','preview-shape'):
            p=ProbeProvider()
            if mode=='secret':p.settings['bindings']=[{'name':'secret','type':'secret_text','text':'DO_NOT_LOG'}]
            elif mode=='unknown':p.settings['unknown_sensitive']='DO_NOT_LOG'
            else:p.subdomain['unreviewed']='DO_NOT_LOG'
            with self.subTest(mode=mode),patch.object(probe,'trusted_control',return_value=context()),patch.object(publish,'provider_transport',return_value=(ACCOUNT,p)):
                with self.assertRaises(ValueError):probe.observe()
    def test_private_canaries_never_reach_receipt_or_stdout(self):
        import contextlib,io
        canary='PRIVATE_CANARY_MUST_NOT_LEAVE'
        for field in ('tags','placement','limits','compatibility_flags','zone_id','zone_name','id','observability'):
            provider=ProbeProvider()
            if field in ('zone_id','zone_name','id'):provider.domains[0][field]=canary
            elif field in ('tags','compatibility_flags'):provider.settings[field]=[canary]
            else:provider.settings[field]={'private':canary}
            old=Path.cwd()
            with self.subTest(field=field),tempfile.TemporaryDirectory() as tmp:
                try:
                    os.chdir(tmp);stdout=io.StringIO()
                    with patch.object(probe,'trusted_control',return_value=context()),patch.object(probe,'current_refs'),patch.object(publish,'provider_transport',return_value=(ACCOUNT,provider)),patch.object(sys,'argv',['probe','--report','provider-observation.json']),contextlib.redirect_stdout(stdout):
                        self.assertEqual(probe.main(),1)
                    raw=Path('provider-observation.json').read_text();self.assertNotIn(canary,raw+stdout.getvalue());self.assertNotIn('providerState',json.loads(raw))
                finally:os.chdir(old)
    def test_live_nondefault_settings_are_observed_without_acceptance(self):
        p=ProbeProvider();p.settings['usage_model']='bundled'
        with patch.object(probe,'trusted_control',return_value=context()),patch.object(probe,'current_refs'),patch.object(publish,'provider_transport',return_value=(ACCOUNT,p)):
            result=probe.observe()
        self.assertEqual(result['providerState']['settings']['usage_model'],'bundled');self.assertEqual(result['providerApproval'],'NOT_GRANTED')
    def test_after_read_ref_movement_blocks_approval_free_observation(self):
        with patch.object(probe,'trusted_control',return_value=context()),patch.object(probe,'current_refs',side_effect=ValueError('probe_main_or_source_moved')),patch.object(publish,'provider_transport',return_value=(ACCOUNT,ProbeProvider())):
            with self.assertRaisesRegex(ValueError,'probe_main_or_source_moved'):probe.observe()
    def test_transport_denial_is_not_retried_and_legacy_route_is_forbidden(self):
        with patch.dict(os.environ,{'CLOUDFLARE_ACCOUNT_ID':ACCOUNT,'CLOUDFLARE_API_TOKEN':'UNIT_SECRET_DO_NOT_LOG'}),patch.object(publish,'build_opener') as opener:
            opener.return_value.open.side_effect=HTTPError('https://api.cloudflare.com',403,'UNIT_SECRET_DO_NOT_LOG',{},None)
            _,get=publish.provider_transport()
            with self.assertRaises(HTTPError):get('/accounts/'+ACCOUNT)
            with self.assertRaisesRegex(ValueError,'provider_operation_forbidden'):get('/zones/private/workers/routes')
            self.assertEqual(opener.return_value.open.call_count,1)
    def test_mutating_methods_or_foreign_endpoint_are_not_exposed(self):
        with patch.dict(os.environ,{'CLOUDFLARE_ACCOUNT_ID':ACCOUNT,'CLOUDFLARE_API_TOKEN':'UNIT_SECRET'}),patch.object(publish,'build_opener') as opener:
            _,get=publish.provider_transport()
            with self.assertRaises(TypeError):get('POST','/accounts/'+ACCOUNT,{})
            for path in ['/accounts/'+ACCOUNT+'/tokens','/accounts/'+ACCOUNT+'/workers/scripts/foreign/settings','/zones/zone/workers/routes','/accounts/'+ACCOUNT+'/workers/domains?custom=1']:
                with self.assertRaises(ValueError):get(path)
            opener.return_value.open.assert_not_called()
    def test_fixed_identity_drift_before_credentials_is_rejected(self):
        with patch.object(probe,'trusted_control',return_value=context()),patch.object(publish,'WORKER','other'),patch.object(publish,'provider_transport') as transport:
            with self.assertRaisesRegex(ValueError,'probe_fixed_target_drift'):probe.observe()
            transport.assert_not_called()
    def test_trusted_main_and_source_ref_negatives(self):
        good=(CODE+'\trefs/heads/main\n'+SOURCE+'\trefs/heads/'+probe.SOURCE_BRANCH+'\n').encode()
        with patch.object(probe,'git',return_value=good):probe.current_refs(CODE,SOURCE)
        for data in [b'',good.replace(SOURCE.encode(),b'b'*40),good.replace(CODE.encode(),b'd'*40),good+good]:
            with patch.object(probe,'git',return_value=data):
                with self.assertRaises(ValueError):probe.current_refs(CODE,SOURCE)
    def test_invalid_dispatch_context_source_sha_and_reruns_block(self):
        for key,value in [('GITHUB_REPOSITORY','foreign/repo'),('GITHUB_REF','refs/heads/source'),('GITHUB_EVENT_NAME','push'),('GITHUB_SHA','short'),('EXPECTED_REVISION',''),('GITHUB_RUN_ATTEMPT','2')]:
            e=env();e[key]=value
            with self.subTest(key=key),patch.dict(os.environ,e),patch.object(probe,'git') as git:
                with self.assertRaises(ValueError):probe.trusted_control()
                git.assert_not_called()
    def test_exact_git_blob_checks_and_drift_symlink_negatives(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            for name in probe.CODE_FILES:
                p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'fixture code\n')
            def git(*args):
                if args[0]=='rev-parse':return (CODE+'\n').encode()
                if args[0]=='ls-tree':return ('100644 blob '+'1'*40+'\t'+args[-1]+'\n').encode()
                if args[0]=='show':return b'fixture code\n'
                raise AssertionError(args)
            with patch.object(probe,'CONTROL',root),patch.dict(os.environ,env()),patch.object(probe,'current_refs'),patch.object(probe,'git',side_effect=git),patch.object(probe,'verify_source_identity',return_value={'sourceFilesVerified':182}):
                self.assertEqual(len(probe.trusted_control()['trustedCode']),len(probe.CODE_FILES))
                p=root/probe.CODE_FILES[-1];p.write_bytes(b'changed')
                with self.assertRaisesRegex(ValueError,'probe_code_worktree_drift'):probe.trusted_control()
                p.unlink();p.symlink_to(root/probe.CODE_FILES[0])
                with self.assertRaisesRegex(ValueError,'probe_code_symlink'):probe.trusted_control()
    def test_full_source_blob_path_hash_size_negatives(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);p=root/probe.MANIFEST;p.parent.mkdir(parents=True)
            files=[{'path':'f'+str(i),'gitBlob':format(i,'040x'),'sha256':probe.sha(b'x'),'bytes':1} for i in range(182)]
            p.write_text(json.dumps({'fileCount':182,'files':files}));manifest_hash=probe.sha(p.read_bytes())
            rows=b''.join(('100644 blob '+row['gitBlob']+'\t'+probe.SOURCE_ROOT+'/'+row['path']).encode()+b'\0' for row in files)
            for case in ('good','missing','symlink','blob','bytes','manifest'):
                tree=rows
                if case=='missing':tree=rows.split(b'\0',1)[1]
                elif case=='symlink':tree=rows.replace(b'100644',b'120000',1)
                elif case=='blob':tree=rows.replace(b'0'*40,b'f'*40,1)
                def git(*args):return tree if args[0]=='ls-tree' else b'changed' if case=='bytes' else b'x'
                with self.subTest(case=case),patch.object(probe,'CONTROL',root),patch.object(probe,'MANIFEST_SHA256','0'*64 if case=='manifest' else manifest_hash),patch.object(probe,'git',side_effect=git):
                    if case=='good':self.assertEqual(probe.verify_source_identity(SOURCE)['sourceFilesVerified'],182)
                    else:
                        with self.assertRaises(ValueError):probe.verify_source_identity(SOURCE)
    def test_safe_error_never_exposes_provider_bodies_or_credentials(self):
        self.assertEqual(probe.safe_error(HTTPError('https://private',403,'SECRET',{},None)),'provider_http_403')
        self.assertEqual(probe.safe_error(ValueError('secret token value: SECRET')),'ValueError')
        self.assertEqual(probe.safe_error(RuntimeError('SECRET')),'RuntimeError')
    def test_main_retains_sanitized_failure_and_no_approval(self):
        old=Path.cwd()
        with tempfile.TemporaryDirectory() as tmp:
            try:
                os.chdir(tmp)
                with patch.object(sys,'argv',['probe','--report','provider-observation.json']),patch.object(probe,'observe',side_effect=HTTPError('https://private',403,'SECRET',{},None)):
                    self.assertEqual(probe.main(),1)
                raw=Path('provider-observation.json').read_text();self.assertNotIn('SECRET',raw);self.assertNotIn('https://private',raw);self.assertEqual(json.loads(raw)['status'],'BLOCKED_NOT_APPROVED')
            finally:os.chdir(old)
    def test_workflow_probe_isolation_fixed_source_and_permissions(self):
        workflow=(Path(__file__).resolve().parents[2]/probe.WORKFLOW).read_text();section=workflow.split('  provider_probe:\n',1)[1].split('  build:\n',1)[0]
        self.assertIn("inputs.provider_probe_only == true",section);self.assertIn('EXPECTED_REVISION: ${{ inputs.expected_revision }}',section)
        self.assertIn("ref: 'heads/"+probe.SOURCE_BRANCH+"'",section);self.assertIn('ref: ${{ github.sha }}',section);self.assertIn('persist-credentials: false',section)
        for forbidden in ['working-directory: target','npm ','wrangler@','issues: write','indexnow --','provider-before','upload-ready','source-before','actions/setup-node','expected_revision }}\n          path: target']:
            self.assertNotIn(forbidden,section)
        for job in ['build','publish','finalize_indexnow']:
            text=workflow.split('  '+job+':\n',1)[1]
            self.assertRegex(text,r'(?m)^    if: inputs.provider_probe_only != true')
        self.assertIn("INDEXNOW_ONLY === 'true'",section);self.assertEqual(set(re.findall(r'secrets[.]([A-Z_]+)',section)),{'CLOUDFLARE_API_TOKEN','CLOUDFLARE_ACCOUNT_ID'})
    def test_probe_code_does_not_call_approval_or_mutation(self):
        text=Path(probe.__file__).read_text()
        for forbidden in ['guard.control(',"'authority.json'",'subprocess.run(','write_assets_only_config','indexnow(',"method='PUT'","method='POST'",'npx','npm']:
            self.assertNotIn(forbidden,text)
        self.assertIn("status='OBSERVED_NOT_APPROVED'",text);self.assertIn("providerApproval='NOT_GRANTED'",text)


if __name__=='__main__':unittest.main()
