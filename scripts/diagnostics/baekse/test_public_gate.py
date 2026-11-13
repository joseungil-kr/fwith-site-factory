import io
import tempfile
import pathlib
import unittest
import urllib.error
from email.message import Message
from public_gate import ASSETS, BASE, NoRedirect, gate

class Response(io.BytesIO):
    def __init__(self,status=200,body=b'fixture',headers=None):
        super().__init__(body);self.status=status
        self.headers=headers or {'X-Robots-Tag':'noindex','Cache-Control':'no-store'}

class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=pathlib.Path(self.tmp.name)
        for name in ASSETS.values():
            p=self.root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'fixture')
        self.calls=[];self.logs=[]
    def tearDown(self):self.tmp.cleanup()
    def op(self,url,timeout):
        self.calls.append(url)
        if url.endswith('/api/session'):raise urllib.error.HTTPError(url,401,'',{},io.BytesIO(b'PRIVATE'))
        return Response()
    def test_baseline_pass(self):
        self.assertTrue(gate('baseline',self.root,self.op,self.logs.append));self.assertEqual(len(self.calls),5)
    def test_candidate_pass(self):self.assertTrue(gate('candidate',self.root,self.op,self.logs.append))
    def test_403_stops_no_retry_or_body(self):
        class NoRead(io.BytesIO):
            def read(self,*a):raise AssertionError('must not read')
        def op(url,timeout):
            self.calls.append(url);raise urllib.error.HTTPError(url,403,'PRIVATE',{'Set-Cookie':'PRIVATE'},NoRead(b'PRIVATE'))
        self.assertFalse(gate('baseline',self.root,op,self.logs.append));self.assertEqual(len(self.calls),1)
        self.assertNotIn('PRIVATE',''.join(self.logs))
    def test_hash_mismatch_stops(self):self.assertFalse(gate('candidate',self.root,lambda *a,**k:Response(body=b'wrong'),self.logs.append))
    def test_missing_header_stops(self):self.assertFalse(gate('candidate',self.root,lambda *a,**k:Response(headers={'Cache-Control':'no-store'}),self.logs.append))
    def test_anonymous_200_rejected(self):
        self.assertFalse(gate('baseline',self.root,lambda *a,**k:Response(),self.logs.append))
    def test_exception_secret_omitted(self):
        def op(*a,**k):raise ValueError('PRIVATE')
        self.assertFalse(gate('baseline',self.root,op,self.logs.append));self.assertNotIn('PRIVATE',''.join(self.logs))
    def test_redirect_blocked(self):self.assertIsNone(NoRedirect().redirect_request(None,None,302,'',{},'https://elsewhere'))

if __name__=='__main__':unittest.main()
