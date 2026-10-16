"""Additional offline raw HTTP-header regression. No request is made."""
from email.message import Message
import unittest
import managed_robots as robots

class ExactRobotsHeaders(unittest.TestCase):
 def test_duplicate_content_type_even_equal_is_rejected(self):
  for second in ['text/plain','text/plain; charset=utf-8','text/html']:
   headers=Message();headers['Content-Type']='text/plain';headers['Content-Type']=second
   with self.subTest(second=second),self.assertRaisesRegex(ValueError,'robots_content_type_mismatch'):robots.verify_headers(headers)
 def test_utf16_parameters_and_whitespace_smuggling_rejected(self):
  values=['text/plain; charset=utf-16','text/plain; charset="utf-16"','text/plain; charset=utf-8; charset=utf-8','text/plain; boundary=a','text/plain; charset=utf-8, text/html','text/plain\r\n','text/plain\x00','text/plain; charset=utf-8; foo=bar']
  for value in values:
   with self.subTest(value=value),self.assertRaisesRegex(ValueError,'robots_content_type_mismatch'):robots.verify_headers({'content-type':value})
 def test_only_supported_plain_utf8_header_shapes_accept(self):
  for value in ['text/plain','text/plain; charset=utf-8','text/plain; charset="utf-8"','TEXT/PLAIN; CHARSET=UTF-8']:
   robots.verify_headers({'content-type':value})
if __name__=='__main__':unittest.main(verbosity=2)

