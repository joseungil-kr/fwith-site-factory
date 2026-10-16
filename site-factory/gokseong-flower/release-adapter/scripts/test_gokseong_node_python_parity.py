"""Fresh Node offline head transformation; no synthetic production approvals or proof."""
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
  r=subprocess.run(['node',str(A/'scripts/write_gokseong_release_files.mjs')],cwd=S/'candidate',env=adapter.private_environment(),capture_output=True,text=True);self.assertNotEqual(r.returncode,0);self.assertIn('production_writer_disabled',r.stderr)
if __name__=='__main__':unittest.main(verbosity=2)
