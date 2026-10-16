"""Portable offline regressions. Synthetic data never opens the operational seal."""
import ast
import copy
from email.message import Message
import io
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
import unittest
from unittest.mock import patch, Mock
import publish_existing_update as c
import test_existing_update as old


def pins_fixture():
    pins=c.read_json(c.ROOT/'docs/direct-damyang-recovery/update-caller-binding.json')
    pins.update(baseline={'runId':910001,'artifactId':910002,'controlRevision':'b'*40,
        'artifactDigest':'sha256:'+'c'*64,'artifactName':'SYNTHETIC_TEST_ONLY','artifactBytes':123},
        review={'path':'docs/direct-damyang-recovery/SYNTHETIC.json','sha256':'e'*64})
    return pins


def env_fixture():
    return {'GITHUB_REPOSITORY':c.journal.REPOSITORY,'GITHUB_REF':'refs/heads/main',
        'GITHUB_ACTOR':c.reader.OWNER,'GITHUB_TRIGGERING_ACTOR':c.reader.OWNER,'GITHUB_RUN_ATTEMPT':'1',
        'GITHUB_EVENT_NAME':'issues','GITHUB_JOB':c.JOB,'RUNNER_ENVIRONMENT':'github-hosted',
        'GITHUB_SHA':'a'*40,'GITHUB_RUN_ID':'910003'}


def event_fixture(pins,env):
    return {'action':'opened','repository':{'full_name':c.journal.REPOSITORY,
        'owner':{'login':c.reader.OWNER,'type':'User'}},'sender':{'login':c.reader.OWNER,'type':'User'},
        'issue':{'number':910004,'state':'open','title':c.TITLE,'user':{'login':c.reader.OWNER,'type':'User'},
        'body':json.dumps({'schemaVersion':1,'mode':'existing-host-static-proof-update',
            'source_branch':c.reader.SOURCE_BRANCH,'source_revision':c.SOURCE,
            'expected_control_revision':env['GITHUB_SHA'],'receipt_issue':377,
            'operational_binding_sha256':c.journal.digest(pins)})}}


