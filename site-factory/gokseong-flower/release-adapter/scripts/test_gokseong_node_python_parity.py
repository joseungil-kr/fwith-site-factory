"""Fresh offline and explicitly SYNTHETIC production-like Node output; no actual authorization."""
from pathlib import Path
from contextlib import contextmanager
import tempfile,json,subprocess,unittest
import gokseong_release_output as output
import gokseong_adapter as adapter
A=Path(__file__).resolve().parents[1];S=A.parent
@contextmanager
def synthetic_node_output():
 with tempfile.TemporaryDirectory(prefix='gokseong-offline-parity-') as temporary:
  dest=Path(temporary)/'inspection';adapter.frozen_source();adapter.verify_private_dist(S/'candidate/dist')
  run=subprocess.run(['node',str(A/'scripts/write_gokseong_release_files.mjs'),'--offline-inspection',str(dest)],cwd=S/'candidate',env=adapter.private_environment(),text=True,capture_output=True);assert run.returncode==0,run.stdout+run.stderr
  adapter.frozen_source();yield dest,dict(mode='offline-inspection',indexable=True,origin=output.ORIGIN,revision='local-inspection')
class NodePythonParity(unittest.TestCase):
 def test_exact_offline_writer_parity(self):
  with synthetic_node_output() as (dist,mode):
   result=output.inspect_dist(dist,mode);self.assertEqual(result['previewEquivalence'],{'htmlBodiesByteIdentical':2,'staticAssetsByteIdentical':9,'headChangesExactlyAllowed':2});self.assertEqual(len(result['files']),15);self.assertEqual(result['sitemapUrls'],[output.ORIGIN+'/']);self.assertIsNone(result['indexNowProof'])
   for filename,route in output.FILES.items():
    before=(S/'candidate/dist'/filename).read_bytes();after=(dist/filename).read_bytes();i=before.index(b'<body');self.assertEqual(after,output.transformed_prefix(before[:i].decode(),route,mode['revision']).encode()+before[i:])
   print(json.dumps({'status':'LOCAL_OFFLINE_HEAD_WRITER_PARITY_PASSED','actualSourceCommit':None,'remoteSaved':False,'actualApprovalUsed':False,'actualProductionRunner':False,'networkOrProviderCalls':0,'indexNowProof':None,'outputFiles':len(result['files'])}))
 def test_unconfigured_production_writer_rejected(self):
  r=subprocess.run(['node',str(A/'scripts/write_gokseong_release_files.mjs')],cwd=S/'candidate',env=adapter.private_environment(),capture_output=True,text=True);self.assertNotEqual(r.returncode,0);self.assertIn('selected_mode_required',r.stderr)
from gokseong_test_fixtures import synthetic_production_output,copy_source,fixture_environment
import hashlib,shutil
class ProductionNodePythonParity(unittest.TestCase):
 def test_exact_synthetic_production_writer_parity(self):
  with synthetic_production_output() as (dist,mode):
   result=output.inspect_dist(dist,mode)
   self.assertEqual(result['previewEquivalence'],{'htmlBodiesByteIdentical':2,'staticAssetsByteIdentical':9,'headChangesExactlyAllowed':2});self.assertEqual(len(result['files']),16)
   self.assertEqual(result['indexNowProof'],output.PROOF);self.assertFalse(result['publicHTTPVerified']);self.assertFalse(result['publishableArtifact'])
   self.assertEqual(output.indexnow_payload(result['sitemapUrls']),{'host':'gokseong.fwith.kr','key':Path(output.PROOF['path']).stem,'keyLocation':output.ORIGIN+output.PROOF['path'],'urlList':[output.ORIGIN+'/']})
   for filename,route in output.FILES.items():
    before=(S/'candidate/dist'/filename).read_bytes();after=(dist/filename).read_bytes();i=before.index(b'<body');self.assertEqual(after,output.transformed_prefix(before[:i].decode(),route,mode['revision']).encode()+before[i:])
   print(json.dumps({'status':'LOCAL_SYNTHETIC_PRODUCTION_WRITER_PARITY_PASSED','fixtureRevision':mode['revision'],'actualSourceCommit':None,'actualApprovalUsed':False,'actualProductionRunner':False,'networkOrProviderCalls':0,'outputFiles':len(result['files'])}))
 def test_missing_dedicated_proof_rejected(self):
  with self.assertRaisesRegex(AssertionError,'ENOENT'):
   with synthetic_production_output(lambda root,env:(root/'release-adapter/release/gokseong-indexnow-proof.txt').unlink()):pass
 def test_changed_dedicated_proof_rejected(self):
  with self.assertRaisesRegex(AssertionError,'exact_dedicated_proof_bytes'):
   with synthetic_production_output(lambda root,env:(root/'release-adapter/release/gokseong-indexnow-proof.txt').write_bytes(b'changed\n')):pass
 def test_second_transform_rejected(self):
  with synthetic_production_output() as (dist,mode):
   root=dist.parents[1];env=fixture_environment(root,root.parent/'production-binding.json');before={p.relative_to(dist).as_posix():p.read_bytes() for p in dist.rglob('*') if p.is_file()}
   run=subprocess.run(['node',str(root/'release-adapter/scripts/write_gokseong_release_files.mjs')],env=env,text=True,capture_output=True)
   self.assertNotEqual(run.returncode,0);self.assertIn('exact_private_inventory_required',run.stderr);self.assertEqual(before,{p.relative_to(dist).as_posix():p.read_bytes() for p in dist.rglob('*') if p.is_file()})
 def test_internal_binding_rejected(self):
  def edit(root,env):
   original=Path(env['SITE_RELEASE_BINDING_PATH']);target=root/'release-adapter/release/production-binding.json';target.write_bytes(original.read_bytes());env['SITE_RELEASE_BINDING_PATH']=str(target)
  with self.assertRaisesRegex(AssertionError,'source_internal_binding_forbidden'):
   with synthetic_production_output(edit):pass
 def test_provider_credentials_rejected_before_transform(self):
  with self.assertRaisesRegex(AssertionError,'provider_credentials_forbidden'):
   with synthetic_production_output(lambda root,env:env.update(CLOUDFLARE_API_TOKEN='TEST_ONLY_NOT_A_CREDENTIAL')):pass
if __name__=='__main__':unittest.main(verbosity=2)
