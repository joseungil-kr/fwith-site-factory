import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import manual_indexnow as m

class MemoryJournal:
    def __init__(self, records=None): self.rows = records or []
    def records(self): return self.rows
    def write(self, record): self.rows.append(dict(record)); return 'receipt'

class Tests(unittest.TestCase):
    def setUp(self):
        self.site = json.loads(Path(__file__).with_name('plan.pending.json').read_text())['sites'][0]
        self.urls = [self.site['origin'] + '/']
    def test_pending_attestation_blocks(self):
        self.site['qa']['status'] = 'pending'
        with self.assertRaisesRegex(ValueError, 'independent_public_qa_pending'):
            m.attest(self.site, Path('.'), lambda p: self.fail('network before QA approval'))
    def test_exact_scope(self):
        self.assertEqual(sum(count for rev, count in m.ALLOWED.values()), 301)
        self.assertNotIn('ansan-flower-test', m.ALLOWED)
        self.assertNotIn('yongin-flower-v2', m.ALLOWED)
    def test_one_accepted_post(self):
        calls=[]; j=MemoryJournal()
        def post(*args):
            self.assertEqual(j.rows[-1]['state'], 'started'); calls.append(args); return 200, '', {}
        result=m.submit(self.site,self.urls,j,post)
        self.assertEqual(result['state'],'received'); self.assertEqual(len(calls),1)
        self.assertEqual(m.submit(self.site,self.urls,j,post)['state'],'already_received')
        self.assertEqual(len(calls),1)
    def test_202_not_claim_indexing(self):
        result=m.submit(self.site,self.urls,MemoryJournal(),lambda *a:(202,'',{}))
        self.assertEqual(result['state'],'received_key_validation_pending')
    def test_unknown_no_retry(self):
        j=MemoryJournal(); calls=[]
        def timeout(*args): calls.append(args); raise TimeoutError()
        with self.assertRaisesRegex(ValueError,'unknown'): m.submit(self.site,self.urls,j,timeout)
        self.assertEqual(j.rows[-1]['state'],'unknown')
        with self.assertRaisesRegex(ValueError,'do_not_replay'): m.submit(self.site,self.urls,j,timeout)
        self.assertEqual(len(calls),1)
    def test_429_no_automatic_retry(self):
        j=MemoryJournal(); calls=[]
        def reject(*args): calls.append(args); return 429,'',{'retry-after':'1'}
        with self.assertRaisesRegex(ValueError,'not_accepted'): m.submit(self.site,self.urls,j,reject)
        with self.assertRaisesRegex(ValueError,'do_not_replay'): m.submit(self.site,self.urls,j,reject)
        self.assertEqual(len(calls),1)
    def test_journal_failure_no_post(self):
        j=MemoryJournal(); j.write=lambda _: (_ for _ in ()).throw(OSError())
        with self.assertRaises(OSError): m.submit(self.site,self.urls,j,lambda *a:self.fail('POST'))
    def test_missing_final_receipt_blocks(self):
        j=MemoryJournal()
        def write(row):
            if row['state']!='started': raise OSError()
            j.rows.append(dict(row))
        j.write=write
        with self.assertRaises(OSError): m.submit(self.site,self.urls,j,lambda *a:(200,'',{}))
        with self.assertRaisesRegex(ValueError,'do_not_replay'): m.submit(self.site,self.urls,j,lambda *a:self.fail('POST'))
    def test_exact_html_mime(self):
        self.assertEqual(m.mime(' text/html; charset=utf-8'), 'text/html')
        self.assertNotEqual(m.mime('application/not-text/html'), 'text/html')
        self.assertNotEqual(m.mime('text/html,text/plain'), 'text/html')
    def test_safe_paths(self):
        for url in ['https://other.test/','http://namyangju.fwith.kr/','https://namyangju.fwith.kr/a?b','https://namyangju.fwith.kr/%2e%2e/a']:
            with self.assertRaises(ValueError): m.normalize(url,self.site['origin'])
    def test_page_revision_canonical_robots(self):
        html=f'<meta name="site-factory-revision" content="{self.site["revision"]}"><meta name="robots" content="index,follow"><link rel="canonical" href="{self.urls[0]}">'
        m.validate_page(html,{},self.urls[0],self.site)
        for value in [html.replace('index,follow','noindex'),html.replace(self.site['revision'],'0'*40),html.replace(self.urls[0],self.site['origin']+'/wrong/')]:
            with self.assertRaises(ValueError):m.validate_page(value,{},self.urls[0],self.site)
    def test_prior_run_blocks(self):
        env={'GITHUB_REPOSITORY':m.REPO,'GITHUB_RUN_ATTEMPT':'1','GITHUB_REF':'refs/heads/manual-namyangju-indexnow-final-20261007','GITHUB_EVENT_NAME':'push','GITHUB_RUN_ID':'1'}
        with patch.dict(os.environ,env):
            with self.assertRaisesRegex(ValueError,'prior_one_time_run'):
                m.execution_guard(self.site,{},lambda p:{'workflow_runs':[{'id':1},{'id':2}]})
    def test_missing_durable_intent_blocks(self):
        env={'GITHUB_REPOSITORY':m.REPO,'GITHUB_RUN_ATTEMPT':'1','GITHUB_REF':'refs/heads/manual-namyangju-indexnow-final-20261007','GITHUB_EVENT_NAME':'push','GITHUB_RUN_ID':'1'}
        with patch.dict(os.environ,env):
            with self.assertRaisesRegex(ValueError,'durable_intent_artifact_missing'):
                m.execution_guard(self.site,{},lambda p:{'workflow_runs':[{'id':1,'head_sha':os.environ.get('GITHUB_SHA'),'head_branch':'manual-namyangju-indexnow-final-20261007','event':'push','run_attempt':1,'path':'.github/workflows/namyangju-manual-indexnow-final-20261007.yml'}]} if '/workflows/' in p else {'artifacts':[]})
    def test_rerun_blocked(self):
        with patch.dict(os.environ,{'GITHUB_REPOSITORY':m.REPO,'GITHUB_RUN_ATTEMPT':'2'}):
            with self.assertRaisesRegex(ValueError,'first_trusted'): m.execution_guard(self.site,{},lambda _:self.fail('api'))
    def test_disk_receipt_readback(self):
        with tempfile.TemporaryDirectory() as d:
            j=m.Journal(Path(d)/'receipt.json'); j.write({'state':'started'})
            self.assertEqual(j.records(),[{'state':'started'}])
    def test_entire_cli_prepare_then_submit(self):
        import shutil, sys
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary); plan=root/'plan.json'
            plan.write_text(json.dumps({'repository':m.REPO,'endpoint':m.ENDPOINT,'sites':[self.site]}))
            intent=root/'indexnow-intent.json'; receipt=root/'receipt.json'
            env={'GITHUB_REPOSITORY':m.REPO,'GITHUB_RUN_ATTEMPT':'1','GITHUB_REF':'refs/heads/manual-namyangju-indexnow-final-20261007','GITHUB_EVENT_NAME':'push','GITHUB_RUN_ID':'1','GITHUB_SHA':'abc'}
            args=['test','--plan',str(plan),'--site',self.site['siteKey'],'--intent',str(intent),'--report',str(receipt)]
            evidence={'urlSetSha256':m.sha(m.canonical(self.urls))}
            posted=[]
            def api(path):
                if '/workflows/' in path:return {'workflow_runs':[{'id':1,'head_sha':'abc','head_branch':'manual-namyangju-indexnow-final-20261007','event':'push','run_attempt':1,'path':'.github/workflows/namyangju-manual-indexnow-final-20261007.yml'}]}
                if '/artifacts?' in path:
                    data=json.loads(intent.read_text());return {'artifacts':[{'name':'indexnow-intent-namyangju-'+m.sha(m.canonical(data)),'expired':False,'size_in_bytes':len(intent.read_bytes())}]}
                if '/git/ref/' in path:return {'object':{'sha':self.site['revision']}}
                self.fail(path)
            def post(method,url,payload):posted.append((method,url,payload));return 200,b'',{}
            original_guard=m.execution_guard
            with patch.dict(os.environ,env), patch.object(m,'attest',return_value=evidence), patch.object(m,'verify',return_value=self.urls) as verify, patch.object(m,'public_api',side_effect=api), patch.object(m,'execution_guard',side_effect=lambda site,intent:original_guard(site,intent,api)), patch.object(m,'request',side_effect=post):
                with patch.object(sys,'argv',args):self.assertEqual(m.run_cli(),0)
                self.assertEqual(posted,[])
                downloaded=root/'downloaded'/'indexnow-intent.json';downloaded.parent.mkdir();shutil.copyfile(intent,downloaded)
                submitargs=args.copy();submitargs[submitargs.index('--intent')+1]=str(downloaded);submitargs+=['--submit']
                with patch.object(sys,'argv',submitargs):self.assertEqual(m.run_cli(),0)
                self.assertEqual(len(posted),1);self.assertEqual(verify.call_count,2)
                self.assertEqual(json.loads(receipt.read_text())['state'],'received')
                with patch.object(sys,'argv',submitargs):self.assertEqual(m.run_cli(),1)
                self.assertEqual(len(posted),1);self.assertEqual(json.loads(receipt.read_text())['state'],'received')

    def test_entrypoint_routes_cli_without_post(self):
        with patch.object(m, 'run_cli', return_value=0) as run, patch.object(m, 'request', side_effect=AssertionError('unexpected request')):
            self.assertEqual(m.main(), 0)
            run.assert_called_once_with()

if __name__=='__main__':unittest.main()