class Case(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        for target in ('socket.create_connection','socket.socket.connect'):
            block=patch(target,side_effect=AssertionError('offline_network_forbidden'));block.start();self.addCleanup(block.stop)
    def blocked(self,fn,reason='.*'):
        with self.assertRaisesRegex((ValueError,c.journal.RecoveryBlocked,AssertionError),reason):fn()


class Authorization(Case):
    def test_dormant_seal_and_exact_actual_baseline_binding(self):
        self.assertIs(c.OPERATIONAL_CONTROLS_ENABLED,True)
        self.assertIs(c.reader.OPERATIONAL_CONTROLS_ENABLED,False)
        pins=c.read_json(c.ROOT/'docs/direct-damyang-recovery/update-caller-binding.json')
        states={'PENDING_INDEPENDENT_UPDATE_CONTROL_REVIEW_WITH_ACCEPTED_ACTUAL_BASELINE':False,
                'INDEPENDENTLY_REVIEWED_ACTUAL_STATIC_UPDATE':True}
        self.assertIn(pins['status'],states)
        self.assertIs(pins['operationalActivationAllowed'],states[pins['status']])
        self.assertTrue(pins['providerBaselineAccepted'])
        desc,observation,review=c.update.accepted_baseline()
        self.assertEqual(desc['observationRunId'],38908264056)
        self.assertEqual(desc['sha256'],'76b26bc3f344e9350b240581ce2bf51ff4858908b797a4aa99b8a87d57a25556')
        self.assertEqual(pins['baseline']['files']['baseline-observation.json'],desc['sha256'])
        self.assertEqual(pins['baseline']['independentAcceptance'],review)
        self.assertIs(observation['baselineAccepted'],False)
        self.assertIs(review['baselineAccepted'],True)
        path=c.ROOT/'docs/direct-damyang-recovery/update-caller-binding.json'
        if pins['operationalActivationAllowed'] is False:
            for key in ('review','controlFiles','workflowFiles','reviewedControlRevision'):self.assertIsNone(pins[key])
            self.blocked(lambda:c.approved_pins(path),'actual_baseline_and_operational_acceptance_required')
        else:
            self.assertEqual(c.approved_pins(path),pins)
            self.assertTrue(c.verify_controls(c.ROOT,pins))
    def test_seal_false_blocks_all_cli_modes_before_environment_or_network(self):
        for mode in c.MODES:
            with self.subTest(mode=mode),patch.object(c,'OPERATIONAL_CONTROLS_ENABLED',False),patch.object(c.sys,'argv',['caller',mode,'--report',str(self.root/'report.json')]),patch.object(c,'UpdateHTTP') as http,patch.dict(os.environ,{'CLOUDFLARE_API_TOKEN':'PRIVATE_SENTINEL','PYTHONPATH':'PRIVATE_SENTINEL'},clear=True):
                self.assertEqual(c.main(),1);http.assert_not_called()
                report=(self.root/'report.json').read_text();self.assertNotIn('PRIVATE_SENTINEL',report);self.assertIn('operational_review_seal_missing',report)
    def pending_binding(self):
        pins=c.read_json(c.ROOT/'docs/direct-damyang-recovery/update-caller-binding.json')
        pins.update(status='PENDING_INDEPENDENT_UPDATE_CONTROL_REVIEW_WITH_ACCEPTED_ACTUAL_BASELINE',operationalActivationAllowed=False,
                    review=None,controlFiles=None,workflowFiles=None,reviewedControlRevision=None)
        path=self.root/'pending-control/docs/direct-damyang-recovery/update-caller-binding.json'
        path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(pins))
        return path
    def test_pending_binding_blocks_all_cli_before_environment_and_transport(self):
        path=self.pending_binding()
        for mode in c.MODES:
            with self.subTest(mode=mode),patch.object(c.sys,'argv',['caller',mode,'--control-root',str(path.parents[2]),'--report',str(self.root/'dormant.json')]),patch.object(c,'authorize') as authorize,patch.object(c,'UpdateHTTP') as http,patch.dict(os.environ,{'CLOUDFLARE_API_TOKEN':'PRIVATE_SENTINEL','GH_TOKEN':'PRIVATE_SENTINEL','GITHUB_EVENT_PATH':'NEVER_READ_EVENT_SENTINEL'},clear=True):
                self.assertEqual(c.main(),1);authorize.assert_not_called();http.assert_not_called()
                report=(self.root/'dormant.json').read_text()
                self.assertNotIn('PRIVATE_SENTINEL',report);self.assertNotIn('NEVER_READ_EVENT_SENTINEL',report)
                self.assertIn('actual_baseline_and_operational_acceptance_required',report)
    def test_only_code_seal_change_cannot_open_null_binding(self):
        path=self.pending_binding()
        with patch.object(c,'OPERATIONAL_CONTROLS_ENABLED',True):
            self.blocked(lambda:c.approved_pins(path),'actual_baseline')
    def test_exact_owner_opened_main_first_hosted_job(self):
        pins=pins_fixture();env=env_fixture();self.assertEqual(c.authorize(pins,env,event_fixture(pins,env),'prepare')['receipt_issue'],377)
    def test_wrong_environment_identity_rejected(self):
        for key,value in [('GITHUB_REPOSITORY','x/y'),('GITHUB_REF','refs/heads/dev'),('GITHUB_ACTOR','other'),('GITHUB_TRIGGERING_ACTOR','other'),('GITHUB_RUN_ATTEMPT','2'),('GITHUB_EVENT_NAME','workflow_dispatch'),('GITHUB_JOB','publish'),('RUNNER_ENVIRONMENT','self-hosted'),('GITHUB_SHA','main'),('GITHUB_RUN_ID','0')]:
            pins=pins_fixture();env=env_fixture();env[key]=value
            with self.subTest(key=key):self.blocked(lambda:c.authorize(pins,env,event_fixture(pins,env),'prepare'))
    def test_closed_issue_body_and_author_identity(self):
        for kind in ('sender','sender-type','owner','issue-user','title','closed','receipt','pr','action','body-extra','body-duplicate','body-long'):
            pins=pins_fixture();env=env_fixture();event=event_fixture(pins,env)
            if kind=='sender':event['sender']['login']='other'
            elif kind=='sender-type':event['sender']['type']='Bot'
            elif kind=='owner':event['repository']['owner']['type']='Organization'
            elif kind=='issue-user':event['issue']['user']['login']='other'
            elif kind=='title':event['issue']['title']='other'
            elif kind=='closed':event['issue']['state']='closed'
            elif kind=='receipt':event['issue']['number']=377
            elif kind=='pr':event['issue']['pull_request']={}
            elif kind=='action':event['action']='reopened'
            elif kind=='body-extra':event['issue']['body']=event['issue']['body'][:-1]+',"extra":true}'
            elif kind=='body-duplicate':event['issue']['body']=event['issue']['body'][:-1]+',"schemaVersion":1}'
            else:event['issue']['body']='x'*4097
            with self.subTest(kind=kind):self.blocked(lambda:c.authorize(pins,env,event,'prepare'))
    def test_provider_credential_scope_and_unknown_environment(self):
        for mode in c.MODES:
            pins=pins_fixture();env=env_fixture();credentials={k:'SYNTHETIC_PRIVATE' for k in c.PROVIDER_KEYS}
            if mode in c.PROVIDER_MODES:
                self.blocked(lambda:c.authorize(pins,env,event_fixture(pins,env),mode),'credentials_required')
                c.authorize(pins,{**env,**credentials},event_fixture(pins,env),mode)
            else:
                self.blocked(lambda:c.authorize(pins,{**env,**credentials},event_fixture(pins,env),mode))
            for key in ('PYTHONPATH','NODE_OPTIONS','CF_API_TOKEN','WRANGLER_SEND_METRICS','GITHUB_ENV'):
                with self.subTest(mode=mode,key=key):self.blocked(lambda:c.authorize(pins,{**env,**(credentials if mode in c.PROVIDER_MODES else {}),key:'SENTINEL'},event_fixture(pins,env),mode))
    def test_exact_actual_build_and_review_pins(self):
        for role in ('build','acceptedBuildReview'):
            for key in pins_fixture()[role]:
                pins=pins_fixture();pins[role][key]=None;env=env_fixture()
                with self.subTest(role=role,key=key):self.blocked(lambda:c.authorize(pins,env,event_fixture(pins,env),'prepare'))
    def test_null_baseline_and_wrong_actual_types(self):
        for key,value in [('runId',True),('artifactId',None),('artifactBytes',0),('artifactDigest','sha256:'+'f'*63),('controlRevision','main'),('artifactName','')]:
            pins=pins_fixture();pins['baseline'][key]=value;env=env_fixture()
            with self.subTest(key=key):self.blocked(lambda:c.authorize(pins,env,event_fixture(pins,env),'prepare'))
    def test_all_helpers_exact_and_before_import(self):
        c.verify_imports();self.assertEqual(c.IMPORT_PINS['finalize_recovery.py'],'87953c7d9bd89f81a7c7dcedacceadc27627dfe4ecb9cac67574ea076dbe3825')
        tree=ast.parse((c.D/'publish_existing_update.py').read_text());verify=next(n for n in tree.body if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and getattr(n.value.func,'id',None)=='verify_imports')
        imports=[n for n in tree.body if isinstance(n,ast.Import) and any(x.name in ('finalize_recovery','existing_update') for x in n.names)]
        self.assertTrue(all(verify.lineno<n.lineno for n in imports))
    def test_helper_mutation_blocks_before_import(self):
        d=self.root/'scripts/direct-damyang-recovery';d.mkdir(parents=True)
        for name in c.IMPORT_PINS:(d/name).write_bytes((c.D/name).read_bytes())
        for name in c.IMPORT_PINS:
            raw=(d/name).read_bytes();(d/name).write_bytes(raw+b'\n')
            with self.subTest(name=name):self.blocked(lambda:c.verify_imports(self.root),'immutable_update_helper')
            (d/name).write_bytes(raw)


