"""Trusted offline finalizer tests. All HTTP is a local fake opener."""
import copy, hashlib, io, json, os, socket, tempfile, unittest
from pathlib import Path
from http.client import IncompleteRead
from unittest.mock import patch
import finalize_recovery as f
import indexnow_recovery as g

D=Path(__file__).resolve().parent;ROOT=D.parents[1]
CONTRACT=g.load_contract(D/'contract-source')
URL=g._submission_url(CONTRACT)

class Headers:
    def __init__(self,rows):self.rows=rows
    def items(self):return self.rows
class Response:
    def __init__(self,body=b'Invalid urls',status=422,headers=None,url=URL):
        self.body=body;self.code=status;self.headers=Headers(headers if headers is not None else [('content-type','text/plain'),('content-length',str(len(body)))]);self.url=url;self.pos=0
    def geturl(self):return self.url
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def read(self,n):
        b=self.body[self.pos:self.pos+n];self.pos+=len(b);return b
class Opener:
    def __init__(self,response):self.response=response;self.calls=[]
    def open(self,request,timeout):
        self.calls.append((request,timeout))
        if isinstance(self.response,Exception):raise self.response
        return self.response
class Case(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        for name in ('socket.create_connection','socket.socket.connect'):
            p=patch(name,side_effect=AssertionError('network_forbidden'));p.start();self.addCleanup(p.stop)
    def http(self,response=None):
        opener=Opener(response if response is not None else Response())
        value=f.BoundedHTTP('offline-fixture-token',set(),{g.HOME},opener=opener,contract=CONTRACT,evidence=self.root/'evidence')
        return value,opener
    def blocked(self,fn,reason='.*'):
        with self.assertRaisesRegex((g.RecoveryBlocked,ValueError,AssertionError),reason):fn()

class SingleGetHTTP(Case):
    def test_exact_get_request_and_response_raw(self):
        h,o=self.http();r=h.call('GET',URL)
        self.assertEqual(r.status,422);self.assertEqual(len(o.calls),1)
        req,timeout=o.calls[0];self.assertEqual(req.get_method(),'GET');self.assertIsNone(req.data)
        self.assertEqual(req.full_url,URL);self.assertIsNone(req.get_header('Authorization'))
        self.assertEqual(timeout,20);self.assertTrue(h.submission_reserved)
        obs=f.read_json(self.root/'evidence/request-observation.json')
        self.assertEqual(obs['urlBytes'],197);self.assertEqual(obs['bodyBytes'],0);self.assertTrue(obs['actualDataIsNone'])
        self.assertEqual(obs['semanticIntentBytes'],193);self.assertFalse(obs['authorizationHeaderPresent'])
        self.assertEqual((self.root/'evidence/response-body.txt').read_bytes(),b'Invalid urls')
        response=f.read_json(self.root/'evidence/response-observation.json')
        self.assertTrue(response['responseBodyReadComplete']);self.assertEqual(response['rawBodyBytes'],12)
    def test_naver_post_and_other_single_get_urls_rejected_before_open(self):
        bad=[URL+'&x=1',URL+'&url='+g.HOME,URL.replace('damyang','gokseong'),URL.replace('%3A','%253A'),URL+'#x',URL.replace('https://searchadvisor','http://searchadvisor'),URL.replace('searchadvisor.naver.com','searchadvisor.naver.com.evil'),URL.replace('/indexnow?','/indexnow/?'),g.ENDPOINT]
        for url in bad:
            h,o=self.http()
            with self.subTest(url=url):self.blocked(lambda:h.call('GET',url),'fixed_http_scope');self.assertEqual(o.calls,[])
        h,o=self.http();self.blocked(lambda:h.call('POST',g.ENDPOINT,json.dumps(g._payload(CONTRACT)).encode()),'fixed_http_scope');self.assertEqual(o.calls,[])
    def test_get_payload_forbidden(self):
        for payload in (b'',b'{}',{},''):
            h,o=self.http()
            with self.subTest(payload=payload):self.blocked(lambda:h.call('GET',URL,payload),'fixed_http_scope');self.assertEqual(o.calls,[])
    def test_submission_reservation_before_request_constructor(self):
        h,o=self.http()
        with patch.object(f,'Request',side_effect=ValueError('synthetic_constructor_failure')):self.blocked(lambda:h.call('GET',URL))
        self.assertTrue(h.submission_reserved);self.assertEqual(o.calls,[])
        self.blocked(lambda:h.call('GET',URL),'caller_single_submission_only')
    def test_timeout_never_retries_or_falls_back(self):
        h,o=self.http(TimeoutError('synthetic'))
        self.blocked(lambda:h.call('GET',URL),'http_outcome_unconfirmed')
        self.blocked(lambda:h.call('GET',URL),'caller_single_submission_only')
        self.assertEqual(len(o.calls),1);self.assertEqual(o.calls[0][0].get_method(),'GET')
    def test_statuses_complete_and_second_submission_denied(self):
        for status in (200,202,403,422,429,500):
            h,o=self.http(Response(b'',status))
            with self.subTest(status=status):
                self.assertEqual(h.call('GET',URL).status,status)
                self.blocked(lambda:h.call('GET',URL),'caller_single_submission_only');self.assertEqual(len(o.calls),1)
    def test_redirect_or_changed_response_url_is_not_followed(self):
        for response in (Response(status=301),Response(url='https://other.invalid/')):
            h,o=self.http(response)
            with self.subTest(response=response.url):self.blocked(lambda:h.call('GET',URL));self.assertEqual(len(o.calls),1)
    def test_truncated200_and202_are_unknown_and_budget_spent(self):
        for status in (200,202,422):
            h,o=self.http(Response(b'partial',status,[('content-length','100')]))
            with self.subTest(status=status):
                self.blocked(lambda:h.call('GET',URL),'truncated_http_body')
                v=f.read_json(self.root/'evidence/response-failure-observation.json')
                self.assertFalse(v['responseBodyReadComplete']);self.assertFalse(v['submissionOutcomeConfirmed'])
                self.assertTrue(v['submissionBudgetSpent']);self.assertEqual(v['capturedPrefixBytes'],7)
                self.blocked(lambda:h.call('GET',URL),'caller_single_submission_only');self.assertEqual(len(o.calls),1)
    def test_incomplete_read_keeps_prefix_without_retry(self):
        class Partial(Response):
            def read(self,n):raise IncompleteRead(b'partial',93)
        h,o=self.http(Partial(b'',200,[('content-length','100')]))
        self.blocked(lambda:h.call('GET',URL),'http_outcome_unconfirmed')
        v=f.read_json(self.root/'evidence/response-failure-observation.json')
        self.assertEqual(v['capturedPrefixSha256'],g.sha(b'partial'));self.assertFalse(v['responseBodyReadComplete']);self.assertEqual(len(o.calls),1)
    def test_unsafe_raw_withheld_but_complete_diagnostics_survive(self):
        h,o=self.http(Response(b'Bearer PRIVATE_SENTINEL'))
        h.call('GET',URL);v=f.read_json(self.root/'evidence/response-observation.json')
        self.assertTrue(v['responseBodyReadComplete']);self.assertFalse(v['rawBodyRetained'])
        self.assertFalse((self.root/'evidence/response-body.txt').exists());self.assertNotIn('PRIVATE_SENTINEL',json.dumps(v))
    def test_capture_write_failure_still_has_no_second_submission(self):
        h,o=self.http();(self.root/'evidence').mkdir();(self.root/'evidence/response-body.txt').mkdir()
        self.blocked(lambda:h.call('GET',URL),'http_outcome_unconfirmed')
        self.blocked(lambda:h.call('GET',URL),'caller_single_submission_only');self.assertEqual(len(o.calls),1)
    def test_public_probe_remains_unreserved_and_credential_free(self):
        h,o=self.http(Response(b'home',200,url=g.HOME));h.call('GET',g.HOME)
        self.assertFalse(h.submission_reserved);self.assertIsNone(o.calls[0][0].get_header('Authorization'))
        self.assertFalse((self.root/'evidence').exists())
    def test_github_token_only_to_fixed_repository_api(self):
        url=g.API_BASE+'/actions/runs/1';o=Opener(Response(b'{}',200,url=url))
        h=f.BoundedHTTP('offline-fixture-token',{url},set(),opener=o,contract=CONTRACT,evidence=self.root/'evidence')
        h.call('GET',url);self.assertEqual(o.calls[0][0].get_header('Authorization'),'Bearer offline-fixture-token')
        self.assertFalse(h.submission_reserved)
    def test_raw_safety_exact_only(self):
        allowed=[b'Invalid urls',b'']
        denied=[b'{"message":"Invalid urls","status":422}',b'{"token":"secret"}',b'{"arbitrary":"data"}',b'{"message":{"x":1}}',b'[1]',b'{"message":"bad\\nvalue"}',b'{"message":',b'api-key=abc',b'pwd=abc',b'\xff',b'x'*4097]
        for raw in allowed:
            with self.subTest(raw=raw):self.assertEqual(f.safe_raw_body(g.RawResponse(422,raw,[]),CONTRACT),raw)
        for raw in denied:
            with self.subTest(raw=raw):self.assertIsNone(f.safe_raw_body(g.RawResponse(422,raw,[]),CONTRACT))

    def test_raw_literal_canaries_and_near_matches_always_withheld(self):
        values=[b'Basic YWJjOjEyMw==',b'auth=abcd1234',b'session=abcd1234',b'access_key=abcd1234',
            b'Invalid urls\n',b' Invalid urls',b'invalid urls',b'Invalid urls Basic YWJjOjEyMw==',
            b'{"message":"auth=abcd1234"}',b'Basic\x00YWJjOjEyMw==',b'api-key=abcd1234',
            b'Bearer abcd1234',b'password=abcd1234',b'Invalid urls\r',b'Invalid urls\t',
            b'Invalid urls; auth=abcd1234',b'Invalid urls'+b'x'*4096]
        for raw in values:
            with self.subTest(raw=raw):self.assertIsNone(f.safe_raw_body(g.RawResponse(422,raw,[]),CONTRACT))
        self.assertIsNone(f.safe_raw_body(g.RawResponse(422,bytearray(b'Invalid urls'),[]),CONTRACT))
    def test_complete_and_partial_canaries_not_written_as_raw(self):
        canaries=[b'Basic YWJjOjEyMw==',b'auth=abcd1234',b'session=abcd1234',b'access_key=abcd1234']
        for raw in canaries:
            for status in (200,202,422):
                for partial in (False,True):
                    with self.subTest(raw=raw,status=status,partial=partial):
                        h,o=self.http(Response(raw,status,[('content-length','100')]if partial else None))
                        if partial:self.blocked(lambda:h.call('GET',URL),'truncated_http_body')
                        else:h.call('GET',URL)
                        self.assertFalse((self.root/'evidence/response-body.txt').exists())
                        self.assertFalse((self.root/'evidence/response-body.failed-prefix.txt').exists())
                        name='response-failure-observation.json'if partial else'response-observation.json'
                        evidence=f.read_json(self.root/'evidence'/name)
                        self.assertEqual(evidence['capturedPrefixSha256'if partial else'rawBodySha256'],g.sha(raw))
                        self.assertEqual(evidence['capturedPrefixBytes'if partial else'rawBodyBytes'],len(raw))
                        self.assertEqual(evidence['responseBodyReadComplete'],not partial)
                        self.assertNotIn(raw.decode(),json.dumps(evidence))
                        self.blocked(lambda:h.call('GET',URL),'caller_single_submission_only')
                        self.assertEqual(len(o.calls),1)

class HistoricalIdentity(Case):
    def fixture(self):
        row=f.ACTUAL_RECONCILIATION
        run={'id':row['runId'],'run_attempt':1,'event':'issues','head_branch':'main','head_sha':row['controlRevision'],'path':f.WORKFLOW,'repository':{'id':1360554691,'full_name':g.REPOSITORY},'actor':{'login':f.OWNER},'triggering_actor':{'login':f.OWNER},'status':'completed','conclusion':'success'}
        job={'id':117108113694,'run_id':row['runId'],'run_attempt':1,'head_branch':'main','head_sha':row['controlRevision'],'name':'recovery_static_update','status':'completed','conclusion':'success','steps':copy.deepcopy(f.ACTUAL_RECONCILIATION_STEPS)}
        return run,job
    def test_exact_get_only_identity(self):
        self.assertTrue(f.verify_reconciliation_run(*self.fixture()))
    def test_mutation_steps_cannot_be_promoted_from_skipped(self):
        for number in (9,10,11,12,13,14,16):
            run,job=self.fixture();next(x for x in job['steps']if x['number']==number)['conclusion']='success'
            with self.subTest(step=number):self.blocked(lambda:f.verify_reconciliation_run(run,job),'exact_get_only_steps')
    def test_run_identity_failure_and_wrong_repository_rejected(self):
        for key,value in [('conclusion','failure'),('run_attempt',2),('id',38940944527),('head_sha','a'*40),('head_branch','source'),('repository',{'id':1360554692,'full_name':g.REPOSITORY})]:
            run,job=self.fixture();run[key]=value
            with self.subTest(key=key):self.blocked(lambda:f.verify_reconciliation_run(run,job))
    def test_old_failed_run_still_rejected_by_generic_success_checker(self):
        run,_=self.fixture();run.update(id=f.EXACT_FAILED_UPDATE['runId'],head_sha=f.EXACT_FAILED_UPDATE['controlRevision'],conclusion='failure')
        self.blocked(lambda:f.verify_run(f.EXACT_FAILED_UPDATE,run,f.WORKFLOW),'workflow_run_not_successful')
    def test_two_different_artifacts_remain_bound(self):
        self.assertEqual(len(f.EXACT_FAILED_UPDATE_FILES),17);self.assertEqual(len(f.ACTUAL_RECONCILIATION_FILES),23)
        self.assertNotEqual(f.EXACT_FAILED_UPDATE['artifactDigest'],f.ACTUAL_RECONCILIATION['artifactDigest'])
        self.assertIn('public-http.json',f.EXACT_FAILED_UPDATE_FILES);self.assertNotIn('public-http.json',f.ACTUAL_RECONCILIATION_FILES)
    def test_fixed_four_download_roots_are_opt_in_and_old_three_unchanged(self):
        roots={k:self.root/v for k,v in f.DOWNLOAD_NAMES.items()}
        self.assertTrue(f.verify_download_roots(str(self.root),roots,preparing=True,reconciliation=True))
        self.blocked(lambda:f.verify_download_roots(str(self.root),roots,preparing=True),'fixed_download_workspace')
        roots.pop('reconciliation');self.assertTrue(f.verify_download_roots(str(self.root),roots,preparing=True))
        self.blocked(lambda:f.verify_download_roots(str(self.root),roots,preparing=True,reconciliation=True))

    def test_binding_rechecks_whole_original_claim_before_submission(self):
        pins={'build':{'artifactDigest':'sha256:'+'a'*64}}
        class Journal:
            def get(self,url):
                self_url=g.ISSUE_URL
                if url!=self_url:raise AssertionError('unexpected test URL')
                return {'number':377,'state':'open','title':'[DAMYANG-INDEXNOW-RECEIPTS] 20261016',
                    'user':{'login':f.OWNER},'repository_url':g.API_BASE},None
        r=f.Runtime(pins=pins,env={'GITHUB_SHA':'b'*40,'GITHUB_RUN_ID':'999000001'},
            control_root=ROOT,artifact_root=self.root,baseline_root=self.root,update_root=self.root,
            reconciliation_root=self.root,github=Journal(),http=None)
        def claim_boundary(github,claim,*,whole_repository):
            self.assertIs(whole_repository,True)
            raise RuntimeError('whole-claim-boundary-reached')
        with patch.object(f,'read_json',return_value={}),patch.object(f,'validate_source'),patch.object(f,'verify_bound_role'),patch.object(f,'validate_retained_artifact'),patch.object(f,'validate_actual_build_review'),patch.object(f,'validate_update_evidence'),patch.object(f,'verify_original_upload_claim',side_effect=claim_boundary)as check:
            with self.assertRaisesRegex(RuntimeError,'whole-claim-boundary-reached'):r.validate_binding(r.binding)
            check.assert_called_once()

class DormantBoundary(Case):
    def test_pending_two_modes_stop_before_event_token_or_http(self):
        pins=json.loads((ROOT/'docs/direct-damyang-recovery/finalizer-binding.json').read_text())
        pins['review']=None
        for mode in ('prepare','finalize'):
            with self.subTest(mode=mode),patch.object(f,'read_json',return_value=pins)as read,patch.object(f.sys,'argv',['finalizer',mode,'--control-root',str(ROOT),'--report',str(self.root/'blocked.json')]),patch.object(f,'authorize')as authorize,patch.object(f,'BoundedHTTP')as http,patch.dict(os.environ,{'GH_TOKEN':'PRIVATE_SENTINEL','CLOUDFLARE_API_TOKEN':'PRIVATE_SENTINEL','GITHUB_EVENT_PATH':'DO_NOT_READ'},clear=True):
                self.assertEqual(f.main(),1);authorize.assert_not_called();http.assert_not_called();self.assertEqual(read.call_count,1)
                raw=(self.root/'blocked.json').read_text();self.assertNotIn('PRIVATE_SENTINEL',raw);self.assertIn('exact_independent_operational_review_required',raw)
    def test_code_seal_false_also_blocks_before_files(self):
        with patch.object(f,'OPERATIONAL_CONTROLS_ENABLED',False),patch.object(f,'read_json')as read:
            self.blocked(lambda:f.approved_pins('unused'),'operational_review_seal_missing');read.assert_not_called()
    def test_other_operational_bindings_pending(self):
        for filename in ('update-caller-binding.json','reconciliation-binding.json'):
            pins=f.read_json(ROOT/'docs/direct-damyang-recovery'/filename)
            self.assertIs(pins['operationalActivationAllowed'],False);self.assertIsNone(pins['review'])
    def test_workflow_no_new_credentials_and_four_artifact_roles(self):
        raw=(ROOT/f.WORKFLOW).read_text();job=raw.split('\n  recovery_finalize_indexnow:\n')[1]
        self.assertEqual(job.count('GH_TOKEN: ${{ github.token }}'),2)
        self.assertEqual(job.count('uses: actions/download-artifact@v4'),4)
        self.assertIn('path: damyang-recovery-reconciliation',job);self.assertIn('submission-evidence/',job)
        self.assertNotIn('CLOUDFLARE_',job);self.assertNotIn('setup-node',job);self.assertNotIn('npx',job)
        self.assertIn('contents: read\n      actions: read\n      issues: write',job)


class GuardTransportIntegration(Case):
    def scenario(self,status=200,partial=False,timeout=False):
        # Synthetic local five-resource site; real immutable shared helper and guard.
        revision='a'*40;dist=self.root/'release/dist';dist.mkdir(parents=True)
        files={'index.html':('<html><head><meta name="robots" content="index,follow">'
            '<meta name="site-factory-revision" content="'+revision+'">'
            '<link rel="canonical" href="'+g.HOME+'"></head><body>LOCAL TEST</body></html>'),
            'robots.txt':'User-agent: *\nAllow: /\n',
            'sitemap-index.xml':'<sitemapindex><sitemap><loc>'+g.ORIGIN+'/sitemap-0.xml</loc></sitemap></sitemapindex>',
            'sitemap-0.xml':'<urlset><url><loc>'+g.HOME+'</loc></url></urlset>',
            CONTRACT.active_key+'.txt':CONTRACT.active_key+'\n'}
        public={}
        for name,value in files.items():
            (dist/name).write_text(value);public[g.ORIGIN+('/'if name=='index.html'else'/'+name)]=value.encode()
        def comment(identifier,record):
            return {'id':identifier,'user':{'id':g.BOT_ID,'login':'github-actions[bot]','type':'Bot'},
                'url':g.API_BASE+'/issues/comments/'+str(identifier),'issue_url':g.ISSUE_URL,
                'html_url':g.WEB_ISSUE+'#issuecomment-'+str(identifier),
                'body':g.MARKER+json.dumps(record,ensure_ascii=False,sort_keys=True)}
        comments=[comment(g.CHAIN['originalStartedCommentId'],g.original_record('started')),
                  comment(g.CHAIN['originalRejectedCommentId'],g.original_record('rejected'))]
        writes=[]
        def read_page(number):
            self.assertEqual(number,1);return g.AuditPage(g.page_url(1),200,copy.deepcopy(comments),None,True)
        def write(record):
            writes.append(copy.deepcopy(record));saved=comment(9000000000+len(writes),record);comments.append(saved);return copy.deepcopy(saved)
        case=self;simulate_timeout=timeout
        class Router:
            def __init__(self):self.calls=[]
            def open(self,req,timeout):
                self.calls.append(req)
                case.assertIsNone(req.get_header('Authorization'))
                if req.full_url==URL:
                    case.assertEqual([x['state']for x in writes],['started'])
                    if simulate_timeout:raise TimeoutError('LOCAL_TEST')
                    return Response(b'partial'if partial else b'Invalid urls'if status==422 else b'',status,
                        [('content-length','100')]if partial else None)
                case.assertIn(req.full_url,public)
                return Response(public[req.full_url],200,[('content-type','text/plain'),('Server-Timing','a'),('server-timing','b')],req.full_url)
        router=Router();http=f.BoundedHTTP('offline-fixture-token',set(),set(public),opener=router,contract=CONTRACT,evidence=self.root/'evidence')
        adapter=g.RecoveryAdapter(contract=CONTRACT,binding=g.Binding(revision,'b'*40,'c'*64,
                'https://github.com/'+g.REPOSITORY+'/actions/runs/99999999999'),helper_path=ROOT/'site-factory/engine/indexnow_finalize.py',
            read_page=read_page,write_record=write,transport=http.call,validate_binding=lambda binding:True,
            assert_serialized=lambda:True,validate_full_public_release=lambda binding:True)
        site={'siteKey':g.SITE_KEY,'siteUrl':g.ORIGIN,'indexnowKey':CONTRACT.active_key,'productionEnabled':True,'launchMode':'live'}
        try:result=adapter.run(self.root/'release',site);error=None
        except g.RecoveryBlocked as e:result=None;error=str(e)
        return result,error,writes,router.calls,adapter,http
    def test_full_shared_helper_and_bounded_wire_get200(self):
        value,error,writes,calls,adapter,http=self.scenario()
        self.assertIsNone(error);self.assertEqual(value['state'],'received')
        self.assertEqual([x['state']for x in writes],['started','received'])
        self.assertEqual(sum(x.full_url==URL for x in calls),1);self.assertTrue(all(x.get_method()=='GET'and x.data is None for x in calls))
        self.assertEqual(value['submissionCallsThisInvocation'],1);self.assertEqual(value['httpPostCallsThisInvocation'],0)
        self.assertEqual(adapter.submission_calls,1);self.assertTrue(http.submission_reserved)
    def test_full_helper_and_bounded_wire202(self):
        value,error,writes,calls,adapter,http=self.scenario(202)
        self.assertIsNone(error);self.assertEqual(value['state'],'received_key_validation_pending');self.assertEqual(len(writes),2)
    def test_full_helper422_is_durable_rejection_no_second_get(self):
        value,error,writes,calls,adapter,http=self.scenario(422)
        self.assertIsNotNone(error);self.assertEqual([x['state']for x in writes],['started','rejected'])
        self.assertEqual(writes[-1]['httpStatus'],422);self.assertEqual(sum(x.full_url==URL for x in calls),1)
        self.assertEqual((self.root/'evidence/response-body.txt').read_bytes(),b'Invalid urls')
    def test_full_helper429_has_no_automatic_repeat(self):
        value,error,writes,calls,adapter,http=self.scenario(429)
        self.assertIsNotNone(error);self.assertEqual([x['state']for x in writes],['started','rejected'])
        self.assertEqual(sum(x.full_url==URL for x in calls),1);self.assertEqual(adapter.submission_calls,1)
    def test_partial200_never_becomes_received(self):
        value,error,writes,calls,adapter,http=self.scenario(200,partial=True)
        self.assertIsNotNone(error);self.assertEqual([x['state']for x in writes],['started','unknown'])
        self.assertEqual(sum(x.full_url==URL for x in calls),1);self.assertTrue(http.submission_reserved)
    def test_partial202_never_becomes_key_validation_pending(self):
        value,error,writes,calls,adapter,http=self.scenario(202,partial=True)
        self.assertIsNotNone(error);self.assertEqual([x['state']for x in writes],['started','unknown'])
        self.assertEqual(sum(x.full_url==URL for x in calls),1)

if __name__=='__main__':unittest.main()
