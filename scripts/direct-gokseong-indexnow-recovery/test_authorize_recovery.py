"""Pure exact-request tests. These do not open the independent operational seal."""
import copy,json,unittest
from pathlib import Path
import finalize_recovery as f,indexnow_recovery as g
class AuthorizationTests(unittest.TestCase):
    def setUp(self):
        self.p=f.read_json(Path(__file__).parent/'recovery-binding.json')
        self.p.update(status='INDEPENDENTLY_REVIEWED_ACTUAL_RECOVERY',controlFiles={'offline':'fixture'},workflowFiles={'offline':'fixture'},independentOperationalReview={'path':'offline'})
        self.e=dict(GITHUB_REPOSITORY=g.REPOSITORY,GITHUB_REF='refs/heads/main',GITHUB_ACTOR=f.OWNER,GITHUB_TRIGGERING_ACTOR=f.OWNER,GITHUB_RUN_ATTEMPT='1',GITHUB_EVENT_NAME='issues',GITHUB_JOB=f.JOB,RUNNER_ENVIRONMENT='github-hosted',REVISION=f.SOURCE,GITHUB_SHA='b'*40,GITHUB_RUN_ID='99999999999')
        self.body=dict(schemaVersion=1,mode='no-deploy-indexnow-recovery',source_branch=f.BRANCH,source_revision=f.SOURCE,expected_control_revision=self.e['GITHUB_SHA'],receipt_issue=399,operational_binding_sha256=g.digest(self.p))
        self.event=dict(action='opened',repository={'full_name':g.REPOSITORY,'owner':{'login':f.OWNER,'type':'User'}},sender={'login':f.OWNER,'type':'User'},issue={'title':f.TITLE,'user':{'login':f.OWNER,'type':'User'},'state':'open','number':999999,'body':json.dumps(self.body)})
    def test_exact_request_is_only_a_pure_authorization_check(self):
        before=f.OPERATIONAL_CONTROLS_ENABLED
        self.assertEqual(f.authorize(self.p,self.e,self.event),self.body)
        self.assertIs(f.OPERATIONAL_CONTROLS_ENABLED,before)
    def test_wrong_owner_ref_attempt_job_runner_or_source_blocks(self):
        for key,value in [('GITHUB_ACTOR','other'),('GITHUB_TRIGGERING_ACTOR','other'),('GITHUB_REF','refs/heads/feature'),('GITHUB_RUN_ATTEMPT','2'),('GITHUB_JOB','publish'),('RUNNER_ENVIRONMENT','self-hosted'),('REVISION','d'*40),('GITHUB_EVENT_NAME','workflow_dispatch')]:
            env={**self.e,key:value}
            with self.subTest(key=key),self.assertRaises(g.RecoveryBlocked):f.authorize(self.p,env,self.event)
    def test_unknown_or_provider_environment_is_forbidden(self):
        for name in ['CLOUDFLARE_API_TOKEN','WRANGLER_SEND_METRICS','PYTHONPATH','EXTRA','NODE_OPTIONS']:
            with self.subTest(name=name),self.assertRaisesRegex(g.RecoveryBlocked,'trusted_finalizer_environment_required'):f.authorize(self.p,{**self.e,name:'offline'},self.event)
    def test_missing_review_or_dormant_status_blocks(self):
        for key,value in [('status','DORMANT_UNREVIEWED_NO_EXECUTION'),('independentOperationalReview',None),('controlFiles',{}),('workflowFiles',{})]:
            pins={**self.p,key:value};event=copy.deepcopy(self.event);body={**self.body,'operational_binding_sha256':g.digest(pins)};event['issue']['body']=json.dumps(body)
            with self.subTest(key=key),self.assertRaises(g.RecoveryBlocked):f.authorize(pins,self.e,event)
    def test_extra_issue_field_or_changed_fingerprint_blocks(self):
        for key,value in [('maximumAdditionalPOSTs',2),('originalFingerprint','0'*64),('sourceRevision','d'*40),('receiptIssue',400),('extra',True)]:
            pins={**self.p,key:value};event=copy.deepcopy(self.event);event['issue']['body']=json.dumps({**self.body,'operational_binding_sha256':g.digest(pins)})
            with self.subTest(key=key),self.assertRaises(g.RecoveryBlocked):f.authorize(pins,self.e,event)
    def test_alternate_payload_key_or_endpoint_in_request_blocks(self):
        for key,value in [('key','0'*32),('endpoint','https://api.indexnow.org/indexnow'),('mode','publish'),('receipt_issue',400)]:
            event=copy.deepcopy(self.event);event['issue']['body']=json.dumps({**self.body,key:value})
            with self.subTest(key=key),self.assertRaisesRegex(g.RecoveryBlocked,'closed_exact_request_required'):f.authorize(self.p,self.e,event)
    def test_request_from_other_actor_or_existing_journal_blocks(self):
        for field,value in [('number',399),('user',{'login':'other','type':'User'}),('state','closed'),('pull_request',{}),('title',f.TITLE+' ')]:
            event=copy.deepcopy(self.event);event['issue'][field]=value
            with self.subTest(field=field),self.assertRaises(g.RecoveryBlocked):f.authorize(self.p,self.e,event)
    def test_request_duplicate_fields_and_boolean_numbers_block(self):
        event=copy.deepcopy(self.event);event['issue']['body']='{"schemaVersion":1,"schemaVersion":1}'
        with self.assertRaises(g.RecoveryBlocked):f.authorize(self.p,self.e,event)
        for key in ['receiptIssue','maximumAdditionalPOSTs','schemaVersion']:
            pins={**self.p,key:True};event=copy.deepcopy(self.event);event['issue']['body']=json.dumps({**self.body,'operational_binding_sha256':g.digest(pins)})
            with self.subTest(key=key),self.assertRaises(g.RecoveryBlocked):f.authorize(pins,self.e,event)
    def test_original_build_and_failed_publication_cannot_be_replaced(self):
        for role,field,value in [('build','runId',1),('build','artifactDigest','sha256:'+'f'*64),('build','expectedConclusion','failure'),('publication','expectedConclusion','success'),('publication','controlRevision','a'*40)]:
            pins=copy.deepcopy(self.p);pins[role][field]=value;event=copy.deepcopy(self.event);event['issue']['body']=json.dumps({**self.body,'operational_binding_sha256':g.digest(pins)})
            with self.subTest(role=role,field=field),self.assertRaises(g.RecoveryBlocked):f.authorize(pins,self.e,event)
if __name__=='__main__':unittest.main()
