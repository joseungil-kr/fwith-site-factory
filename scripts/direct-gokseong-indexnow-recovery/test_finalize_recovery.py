"""Offline caller tests. No HTTP, workflow issue, provider, or live POST occurs."""
import copy, hashlib, json, os, socket, tempfile, unittest
from email.message import Message
from pathlib import Path
from unittest.mock import patch
import finalize_recovery as f
import indexnow_recovery as g
from test_indexnow_recovery import SOURCE

class Response:
    def __init__(self,url,body=b'',code=200,headers=None):
        self.url=url;self.body=body;self.code=code;self.offset=0
        self.headers=Message()
        for k,v in headers or [('content-type','text/plain')]:self.headers[k]=v
    def geturl(self):return self.url
    def read(self,n):result=self.body[self.offset:self.offset+n];self.offset+=len(result);return result
    def __enter__(self):return self
    def __exit__(self,*args):return False
class Opener:
    def __init__(self,response=None,error=None):self.response=response;self.error=error;self.calls=[]
    def open(self,request,timeout):
        self.calls.append(request)
        if self.error:raise self.error
        return self.response

class CallerTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.contract=g.load_contract(SOURCE)
        self.p=patch.object(socket.socket,'connect',side_effect=AssertionError('network forbidden'));self.p.start();self.addCleanup(self.p.stop)
    def transport(self,body=b'Invalid request',status=422,headers=None):
        opener=Opener(Response(g.ENDPOINT,body,status,headers))
        http=f.BoundedHTTP('offline-fixture-token',{g.ISSUE_URL},{g.HOME},opener=opener)
        http.contract=self.contract;http.evidence=self.root/'evidence'
        return http,opener
    def test_false_seal_blocks_before_reading_path(self):
        with patch.object(f,'OPERATIONAL_CONTROLS_ENABLED',False),patch.object(f,'read_json',side_effect=AssertionError('read forbidden')):
            with self.assertRaisesRegex(g.RecoveryBlocked,'operational_review_seal_missing'):f.approved_pins('/never')
    def test_environment_cannot_override_missing_seal(self):
        with patch.object(f,'OPERATIONAL_CONTROLS_ENABLED',False),patch.dict(os.environ,OPERATIONAL_CONTROLS_ENABLED='true'):
            with self.assertRaisesRegex(g.RecoveryBlocked,'operational_review_seal_missing'):f.approved_pins('/never')
    def test_true_flag_still_requires_independent_review(self):
        with patch.object(f,'OPERATIONAL_CONTROLS_ENABLED',True),patch.object(f,'read_json',return_value={'independentOperationalReview':None}):
            with self.assertRaisesRegex(g.RecoveryBlocked,'independent_operational_review_required'):f.approved_pins('/offline-fixture')
    def test_actual_request_data_and_raw_response_are_retained(self):
        http,opener=self.transport('URL이 key 정보와 일치하지 않습니다'.encode())
        raw=json.dumps(g._payload(self.contract)).encode();r=http.call('POST',g.ENDPOINT,raw)
        self.assertEqual(len(opener.calls),1);self.assertIsNone(opener.calls[0].get_header('Authorization'))
        self.assertEqual((http.evidence/'request-body.json').read_bytes(),raw)
        self.assertEqual((http.evidence/'response-body.txt').read_bytes(),r.body)
        obs=json.loads((http.evidence/'request-observation.json').read_text())
        self.assertEqual(obs['bodyBytes'],196);self.assertEqual(obs['bodySha256'],g.sha(raw))
        self.assertIn('Request.data',obs['provenance'])
    def test_second_post_never_reaches_opener(self):
        h,o=self.transport();raw=json.dumps(g._payload(self.contract)).encode();h.call('POST',g.ENDPOINT,raw)
        with self.assertRaisesRegex(g.RecoveryBlocked,'caller_single_post_only'):h.call('POST',g.ENDPOINT,raw)
        self.assertEqual(len(o.calls),1)
    def test_timeout_reserves_budget_and_never_retries(self):
        h,o=self.transport();o.error=TimeoutError();raw=json.dumps(g._payload(self.contract)).encode()
        with self.assertRaisesRegex(g.RecoveryBlocked,'http_outcome_unconfirmed'):h.call('POST',g.ENDPOINT,raw)
        with self.assertRaisesRegex(g.RecoveryBlocked,'caller_single_post_only'):h.call('POST',g.ENDPOINT,raw)
        self.assertEqual(len(o.calls),1)
    def test_request_retention_failure_prevents_network(self):
        h,o=self.transport();h.evidence.mkdir();(h.evidence/'request-body.json').mkdir()
        with self.assertRaises(OSError):h.call('POST',g.ENDPOINT,json.dumps(g._payload(self.contract)).encode())
        self.assertEqual(o.calls,[]);self.assertTrue(h.post_reserved)
    def test_response_retention_failure_spends_budget(self):
        h,o=self.transport();h.evidence.mkdir();(h.evidence/'response-body.txt').mkdir()
        with self.assertRaises(g.RecoveryBlocked):h.call('POST',g.ENDPOINT,json.dumps(g._payload(self.contract)).encode())
        self.assertEqual(len(o.calls),1)
        with self.assertRaisesRegex(g.RecoveryBlocked,'caller_single_post_only'):h.call('POST',g.ENDPOINT,json.dumps(g._payload(self.contract)).encode())
    def test_changed_serialized_payload_prevents_network(self):
        h,o=self.transport();raw=json.dumps(g._payload(self.contract),separators=(',',':')).encode()
        with self.assertRaisesRegex(g.RecoveryBlocked,'actual_request_bytes_mismatch'):h.call('POST',g.ENDPOINT,raw)
        self.assertEqual(o.calls,[])
    def test_unsafe_body_is_hash_length_only(self):
        for body in [b'Bearer SECRET',b'password=DO_NOT_RETAIN',b'<html>challenge</html>',b'\xff',b'a'*4097,b'http://other.example/secret']:
            self.assertIsNone(f.safe_raw_body(g.RawResponse(422,body,[]),self.contract))
        h,o=self.transport(b'Bearer SECRET');h.call('POST',g.ENDPOINT,json.dumps(g._payload(self.contract)).encode())
        obs=json.loads((h.evidence/'response-observation.json').read_text())
        self.assertFalse(obs['rawBodyRetained']);self.assertFalse((h.evidence/'response-body.txt').exists())
        self.assertEqual(obs['rawBodySha256'],g.sha(b'Bearer SECRET'))
    def test_safe_body_is_not_transformed(self):
        for b in [b'',b'Invalid request\n',b'{"message": "invalid key"}','URL이 key 정보와 일치하지 않습니다'.encode()]:
            self.assertEqual(f.safe_raw_body(g.RawResponse(422,b,[]),self.contract),b)
    def test_api_token_only_exact_github_destination(self):
        o=Opener(Response(g.ISSUE_URL,b'{}',200,[('content-type','application/json')]))
        h=f.BoundedHTTP('offline-fixture-token',{g.ISSUE_URL},{g.HOME},opener=o);h.call('GET',g.ISSUE_URL)
        self.assertEqual(o.calls[0].get_header('Authorization'),'Bearer offline-fixture-token')
        o.response=Response(g.HOME,b'public');h.call('GET',g.HOME)
        self.assertIsNone(o.calls[1].get_header('Authorization'))
    def test_foreign_endpoint_and_get_submission_are_forbidden(self):
        h,o=self.transport()
        for method,url,payload in [('POST','https://api.indexnow.org/indexnow',b'{}'),('GET',g.ENDPOINT+'?url=x',None),('GET','https://api.github.com/user',None)]:
            with self.assertRaisesRegex(g.RecoveryBlocked,'fixed_http_scope_required'):h.call(method,url,payload)
        self.assertEqual(o.calls,[])
    def test_redirect_never_followed(self):
        h,o=self.transport();o.response=Response('https://elsewhere.example',b'',302)
        with self.assertRaisesRegex(g.RecoveryBlocked,'unexpected_response_url'):h.call('GET',g.HOME)
        self.assertIsNone(f.NoRedirect().redirect_request(None,None,None,None,None,None))
    def test_truncated_body_and_compressed_body_are_rejected(self):
        for headers in [[('content-length','10')],[('content-encoding','gzip')],[('content-length','1'),('content-length','1')]]:
            h,o=self.transport();o.response=Response(g.HOME,b'x',200,headers)
            with self.assertRaises(g.RecoveryBlocked):h.call('GET',g.HOME)
    def test_telemetry_duplicate_only(self):
        good=g.RawResponse(200,b'x',[('content-type','text/plain'),('server-timing','a'),('server-timing','b')])
        self.assertEqual(f.checked_headers(good)['Server-Timing'],'a')
        for headers in [[('content-type','a'),('Content-Type','a')],[('content-type','a'),('server-timing','a\nb')],[('content-type','a')]*101]:
            with self.assertRaises(g.RecoveryBlocked):f.checked_headers(g.RawResponse(200,b'x',headers))
    def test_numeric_github_link_exact_repository_normalized(self):
        class HTTP:
            def call(self,*args):return g.RawResponse(200,b'[]',[('content-type','application/json'),('link','<https://api.github.com/repositories/1360554691/issues/comments?per_page=100&page=2>; rel="next"')])
        page=f.GitHubClient(HTTP()).read_page(1)
        self.assertEqual(page.next_url,g.page_url(2))
    def test_link_foreign_repository_query_and_page_rejected(self):
        for dest in ['https://api.github.com/repositories/1/issues/comments?per_page=100&page=2',g.API_BASE+'/issues/comments?page=2&per_page=100',g.page_url(3),g.API_BASE+'/issues/399/comments?per_page=100&page=2']:
            class HTTP:
                def call(self,*args):return g.RawResponse(200,b'[]',[('content-type','application/json'),('link','<'+dest+'>; rel="next"')])
            with self.assertRaises(g.RecoveryBlocked):f.GitHubClient(HTTP()).read_page(1)
    def test_duplicate_and_nonfinite_json_rejected(self):
        for raw in [b'{"a":1,"a":2}',b'{"a":NaN}']:
            with self.assertRaises(g.RecoveryBlocked):f.json_raw(raw)
    def test_exact_run_failure_is_valid_only_for_original_publication(self):
        pins=f.read_json(Path(__file__).parent/'recovery-binding.json');row=pins['publication']
        data=dict(id=row['runId'],run_attempt=1,event='issues',head_branch='main',head_sha=row['controlRevision'],path=row['workflowPath'],repository={'full_name':g.REPOSITORY},actor={'login':f.OWNER},triggering_actor={'login':f.OWNER},status='completed',conclusion='failure')
        f.verify_run(row,data,row['workflowPath'])
        for key,value in [('conclusion','success'),('run_attempt',2),('head_sha','a'*40),('actor',{'login':'other'})]:
            changed=copy.deepcopy(data);changed[key]=value
            with self.assertRaises(g.RecoveryBlocked):f.verify_run(row,changed,row['workflowPath'])
    def test_artifact_digest_and_expiry_must_match(self):
        row=f.read_json(Path(__file__).parent/'recovery-binding.json')['build']
        data=dict(id=row['artifactId'],name=row['artifactName'],digest=row['artifactDigest'],expired=False,size_in_bytes=row['artifactBytes'],workflow_run=dict(id=row['runId'],head_sha=row['controlRevision'],head_branch='main'))
        f.verify_artifact_meta(row,data)
        for key,value in [('digest','sha256:'+'0'*64),('expired',True),('size_in_bytes',0),('id',True)]:
            changed=copy.deepcopy(data);changed[key]=value
            with self.assertRaises(g.RecoveryBlocked):f.verify_artifact_meta(row,changed)
    def test_inventory_rejects_symlinks(self):
        p=self.root/'tree';p.mkdir();(p/'good').write_bytes(b'a');self.assertEqual(f.inventory(p),{'good':g.sha(b'a')})
        (p/'link').symlink_to(p/'good')
        with self.assertRaises(g.RecoveryBlocked):f.inventory(p)
    def test_fixed_fresh_download_roots(self):
        roots={k:self.root/name for k,name in f.DOWNLOAD_NAMES.items()};f.verify_roots(str(self.root),roots,True)
        for root in roots.values():root.mkdir()
        f.verify_roots(str(self.root),roots,False)
        with self.assertRaises(g.RecoveryBlocked):f.verify_roots(str(self.root),roots,True)
    def test_workflow_has_only_same_serialization_permissions_and_no_provider_step(self):
        raw=(Path(__file__).parents[2]/f.WORKFLOW).read_text()
        self.assertIn('\nconcurrency:\n  group: '+f.CONCURRENCY+'\n  cancel-in-progress: false\n',raw)
        self.assertIn('actions: read',raw);self.assertIn('issues: write',raw)
        for token in ['CLOUDFLARE_','wrangler','setup-node','continue-on-error','workflow_dispatch']:self.assertNotIn(token,raw)
if __name__=='__main__':unittest.main()
