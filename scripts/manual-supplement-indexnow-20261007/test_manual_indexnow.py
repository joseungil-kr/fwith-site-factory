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
        self.site.update(revision='a'*40, urlCount=2, changedUrls=[self.site['origin']+'/changed/'], changedUrlCount=1, changes={'evidenceSha256':'b'*64}, qa={'evidenceSha256':'c'*64})
        self.urls = self.site['changedUrls']
        self.site['changedUrlsSha256'] = m.sha(m.canonical(self.urls))
    def test_pending_attestation_blocks(self):
        self.site['revision'] = None
        self.site['qa']['status'] = 'pending'
        with self.assertRaisesRegex(ValueError, 'final_source_pending'):
            m.attest(self.site, Path('.'), lambda p: self.fail('network before QA approval'))
    def test_exact_scope(self):
        self.assertEqual(len(m.ALLOWED), 5)
        self.assertTrue(all(pin == (None,None,None) for key,pin in m.ALLOWED.items() if key != 'suwon-flower-test'))
        self.assertEqual(m.ALLOWED['suwon-flower-test'],('962a279cfb7e3787a02d89c17847bf5f908b7b70',55,'bb47fc73744e420727e13b3352358d7815905c056911a0481c651518cfa0af68'))
        self.assertNotIn('ansan-flower-test', m.ALLOWED)
        self.assertIn('yongin-flower-v2', m.ALLOWED)
        self.assertNotIn('namyangju-flower-v2',m.ALLOWED)
        self.assertNotIn('bucheon-flower-v2',m.ALLOWED)
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
        env={'GITHUB_REPOSITORY':m.REPO,'GITHUB_RUN_ATTEMPT':'1','GITHUB_REF':'refs/heads/manual-suwon-indexnow-supplement-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa','GITHUB_EVENT_NAME':'push','GITHUB_RUN_ID':'1'}
        with patch.dict(os.environ,env):
            with self.assertRaisesRegex(ValueError,'prior_one_time_run'):
                m.execution_guard(self.site,{},lambda p:{'workflow_runs':[{'id':1},{'id':2}]})
    def test_missing_durable_intent_blocks(self):
        env={'GITHUB_REPOSITORY':m.REPO,'GITHUB_RUN_ATTEMPT':'1','GITHUB_REF':'refs/heads/manual-suwon-indexnow-supplement-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa','GITHUB_EVENT_NAME':'push','GITHUB_RUN_ID':'1'}
        with patch.dict(os.environ,env):
            with self.assertRaisesRegex(ValueError,'durable_intent_artifact_missing'):
                m.execution_guard(self.site,{},lambda p:{'workflow_runs':[{'id':1,'head_sha':os.environ.get('GITHUB_SHA'),'head_branch':'manual-suwon-indexnow-supplement-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa','event':'push','run_attempt':1,'path':'.github/workflows/suwon-manual-indexnow-supplement-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.yml'}]} if '/workflows/' in p else {'artifacts':[]})
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
            env={'GITHUB_REPOSITORY':m.REPO,'GITHUB_RUN_ATTEMPT':'1','GITHUB_REF':'refs/heads/manual-suwon-indexnow-supplement-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa','GITHUB_EVENT_NAME':'push','GITHUB_RUN_ID':'1','GITHUB_SHA':'abc'}
            args=['test','--plan',str(plan),'--site',self.site['siteKey'],'--intent',str(intent),'--report',str(receipt)]
            evidence={'urlSetSha256':m.sha(m.canonical(self.urls)), '_changed':self.urls}
            posted=[]
            def api(path):
                if '/workflows/' in path:return {'workflow_runs':[{'id':1,'head_sha':'abc','head_branch':'manual-suwon-indexnow-supplement-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa','event':'push','run_attempt':1,'path':'.github/workflows/suwon-manual-indexnow-supplement-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.yml'}]}
                if '/artifacts?' in path:
                    data=json.loads(intent.read_text());return {'artifacts':[{'name':'indexnow-supplement-intent-suwon-'+m.sha(m.canonical(data)),'expired':False,'size_in_bytes':len(intent.read_bytes())}]}
                if '/git/ref/' in path:return {'object':{'sha':self.site['revision']}}
                self.fail(path)
            def post(method,url,payload):posted.append((method,url,payload));return 200,b'',{}
            original_guard=m.execution_guard
            with patch.dict(os.environ,env), patch.object(m,'attest',return_value=evidence), patch.object(m,'verify',return_value=[self.site['origin']+'/']+self.urls) as verify, patch.object(m,'public_api',side_effect=api), patch.object(m,'execution_guard',side_effect=lambda site,intent:original_guard(site,intent,api)), patch.object(m,'request',side_effect=post):
                with patch.object(sys,'argv',args):self.assertEqual(m.run_cli(),0)
                self.assertEqual(posted,[])
                downloaded=root/'downloaded'/'indexnow-intent.json';downloaded.parent.mkdir();shutil.copyfile(intent,downloaded)
                submitargs=args.copy();submitargs[submitargs.index('--intent')+1]=str(downloaded);submitargs+=['--submit']
                with patch.object(sys,'argv',submitargs):self.assertEqual(m.run_cli(),0)
                self.assertEqual(len(posted),1);self.assertEqual(verify.call_count,2)
                self.assertEqual(posted[0][2]['urlList'],self.urls)
                self.assertEqual(json.loads(intent.read_text())['fullUrlCount'],2)
                self.assertEqual(json.loads(receipt.read_text())['state'],'received')
                with patch.object(sys,'argv',submitargs):self.assertEqual(m.run_cli(),1)
                self.assertEqual(len(posted),1);self.assertEqual(json.loads(receipt.read_text())['state'],'received')

    def test_entrypoint_routes_cli_without_post(self):
        with patch.object(m, 'run_cli', return_value=0) as run, patch.object(m, 'request', side_effect=AssertionError('unexpected request')):
            self.assertEqual(m.main(), 0)
            run.assert_called_once_with()

class ProofTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.root=Path(self.temp.name)
        self.addCleanup(self.temp.cleanup)
        self.site=dict(siteKey='suwon-flower-test',origin='https://suwon.fwith.kr',revision='a'*40,baselineRevision=m.BASELINES['suwon-flower-test'])
        self.url=self.site['origin']+'/changed/'
        self.site.update(changedUrls=[self.url],changedUrlCount=1,changedUrlsSha256=m.sha(m.canonical([self.url])))
        def html(rev,body):return (f'<html><head><meta name="site-factory-revision" content="{rev}"><meta name="robots" content="index,follow"><link rel="canonical" href="{self.url}"></head><body>{body}</body></html>').encode()
        self.html=html
        self.before=html(self.site['baselineRevision'],'old content');self.after=html(self.site['revision'],'new content')
        self.page=dict(url=self.url,kind='changed-detail',semanticReview=True,before=self.save('before.html',self.before),after=self.save('after.html',self.after))
        self.proof=dict(status='passed',author='content-author',reviewer='independent-content-review',siteKey=self.site['siteKey'],origin=self.site['origin'],sourceRevision=self.site['revision'],baselineRevision=self.site['baselineRevision'],pages=[self.page])
        self.http={'responses':[dict(url=self.url,expectedStatus=200,headers={'content-type':'text/html'},expectedSha256=m.sha(self.after))]}
    def save(self,name,data):
        (self.root/name).write_bytes(data);return {'path':name,'sha256':m.sha(data)}
    def check(self):
        baseline={'sourceRevision':self.site['baselineRevision'],'origin':self.site['origin'],'complete':True,'htmlUrls':{self.url:m.sha(self.before)}}
        old_http={'passed':True,'phase':'production','sourceRevision':self.site['baselineRevision'],'origin':self.site['origin'],'responses':[dict(url=self.url,status=200,expectedStatus=200,exactFinalUrl=True,expectedSha256=m.sha(self.before),comparison={'expectedArtifactSha256':m.sha(self.before)},headers={'content-type':'text/html'})]}
        baseline['publicHttp']=self.save('old-http.json',m.canonical(old_http))
        self.proof['baselineManifest']=self.save('baseline.json',m.canonical(baseline))
        raw=m.canonical(self.proof);(self.root/'changes.json').write_bytes(raw)
        self.site['changes']={'evidencePath':'changes.json','evidenceSha256':m.sha(raw)}
        with patch.dict(m.BASELINE_HTTP_SHA256,{self.site['siteKey']:baseline['publicHttp']['sha256']}):
            return m.validate_changes(self.site,self.root,self.http)
    def test_content_subset_proof(self):self.assertEqual(self.check(),[self.url])
    def test_subset_not_in_sitemap(self):
        with self.assertRaisesRegex(ValueError,'not_in_verified_sitemap'):m.select_changed(self.site,{'_changed':self.check()},[self.site['origin']+'/'])
    def test_noindex_rejected(self):
        self.after=self.after.replace(b'index,follow',b'noindex,follow');self.page['after']=self.save('after.html',self.after);self.http['responses'][0]['expectedSha256']=m.sha(self.after)
        with self.assertRaisesRegex(ValueError,'robots_blocked'):self.check()
    def test_revision_only_change_rejected(self):
        self.after=self.html(self.site['revision'],'old content');self.page['after']=self.save('after.html',self.after);self.http['responses'][0]['expectedSha256']=m.sha(self.after)
        with self.assertRaisesRegex(ValueError,'unchanged_content_candidate'):self.check()
    def test_metadata_only_change_rejected(self):
        self.after=self.html(self.site['revision'],'old content').replace(b'</head>',b'<meta name="description" content="changed"></head>')
        self.page['after']=self.save('after.html',self.after);self.http['responses'][0]['expectedSha256']=m.sha(self.after)
        with self.assertRaisesRegex(ValueError,'unchanged_content_candidate'):self.check()
    def test_formatting_only_change_rejected(self):
        self.after=self.html(self.site['revision'],'old   content')
        self.page['after']=self.save('after.html',self.after);self.http['responses'][0]['expectedSha256']=m.sha(self.after)
        with self.assertRaisesRegex(ValueError,'unchanged_content_candidate'):self.check()
    def test_non_html_mime_change_rejected(self):
        row=dict(url=self.site['origin']+'/image.png',expectedStatus=200,expectedSha256=m.sha(b'png'),headers={'content-type':'image/png'},comparison={'expectedArtifactBytes':3})
        with self.assertRaisesRegex(ValueError,'reviewed_content_type_changed'):
            m.verify(self.site|{'indexnowKey':'12345678'},{'_http':{'responses':[row]}},lambda *a:(200,b'png',{'content-type':'text/html'}))
    def test_digest_changed(self):
        (self.root/'after.html').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'content_proof_digest_changed'):self.check()
    def test_source_changed(self):
        self.proof['sourceRevision']='f'*40
        with self.assertRaisesRegex(ValueError,'changed_url_source_mismatch'):self.check()
    def test_live_artifact_stays_exact(self):
        row={'expectedSha256':m.sha(self.before),'headers':{'content-type':'text/html'},'comparison':{'expectedArtifactBytes':len(self.before)}}
        self.assertFalse(m.artifact_matches(self.before.replace(self.site['baselineRevision'].encode(),self.site['revision'].encode()),row))
    def test_unknown_beacon_rejected(self):
        row={'expectedSha256':m.sha(self.after),'headers':{'content-type':'text/html'},'comparison':{'expectedArtifactBytes':len(self.after)}}
        self.assertFalse(m.artifact_matches(self.after.replace(b'</body>',b'<script src="unknown"></script></body>'),row))
    def test_full_site_verified_but_only_changed_subset_selected(self):
        origin=self.site['origin'];site=self.site|{'indexnowKey':'12345678','urlCount':3}
        urls=sorted([origin+'/',self.url,origin+'/unchanged/'])
        bodies={origin+'/12345678.txt':(200,b'12345678','text/plain'),origin+'/robots.txt':(200,b'User-agent: *\nAllow: /','text/plain'),origin+'/sitemap-index.xml':(200,('<urlset>'+''.join('<url><loc>'+u+'</loc></url>' for u in urls)+'</urlset>').encode(),'application/xml'),origin+'/image.png':(200,b'png','image/png'),origin+'/missing/':(404,b'missing','text/html'),origin+'/thin/':(200,b'noindex retained bytes','text/html')}
        for u in urls:bodies[u]=(200,self.html(site['revision'],'content').replace(self.url.encode(),u.encode()),'text/html')
        rows=[dict(url=u,expectedStatus=status,expectedSha256=m.sha(body),headers={'content-type':mime},comparison={'expectedArtifactBytes':len(body)}) for u,(status,body,mime) in bodies.items()]
        evidence={'_http':{'responses':rows},'urlSetSha256':m.sha(m.canonical(urls)),'_changed':[self.url]};called=[]
        def transport(method,url):
            called.append(url);status,body,mime=bodies[url];return status,body,{'content-type':mime}
        full=m.verify(site,evidence,transport)
        self.assertEqual(full,urls);self.assertEqual(set(called),set(bodies))
        self.assertEqual(m.select_changed(site,evidence,full),[self.url])

    def test_whole_scan_not_subset(self):
        # Even an unrelated retained artifact must be checked before subset selection.
        rows=[];called=[]
        for suffix in ('/unsubmitted.png','/changed/'):
            body=b'bytes';rows.append(dict(url=self.site['origin']+suffix,expectedStatus=200,expectedSha256=m.sha(body),headers={'content-type':'image/png'},comparison={'expectedArtifactBytes':len(body)}))
        site=self.site|{'indexnowKey':'12345678'}
        def transport(method,url):
            called.append(url);return 200,b'bytes' if len(called)==1 else b'corrupt',{'content-type':'image/png'}
        with self.assertRaisesRegex(ValueError,'reviewed_artifact_bytes_changed'):m.verify(site,{'_http':{'responses':rows}},transport)
        self.assertEqual(called,[r['url'] for r in rows])

if __name__=='__main__':unittest.main()