class Boundaries(Case):
    def test_fresh_exact_download_roots_and_repeat_rejected(self):
        old=Path.cwd();os.chdir(self.root);self.addCleanup(os.chdir,old)
        roots=[self.root/name for name in c.DOWNLOAD_NAMES.values()]
        self.assertTrue(c.verify_roots(str(self.root),*roots,preparing=True))
        for p in roots:p.mkdir()
        self.assertTrue(c.verify_roots(str(self.root),*roots,preparing=False))
        self.blocked(lambda:c.verify_roots(str(self.root),*roots,preparing=True))
    def test_wrappers_orphans_and_symlink_roots_rejected(self):
        old=Path.cwd();os.chdir(self.root);self.addCleanup(os.chdir,old)
        good=[self.root/name for name in c.DOWNLOAD_NAMES.values()]
        for name in ('artifact','damyang-recovery-build/artifact','../damyang-recovery-build','stage/build'):
            with self.subTest(name=name):self.blocked(lambda:c.verify_roots(str(self.root),self.root/name,good[1],preparing=True))
        (self.root/'target').mkdir();good[0].symlink_to(self.root/'target',target_is_directory=True)
        self.blocked(lambda:c.verify_roots(str(self.root),*good,preparing=True),'root_required')
    def test_preexisting_outputs_fail_closed(self):
        old=Path.cwd();os.chdir(self.root);self.addCleanup(os.chdir,old)
        roots=[self.root/name for name in c.DOWNLOAD_NAMES.values()]
        for name in ('release','update-source-config.json','deployment-attempt-claim.json','provider-state-before.json'):
            p=self.root/name;p.write_text('old')
            with self.subTest(name=name):self.blocked(lambda:c.verify_roots(str(self.root),*roots,preparing=True),'fresh_update')
            p.unlink()
    def test_original_actual_config_exact_bytes_and_provenance(self):
        raw=c.original_config(c.ROOT);self.assertEqual(c.sha(raw),c.PRIOR_CONFIG_SHA256)
        config=c.reader.json_raw(raw);self.assertEqual(set(config),{'assets','compatibility_date','name','workers_dev'})
        self.assertEqual(config['name'],c.update.WORKER);self.assertNotIn('routes',config)
        p=self.root/c.PRIOR_CONFIG;p.parent.mkdir(parents=True);p.write_bytes(raw+b' ')
        self.blocked(lambda:c.original_config(self.root),'original_actual_static_config_bytes')
    def test_update_transport_has_no_indexnow_or_provider_write_branch(self):
        tree=ast.parse((c.D/'publish_existing_update.py').read_text())
        attrs=[n.attr for n in ast.walk(tree) if isinstance(n,ast.Attribute)]
        self.assertNotIn('ENDPOINT',attrs);self.assertNotIn('RecoveryAdapter',attrs)
        literals=[n.value for n in ast.walk(tree) if isinstance(n,ast.Constant) and type(n.value) is str]
        self.assertFalse(any('api.indexnow' in s or 'api.cloudflare' in s for s in literals))
        self.assertFalse(any(s in ('PUT','PATCH','DELETE') for s in literals))
    def test_workflow_original_two_jobs_exact_prefix(self):
        raw=(c.ROOT/c.WORKFLOW).read_bytes();original=(c.ROOT/'workflow/original-damyang-production-publish.yml').read_bytes()
        self.assertEqual((len(original),c.sha(original)),(c.ORIGINAL_WORKFLOW_BYTES,c.ORIGINAL_WORKFLOW_SHA256))
        self.assertEqual(raw[:len(original)],original)
        self.assertEqual(raw[len(original):],(c.ROOT/'workflow/additive-update-job.yml').read_bytes()+(c.ROOT/'workflow/additive-finalizer-job.yml').read_bytes())
        self.assertEqual(raw,(c.ROOT/'workflow/damyang-update-and-finalizer-proposed.yml').read_bytes())
        self.assertEqual((c.ROOT/'workflow/damyang-existing-update-proposed.yml').read_bytes(),original+(c.ROOT/'workflow/additive-update-job.yml').read_bytes())
    def test_workflow_exact_downloads_single_uploader_and_safe_retention(self):
        job=(c.ROOT/'workflow/additive-update-job.yml').read_text()
        self.assertEqual(job.count('actions/download-artifact@v4'),3);self.assertEqual(job.count('wrangler@4.148.0 deploy --config'),1)
        self.assertEqual(job.count('CLOUDFLARE_API_TOKEN: ${{ secrets.CLOUDFLARE_API_TOKEN }}'),4)
        self.assertNotIn('indexnow_finalize.py',job);self.assertNotIn('finalize_recovery.py',job);self.assertNotIn('recovery_build.py',job)
        retained=job.split('          path: |\n')[1].split('          if-no-files-found:')[0]
        self.assertNotIn('private.log',retained);self.assertNotIn('RUNNER_TEMP',retained);self.assertNotIn('*',retained)
        self.assertIn('public-http.json',retained);self.assertIn('provider-state-after-observed.json',retained)
        self.assertIn("steps.deploy.outcome == 'failure'",job);self.assertIn('test "$DEPLOY" = success',job)
    def test_every_python_operational_call_uses_clean_environment(self):
        job=(c.ROOT/'workflow/additive-update-job.yml').read_text()
        calls=job.split('      - name:')[1:]
        for block in calls:
            if 'publish_existing_update.py' in block:
                with self.subTest(name=block.splitlines()[0]):self.assertIn('env -i \\',block)
        self.assertIn('persist-credentials: false',job)


