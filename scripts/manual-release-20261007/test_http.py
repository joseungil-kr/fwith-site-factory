import unittest
from verify_http import verify_headers,Meta,directives
class HTTPTests(unittest.TestCase):
 def test_unexpected_provider_noindex(self):
  with self.assertRaisesRegex(AssertionError,'Unexpected provider robots'):verify_headers('/',{'x-robots-tag':'noindex'},[])
 def test_approved_noindex_header(self):verify_headers('/',{'x-robots-tag':'noindex,nofollow'},[('/*',{'x-robots-tag':'noindex, nofollow'})])
 def test_body_word_not_meta(self):
  m=Meta();m.feed('<p>The word noindex is not a directive</p>');self.assertEqual(m.robots,[])
if __name__=='__main__':unittest.main()
