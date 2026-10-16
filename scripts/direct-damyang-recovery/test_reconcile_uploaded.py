"""Offline exact-upload reconciliation tests; no source or network execution."""
import copy,json,os
from pathlib import Path
import re
import unittest
from unittest.mock import patch,Mock
import reconcile_uploaded as q
import test_update_caller as shared
c=q.c


def pins_fixture():
    p=c.read_json(c.ROOT/'docs/direct-damyang-recovery/reconciliation-binding.json')
    p.update(status='INDEPENDENTLY_REVIEWED_GET_ONLY_UPLOADED_RECONCILIATION',operationalActivationAllowed=True,
        review={'path':'docs/direct-damyang-recovery/SYNTHETIC_ONLY.json','sha256':'a'*64},
        controlFiles={'SYNTHETIC':'b'*64},workflowFiles={'SYNTHETIC':'c'*64},reviewedControlRevision='d'*40)
    return p


def event_fixture(pins,env):
    event=shared.event_fixture(pins,env);event['issue']['title']=q.TITLE
    event['issue']['body']=json.dumps({'schemaVersion':1,'mode':'uploaded-proof-get-only-reconciliation',
        'source_branch':c.reader.SOURCE_BRANCH,'source_revision':c.SOURCE,
        'expected_control_revision':env['GITHUB_SHA'],'receipt_issue':377,
        'original_update_run_id':38927541164,'original_update_artifact_id':12056828086,
        'original_claim_comment_id':6219311010,'reconciliation_binding_sha256':c.journal.digest(pins)})
    return event


def historical_run():
    return {'id':38927541164,'run_attempt':1,'event':'issues','head_branch':'main',
        'head_sha':'683aae06c27d18e0a674fb32b61be17abcfd5996','path':c.WORKFLOW,
        'repository':{'id':1360554691,'full_name':c.journal.REPOSITORY},
        'actor':{'login':c.reader.OWNER},'triggering_actor':{'login':c.reader.OWNER},
        'status':'completed','conclusion':'failure'}


def historical_job():
    return {'id':117062829774,'run_id':38927541164,'run_attempt':1,'head_branch':'main',
        'head_sha':'683aae06c27d18e0a674fb32b61be17abcfd5996','name':c.JOB,
        'status':'completed','conclusion':'failure','steps':copy.deepcopy(c.reader.EXACT_FAILED_UPDATE_STEPS)}


