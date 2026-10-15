"""Run synthetic offline production envelope only; never network, provider or remote evidence."""
from pathlib import Path
import tempfile,shutil,json,hashlib,subprocess,os,unittest,sys
import namgu_release_output as output
import namgu_adapter as adapter
A=Path(__file__).resolve().parents[1];S=A.parent
class NodePythonParity(unittest.TestCase):
 def test_exact_synthetic_writer_parity(self):
  with tempfile.TemporaryDirectory(prefix='namgu-test-only-') as temporary:
   temp=Path(temporary);root=temp/'source'
   for row in adapter.frozen_source():
    dest=root/row['path'];dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((S/row['path']).read_bytes())
   shutil.copytree(A,root/'release-adapter',ignore=shutil.ignore_patterns('__pycache__'))
   shutil.copytree(S/'candidate/dist',root/'candidate/dist')
   contract=json.loads((A/'release/bounded-contract.json').read_text());revision='a'*40
   fixture=dict(schemaVersion=1,state='approved',repository='joseungil-kr/fwith-site-factory',sourceRoot='site-factory/gwangju-namgu-flower',siteKey='gwangju-namgu-flower-direct',hostname='gwangju-namgu.fwith.kr',origin=output.ORIGIN,worker='gwangju-namgu-flower-guide',frozenInputSha256=contract['frozenInputsManifestSHA256'],frozenPrivateTreeSha256=contract['frozenSource']['frozenTreeSHA256'],sourceRevision=revision,proof=output.PROOF,sitemapRoutes=output.ROUTES,htmlFiles=4,directoryRobots='noindex,follow',notFoundStatus=404,publicHttpVerified=False,indexNowSubmitted=False,boundedContractSha256=hashlib.sha256((A/'release/bounded-contract.json').read_bytes()).hexdigest(),coreHubLaunchStatus='NOT_ASSESSED',fullLaunchStatus='NOT_ASSESSED',approvals=dict(publication=True,hostBinding=True,indexNowProof=True),authorizationEvidence='https://github.com/joseungil-kr/fwith-site-factory/blob/'+('c'*40)+'/docs/direct-gwangju-namgu/production-authorization-20261015.json',sourceContractSha256='d'*64)
   binding=temp/'production-binding.json';binding.write_text(json.dumps(fixture));env=dict(os.environ,SITE_RELEASE_MODE='production',SITE_INDEXABLE='true',SITE_URL=output.ORIGIN,SITE_FACTORY_REVISION=revision,SITE_RELEASE_BINDING_PATH=str(binding),SITE_RELEASE_BINDING_SHA256=hashlib.sha256(binding.read_bytes()).hexdigest())
   run=subprocess.run(['node',str(root/'release-adapter/scripts/write_namgu_release_files.mjs')],cwd=root/'candidate',env=env,text=True,capture_output=True)
   self.assertEqual(run.returncode,0,run.stdout+run.stderr)
   result=output.inspect_dist(root/'candidate/dist',dict(mode='production',indexable=True,origin=output.ORIGIN,revision=revision))
   self.assertEqual(result['previewEquivalence'],{'htmlBodiesByteIdentical':4,'staticAssetsByteIdentical':9,'headChangesExactlyAllowed':4})
   self.assertEqual(len(result['files']),18)
   adapter.frozen_source(root)
   self.assertEqual(hashlib.sha256((root/'inputs/reviewed-copy/customer-copy.json').read_bytes()).hexdigest(),'052f89035bce44c5e4f403e7e42b9306dc0f49588e10d7aa89a8f088a8cadf08')
   print(json.dumps({'status':'SYNTHETIC_LOCAL_ENVELOPE_AND_HEAD_WRITER_PARITY_PASSED','fixtureRevisionUsed':True,'actualSourceCommit':None,'remoteSaved':False,'actualApprovalUsed':False,'actualProductionRunner':False,'networkOrProviderCalls':0,'htmlBodiesByteIdentical':4,'staticAssetsByteIdentical':9,'headChangesExactlyAllowed':4,'outputFiles':18}))
if __name__=='__main__':unittest.main(verbosity=2)
