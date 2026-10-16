"""Offline incomplete-body/retention boundary tests; no real network is used."""
from http.client import IncompleteRead
import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import finalize_recovery as f,indexnow_recovery as g
from test_finalize_recovery import Response,Opener
from test_indexnow_recovery import SOURCE
class PartialResponseTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        self.contract=g.load_contract(SOURCE);self.payload=json.dumps(g._payload(self.contract)).encode()
    def run_failure(self,response):
        opener=Opener(response);h=f.BoundedHTTP('offline-fixture-token',set(),set(),opener=opener);h.contract=self.contract;h.evidence=self.root
        with self.assertRaises(g.RecoveryBlocked):h.call('POST',g.ENDPOINT,self.payload)
        self.assertEqual(len(opener.calls),1)
        with self.assertRaisesRegex(g.RecoveryBlocked,'caller_single_post_only'):h.call('POST',g.ENDPOINT,self.payload)
        self.assertEqual(len(opener.calls),1)
        return f.read_json(self.root/'response-failure-observation.json')
    def test_content_length_100_actual_7_is_partial_never_complete(self):
        obs=self.run_failure(Response(g.ENDPOINT,b'partial',422,[('content-type','text/plain'),('content-length','100')]))
        self.assertFalse(obs['responseBodyReadComplete']);self.assertEqual(obs['declaredContentLength'],100)
        self.assertEqual(obs['capturedPrefixBytes'],7);self.assertEqual(obs['capturedPrefixSha256'],g.sha(b'partial'))
        self.assertEqual((self.root/'response-body.failed-prefix.txt').read_bytes(),b'partial')
        self.assertFalse(obs['submissionOutcomeConfirmed']);self.assertTrue(obs['postBudgetSpent']);self.assertFalse(obs['retryAllowed'])
        self.assertFalse((self.root/'response-observation.json').exists())
    def test_incomplete_read_partial_bytes_are_preserved(self):
        class Incomplete(Response):
            def read(self,n):raise IncompleteRead(b'partial',93)
        obs=self.run_failure(Incomplete(g.ENDPOINT,b'',422,[('content-length','100')]))
        self.assertFalse(obs['responseBodyReadComplete']);self.assertEqual(obs['capturedPrefixBytes'],7)
        self.assertEqual((self.root/'response-body.failed-prefix.txt').read_bytes(),b'partial')
    def test_prior_chunks_and_exception_prefix_are_both_hashed(self):
        class Incomplete(Response):
            def read(self,n):
                if self.offset==0:self.offset=1;return b'first'
                raise IncompleteRead(b'second',89)
        obs=self.run_failure(Incomplete(g.ENDPOINT,b'',422,[('content-length','100')]))
        self.assertEqual(obs['capturedPrefixBytes'],11);self.assertEqual(obs['capturedPrefixSha256'],g.sha(b'firstsecond'))
    def test_incomplete_utf8_prefix_is_withheld_with_hash(self):
        obs=self.run_failure(Response(g.ENDPOINT,b'prefix\xe2',422,[('content-length','100')]))
        self.assertFalse(obs['rawPrefixRetained']);self.assertEqual(obs['capturedPrefixSha256'],g.sha(b'prefix\xe2'))
        self.assertFalse((self.root/'response-body.failed-prefix.txt').exists())
    def test_unsafe_prefix_is_withheld(self):
        obs=self.run_failure(Response(g.ENDPOINT,b'Bearer TOKEN',422,[('content-length','100')]))
        self.assertFalse(obs['rawPrefixRetained']);self.assertEqual(obs['capturedPrefixBytes'],12)
    def test_size_cap_keeps_bounded_observed_prefix_only(self):
        class Incomplete(Response):
            def read(self,n):raise IncompleteRead(b'x'*(g.MAX_RESPONSE+20),1)
        obs=self.run_failure(Incomplete(g.ENDPOINT,b'',422))
        self.assertEqual(obs['capturedPrefixBytes'],g.MAX_RESPONSE+1);self.assertEqual(obs['additionalExceptionBytesOmitted'],19)
        self.assertFalse(obs['responseBodyReadComplete']);self.assertFalse(obs['rawPrefixRetained'])
    def test_body_capture_failure_after_complete_read_does_not_claim_submission(self):
        (self.root/'response-body.txt').mkdir()
        obs=self.run_failure(Response(g.ENDPOINT,b'Invalid request',422,[('content-length','15')]))
        self.assertTrue(obs['responseBodyReadComplete']);self.assertFalse(obs['submissionOutcomeConfirmed'])
        self.assertEqual(obs['reason'],'response_capture_failed');self.assertEqual(obs['capturedPrefixSha256'],g.sha(b'Invalid request'))
    def test_complete_response_marks_body_complete_and_has_no_failure_file(self):
        o=Opener(Response(g.ENDPOINT,b'Invalid request',422,[('content-length','15')]))
        h=f.BoundedHTTP('offline-fixture-token',set(),set(),opener=o);h.contract=self.contract;h.evidence=self.root
        h.call('POST',g.ENDPOINT,self.payload);obs=f.read_json(self.root/'response-observation.json')
        self.assertTrue(obs['responseBodyReadComplete']);self.assertEqual(obs['rawBodyBytes'],15)
        self.assertFalse((self.root/'response-failure-observation.json').exists())
    def test_escaped_sensitive_json_is_withheld_without_transformation(self):
        for raw in [b'{"pass\\u0077ord":"abc123"}',b'{"\\u0074oken":"abc123"}',b'{"message":"invalid\\nrequest"}',b'password=abc123']:
            with self.subTest(raw=raw):self.assertIsNone(f.safe_raw_body(g.RawResponse(422,raw,[]),self.contract))
    def test_failed_response_capture_state_survives_evidence_write_failure(self):
        opener=Opener(Response(g.ENDPOINT,b'partial',422,[('content-length','100')]))
        h=f.BoundedHTTP('offline-fixture-token',set(),set(),opener=opener);h.contract=self.contract;h.evidence=self.root
        original=f.save
        def broken(path,value):
            if str(path).endswith('response-failure-observation.json'):raise OSError('offline storage failure')
            return original(path,value)
        with patch.object(f,'save',side_effect=broken):
            with self.assertRaises(g.RecoveryBlocked):h.call('POST',g.ENDPOINT,self.payload)
        self.assertEqual(h.request_evidence_state,'actual_request_data_retained')
        self.assertEqual(h.response_evidence_state,'failed_response_capture_unconfirmed')
        self.assertTrue(h.post_reserved);self.assertEqual(len(opener.calls),1)
    def test_unknown_nested_or_malformed_json_is_withheld(self):
        bodies=[b'{"api-key":"abc123"}',b'{"pwd":"abc123"}',b'{"unknown":"abc123"}',b'{"message":{"detail":"abc"}}',b'{"message":["abc"]}',b'["error"]',b'{"message":"truncated',b'{"message":"a","message":"b"}',b'{"status":1e309}',b'{"message":NaN}',b'prefix {"message":"a"}']
        for raw in bodies:
            with self.subTest(raw=raw):self.assertIsNone(f.safe_raw_body(g.RawResponse(422,raw,[]),self.contract))
    def test_plain_credential_labels_are_withheld(self):
        for raw in [b'api-key: abc123',b'API_KEY=abc123',b'api key abc123',b'pwd: abc123',b'passwd=abc123']:
            with self.subTest(raw=raw):self.assertIsNone(f.safe_raw_body(g.RawResponse(422,raw,[]),self.contract))
    def test_closed_scalar_diagnostics_preserve_exact_original_bytes(self):
        for raw in [b'{ "message" : "Invalid request", "code": 422 }\n',b'{"error":"invalid key","status":false,"detail":null}','{"message":"URL과 key 정보가 일치하지 않습니다"}'.encode(),b'Invalid request',b'']:
            with self.subTest(raw=raw):self.assertEqual(f.safe_raw_body(g.RawResponse(422,raw,[]),self.contract),raw)
    def test_partial_unknown_json_keeps_hash_without_raw_prefix(self):
        raw=b'{"api-key":"abc123"}'
        obs=self.run_failure(Response(g.ENDPOINT,raw,422,[('content-length','100')]))
        self.assertFalse(obs['rawPrefixRetained']);self.assertEqual(obs['capturedPrefixSha256'],g.sha(raw))
    def test_compatibility_and_unexpected_script_labels_are_withheld(self):
        for text in ['ａｐｉ－ｋｅｙ: abc123','ｐａｓｓｗｏｒｄ: abc123','pаsswоrd: abc123']:
            with self.subTest(text=text):self.assertIsNone(f.safe_raw_body(g.RawResponse(422,text.encode(),[]),self.contract))
if __name__=='__main__':unittest.main()
