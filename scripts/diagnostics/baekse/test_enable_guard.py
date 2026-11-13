import importlib
import json
import os
import pathlib
import tempfile
import unittest
from unittest.mock import patch
os.environ.setdefault('CLOUDFLARE_ACCOUNT_ID','synthetic')
os.environ.setdefault('CLOUDFLARE_API_TOKEN','synthetic')
import enable_guard as g

OLD='54478f7d-8dd3-437b-9f0a-ad92864e9152'
NEW='00000000-0000-4000-8000-000000000001'
RAW=[{'type':'assets','name':'ASSETS'},{'type':'durable_object_namespace','name':'ORDER_DB','class_name':'OrderDatabase','namespace_id':'synthetic-namespace'},*({'type':'secret_text','name':x} for x in ('ADMIN_PASSWORD','TELEGRAM_ORDER_BOT_TOKEN','TELEGRAM_ORDER_CHAT_ID'))]

class Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.state=pathlib.Path(self.tmp.name)/'state.json'
  self.old={'version':OLD,'scope':{'domain':'synthetic','subdomain':False},'bindings':g.normalize(RAW)}
  self.new={**self.old,'version':NEW,'bindings':g.enabled_bindings(self.old)}
  self.state.write_text(json.dumps(self.old))
  self.env=patch.dict(os.environ,EXPECTED_LIVE_VERSION=OLD,UPLOADED_VERSION=NEW,SOURCE_SHA='synthetic-sha',GITHUB_OUTPUT=str(pathlib.Path(self.tmp.name)/'output'))
  self.env.start();self.sp=patch.object(g,'STATE',self.state);self.sp.start()
 def tearDown(self):self.sp.stop();self.env.stop();self.tmp.cleanup()
 def run_mode(self,mode,live,remote=None):
  with patch.object(g,'snapshot',return_value=live),patch.object(g,'get',return_value=remote),patch.object(g.sys,'argv',['guard',mode]):g.main()
 def test_capture_exact_uuid(self):self.run_mode('capture',self.old)
 def test_capture_no_recipient_fails(self):
  bad={**self.old,'bindings':[b for b in self.old['bindings'] if b[1]!='TELEGRAM_ORDER_CHAT_ID']}
  with self.assertRaises(AssertionError):self.run_mode('capture',bad)
 def test_capture_already_enabled_fails(self):
  with self.assertRaises(AssertionError):self.run_mode('capture',{**self.new,'version':OLD})
 def test_only_flag_allowed_upload(self):
  self.run_mode('uploaded',self.old,{'id':NEW,'annotations':{'workers/tag':'synthetic-sha'},'resources':{'bindings':RAW+[{'type':'plain_text','name':'TELEGRAM_ORDER_ENABLED','text':'true'}]}})
 def test_missing_flag_upload_fails(self):
  with self.assertRaises(AssertionError):self.run_mode('uploaded',self.old,{'id':NEW,'annotations':{'workers/tag':'synthetic-sha'},'resources':{'bindings':RAW}})
 def test_post_then_safe_rollback(self):
  self.run_mode('post',self.new);self.run_mode('rollback-safe',self.new);self.run_mode('rolled-back',self.old)
 def test_scope_drift_fails(self):
  with self.assertRaises(AssertionError):self.run_mode('post',{**self.new,'scope':{}})
 def test_concurrent_version_forbids_rollback(self):
  self.run_mode('post',self.new)
  with self.assertRaises(AssertionError):self.run_mode('rollback-safe',{**self.new,'version':'other'})

if __name__=='__main__':unittest.main()
