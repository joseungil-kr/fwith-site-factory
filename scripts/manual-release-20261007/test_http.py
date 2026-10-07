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


# Bounded 367-byte public provider insertion, captured from existing public HTML
# and independently pinned in the existing M2 engine matcher. These public script
# attributes are test data, never a credential or runtime configuration. Do not
# log fixture bytes. All HTML artifacts below are synthetic and offline-only.
import contextlib,hashlib,io,json,tempfile
from email.message import Message
from pathlib import Path
from unittest.mock import patch
import verify_http as verifier

PINNED_PUBLIC_BEACON = b'<script type="module" src="https://static.cloudflareinsights.com/beacon.min.js/v31edd6df95cf4e85bb4c19e7a9bdbcba1788362987495" integrity="sha512-iIg7k2xntmwu6/uSb5tpc/hySgZc4eoL31yB29W6tJFo2akwjPWcEqnCEdJvGexCL0KEQwVYv5BlowfhVz26hg==" data-cf-beacon=\'{"version":"2024.11.0","token":"0e03c93ae1fd4f719264f966b161d3dc","r":1,"spa":2}\' crossorigin="anonymous"></script>\n'

class BeaconFixture(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.beacon=PINNED_PUBLIC_BEACON
  assert len(cls.beacon)==367,'Public fixture size mismatch'
  assert hashlib.sha256(cls.beacon).hexdigest()==verifier.GOYANG_CF_BEACON_SHA256,'Public fixture digest mismatch'
  cls.artifact=(b'<html><head><link rel="canonical" href="https://qa.example.test/">'
    b'<meta name="site-factory-revision" content="revision-fixture">'
    b'<script type="application/ld+json">{"@type":"WebPage","name":"Original"}</script>'
    b'</head><body><h1>Original</h1><a href="/contact/">Contact</a></body></html>')
  cls.baselines=[]
  for artifact in [cls.artifact,cls.artifact.replace(b'<h1>Original',b'<h1>Second synthetic fixture',1)]:
   cls.baselines.append((cls.inserted(artifact),artifact))
 @classmethod
 def inserted(cls,artifact=None,beacon=None):
  artifact=cls.artifact if artifact is None else artifact
  return artifact[:-14]+(cls.beacon if beacon is None else beacon)+b'</body></html>'
 def rejected(self,data,artifact=None,phase='production',is_html=True):
  self.assertIsNone(verifier.artifact_comparison(data,self.artifact if artifact is None else artifact,phase,is_html))

class ArtifactTests(BeaconFixture):
 def test_pinned_public_beacon_on_two_synthetic_artifacts(self):
  for live,artifact in self.baselines:
   receipt=verifier.artifact_comparison(live,artifact,'production',True)
   self.assertIsNotNone(receipt);self.assertEqual(receipt['matchMode'],'pinned-managed-beacon')
   self.assertNotEqual(receipt['rawBodySha256'],receipt['expectedArtifactSha256'])
   self.assertEqual(receipt['rawBodySha256'],hashlib.sha256(live).hexdigest())
   self.assertEqual(receipt['expectedArtifactSha256'],hashlib.sha256(artifact).hexdigest())
   self.assertEqual(receipt['managedBeaconCount'],1)
   self.assertEqual(receipt['managedBeaconSha256'],verifier.GOYANG_CF_BEACON_SHA256)
 def test_exact_bytes_remain_valid_in_every_phase_and_artifact_type(self):
  for phase in ['preview','production']:
   for is_html in [True,False]:
    receipt=verifier.artifact_comparison(self.artifact,self.artifact,phase,is_html)
    self.assertEqual(receipt['matchMode'],'exact');self.assertEqual(receipt['managedBeaconCount'],0)
    self.assertIsNone(receipt['managedBeaconSha256'])
    self.assertEqual(receipt['rawBodySha256'],receipt['expectedArtifactSha256'])
 def test_actual_pinned_insert_matches_synthetic_html(self):
  self.assertIsNotNone(verifier.artifact_comparison(self.inserted(),self.artifact,'production',True))
 def test_preview_never_allows_beacon(self):self.rejected(self.inserted(),phase='preview')
 def test_non_html_never_allows_beacon(self):self.rejected(self.inserted(),is_html=False)
 def test_wrong_beacon_version(self):
  self.rejected(self.inserted(beacon=self.beacon.replace(verifier.GOYANG_CF_BEACON_SRC,verifier.GOYANG_CF_BEACON_SRC+b'0',1)))
 def test_wrong_digest_with_same_start_and_end(self):
  self.rejected(self.inserted(beacon=self.beacon[:-10]+b' '+self.beacon[-10:]))
 def test_changed_or_added_attributes(self):
  for beacon in [self.beacon.replace(b'type="module"',b'type="text/javascript"',1),
                 self.beacon.replace(b'<script ',b'<script async ',1),
                 self.beacon.replace(b' src=',b' data-src=',1)]:self.rejected(self.inserted(beacon=beacon))
 def test_double_beacon(self):self.rejected(self.inserted(beacon=self.beacon+self.beacon))
 def test_additional_unpinned_script(self):
  self.rejected(self.inserted(beacon=self.beacon+b'<script>window.changed=true</script>\n'))
 def test_customer_body_canonical_schema_and_cta_changes(self):
  for before,after in [(b'<h1>Original',b'<h1>Changed'),(b'https://qa.example.test/',b'https://other.example.test/'),
                       (b'"name":"Original"',b'"name":"Changed"'),(b'href="/contact/"',b'href="/different/"')]:
   self.rejected(self.inserted().replace(before,after,1))
 def test_customer_whitespace_change(self):self.rejected(self.inserted().replace(b'</head>',b' </head>',1))
 def test_wrong_insertion_position(self):self.rejected(self.artifact.replace(b'</head>',self.beacon+b'</head>',1))
 def test_trailing_bytes_or_wrong_closing(self):
  self.rejected(self.inserted()+b'\n');self.rejected(self.inserted().replace(b'</body></html>',b'</body> </html>'))
 def test_non_utf8_body_fails_closed(self):self.rejected(b'\xff'+self.inserted())
 def test_fixture_body_rejection_does_not_log_values(self):
  output=io.StringIO()
  with contextlib.redirect_stdout(output):
   with self.assertRaisesRegex(AssertionError,'artifact bytes'):
    verifier.verify_artifact(self.inserted()+b'changed',self.artifact,'production',True,'/')
  self.assertEqual(output.getvalue(),'')

class OfflineEndToEndTests(BeaconFixture):
 def run_main(self,phase='production',change=None):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);dist=root/'dist';dist.mkdir();page=self.artifact
   if phase=='preview':page=page.replace(b'</head>',b'<meta name="robots" content="noindex"></head>')
   missing=page.replace(b'<h1>Original',b'<meta name="robots" content="noindex"><h1>Missing')
   (dist/'index.html').write_bytes(page);(dist/'404.html').write_bytes(missing)
   (dist/'asset.css').write_bytes(b'body{color:black}')
   (dist/'_headers').write_text('/*\n  X-Content-Type-Options: nosniff\n')
   policy=root/'policy.json';policy.write_text(json.dumps({'previewOrigin':'https://qa.example.test','productionOrigin':'https://qa.example.test'}))
   bodies={'/':page,'/asset.css':b'body{color:black}','/__manual_release_missing_20261007__':missing}
   if phase=='production':
    for route in ['/','/__manual_release_missing_20261007__']:bodies[route]=self.inserted(bodies[route])
   calls=[]
   class Response(io.BytesIO):pass
   def fetch(url,request_phase,opener=None):
    self.assertEqual(request_phase,phase);route=url.removeprefix('https://qa.example.test');calls.append(route)
    response=Response(bodies[route]);response.url=url;response.status=404 if route.startswith('/__manual') else 200
    response.headers=Message();response.headers['X-Content-Type-Options']='nosniff'
    if change:response=change(route,response)
    return response
   output=io.StringIO()
   with patch.object(verifier,'request_response',fetch),patch.object(verifier.sys,'argv',['verify_http.py',str(policy),phase,str(dist),'revision-fixture']),patch('urllib.request.urlopen',side_effect=AssertionError('Unexpected network request')),contextlib.redirect_stdout(output):
    result=verifier.main()
   self.assertEqual(len(calls),3);self.assertNotIn('data-cf-beacon',output.getvalue());return result
 def test_complete_production_checks_keep_separate_hash_receipts(self):
  receipts=self.run_main();self.assertEqual(len(receipts),3)
  modes=[r['matchMode'] for r in receipts];self.assertEqual(modes.count('exact'),1);self.assertEqual(modes.count('pinned-managed-beacon'),2)
  for receipt in receipts:self.assertNotIn('route',receipt)
 def test_complete_preview_uses_exact_artifacts(self):self.assertTrue(all(r['matchMode']=='exact' for r in self.run_main('preview')))
 def test_real_404_status_is_still_required(self):
  def change(route,response):
   if route.startswith('/__manual'):response.status=200
   return response
  with self.assertRaisesRegex(AssertionError,'status/redirect'):self.run_main(change=change)
 def test_wrong_404_artifact_still_fails(self):
  def change(route,response):
   if route.startswith('/__manual'):
    response.seek(0);body=response.read();response.seek(0);response.truncate(0);response.write(body.replace(b'Missing',b'Incorrect',1));response.seek(0)
   return response
  with self.assertRaisesRegex(AssertionError,'artifact bytes'):self.run_main(change=change)
 def test_unexpected_provider_noindex_still_fails(self):
  def change(route,response):response.headers['X-Robots-Tag']='noindex';return response
  with self.assertRaisesRegex(AssertionError,'Unexpected provider robots'):self.run_main(change=change)
 def test_header_rule_still_required(self):
  def change(route,response):del response.headers['X-Content-Type-Options'];return response
  with self.assertRaises(AssertionError):self.run_main(change=change)
 def test_revision_metadata_still_checked(self):
  with patch.object(verifier.Meta,'feed',lambda self,data:None):
   with self.assertRaisesRegex(AssertionError,'revision'):self.run_main()
 def test_preview_noindex_still_checked(self):
  original=verifier.Meta.feed
  def feed(meta,data):original(meta,data);meta.robots=[]
  with patch.object(verifier.Meta,'feed',feed):
   with self.assertRaisesRegex(AssertionError,'preview indexable'):self.run_main('preview')
 def test_404_noindex_still_checked(self):
  original=verifier.Meta.feed
  def feed(meta,data):
   original(meta,data)
   if 'Missing' in data:meta.robots=[]
  with patch.object(verifier.Meta,'feed',feed):
   with self.assertRaisesRegex(AssertionError,'404 indexing mismatch'):self.run_main()

if __name__=='__main__':unittest.main()
