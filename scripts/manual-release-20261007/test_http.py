import unittest
from types import SimpleNamespace
from urllib.error import HTTPError
from verify_http import request_response,assert_response_status,CLIENT_IDENTITIES
from verify_http import verify_headers,Meta,directives
class HTTPTests(unittest.TestCase):
 def test_unexpected_provider_noindex(self):
  with self.assertRaisesRegex(AssertionError,'Unexpected provider robots'):verify_headers('/',{'x-robots-tag':'noindex'},[])
 def test_approved_noindex_header(self):verify_headers('/',{'x-robots-tag':'noindex,nofollow'},[('/*',{'x-robots-tag':'noindex, nofollow'})])
 def test_body_word_not_meta(self):
  m=Meta();m.feed('<p>The word noindex is not a directive</p>');self.assertEqual(m.robots,[])
 def test_existing_application_identity_from_first_request(self):
  for phase,identity in [('preview','SiteFactory-StagingQA/3.0'),('production','SiteFactory-LiveQA/3.0')]:
   calls=[]
   def opener(request,timeout):
    calls.append(request);self.assertEqual(request.get_header('User-agent'),identity);self.assertEqual(request.get_header('Cache-control'),'no-cache');self.assertEqual(timeout,30)
    return SimpleNamespace(status=200,url=request.full_url)
   response=request_response('https://qa.example.test/',phase,opener);self.assertEqual(len(calls),1);assert_response_status(response,'https://qa.example.test/','/',200)
 def test_unknown_phase_cannot_select_an_unreviewed_identity(self):
  with self.assertRaisesRegex(AssertionError,'Unsupported'):request_response('https://qa.example.test/','anything',lambda *a: self.fail('No request allowed'))
 def test_access_denials_do_not_retry_or_rotate(self):
  for phase in CLIENT_IDENTITIES:
   for status in [401,403,429]:
    calls=[]
    def opener(request,timeout):
     calls.append(request);raise HTTPError(request.full_url,status,'denied',{},None)
    response=request_response('https://qa.example.test/',phase,opener)
    with self.assertRaisesRegex(AssertionError,'denied'):assert_response_status(response,'https://qa.example.test/','/',200)
    self.assertEqual(len(calls),1);self.assertEqual(calls[0].get_header('User-agent'),CLIENT_IDENTITIES[phase])
 def test_wrong_status_and_redirect_still_fail(self):
  for status,url in [(404,'https://qa.example.test/'),(200,'https://other.example.test/')]:
   with self.assertRaisesRegex(AssertionError,'status/redirect'):assert_response_status(SimpleNamespace(status=status,url=url),'https://qa.example.test/','/',200)
 def test_expected_exact_404_is_preserved(self):assert_response_status(SimpleNamespace(status=404,url='https://qa.example.test/missing'),'https://qa.example.test/missing','/missing',404)
if __name__=='__main__':unittest.main()