class Authorization(shared.Case):
    def test_pending_binding_all_three_cli_stop_before_event_credentials_transport(self):
        for mode in q.MODES:
            with self.subTest(mode=mode),patch.object(q.sys,'argv',['reconcile',mode,'--control-root',str(c.ROOT),'--report',str(self.root/'blocked.json')]),patch.object(q,'authorize')as auth,patch.object(q,'ReadOnlyHTTP')as http,patch.dict(os.environ,{'GH_TOKEN':'PRIVATE_SENTINEL','CLOUDFLARE_API_TOKEN':'PRIVATE_SENTINEL','GITHUB_EVENT_PATH':'DO_NOT_READ'},clear=True):
                self.assertEqual(q.main(),1);auth.assert_not_called();http.assert_not_called()
                raw=(self.root/'blocked.json').read_text();self.assertNotIn('PRIVATE_SENTINEL',raw);self.assertIn('independent_get_only_reconciliation_acceptance_required',raw)
    def test_disabled_code_seal_all_three_modes_stops_before_environment(self):
        for mode in q.MODES:
            with self.subTest(mode=mode),patch.object(q,'OPERATIONAL_CONTROLS_ENABLED',False),patch.object(q.sys,'argv',['reconcile',mode,'--report',str(self.root/'blocked.json')]),patch.object(q,'authorize')as auth,patch.object(q,'ReadOnlyHTTP')as http:
                self.assertEqual(q.main(),1);auth.assert_not_called();http.assert_not_called()
    def test_only_exact_closed_new_request_allowed_in_each_get_mode(self):
        for mode in q.MODES:
            pins=pins_fixture();env=shared.env_fixture()
            if mode=='observe':env.update({k:'SYNTHETIC'for k in c.PROVIDER_KEYS})
            with self.subTest(mode=mode):q.authorize(pins,env,event_fixture(pins,env),mode)
    def test_provider_environment_only_in_observe_and_unknown_variables_rejected(self):
        for mode in q.MODES:
            for key in ('PYTHONPATH','NODE_OPTIONS','CF_API_TOKEN','GITHUB_ENV','WRANGLER_SEND_METRICS'):
                pins=pins_fixture();env=shared.env_fixture()
                if mode=='observe':env.update({k:'SYNTHETIC'for k in c.PROVIDER_KEYS})
                env[key]='PRIVATE_SENTINEL'
                with self.subTest(mode=mode,key=key):self.blocked(lambda:q.authorize(pins,env,event_fixture(pins,env),mode),'clean_reconciliation')
        pins=pins_fixture();env=shared.env_fixture()
        self.blocked(lambda:q.authorize(pins,env,event_fixture(pins,env),'observe'),'provider_get_credentials')
        for mode in ('prepare','artifact'):
            with self.subTest(mode=mode):self.blocked(lambda:q.authorize(pins,{**env,**{k:'SYNTHETIC'for k in c.PROVIDER_KEYS}},event_fixture(pins,env),mode))
    def test_current_run_identity_cannot_be_historical_or_foreign(self):
        for key,value in [('GITHUB_RUN_ID','38927541164'),('GITHUB_RUN_ID','0'),('GITHUB_SHA','main'),('GITHUB_JOB','publish'),('GITHUB_ACTOR','other'),('GITHUB_TRIGGERING_ACTOR','other'),('GITHUB_REPOSITORY','other/repo'),('GITHUB_REF','refs/heads/dev'),('GITHUB_RUN_ATTEMPT','2'),('GITHUB_EVENT_NAME','workflow_dispatch'),('RUNNER_ENVIRONMENT','self-hosted')]:
            pins=pins_fixture();env=shared.env_fixture();env[key]=value
            with self.subTest(key=key):self.blocked(lambda:q.authorize(pins,env,event_fixture(pins,env),'prepare'))
    def test_request_fields_title_sender_and_claim_are_closed(self):
        for key,value in [('mode','existing-host-static-proof-update'),('original_update_run_id',38927541165),('original_update_artifact_id',12056828087),('original_claim_comment_id',6219311011),('receipt_issue',378),('source_revision','f'*40),('extra',True)]:
            pins=pins_fixture();env=shared.env_fixture();event=event_fixture(pins,env);body=json.loads(event['issue']['body']);body[key]=value;event['issue']['body']=json.dumps(body)
            with self.subTest(key=key):self.blocked(lambda:q.authorize(pins,env,event,'prepare'),'closed_exact')
        for kind in ('title','sender','user','pr','action','duplicate','long'):
            pins=pins_fixture();env=shared.env_fixture();event=event_fixture(pins,env)
            if kind=='title':event['issue']['title']=c.TITLE
            elif kind=='sender':event['sender']['login']='other'
            elif kind=='user':event['issue']['user']['login']='other'
            elif kind=='pr':event['issue']['pull_request']={}
            elif kind=='action':event['action']='edited'
            elif kind=='duplicate':event['issue']['body']=event['issue']['body'][:-1]+',"mode":"uploaded-proof-get-only-reconciliation"}'
            else:event['issue']['body']='x'*4097
            with self.subTest(kind=kind):self.blocked(lambda:q.authorize(pins,env,event,'prepare'))
    def test_original_update_modes_cannot_accept_reconciliation_request(self):
        pins=pins_fixture();env=shared.env_fixture();event=event_fixture(pins,env)
        for mode in c.MODES:
            given={**env,**{k:'SYNTHETIC'for k in c.PROVIDER_KEYS}}if mode in c.PROVIDER_MODES else env
            with self.subTest(mode=mode):self.blocked(lambda:c.authorize(pins,given,event,mode))
        for mode in ('claim','preflight','recheck','parse-upload','readback','public','indexnow','deploy'):
            with self.subTest(mode=mode):self.blocked(lambda:q.authorize(pins,env,event,mode),'fixed_unoptimized_get_only_mode')
    def test_exact_helper_pin_and_finalizer_remains_disabled(self):
        self.assertEqual(q.CALLER_SHA256,c.sha((c.D/'publish_existing_update.py').read_bytes()))
        self.assertFalse(c.reader.OPERATIONAL_CONTROLS_ENABLED)
        self.assertEqual(c.sha((c.ROOT/'docs/direct-damyang-recovery/update-caller-binding.json').read_bytes()),q.PENDING_UPDATE_SHA256)