class Response:
    def __init__(self,url,status=200,body=b'{}',headers=None):
        self.url=url;self.code=status;self.buffer=io.BytesIO(body);self.headers=Message()
        for k,v in (headers if headers is not None else [('content-type','application/json')]):self.headers[k]=v
    def read(self,n):return self.buffer.read(n)
    def geturl(self):return self.url
    def __enter__(self):return self
    def __exit__(self,*a):pass

class Opener:
    def __init__(self,response):self.response=response;self.calls=[]
    def open(self,request,timeout):
        self.calls.append((request,timeout))
        if isinstance(self.response,Exception):raise self.response
        return self.response


class Transport(Case):
    def client(self,url=None,response=None,**kw):
        url=url or c.journal.HOME;op=Opener(response or Response(url))
        return c.UpdateHTTP('SYNTHETIC_TOKEN',[c.journal.ISSUE_URL],[c.journal.HOME],opener=op,**kw),op
    def test_public_get_no_token_api_get_has_token(self):
        for url,expected in [(c.journal.HOME,None),(c.journal.ISSUE_URL,'Bearer SYNTHETIC_TOKEN')]:
            http,op=self.client(url);http.call('GET',url);self.assertEqual(op.calls[0][0].get_header('Authorization'),expected)
    def test_only_original_claim_post_and_no_retries(self):
        url=c.journal.ISSUE_URL+'/comments';http,op=self.client(url);http.call('POST',url,b'{}')
        self.blocked(lambda:http.call('POST',url,b'{}'),'single_claim');self.assertEqual(len(op.calls),1)
    def test_unknown_claim_outcome_spends_current_write(self):
        url=c.journal.ISSUE_URL+'/comments';http,op=self.client(url,TimeoutError('PRIVATE_RAW'))
        self.blocked(lambda:http.call('POST',url,b'{}'),'outcome_unconfirmed')
        self.blocked(lambda:http.call('POST',url,b'{}'),'single_claim');self.assertEqual(len(op.calls),1)
    def test_all_foreign_writes_and_indexnow_block_before_io(self):
        http,op=self.client()
        for method in ('GET','POST','PUT','PATCH','DELETE'):
            for url in ('https://api.indexnow.org/indexnow','https://api.cloudflare.com/client/v4',c.journal.API_BASE+'/issues/378/comments','https://evil.example/'):
                with self.subTest(method=method,url=url):self.blocked(lambda:http.call(method,url,None if method=='GET' else b'{}'),'scope')
        self.assertEqual(op.calls,[])
    def test_issue_only_get_and_noncanonical_pages_forbidden(self):
        http,op=self.client()
        for url in (c.journal.ISSUE_URL+'/comments',c.journal.API_BASE+'/issues/comments?page=1&per_page=100',c.journal.page_url(c.journal.MAX_PAGES+1)):
            with self.subTest(url=url):self.blocked(lambda:http.call('GET',url),'scope')
        self.assertEqual(op.calls,[])
    def test_canonical_repo_page_and_direct_comment_supported(self):
        for url in (c.journal.page_url(1),c.journal.page_url(c.journal.MAX_PAGES),c.journal.API_BASE+'/issues/comments/123'):
            http,_=self.client(url);self.assertEqual(http.call('GET',url).status,200)
    def test_redirect_changed_url_truncation_compression_headers_and_timeout(self):
        responses=[Response(c.journal.HOME,302),Response('https://evil.example/'),Response(c.journal.HOME,body=b'a',headers=[('content-length','2')]),Response(c.journal.HOME,headers=[('content-encoding','gzip')]),Response(c.journal.HOME,headers=[('content-length','2'),('Content-Length','2')]),Response(c.journal.HOME,headers=[('x','x'*4097)])]
        for response in responses:
            http,op=self.client(response=response)
            with self.subTest(response=response):self.blocked(lambda:http.call('GET',c.journal.HOME));self.assertEqual(len(op.calls),1)
        times=iter([0,61]);http,_=self.client(clock=lambda:next(times));self.blocked(lambda:http.call('GET',c.journal.HOME),'deadline')
    def test_strict_pagination_reused_without_write_method(self):
        self.assertIs(c.GitHubClient.read_page,c.reader.GitHubClient.read_page)
        self.assertIs(c.GitHubClient.get,c.reader.GitHubClient.get)
        self.assertFalse(hasattr(c.GitHubClient,'write_record'))


