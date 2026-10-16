"""Narrow Gokseong same-key/source and diagnostic boundary regression tests."""
import copy, json, tempfile, unittest
from pathlib import Path
import indexnow_recovery as g
from test_indexnow_recovery import Fixture, HELPER, SOURCE

class SameProofTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.f=Fixture(Path(self.temp.name))
    def test_same_key_and_fingerprint(self):
        c=self.f.contract
        self.assertEqual(c.active_key,c.retained_key)
        self.assertEqual(g._fingerprint(c,self.f.binding.source_revision),g.CHAIN['originalFingerprint'])
        self.assertEqual(g.sha(json.dumps(g._payload(c)).encode()),'247e3f4628205514f3c1faf995ad9bd5fbf2f5f71629deac0993c3f1261ce719')
    def test_original_whitespace_and_timestamp_edits_block(self):
        for field,value in [('body',self.f.comments[0]['body']+' '),('created_at','2026-10-16T16:00:52Z'),('updated_at','2026-10-16T16:01:00Z')]:
            old=self.f.comments[0][field];self.f.comments[0][field]=value
            with self.assertRaisesRegex(g.RecoveryBlocked,'original_receipt_bytes_or_time_changed'): self.f.run()
            self.f.comments[0][field]=old
            self.assertEqual(self.f.posts,[])
    def test_different_proof_and_symlinks_block(self):
        root=Path(self.temp.name)/'proof';(root/'dist').mkdir(parents=True)
        p=root/'dist/049d6c691d2c4cb824d23f82e9883ce4.txt';p.write_bytes(b'f'*32+b'\n')
        with self.assertRaisesRegex(g.RecoveryBlocked,'proof_bytes_mismatch'):g.load_contract(root)
        p.unlink();p.symlink_to(SOURCE/'dist'/p.name)
        with self.assertRaisesRegex(g.RecoveryBlocked,'proof_regular_file_required'):g.load_contract(root)
    def test_shared_helper_mutation_blocks_before_callbacks(self):
        helper=Path(self.temp.name)/'helper.py';helper.write_bytes(HELPER.read_bytes()+b'\n')
        with self.assertRaises(g.RecoveryBlocked):self.f.adapter(helper_path=helper)
        self.assertEqual(self.f.calls,[])
    def test_same_fingerprint_attempt_two_is_preserved_and_never_reposted(self):
        result=self.f.run();self.assertEqual(result['fingerprint'],g.CHAIN['originalFingerprint'])
        self.assertEqual([x['attempt'] for x in self.f.writes],[2,2])
        self.f.calls.clear();result=self.f.run()
        self.assertEqual(result['state'],'already_received');self.assertEqual(self.f.posts,[])
    def test_repeat_server_timing_is_only_allowed_duplicate(self):
        original=self.f.transport
        def callback(method,url,payload):
            r=original(method,url,payload)
            if method=='GET':return g.RawResponse(r.status,r.body,r.headers+[('server-timing','a'),('server-timing','b')])
            return r
        self.assertEqual(self.f.run(transport=callback)['state'],'received')
    def test_duplicate_policy_header_blocks_prepost(self):
        original=self.f.transport
        def callback(method,url,payload):
            r=original(method,url,payload)
            return g.RawResponse(r.status,r.body,r.headers+[('content-type','text/plain')]) if method=='GET' else r
        with self.assertRaisesRegex(g.RecoveryBlocked,'ambiguous_public_probe_headers'):self.f.run(transport=callback)
        self.assertEqual(self.f.posts,[])
    def test_malformed_telemetry_header_blocks_prepost(self):
        original=self.f.transport
        def callback(method,url,payload):
            r=original(method,url,payload)
            return g.RawResponse(r.status,r.body,r.headers+[('server-timing','a\nb')]) if method=='GET' else r
        with self.assertRaisesRegex(g.RecoveryBlocked,'invalid_public_probe_header_value'):self.f.run(transport=callback)
        self.assertEqual(self.f.posts,[])
if __name__=='__main__':unittest.main()
