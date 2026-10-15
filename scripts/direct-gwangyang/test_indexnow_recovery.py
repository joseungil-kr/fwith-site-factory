"""Offline recovery boundary tests; fixture identities are not actual evidence."""
import copy
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import publish as p
import test_publish


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.fixture=test_publish.PublisherTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.env,self.event=self.fixture.request()
        self.event['issue']['title']=p.FINALIZE_TITLE
        body=json.loads(self.event['issue']['body'])
        body.update(mode='indexnow-finalize',original_publish_run_id=p.ORIGINAL_PUBLISH_RUN)
        self.event['issue']['body']=json.dumps(body)

    def check(self):
        return p.authorize(self.fixture.c,p.gate.load()[2],self.env,self.event,finalize_only=True)

    def test_exact_recovery_request(self):
        self.assertEqual(self.check()['sourceRevision'],self.fixture.c['sourceRevision'])

    def test_original_publish_cannot_accept_recovery(self):
        with self.assertRaises(ValueError):self.fixture.authorize(self.env,self.event)

    def test_body_mutations_fail_closed(self):
        original=json.loads(self.event['issue']['body'])
        for key,value in [('mode','publish'),('original_publish_run_id',38793139575),('original_publish_run_id','38793139574'),('schemaVersion',True),('source_revision','f'*40),('expected_control_revision','e'*40),('binding_sha256','f'*64),('release_review_sha256','e'*64),('receipt_issue',354),('source_branch','other'),('extra',True)]:
            with self.subTest(key=key,value=value),self.assertRaises(ValueError):
                body=copy.deepcopy(original);body[key]=value;self.event['issue']['body']=json.dumps(body);self.check()
        self.event['issue']['body']=json.dumps(original)

    def test_owner_main_attempt_event_guards_retained(self):
        for key,value in [('GITHUB_ACTOR','other'),('GITHUB_TRIGGERING_ACTOR','other'),('GITHUB_RUN_ATTEMPT','2'),('GITHUB_REPOSITORY','other/repo'),('GITHUB_REF','refs/heads/other'),('GITHUB_EVENT_NAME','push'),('GITHUB_SHA','short')]:
            with self.subTest(key=key),patch.dict(self.env,{key:value}),self.assertRaises(ValueError):self.check()
        for kind in ['title','user','action','repository']:
            original=copy.deepcopy(self.event)
            if kind=='title':self.event['issue']['title']=p.TITLE
            elif kind=='user':self.event['issue']['user']['login']='other'
            elif kind=='action':self.event['action']='edited'
            else:self.event['repository']['owner']['login']='other'
            with self.subTest(kind=kind),self.assertRaises(ValueError):self.check()
            self.event=original

    def test_main_refuses_every_provider_operation_before_dispatch(self):
        with tempfile.TemporaryDirectory() as d:
            event=Path(d)/'event.json';event.write_text(json.dumps(self.event))
            for mode in ['preflight','attach','readback']:
                report=Path(d)/(mode+'.json')
                with self.subTest(mode=mode),patch.object(p.gate,'trusted_control'),patch.object(p,'provider',side_effect=AssertionError('provider must not run')),patch.dict(os.environ,{'GITHUB_EVENT_PATH':str(event)}),patch('sys.argv',['publish.py',mode,'--report',str(report)]):
                    self.assertEqual(p.main(),1)
                    self.assertEqual(json.loads(report.read_text())['code'],'finalize_provider_operation_forbidden')

    def test_exact_static_indexnow_gets_and_mutations(self):
        self.fixture.fixture_release();p.helpers();import indexnow_finalize as n
        with test_publish.working(self.fixture.root):
            p.artifact()
            for path in [p.output.PROOF['path'],'/robots.txt','/sitemap-index.xml','/sitemap-0.xml']:
                exact=(Path('release/dist')/path.lstrip('/')).read_text()
                with self.subTest(path=path),patch.object(n,'request',return_value=(200,exact,{'content-type':'text/plain'})):
                    self.assertEqual(p.observed_indexnow_request('GET',p.ORIGIN+path)[0],200)
                for status,body in [(500,exact),(302,exact),(200,exact+'\n')]:
                    with self.subTest(path=path,status=status),patch.object(n,'request',return_value=(status,body,{})),self.assertRaises(ValueError):
                        p.observed_indexnow_request('GET',p.ORIGIN+path)
                    rows=json.loads(Path('indexnow-http-observations.json').read_text())
                    self.assertEqual(rows[-1]['httpStatus'],status)
                    self.assertEqual(rows[-1]['method'],'GET')

    def test_workflow_has_separate_no_provider_job_and_pinned_evidence(self):
        root=Path(__file__).resolve().parents[2]
        w=(root/'.github/workflows/gwangyang-production-publish.yml').read_text()
        original,recovery=w.split('  finalize_indexnow:\n')
        self.assertNotIn(p.FINALIZE_TITLE,original)
        self.assertIn("github.event.issue.title == '"+p.TITLE+"'",original)
        for word in ['CLOUDFLARE','secrets.','npx ','wrangler@',' preflight ',' attach ',' readback ','continue-on-error','workflow_dispatch']:
            self.assertNotIn(word,recovery)
        for mode in ['authorize','select','artifact','http','indexnow-probe','indexnow']:
            self.assertIn('publish.py" '+mode+' --report',recovery)
        for word in [p.FINALIZE_TITLE,'38793139574','12001425800','d05c5009f29da5bcb7febf9e9444184fa67b9df8','sha256:954a6b89aaddb9f7cd1fff2f0ecf7da56de4f3bfb143cb6648f3f48c3b5682ee',"not (root/'indexnow-receipt.json').exists()",'run.run_attempt !== 1','data.object.sha !== process.env.REVISION','artifact.digest !== review.artifactDigest','merge-multiple: true','listJobsForWorkflowRun','116622567148',"indexnowSteps[0].conclusion !== 'skipped'"]:
            self.assertIn(word,recovery)
        self.assertIn('group: gwangyang-direct-public-release',w)
        self.assertIn('cancel-in-progress: false',w)


if __name__=='__main__':unittest.main()