class HistoricalFailure(shared.Case):
    def test_exact_failure_is_not_promoted_and_default_verify_run_rejects(self):
        result=c.reader.verify_exact_uploaded_failure(historical_run(),historical_job())
        self.assertEqual(result['conclusion'],'failure');self.assertFalse(result['publicAccepted'])
        self.blocked(lambda:c.reader.verify_run(c.reader.EXACT_FAILED_UPDATE,historical_run(),c.WORKFLOW),'workflow_run_not_successful')
    def test_run_scope_and_status_mutations_rejected(self):
        for key,value in [('id',38927541165),('id',True),('run_attempt',2),('run_attempt',True),('head_branch','dev'),('head_sha','b'*40),('event','workflow_dispatch'),('path','other.yml'),('status','in_progress'),('conclusion','success'),('repository',{'full_name':c.journal.REPOSITORY,'id':1360554692}),('actor',{'login':'other'}),('triggering_actor',{'login':'other'})]:
            run=historical_run();run[key]=value
            with self.subTest(key=key):self.blocked(lambda:c.reader.verify_exact_uploaded_failure(run,historical_job()),'exact_historical_failed_upload_run')
    def test_job_identity_and_earlier_or_unknown_failure_rejected(self):
        for key,value in [('id',117062829775),('run_id',38927541165),('run_attempt',2),('head_branch','dev'),('head_sha','f'*40),('name','publish'),('status','in_progress'),('conclusion','success'),('steps',None)]:
            job=historical_job();job[key]=value
            with self.subTest(key=key):self.blocked(lambda:c.reader.verify_exact_uploaded_failure(historical_run(),job))
        for index in range(len(c.reader.EXACT_FAILED_UPDATE_STEPS)):
            for field,value in [('conclusion','cancelled'),('status','in_progress'),('name','unexpected'),('number',999)]:
                job=historical_job();job['steps'][index][field]=value
                with self.subTest(index=index,field=field):self.blocked(lambda:c.reader.verify_exact_uploaded_failure(historical_run(),job),'exact_completed_upload')
        for rows in ([],[None],c.reader.EXACT_FAILED_UPDATE_STEPS[:-1],c.reader.EXACT_FAILED_UPDATE_STEPS+[c.reader.EXACT_FAILED_UPDATE_STEPS[0]]):
            job=historical_job();job['steps']=rows
            with self.subTest(rows=len(rows)):self.blocked(lambda:c.reader.verify_exact_uploaded_failure(historical_run(),job))
    def test_artifact17_inventory_and_foreign_binding_rejected_before_report_use(self):
        pins=pins_fixture()
        self.blocked(lambda:c.reader.validate_failed_uploaded_artifact(self.root,pins,{}),'exact_historical_failed_artifact17')
        for key,value in [('runId',38927541165),('artifactId',12056828087),('artifactDigest','sha256:'+'f'*64),('controlRevision','f'*40)]:
            bad=copy.deepcopy(pins);bad['failedUpdate'][key]=value
            with self.subTest(key=key):self.blocked(lambda:c.reader.validate_failed_uploaded_artifact(self.root,bad,{}),'exact_failed_update_binding')
    def test_no_raw_response_substitution_and_safe_header_projection(self):
        response=c.journal.RawResponse(200,b'x',[('Server-Timing','a'),('server-timing','b'),('report-to','PRIVATE_CANARY')])
        out=q.validated_header_projection(response);self.assertEqual(out['duplicates'],{'server-timing':2});self.assertNotIn('PRIVATE_CANARY',json.dumps(out))
        for value in ('x\r','x\n','x'*4097,None):
            with self.subTest(value=type(value).__name__):self.blocked(lambda:q.validated_header_projection(c.journal.RawResponse(200,b'x',[('report-to',value)])))


