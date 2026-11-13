import io
import json
import unittest
import urllib.error
from email.message import Message
from smoke_diagnostic import BASE, PATHS, NoRedirect, observe

def headers():
    m = Message()
    for k,v in [('Server','cloudflare'),('CF-Ray','synthetic-ray'),('Set-Cookie','SECRET_COOKIE'),('Authorization','SECRET_AUTH')]:
        m[k] = v
    return m

class Response(io.BytesIO):
    status = 200
    def __init__(self, data=b'public test'):
        super().__init__(data)
        self.headers = headers()

class Tests(unittest.TestCase):
    def test_four_public_paths_and_phase(self):
        calls, output = [], []
        def op(url, timeout):
            calls.append(url)
            return Response()
        result=observe('baseline',op,output.append)
        self.assertTrue(result['http_observation_passed'])
        self.assertEqual(calls,[BASE+p for p in PATHS])
        self.assertTrue(all(json.loads(s)['phase']=='baseline' for s in output))
        self.assertNotIn('SECRET', ''.join(output))

    def test_forbidden_second_path_stops_without_retry_or_error_body(self):
        calls, output = [], []
        class Unreadable(io.BytesIO):
            def read(self,*args):
                raise AssertionError('error body must not be read')
        def op(url,timeout):
            calls.append(url)
            if len(calls)==2:
                raise urllib.error.HTTPError(url,403,'SECRET_MESSAGE',headers(),Unreadable(b'SECRET_BODY'))
            return Response()
        result=observe('candidate',op,output.append)
        self.assertFalse(result['http_observation_passed'])
        self.assertEqual(calls,[BASE+'/',BASE+'/app.js'])
        self.assertEqual(result['results'][-1]['path'],'/app.js')
        self.assertEqual(result['results'][-1]['status'],403)
        self.assertNotIn('SECRET',''.join(output))

    def test_exception_details_not_leaked(self):
        output=[]
        def op(*args,**kw): raise ValueError('https://secret.test/?token=SECRET')
        result=observe('baseline',op,output.append)
        self.assertFalse(result['http_observation_passed'])
        self.assertNotIn('SECRET',''.join(output))
        self.assertEqual(len(result['results']),1)

    def test_phase_is_required(self):
        with self.assertRaises(ValueError): observe('pass',lambda *a,**k:Response())

    def test_redirect_not_followed(self):
        self.assertIsNone(NoRedirect().redirect_request(None,None,302,'',{},'https://elsewhere/?secret=1'))

    def test_oversized_body_fails(self):
        r=observe('baseline',lambda *a,**k:Response(b'x'*(2*1024*1024+1)),lambda s:None)
        self.assertFalse(r['http_observation_passed'])
        self.assertEqual(len(r['results']),1)

if __name__=='__main__':unittest.main()
