"""Synthetic offline production envelope from this source's actual private dist only.
No author evidence, saved production fixture, network, provider or remote success claims.
"""
from pathlib import Path
from contextlib import contextmanager
import tempfile,shutil,json,hashlib,subprocess,os,unittest
import damyang_release_output as output
import damyang_adapter as adapter
A=Path(__file__).resolve().parents[1];S=A.parent

@contextmanager
def synthetic_node_output():
 with tempfile.TemporaryDirectory(prefix='damyang-test-only-') as temporary:
  temp=Path(temporary);root=temp/'source'
  for row in adapter.frozen_source():
   dest=root/row['path'];dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((S/row['path']).read_bytes())
  shutil.copytree(A,root/'release-adapter',ignore=shutil.ignore_patterns('__pycache__'))
  adapter.verify_private_dist(S/'candidate/dist')
  shutil.copytree(S/'candidate/dist',root/'candidate/dist')
  contract=json.loads((A/'release/bounded-contract.json').read_text());revision='a'*40
  fixture=dict(schemaVersion=1,state='approved',repository='joseungil-kr/fwith-site-factory',sourceRoot='site-factory/damyang-flower',siteKey='damyang-flower-direct',hostname='damyang.fwith.kr',origin=output.ORIGIN,worker='damyang-flower-guide',frozenInputSha256=contract['frozenInputsManifestSHA256'],frozenPrivateTreeSha256=contract['frozenSource']['frozenTreeSHA256'],sourceRevision=revision,proof=output.PROOF,sitemapRoutes=output.ROUTES,htmlFiles=2,notFoundRobots='noindex,follow',notFoundStatus=404,publicHttpVerified=False,indexNowSubmitted=False,boundedContractSha256=hashlib.sha256((A/'release/bounded-contract.json').read_bytes()).hexdigest(),coreHubLaunchStatus='NOT_ASSESSED',fullLaunchStatus='NOT_ASSESSED',approvals=dict(publication=True,hostBinding=True,indexNowProof=True),authorizationEvidence='https://github.com/joseungil-kr/fwith-site-factory/blob/'+('c'*40)+'/docs/direct-damyang/production-authorization-20261016.json',sourceContractSha256='d'*64)
  binding=temp/'production-binding.json';binding.write_text(json.dumps(fixture));env=dict(adapter.private_environment(),SITE_RELEASE_MODE='production',SITE_INDEXABLE='true',SITE_URL=output.ORIGIN,SITE_FACTORY_REVISION=revision,SITE_RELEASE_BINDING_PATH=str(binding),SITE_RELEASE_BINDING_SHA256=hashlib.sha256(binding.read_bytes()).hexdigest())
  run=subprocess.run(['node',str(root/'release-adapter/scripts/write_damyang_release_files.mjs')],cwd=root/'candidate',env=env,text=True,capture_output=True)
  assert run.returncode==0,run.stdout+run.stderr
  adapter.frozen_source(root)
  yield root/'candidate/dist',dict(mode='production',indexable=True,origin=output.ORIGIN,revision=revision)

class NodePythonParity(unittest.TestCase):
 def test_exact_synthetic_writer_parity(self):
  with synthetic_node_output() as (dist,mode):
   result=output.inspect_dist(dist,mode)
   self.assertEqual(result['previewEquivalence'],{'htmlBodiesByteIdentical':2,'staticAssetsByteIdentical':9,'headChangesExactlyAllowed':2})
   self.assertEqual(len(result['files']),16)
   self.assertEqual(result['sitemapUrls'],[output.ORIGIN+'/'])
   for filename,route in output.FILES.items():
    before=(S/'candidate/dist'/filename).read_bytes();after=(dist/filename).read_bytes();i=before.index(b'<body')
    self.assertEqual(after,output.transformed_prefix(before[:i].decode(),route,mode['revision']).encode()+before[i:])
   print(json.dumps({'status':'SYNTHETIC_LOCAL_ENVELOPE_AND_HEAD_WRITER_PARITY_PASSED','fixtureRevisionUsed':True,'actualSourceCommit':None,'remoteSaved':False,'actualApprovalUsed':False,'actualProductionRunner':False,'networkOrProviderCalls':0,'htmlBodiesByteIdentical':2,'staticAssetsByteIdentical':9,'headChangesExactlyAllowed':2,'outputFiles':len(result['files'])}))
if __name__=='__main__':unittest.main(verbosity=2)