class Flow(Case):
    def setUp(self):
        super().setUp();self.fx=old.UpdateTests('test_exact_synthetic_accepted_chain');self.fx.setUp();self.addCleanup(self.fx.doCleanups)
        self.pins=pins_fixture();self.env=self.fx.env;self.github=Mock();self.http=Mock()
        self.run=c.Runtime(self.pins,self.env,c.ROOT,'build','baseline',self.github,self.http)
        self.fx.staged();before={'state':'EXACT_ACCEPTED_EXISTING_TARGET_RECHECKED','runId':self.env['GITHUB_RUN_ID'],
            'controlRevision':self.env['GITHUB_SHA'],'acceptedObservationSHA256':self.fx.desc['sha256'],
            'providerStateSHA256':c.journal.digest(self.fx.state)}
        c.baseline.save('binding-before.json',before);self.github.pages.return_value=self.fx.history()
    def test_claim_requires_same_run_preflight(self):
        for key in ('state','runId','controlRevision','acceptedObservationSHA256','providerStateSHA256'):
            saved=c.read_json('binding-before.json');bad=dict(saved);bad[key]='wrong';c.baseline.save('binding-before.json',bad)
            with self.subTest(key=key):self.blocked(self.run.claim,'current_run_preflight');self.github.create_claim.assert_not_called()
            c.baseline.save('binding-before.json',saved)
    def test_uncertain_write_reserved_and_not_repeated(self):
        self.github.create_claim.side_effect=TimeoutError('SYNTHETIC')
        with self.assertRaises(TimeoutError):self.run.claim()
        self.assertTrue(Path('claim-write-reserved.json').exists());self.assertFalse(Path('deployment-attempt-claim.json').exists())
        self.blocked(self.run.claim,'write_already_reserved');self.assertEqual(self.github.create_claim.call_count,1)
    def test_successful_claim_is_durable_and_repeated_call_blocks(self):
        self.github.create_claim.side_effect=lambda record:dict(record,commentId=910010)
        claim=self.run.claim();self.assertEqual(claim,c.update.verify_claim(self.run.review,self.env))
        self.blocked(self.run.claim,'local_claim_already');self.assertEqual(self.github.create_claim.call_count,1)
    def test_any_foreign_prior_update_claim_blocks_write(self):
        pages=self.fx.history();pages[0].comments.append(self.fx.comment({'hostname':c.update.HOST,'sourceRevision':'f'*40,'state':'UNKNOWN'},910011,c.update.MARKER))
        self.github.pages.return_value=pages
        self.blocked(self.run.claim,'prior_damyang_update_attempt');self.github.create_claim.assert_not_called()
    def test_global_original_422_history_required_before_claim(self):
        self.github.pages.return_value=[];self.blocked(self.run.claim);self.github.create_claim.assert_not_called()
    def test_recheck_metadata_and_journal_before_final_get_gate(self):
        claim=c.update.select_claim(self.fx.history(),c.update.attempt_identity(self.run.review,self.env));claim['commentId']=910012;c.baseline.save('deployment-attempt-claim.json',claim)
        pages=self.fx.history();pages[0].comments.append(self.fx.comment({k:v for k,v in claim.items() if k!='commentId'},claim['commentId'],c.update.MARKER));self.github.pages.return_value=pages
        order=[]
        with patch.object(self.run,'metadata',side_effect=lambda:order.append('metadata')),patch.object(self.run,'stage_exact',side_effect=lambda:order.append('stage')),patch.object(c.update,'recheck',side_effect=lambda *a:order.append('provider') or {'state':'READY'}):self.assertEqual(self.run.recheck()['state'],'READY')
        self.assertEqual(order,['metadata','stage','provider','stage'])
    def test_provider_drift_stops_recheck_and_never_uploads(self):
        claim=c.update.select_claim(self.fx.history(),c.update.attempt_identity(self.run.review,self.env));claim['commentId']=910012;c.baseline.save('deployment-attempt-claim.json',claim)
        pages=self.fx.history();pages[0].comments.append(self.fx.comment({k:v for k,v in claim.items() if k!='commentId'},claim['commentId'],c.update.MARKER));self.github.pages.return_value=pages
        changed=copy.deepcopy(self.fx.state);changed['hostname']='wrong'
        with patch.object(self.run,'metadata'),patch.object(self.run,'stage_exact'),patch.object(c.update,'observe_current',return_value=changed),patch.object(c.baseline,'old_public') as public:
            self.blocked(self.run.recheck,'provider_changed');public.assert_not_called()
    def test_direct_claim_readback_and_full_repo_exclusivity(self):
        record=c.update.select_claim(self.fx.history(),c.update.attempt_identity(self.run.review,self.env));created=self.fx.comment(record,910013,c.update.MARKER);created['body']=c.update.MARKER+json.dumps(record,ensure_ascii=False,sort_keys=True)
        response=c.journal.RawResponse(201,json.dumps(created).encode(),[('content-type','application/json')]);http=Mock();http.call.return_value=response;github=c.GitHubClient(http)
        pages=self.fx.history();pages[0].comments.append(created)
        with patch.object(github,'get',return_value=(created,None)) as get,patch.object(github,'pages',return_value=pages):
            claim=github.create_claim(record);self.assertEqual(claim['commentId'],created['id']);get.assert_called_once_with(c.journal.API_BASE+'/issues/comments/'+str(created['id']))
        for kind in ('wrong-direct','missing-global','duplicate-global'):
            direct=copy.deepcopy(created);pp=copy.deepcopy(pages)
            if kind=='wrong-direct':direct['id']+=1
            elif kind=='missing-global':pp[0].comments.pop()
            else:pp[0].comments.append(self.fx.comment(record,910014,c.update.MARKER))
            with self.subTest(kind=kind),patch.object(github,'get',return_value=(direct,None)),patch.object(github,'pages',return_value=pp):self.blocked(lambda:github.create_claim(record))
    def test_baseline_artifact_descriptor_cross_binding(self):
        folder=Path('baseline');folder.mkdir();raw=(self.fx.root/self.fx.desc['path']).read_bytes();(folder/'observation.json').write_bytes(raw)
        row={'runId':self.fx.desc['observationRunId'],'controlRevision':self.fx.desc['observationControlRevision'],
            'artifactId':self.fx.desc['observationArtifactId'],'artifactDigest':self.fx.desc['observationArtifactDigest'],
            'files':{'observation.json':c.sha(raw)},'observationPath':'observation.json','independentAcceptance':self.fx.review}
        pins={'baseline':row};self.assertEqual(c.validate_baseline(folder,pins),self.fx.obs)
        for key,value in [('runId',910022),('artifactId',910023),('artifactDigest','sha256:'+'f'*64),('observationPath','missing'),('independentAcceptance',{})]:
            changed=copy.deepcopy(pins);changed['baseline'][key]=value
            with self.subTest(key=key):self.blocked(lambda:c.validate_baseline(folder,changed))
        (folder/'orphan').write_text('extra');self.blocked(lambda:c.validate_baseline(folder,pins),'exact_accepted_baseline_artifact')
    def test_readback_uncertain_upload_still_retains_safe_projection(self):
        claim=c.update.select_claim(self.fx.history(),c.update.attempt_identity(self.run.review,self.env));claim['commentId']=910015;c.baseline.save('deployment-attempt-claim.json',claim)
        with patch.object(c.update,'observe_current',return_value=self.fx.state):self.blocked(lambda:c.update.readback(self.run.review,self.env))
        self.assertEqual(c.read_json('provider-state-after-observed.json'),self.fx.state)
        self.assertFalse(Path('upload-version.json').exists())
    def test_single_uuid_digest_and_ambiguous_upload_rejected(self):
        value='11111111-1111-1111-1111-111111111111';p=Path('private.log');p.write_text('PRIVATE_SENSITIVE_RAW\nCurrent Version ID: '+value+'\n')
        result=c.update.extract_upload_version(p,self.env);self.assertEqual(result['versionIdSHA256'],c.sha(value.encode()))
        self.assertNotIn(value,json.dumps(result));self.assertNotIn('PRIVATE',json.dumps(result))
        for log in ('','Current Version ID: bad',('Current Version ID: '+value+'\n')*2):
            p.write_text(log)
            with self.subTest(log=log):self.blocked(lambda:c.update.extract_upload_version(p,self.env))