class ReadOnlyTransport(shared.Case):
    def test_every_write_method_and_payload_blocked_before_opener(self):
        opener=Mock();http=q.ReadOnlyHTTP('SYNTHETIC',q.api_urls(pins_fixture(),'910003'),[c.journal.HOME],opener=opener)
        for method in ('POST','PUT','PATCH','DELETE','HEAD','get'):
            for url in (c.journal.HOME,c.journal.ISSUE_URL+'/comments',c.journal.ENDPOINT):
                with self.subTest(method=method,url=url):self.blocked(lambda:http.call(method,url,b'{}'),'reconciliation_get_only')
        self.blocked(lambda:http.call('GET',c.journal.HOME,b''),'reconciliation_get_only');opener.open.assert_not_called()
    def test_public_get_does_not_send_authorization_and_alias_not_followed(self):
        opener=shared.Opener(shared.Response(c.journal.HOME,body=b'x'));http=q.ReadOnlyHTTP('PRIVATE_SENTINEL',[],[c.journal.HOME],opener=opener)
        self.assertEqual(http.call('GET',c.journal.HOME).body,b'x')
        request=opener.calls[0][0];self.assertFalse(any(k.lower()=='authorization'for k in request.headers))
        self.blocked(lambda:http.call('GET','https://api.github.com/repositories/1360554691/issues/comments?per_page=100&page=2'),'fixed_update_http_scope')
    def test_provider_or_foreign_get_destination_rejected_by_github_public_transport(self):
        opener=Mock();http=q.ReadOnlyHTTP('SYNTHETIC',[],[c.journal.HOME],opener=opener)
        for url in ('https://api.cloudflare.com/client/v4/accounts/x','https://evil.example/',c.journal.HOME+'other',c.journal.ENDPOINT):
            with self.subTest(url=url):self.blocked(lambda:http.call('GET',url),'fixed_update_http_scope')
        opener.open.assert_not_called()


class Workflow(shared.Case):
    def test_same_job_permissions_and_original_two_jobs_prefix(self):
        text=(c.ROOT/c.WORKFLOW).read_text();job=(c.ROOT/'workflow/additive-update-job.yml').read_text()
        self.assertEqual(text[:c.ORIGINAL_WORKFLOW_BYTES].encode(),(c.ROOT/'workflow/original-damyang-production-publish.yml').read_bytes())
        self.assertEqual(text.count('\n  recovery_static_update:\n'),1);self.assertEqual(text.count('\n  recovery_finalize_indexnow:\n'),1)
        self.assertIn('permissions:\n      contents: read\n      actions: read\n      issues: write',job)
        self.assertEqual(job.count('CLOUDFLARE_API_TOKEN: ${{ secrets.CLOUDFLARE_API_TOKEN }}'),4)
        self.assertIn(q.TITLE,job);self.assertEqual(job.count('wrangler@4.148.0 deploy --config'),1)
    def test_every_mutation_and_original_readback_path_excludes_reconciliation(self):
        job=(c.ROOT/'workflow/additive-update-job.yml').read_text();blocks=job.split('      - ')[1:]
        for marker in ('uses: actions/setup-node@v4','name: GET accepted current target','name: Write one claim','name: Recheck source main','name: Upload fixed existing','name: Parse only one version'):
            block=next(b for b in blocks if b.startswith(marker))
            with self.subTest(marker=marker):self.assertIn("if: env.RECONCILE_ONLY != 'true'",block)
        block=next(b for b in blocks if b.startswith('name: Check public16'))
        self.assertIn("env.RECONCILE_ONLY != 'true'",block)
    def test_reconciliation_download_and_existing_readback_branch_are_fixed(self):
        job=(c.ROOT/'workflow/additive-update-job.yml').read_text()
        self.assertEqual(job.count('actions/download-artifact@v4'),3);self.assertIn('path: damyang-recovery-update',job)
        self.assertIn('artifact-ids: ${{ steps.selected.outputs.update_artifact_id }}',job)
        self.assertIn('run-id: ${{ steps.selected.outputs.update_run_id }}',job)
        self.assertIn("env.RECONCILE_ONLY == 'true' && steps.artifact.outcome == 'success'",job)
        self.assertIn('caller="$CONTROL_DIR/reconcile_uploaded.py"; mode=observe; report=reconciliation-result.json',job)
        self.assertIn('test "$DEPLOY" = skipped && test "$VERSION" = skipped && test "$BINDING" = success && test "$HTTP" = skipped',job)
    def test_all_reconciliation_python_calls_keep_clean_environment(self):
        job=(c.ROOT/'workflow/additive-update-job.yml').read_text()
        for block in job.split('      - ')[1:]:
            if 'reconcile_uploaded.py' in block:
                with self.subTest(name=block.splitlines()[0]):self.assertIn('env -i \\',block)
        retained=job.split('          path: |\n')[1].split('          if-no-files-found:')[0]
        self.assertNotIn('*',retained);self.assertNotIn('private.log',retained);self.assertIn('reconciliation-public-bodies',retained)

if __name__=='__main__':unittest.main(verbosity=2)
