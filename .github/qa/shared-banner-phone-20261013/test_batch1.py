"""Batch-only regressions for strict owner/payload authorization and thin hubs."""
import json, os, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
from copy import deepcopy
from bind import HERE, BATCH_ID, ISSUE_TITLE, verify_runner
from capture import validate_capture
from reused import digest

class BatchTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
  self.event=self.root/'event.json'
  self.sha=digest((HERE/'bindings.json').read_bytes())
  self.payload={'schemaVersion':1,'batchId':BATCH_ID,'bindingsSha256':self.sha}
  self.issue={'action':'opened','issue':{'title':ISSUE_TITLE,'user':{'login':'joseungil-kr'},'body':json.dumps(self.payload)}}
  self.env={'GITHUB_ACTIONS':'true','GITHUB_REPOSITORY':'joseungil-kr/fwith-site-factory','GITHUB_REF':'refs/heads/main','GITHUB_RUN_ATTEMPT':'1','GITHUB_SHA':'a'*40,'GITHUB_ACTOR':'joseungil-kr','GITHUB_TRIGGERING_ACTOR':'joseungil-kr','GITHUB_EVENT_PATH':str(self.event),'GITHUB_EVENT_NAME':'issues'}
 def authorize(self,event,env=None):
  self.event.write_text(json.dumps(event))
  with patch.dict(os.environ,env or self.env,clear=True):verify_runner()
 def test_exact_owner_issue(self):self.authorize(self.issue)
 def test_reject_mismatched_payload_fields(self):
  for key,value in [('schemaVersion',2),('batchId','other'),('bindingsSha256','0'*64),('extra','unapproved')]:
   with self.subTest(key=key):
    event=deepcopy(self.issue);body=deepcopy(self.payload);body[key]=value;event['issue']['body']=json.dumps(body)
    with self.assertRaises(ValueError):self.authorize(event)
 def test_reject_issue_identity_changes(self):
  for change in ['title','owner','action']:
   with self.subTest(change=change):
    event=deepcopy(self.issue)
    if change=='title':event['issue']['title']='other'
    if change=='owner':event['issue']['user']['login']='other'
    if change=='action':event['action']='edited'
    with self.assertRaises(ValueError):self.authorize(event)
 def test_reject_runner_identity_changes(self):
  for key,value in [('GITHUB_ACTOR','other'),('GITHUB_TRIGGERING_ACTOR','other'),('GITHUB_REF','refs/heads/other'),('GITHUB_RUN_ATTEMPT','2'),('GITHUB_EVENT_NAME','push')]:
   with self.subTest(key=key):
    with self.assertRaises(ValueError):self.authorize(self.issue,{**self.env,key:value})
 def test_exact_dispatch_payload(self):
  self.authorize({'inputs':{'batch_id':BATCH_ID,'expected_bindings_sha256':self.sha}},{**self.env,'GITHUB_EVENT_NAME':'workflow_dispatch'})
 def test_dispatch_cannot_change_artifact_binding(self):
  with self.assertRaises(ValueError):self.authorize({'inputs':{'batch_id':BATCH_ID,'expected_bindings_sha256':'0'*64}},{**self.env,'GITHUB_EVENT_NAME':'workflow_dispatch'})
 def thin_fixture(self):
  rows=[]
  for width,height in [(375,812),(1440,1000)]:
   path=f'screenshots/{width}/regions/full.jpg';p=self.root/path;p.parent.mkdir(parents=True);p.write_bytes(f'{width},{height}'.encode())
   shot={'screenshot':path,'screenshotSha256':digest(p.read_bytes()),'dimensions':{'width':width,'height':height}}
   rows.append({'route':'/regions/','width':width,'height':height,'issues':[],'banners':[],'fullPage':shot})
  proof={'routes':['/regions/'],'captureRoutes':['/regions/'],'thinHubRoutes':['/regions/']}
  return rows,proof
 def dimensions(self,b):
  w,h=map(int,b.decode().split(','));return {'width':w,'height':h}
 def test_thin_directory_requires_full_pixels_without_invented_banners(self):
  rows,proof=self.thin_fixture()
  with patch('capture.jpeg_dimensions',self.dimensions):coverage=validate_capture(rows,proof,self.root)
  self.assertEqual(coverage['totalScreenshots'],2);self.assertEqual(coverage['focusedBannerScreenshots'],0)
 def test_thin_directory_rejects_missing_full_pixels(self):
  rows,proof=self.thin_fixture();del rows[0]['fullPage']
  with self.assertRaises(ValueError):validate_capture(rows,proof,self.root)
 def test_thin_directory_rejects_added_banner(self):
  rows,proof=self.thin_fixture();rows[0]['banners']=[{'kind':'message'}]
  with self.assertRaises(ValueError):validate_capture(rows,proof,self.root)

if __name__=='__main__':unittest.main()