class RepositoryLinkCompatibility(Case):
    alias = 'https://api.github.com/repositories/1360554691/issues/comments'
    clients = (c.reader.GitHubClient, c.GitHubClient)

    def url(self, number, alias=True):
        return (self.alias if alias else c.journal.API_BASE + '/issues/comments') + '?per_page=100&page=' + str(number)

    def client(self, cls, comments=None, links=None, headers=None):
        http = Mock()
        pairs = [('content-type', 'application/json')]
        if links is not None: pairs.append(('link', links))
        if headers is not None: pairs.extend(headers)
        http.call.return_value = c.journal.RawResponse(200, json.dumps(comments or []).encode(), pairs)
        return cls(http), http

    def test_exact_name_and_numeric_links_normalize_without_alias_get(self):
        for cls in self.clients:
            for alias in (False, True):
                with self.subTest(client=cls.__module__, alias=alias):
                    links = ', '.join('<' + self.url(n, alias) + '>; rel="' + rel + '"'
                        for n, rel in ((3, 'next'), (1, 'prev'), (1, 'first'), (6, 'last')))
                    client, http = self.client(cls, links=links)
                    page = client.read_page(2)
                    self.assertEqual(page.url, c.journal.page_url(2))
                    self.assertEqual(page.next_url, c.journal.page_url(3))
                    http.call.assert_called_once_with('GET', c.journal.page_url(2))

    def test_observed_fresh_numeric_header_and_terminal_relations(self):
        observed = '<https://api.github.com/repositories/1360554691/issues/comments?per_page=100&page=2>; rel="next", <https://api.github.com/repositories/1360554691/issues/comments?per_page=100&page=6>; rel="last"'
        for cls in self.clients:
            with self.subTest(client=cls.__module__):
                client, _ = self.client(cls, links=observed)
                self.assertEqual(client.read_page(1).next_url, c.journal.page_url(2))
                client, _ = self.client(cls, links='<' + self.url(5) + '>; rel="prev", <' + self.url(1) + '>; rel="first"')
                self.assertIsNone(client.read_page(6).next_url)

    def test_foreign_or_noncanonical_aliases_are_rejected(self):
        good = self.url(2)
        variants = [good.replace('1360554691', '1360554692'), good.replace('1360554691', '01360554691'),
            good.replace('1360554691', 'joseungil-kr/fwith-site-factory'),
            good.replace('api.github.com', 'api.github.com.evil.example'), good.replace('api.github.com', 'API.github.com'),
            good.replace('api.github.com', 'api.github.com:443'), good.replace('api.github.com', 'user@api.github.com'),
            good.replace('https:', 'http:'), good.replace('/repositories/', '//repositories/'),
            good.replace('/repositories/', '/repositories/../repositories/'), good.replace('/issues/comments', '/issues/377/comments'),
            good.replace('/issues/comments', '/issues/comments/'), good.replace('/comments', '/%63omments'),
            good.replace('1360554691', '%31360554691'), good.replace('&page=2', '&page=02'),
            good.replace('&page=2', '&page=0'), good.replace('&page=2', '&page=-1'), good.replace('&page=2', '&page=+2'),
            good.replace('&page=2', '&page=2.0'), good.replace('&page=2', '&page=%32'),
            good.replace('&page=2', '&page=' + str(c.journal.MAX_PAGES + 1)),
            good.replace('per_page=100&page=2', 'page=2&per_page=100'), good.replace('per_page=100', 'per_page=99'),
            good.replace('per_page=100', 'per_page=0100'), good.replace('&page=2', '&Page=2'),
            good + '&page=2', good + '&per_page=100', good + '&since=x', good + '&', good + '#fragment',
            good.replace('&', '&amp;'), good.replace('&page', ';page'), good + '\n',
            c.journal.API_BASE.replace('fwith-site-factory', 'other') + '/issues/comments?per_page=100&page=2']
        for cls in self.clients:
            for dest in variants:
                with self.subTest(client=cls.__module__, dest=dest):
                    client, http = self.client(cls, links='<' + dest + '>; rel="next"')
                    self.blocked(lambda: client.read_page(1), 'foreign_or_noncanonical')
                    http.call.assert_called_once_with('GET', c.journal.page_url(1))

    def test_relation_cycles_jumps_duplicates_and_wrong_first_prev_rejected(self):
        links = [(1, '<' + self.url(1) + '>; rel="next"'), (1, '<' + self.url(3) + '>; rel="next"'),
            (2, '<' + self.url(1) + '>; rel="next"'), (2, '<' + self.url(2) + '>; rel="prev"'),
            (1, '<' + self.url(1) + '>; rel="prev"'), (2, '<' + self.url(2) + '>; rel="first"'),
            (1, '<' + self.url(2) + '>; rel="next", <' + self.url(2, False) + '>; rel="next"'),
            (1, '<' + self.url(2) + '>; rel="unknown"'), (1, '<' + self.url(2) + '>; rel=next'),
            (1, '<' + self.url(2) + '>; rel="next"; x="y"')]
        for cls in self.clients:
            for number, link in links:
                with self.subTest(client=cls.__module__, number=number, link=link):
                    client, http = self.client(cls, links=link)
                    self.blocked(lambda: client.read_page(number))
                    self.assertEqual(http.call.call_count, 1)

    def test_header_and_page_bounds_remain_closed(self):
        for cls in self.clients:
            for number in (True, 0, -1, '1', c.journal.MAX_PAGES + 1):
                with self.subTest(client=cls.__module__, number=number):
                    client, http = self.client(cls)
                    self.blocked(lambda: client.read_page(number)); http.call.assert_not_called()
            for headers in ([('Link', '<' + self.url(2) + '>; rel="next"')], []):
                client, _ = self.client(cls, links=('x' * 4097 if not headers else '<' + self.url(2) + '>; rel="next"'), headers=headers)
                self.blocked(lambda: client.read_page(1))
            client, _ = self.client(cls, links='<' + self.url(c.journal.MAX_PAGES) + '>; rel="last"')
            self.assertIsNone(client.read_page(c.journal.MAX_PAGES).next_url)

    def test_alias_is_not_new_transport_scope_and_redirect_is_not_followed(self):
        for transport in (c.reader.BoundedHTTP, c.UpdateHTTP):
            for dest in (self.url(1), self.url(1).replace('1360554691', '1360554692')):
                with self.subTest(transport=transport.__name__, dest=dest):
                    op = Opener(Response(dest)); http = transport('SYNTHETIC', [], [], opener=op)
                    self.blocked(lambda: http.call('GET', dest), 'scope'); self.assertEqual(op.calls, [])
            for response in (Response(c.journal.page_url(1), 302), Response(self.url(1))):
                op = Opener(response); http = transport('SYNTHETIC', [], [], opener=op)
                self.blocked(lambda: http.call('GET', c.journal.page_url(1)))
                self.assertEqual(len(op.calls), 1)
        self.assertIsNone(c.reader.NoRedirect().redirect_request(None, None, None, None, None, None))
        self.assertIsNone(c.NoRedirect().redirect_request(None, None, None, None, None, None))

    def history(self):
        def comment(record, number):
            return {'id': number, 'user': {'login': 'github-actions[bot]', 'id': 41898282, 'type': 'Bot'},
                'body': c.journal.MARKER + json.dumps(record),
                'url': c.journal.API_BASE + '/issues/comments/' + str(number),
                'issue_url': c.journal.ISSUE_URL, 'html_url': c.journal.WEB_ISSUE + '#issuecomment-' + str(number)}
        return [[{'id': n, 'body': 'unrelated repository comment'} for n in range(1, 101)],
            [comment(c.journal.original_record('started'), 6209522619), comment(c.journal.original_record('rejected'), 6209523005)]]

    def journal_client(self, cls, rows):
        http = Mock()
        def call(method, url):
            self.assertEqual(method, 'GET')
            number = 1 if url == c.journal.page_url(1) else 2
            self.assertEqual(url, c.journal.page_url(number))
            headers = [('content-type', 'application/json')]
            if number == 1: headers.append(('link', '<' + self.url(2) + '>; rel="next", <' + self.url(2) + '>; rel="last"'))
            else: headers.append(('link', '<' + self.url(1) + '>; rel="prev", <' + self.url(1) + '>; rel="first"'))
            return c.journal.RawResponse(200, json.dumps(rows[number - 1]).encode(), headers)
        http.call.side_effect = call
        return cls(http), http

    def test_whole_repository_audits_both_consumers_complete_numeric_links(self):
        contract = c.update._journal_contract()[1]
        client, http = self.journal_client(c.reader.GitHubClient, self.history())
        self.assertFalse(c.journal.audit_chain(client.read_page, contract).successor)
        self.assertEqual(http.call.call_count, 2)
        client, http = self.journal_client(c.GitHubClient, self.history())
        self.assertTrue(c.update.inspect_full_journal(client.pages()))
        self.assertEqual(http.call.call_count, 2)

    def test_whole_repository_duplicate_foreign_and_incomplete_pages_rejected(self):
        contract = c.update._journal_contract()[1]
        for kind in ('duplicate', 'foreign-author', 'foreign-issue', 'short-first', 'missing-original', 'full-last'):
            rows = self.history()
            if kind == 'duplicate': rows[1].append(copy.deepcopy(rows[0][0]))
            elif kind == 'foreign-author': rows[1][0]['user']['id'] = 1
            elif kind == 'foreign-issue': rows[1][0]['issue_url'] = c.journal.API_BASE + '/issues/378'
            elif kind == 'short-first': rows[0].pop()
            elif kind == 'missing-original': rows[1].pop()
            else: rows[1] += [{'id': n, 'body': 'unrelated'} for n in range(101, 199)]
            for cls in self.clients:
                with self.subTest(kind=kind, client=cls.__module__):
                    client, _ = self.journal_client(cls, rows)
                    self.blocked(lambda: c.update.inspect_full_journal(client.pages()) if cls is c.GitHubClient
                        else c.journal.audit_chain(client.read_page, contract))

    def test_existing_host_claim_still_blocks_after_alias_pagination(self):
        for state in ('STARTED_NO_AUTOMATIC_REUPLOAD', 'FAILED', 'UNKNOWN', 'SUCCESS'):
            rows = self.history(); claim = copy.deepcopy(rows[1][0]); claim['id'] = 6209524000
            claim['body'] = c.update.MARKER + json.dumps({'hostname': c.update.HOST, 'sourceRevision': 'f' * 40, 'state': state})
            claim.update(url=c.journal.API_BASE + '/issues/comments/6209524000', html_url=c.journal.WEB_ISSUE + '#issuecomment-6209524000')
            rows[1].append(claim); client, _ = self.journal_client(c.GitHubClient, rows)
            with self.subTest(state=state):
                self.blocked(lambda: c.update.inspect_full_journal(client.pages()), 'prior_damyang_update_attempt')


