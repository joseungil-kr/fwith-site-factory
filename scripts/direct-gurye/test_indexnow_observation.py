"""Synthetic transport only. No live submission or server response is claimed."""
from pathlib import Path
from email.message import Message
import contextlib,hashlib,json,os,sys,tempfile,unittest
from unittest.mock import Mock,patch
import indexnow_observation as o
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'site-factory/engine'))
import indexnow_finalize as n

class Response:
 def __init__(self,body=b'',status=200,headers=None):self.body=body;self.code=status;self.headers=Message();[self.headers.__setitem__(k,v)for k,v in (headers or{}).items()]
 def read(self,limit):return self.body[:limit]
 def __enter__(self):return self
 def __exit__(self,*args):return False
class Observations(unittest.TestCase):
 def setUp(self):
  self.stack=contextlib.ExitStack();self.addCleanup(self.stack.close);self.tmp=Path(self.stack.enter_context(tempfile.TemporaryDirectory()));self.stack.enter_context(patch.object(o,'ROOT',self.tmp/'observations'))
 def perform(self,body=b'',status=200,headers=None):
  opener=Mock();opener.open.return_value=Response(body,status,headers)
  with patch.object(o,'build_opener',return_value=opener)as build:result=o.request('POST',n.ENDPOINT,dict(o.EXPECTED))
  build.assert_called_once_with(n.NoRedirect);opener.open.assert_called_once();return result,opener
 def record(self,name='response.json',attempt=1):return json.loads((o.ROOT/f'attempt-{attempt:03d}'/name).read_text())
 def test_exact_request_data_matches_pinned_helper_transport(self):
  payload=dict(o.EXPECTED);original=Mock();original.open.return_value=Response(b'Success')
  with patch.object(n,'build_opener',return_value=original):n.request('POST',n.ENDPOINT,payload)
  result,new=self.perform(b'Success');a=original.open.call_args.args[0];b=new.open.call_args.args[0]
  self.assertEqual((a.full_url,a.method,a.data,dict(a.header_items())),(b.full_url,b.method,b.data,dict(b.header_items())))
  self.assertEqual(original.open.call_args.kwargs,new.open.call_args.kwargs);self.assertEqual(new.open.call_args.kwargs,{'timeout':40})
  self.assertEqual((o.ROOT/'attempt-001/request-body.json').read_bytes(),b.data)
  r=self.record('request.json');self.assertEqual(r['requestSHA256'],hashlib.sha256(b.data).hexdigest());self.assertEqual(r['requestBytes'],len(b.data));self.assertFalse(r['networkPacketCapture'])
 def test_http_error_body_is_observed_without_exception_reason_leak(self):
  from urllib.error import HTTPError
  from io import BytesIO
  raw=b'{"message":"Unprocessable Entity"}';headers=Message();headers['Authorization']='PRIVATE_SECRET';error=HTTPError(n.ENDPOINT,422,'PRIVATE_SECRET',headers,BytesIO(raw));opener=Mock();opener.open.side_effect=error
  with patch.object(o,'build_opener',return_value=opener):result=o.request('POST',n.ENDPOINT,dict(o.EXPECTED))
  self.assertEqual(result[:2],(422,raw.decode()));self.assertEqual(self.record()['httpStatus'],422);opener.open.assert_called_once();self.assertNotIn('PRIVATE_SECRET',''.join(p.read_text()for p in o.ROOT.rglob('*')if p.is_file()))
 def test_real_stdlib_short_response_never_claims_complete_or_full_hash(self):
  from http.client import HTTPResponse
  from io import BytesIO
  class FakeSocket:
   def makefile(self,*args):return BytesIO(b'HTTP/1.1 200 OK\r\nContent-Length: 100\r\n\r\nSuccess')
  response=HTTPResponse(FakeSocket());response.begin();opener=Mock();opener.open.return_value=response
  with patch.object(o,'build_opener',return_value=opener),self.assertRaisesRegex(ValueError,'incomplete_http_response'):o.request('POST',n.ENDPOINT,dict(o.EXPECTED))
  r=self.record();self.assertFalse(r['responseBodyComplete']);self.assertIsNone(r['responseSHA256']);self.assertEqual(r['readBytesSHA256'],hashlib.sha256(b'Success').hexdigest());self.assertEqual(r['declaredResponseBytes'],100);self.assertEqual(r['responseBytesRead'],7);self.assertEqual(r['withheldReason'],'declared_content_length_mismatch');self.assertFalse(r['rawRetained']);self.assertFalse((o.ROOT/'attempt-001/response-body.bin').exists());opener.open.assert_called_once()
 def test_real_stdlib_complete_length_response_is_retained(self):
  from http.client import HTTPResponse
  from io import BytesIO
  class FakeSocket:
   def makefile(self,*args):return BytesIO(b'HTTP/1.1 200 OK\r\nContent-Length: 7\r\n\r\nSuccess')
  response=HTTPResponse(FakeSocket());response.begin();opener=Mock();opener.open.return_value=response
  with patch.object(o,'build_opener',return_value=opener):result=o.request('POST',n.ENDPOINT,dict(o.EXPECTED))
  self.assertEqual(result[:2],(200,'Success'));r=self.record();self.assertTrue(r['responseBodyComplete']);self.assertTrue(r['rawRetained']);self.assertEqual(r['declaredResponseBytes'],7);self.assertEqual(r['responseSHA256'],hashlib.sha256(b'Success').hexdigest())
 def test_invalid_duplicate_conflicting_lengths_are_not_full_evidence(self):
  for headers in [{'content-length':'7, 7'},{'content-length':'PRIVATE_SECRET'},{'content-length':'8'},{'content-length':'7','transfer-encoding':'chunked'},{'transfer-encoding':'PRIVATE_SECRET'}]:
   with self.subTest(headers=headers):self.assertIsNotNone(o.framing(headers,7)['framingError'])
  opener=Mock();opener.open.return_value=Response(b'Success',422,{'Content-Length':'PRIVATE_SECRET'})
  with patch.object(o,'build_opener',return_value=opener),self.assertRaisesRegex(ValueError,'incomplete_http_response'):o.request('POST',n.ENDPOINT,dict(o.EXPECTED))
  self.assertIsNone(self.record()['declaredResponseBytes']);self.assertNotIn('PRIVATE_SECRET',''.join(p.read_text()for p in o.ROOT.rglob('*')if p.is_file()))
 def test_real_stdlib_truncated_chunked_partial_bytes_are_labeled(self):
  from http.client import HTTPResponse
  from io import BytesIO
  class FakeSocket:
   def makefile(self,*args):return BytesIO(b'HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\n\r\n7\r\nSuccess\r\n')
  response=HTTPResponse(FakeSocket());response.begin();opener=Mock();opener.open.return_value=response
  with patch.object(o,'build_opener',return_value=opener),self.assertRaisesRegex(ValueError,'incomplete_http_response'):o.request('POST',n.ENDPOINT,dict(o.EXPECTED))
  r=self.record();self.assertEqual(r['httpStatus'],200);self.assertFalse(r['responseBodyComplete']);self.assertIsNone(r['responseSHA256']);self.assertEqual(r['readBytesSHA256'],hashlib.sha256(b'Success').hexdigest());self.assertEqual(r['responseBytesRead'],7);self.assertEqual(r['readError'],'incomplete_http_read');self.assertFalse(r['rawRetained']);opener.open.assert_called_once()
 def test_real_stdlib_complete_chunked_body_is_retained(self):
  from http.client import HTTPResponse
  from io import BytesIO
  class FakeSocket:
   def makefile(self,*args):return BytesIO(b'HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\n\r\n7\r\nSuccess\r\n0\r\n\r\n')
  response=HTTPResponse(FakeSocket());response.begin();opener=Mock();opener.open.return_value=response
  with patch.object(o,'build_opener',return_value=opener):result=o.request('POST',n.ENDPOINT,dict(o.EXPECTED))
  self.assertEqual(result[:2],(200,'Success'));r=self.record();self.assertTrue(r['responseBodyComplete']);self.assertIsNone(r['readError']);self.assertTrue(r['rawRetained'])
 def test_exact_endpoint_host_same_proof_and_one_url_are_required(self):
  mutations=[('POST','https://foreign.invalid',o.EXPECTED),('GET',n.ENDPOINT,o.EXPECTED),('POST',n.ENDPOINT,{**o.EXPECTED,'key':'newkey'}),('POST',n.ENDPOINT,{**o.EXPECTED,'host':'gokseong.fwith.kr'}),('POST',n.ENDPOINT,{**o.EXPECTED,'urlList':['https://gurye.fwith.kr/other/']}),('POST',n.ENDPOINT,{**o.EXPECTED,'urlList':o.EXPECTED['urlList']*2}),('POST',n.ENDPOINT,{**o.EXPECTED,'extra':'secret'})]
  for args in mutations:
   with self.subTest(args=args[:2]),patch.object(o,'build_opener')as network,self.assertRaises(ValueError):o.request(*args)
   network.assert_not_called();self.assertFalse(o.ROOT.exists())
 def test_safe_public_response_exact_bytes_status_utf8_and_time(self):
  body='{"status":422,"message":"URL이 key 정보와 일치하지 않습니다."}\n'.encode();result,_=self.perform(body,422)
  self.assertEqual(result[:2],(422,body.decode()));r=self.record();self.assertTrue(r['rawRetained']);self.assertTrue(r['responseUTF8']);self.assertEqual(r['responseBytesRead'],len(body));self.assertEqual(r['responseSHA256'],hashlib.sha256(body).hexdigest());self.assertEqual((o.ROOT/'attempt-001/response-body.bin').read_bytes(),body);self.assertLessEqual(r['transportInvokedAtUTC'],r['observedAtUTC'])
 def test_success_empty_and_known_diagnostics_are_safe(self):
  for raw in [b'',b'Success\n',b'Accepted',b'{"error":{"code":"InvalidKey","message":"Key not found"}}']:
   with self.subTest(raw=raw):self.assertTrue(o.classify(raw)['retainRaw'])
 def test_unknown_or_sensitive_strings_never_enter_raw_artifact(self):
  samples=[b'{"message":"person@example.com"}',b'{"password":"PRIVATE_SECRET"}',b'{"message":"PRIVATE_SECRET","message":"Success"}',b'<html>PRIVATE_SECRET</html>',b'{"message":"Success","data":"PRIVATE_SECRET"}',b'{"message":["Success","PRIVATE_SECRET"]}',b'PRIVATE_SECRET',b'{"code":123456789}',b'{"message":true}']
  for raw in samples:
   with self.subTest(raw=raw):self.assertFalse(o.classify(raw)['retainRaw'])
  self.perform(samples[0],422);r=self.record();self.assertFalse(r['rawRetained']);self.assertEqual(r['responseSHA256'],hashlib.sha256(samples[0]).hexdigest());self.assertFalse((o.ROOT/'attempt-001/response-body.bin').exists());self.assertNotIn('person@example.com',''.join(p.read_text()for p in o.ROOT.rglob('*')if p.is_file()))
 def test_response_headers_and_environment_secrets_are_not_saved(self):
  with patch.dict(os.environ,{'CLOUDFLARE_API_TOKEN':'PRIVATE_SECRET','GH_TOKEN':'PRIVATE_SECRET'}):result,opener=self.perform(b'Success',200,{'Set-Cookie':'PRIVATE_SECRET','Authorization':'Bearer PRIVATE_SECRET','Content-Type':'PRIVATE_SECRET'})
  self.assertIn('authorization',result[2]);self.assertNotIn('PRIVATE_SECRET',''.join(p.read_text()for p in o.ROOT.rglob('*')if p.is_file()));req=opener.open.call_args.args[0];self.assertFalse(req.has_header('Authorization'));self.assertFalse(req.has_header('Cookie'))
 def test_non_utf8_is_hashed_withheld_and_preserves_unknown_failure(self):
  raw=b'\xff\xfePRIVATE_SECRET';opener=Mock();opener.open.return_value=Response(raw,422)
  with patch.object(o,'build_opener',return_value=opener),self.assertRaises(UnicodeDecodeError):o.request('POST',n.ENDPOINT,dict(o.EXPECTED))
  r=self.record();self.assertFalse(r['responseUTF8']);self.assertFalse(r['rawRetained']);self.assertEqual(r['responseSHA256'],hashlib.sha256(raw).hexdigest());self.assertEqual(self.record('failure.json')['errorType'],'UnicodeDecodeError');opener.open.assert_called_once()
 def test_response_capture_limit_never_writes_unreviewed_prefix(self):
  raw=b' '*5000+b'Success';self.perform(raw,200);r=self.record();self.assertFalse(r['rawRetained']);self.assertEqual(r['responseBytesRead'],len(raw));self.assertTrue(r['responseBodyComplete']);self.assertEqual(r['withheldReason'],'body_over_capture_limit_withheld')
 def test_transport_size_limit_is_preserved_and_partial_hash_is_labeled(self):
  opener=Mock();opener.open.return_value=Response(b'X'*100,200)
  with patch.object(n,'MAX_BYTES',64),patch.object(o,'build_opener',return_value=opener),self.assertRaisesRegex(ValueError,'oversized_http_response'):o.request('POST',n.ENDPOINT,dict(o.EXPECTED))
  r=self.record();self.assertFalse(r['responseBodyComplete']);self.assertEqual(r['responseBytesRead'],65);self.assertIsNone(r['responseSHA256']);self.assertEqual(r['readBytesSHA256'],hashlib.sha256(b'X'*65).hexdigest());self.assertFalse(r['rawRetained'])
 def test_timeout_one_call_no_retry_or_secret_exception_text(self):
  opener=Mock();opener.open.side_effect=TimeoutError('PRIVATE_SECRET')
  with patch.object(o,'build_opener',return_value=opener),self.assertRaises(TimeoutError):o.request('POST',n.ENDPOINT,dict(o.EXPECTED))
  opener.open.assert_called_once();r=self.record('failure.json');self.assertEqual(r['errorType'],'TimeoutError');self.assertFalse(r['automaticRetryAdded']);self.assertNotIn('PRIVATE_SECRET',''.join(p.read_text()for p in o.ROOT.rglob('*')if p.is_file()))
 def test_before_post_observation_failure_prevents_network(self):
  with patch.object(o,'save_new',side_effect=OSError('write fail')),patch.object(o,'build_opener')as network,self.assertRaises(OSError):o.request('POST',n.ENDPOINT,dict(o.EXPECTED))
  network.assert_not_called()
 def test_existing_helper_marks_failed_after_post_observation_unknown(self):
  real=o.save_json
  def save(path,value):
   if path.name=='response.json':raise OSError('write fail')
   return real(path,value)
  journal=Mock();journal.records.return_value=[];site=dict(siteKey='gurye-flower-direct',siteUrl='https://gurye.fwith.kr',productionEnabled=True,launchMode='live',indexnowKey=o.PUBLIC_KEY);opener=Mock();opener.open.return_value=Response(b'Success')
  with patch.object(n,'verify_public',return_value=o.EXPECTED['urlList']),patch.object(o,'save_json',side_effect=save),patch.object(o,'build_opener',return_value=opener),self.assertRaisesRegex(ValueError,'submission_outcome_uncertain'):n.finalize(site,'a'*40,'release',journal,transport=o.request)
  opener.open.assert_called_once();self.assertEqual(journal.write.call_args_list[-1].args[0]['state'],'unknown')
 def test_existing_helper_still_refuses_unknown_prior_journal(self):
  urls=o.EXPECTED['urlList'];site=dict(siteKey='gurye-flower-direct',siteUrl='https://gurye.fwith.kr',productionEnabled=True,launchMode='live',indexnowKey=o.PUBLIC_KEY);identity=dict(siteKey=site['siteKey'],origin=site['siteUrl'],revision='a'*40,endpoint=n.ENDPOINT,urlSetSha256=n.digest(urls),urlCount=1);fingerprint=n.digest({**identity,'keySha256':n.digest(o.PUBLIC_KEY)});journal=Mock();journal.records.return_value=[dict(fingerprint=fingerprint,state='unknown')]
  with patch.object(n,'verify_public',return_value=urls),patch.object(o,'build_opener')as network,self.assertRaisesRegex(ValueError,'prior_submission_outcome_uncertain'):n.finalize(site,'a'*40,'release',journal,transport=o.request)
  network.assert_not_called();self.assertFalse(o.ROOT.exists())
 def test_original_retry_policy_is_external_and_at_most_three_folders(self):
  for i in range(3):self.perform(b'Too Many Requests',429)
  with patch.object(o,'build_opener')as network,self.assertRaisesRegex(ValueError,'observation_attempt_layout'):o.request('POST',n.ENDPOINT,dict(o.EXPECTED))
  network.assert_not_called();self.assertEqual(len(list(o.ROOT.iterdir())),3)
 def test_symlink_or_unreviewed_output_layout_prevents_network(self):
  outside=self.tmp/'outside';outside.mkdir();o.ROOT.symlink_to(outside,target_is_directory=True)
  with patch.object(o,'build_opener')as network,self.assertRaisesRegex(ValueError,'observation_symlink_forbidden'):o.request('POST',n.ENDPOINT,dict(o.EXPECTED))
  network.assert_not_called();o.ROOT.unlink();o.ROOT.mkdir();(o.ROOT/'secret').write_text('x')
  with patch.object(o,'build_opener')as network,self.assertRaisesRegex(ValueError,'observation_attempt_layout'):o.request('POST',n.ENDPOINT,dict(o.EXPECTED))
  network.assert_not_called()
 def test_evidence_file_overwrite_is_forbidden(self):
  p=self.tmp/'x';p.write_bytes(b'original')
  with self.assertRaisesRegex(ValueError,'observation_output_exists'):o.save_new(p,b'replacement')
  self.assertEqual(p.read_bytes(),b'original')
if __name__=='__main__':unittest.main()