class PublicTimingHeaders(Case):
    def response(self, headers, status=200, body=b''):
        return c.journal.RawResponse(status, body, headers)
    def test_single_headers_and_first_timing_value_preserved(self):
        pairs=[('Content-Type','text/plain'),('Server-Timing','first;dur=1')]
        self.assertEqual(c.public_release.checked_headers(self.response(pairs)),{'content-type':'text/plain','server-timing':'first;dur=1'})
        for extra in ('server-timing','SERVER-TIMING','Server-Timing'):
            with self.subTest(name=extra):
                response=self.response(pairs+[(extra,'second;dur=2')])
                self.assertEqual(c.public_release.checked_headers(response)['server-timing'],'first;dur=1')
                self.assertEqual(response.headers,pairs+[(extra,'second;dur=2')])
    def test_every_other_duplicate_header_still_rejected(self):
        names=('content-type','content-length','content-encoding','location','content-security-policy','x-robots-tag','cf-mitigated','cache-control','set-cookie','report-to','nel','link','transfer-encoding','connection','x-unknown','server','vary','etag')
        for name in names:
            for second in (name,name.upper()):
                with self.subTest(name=name,second=second):
                    self.blocked(lambda:c.public_release.checked_headers(self.response([(name,'x'),(second,'x')])),'duplicate_or_unsafe_public_header')
    def test_repeated_timing_rows_still_require_valid_tuple_and_string(self):
        for row in (['server-timing','x'],('server-timing',),('server-timing','x','x'),('server-timing',None),('server-timing',1),(1,'x'),(True,'x')):
            with self.subTest(row=row):
                self.blocked(lambda:c.public_release.checked_headers(self.response([('Server-Timing','valid'),row])),'invalid_public_response_header')
    def test_repeated_timing_rows_still_require_safe_full_values(self):
        for value in ('x\r','x\n','x\r\ny','x'*4097):
            with self.subTest(length=len(value)):
                self.blocked(lambda:c.public_release.checked_headers(self.response([('server-timing','valid'),('SERVER-TIMING',value)])),'duplicate_or_unsafe_public_header')
        for name in (' server-timing','server-timing ','server_timing','server:timing','x'*129,''):
            with self.subTest(name=name):
                self.blocked(lambda:c.public_release.checked_headers(self.response([(name,'x')])),'duplicate_or_unsafe_public_header')
    def test_response_and_row_bounds_are_unchanged(self):
        self.assertEqual(c.public_release.checked_headers(self.response([('server-timing','x'*4096)]*100)),{'server-timing':'x'*4096})
        cases=[self.response([('server-timing','x')]*101),self.response((),body=b''),self.response([],status=True),self.response([],body='x'),self.response([],body=b'x'*(c.public_release.LIMIT+1))]
        for response in cases:
            with self.subTest(status=response.status,headers=type(response.headers).__name__):
                self.blocked(lambda:c.public_release.checked_headers(response),'invalid_public_response')
    def test_challenge_encoding_and_public_identity_still_rejected(self):
        for headers in ([('cf-mitigated','challenge')],[('content-encoding','gzip')]):
            with self.subTest(headers=headers):
                self.blocked(lambda:c.public_release.checked_headers(self.response(headers+[('server-timing','x'),('SERVER-TIMING','y')])),'public_challenge|compressed_public')
        self.blocked(lambda:c.public_release.verify_public_response('/foreign','x',200,self.response([]),{}),'fixed_public_response_identity')
    def test_both_proof_bytes_and_status_unchanged_with_timing(self):
        for name,expected in ((c.public_release.ACTIVE,c.journal.ACTIVE_PROOF_SHA256),(c.public_release.LEGACY,c.journal.RETAINED_PROOF_SHA256)):
            pairs=[('content-type','text/plain'),('server-timing','x'),('Server-Timing','y')];body=(name[:-4]+'\n').encode()
            with self.subTest(proof=name):
                row=c.public_release.verify_public_response('/'+name,name,200,self.response(pairs,body=body),{name:expected})
                self.assertEqual(row['artifactSha256'],expected)
                self.blocked(lambda:c.public_release.verify_public_response('/'+name,name,200,self.response(pairs,body=body+b'x'),{name:expected}),'public_bytes_mismatch')
                self.blocked(lambda:c.public_release.verify_public_response('/'+name,name,200,self.response(pairs,status=404,body=body),{name:expected}),'public_http_status_mismatch')
    def test_html_type_robots_and_generic_duplicate_preserved(self):
        pairs=[('server-timing','x'),('Server-Timing','y')]
        for headers,reason in (([('content-type','text/plain')],'public_html_content_type'),([('content-type','text/html'),('x-robots-tag','noindex')],'public_home_header_blocks'),([('content-type','text/html'),('Content-Type','text/html')],'duplicate_or_unsafe')):
            with self.subTest(reason=reason):
                self.blocked(lambda:c.public_release.verify_public_response('/','index.html',200,self.response(pairs+headers),{'index.html':'a'*64}),reason)


if __name__=='__main__':unittest.main(verbosity=2)
