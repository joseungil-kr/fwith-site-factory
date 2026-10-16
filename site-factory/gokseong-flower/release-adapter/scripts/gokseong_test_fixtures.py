"""Explicit local-only test fixtures. Repeated hex SHAs and approval references are
synthetic contract data, not actual source/control commits or release authority.
The context copies frozen source bytes and runs only local Node transformations.
"""
from pathlib import Path
from contextlib import contextmanager
import hashlib,json,shutil,subprocess,tempfile
import gokseong_adapter as adapter
import gokseong_release_output as output
A=Path(__file__).resolve().parents[1];S=A.parent
TEST_REVISION='a'*40

def production_binding(root,revision=TEST_REVISION):
 contract=Path(root)/'release-adapter/release/bounded-contract.json';c=json.loads(contract.read_text())
 return dict(schemaVersion=1,state='approved',repository='joseungil-kr/fwith-site-factory',sourceRoot='site-factory/gokseong-flower',siteKey='gokseong-flower-direct',hostname='gokseong.fwith.kr',origin=output.ORIGIN,worker='gokseong-flower-guide',frozenInputSha256=c['frozenInputsManifestSHA256'],frozenPrivateTreeSha256=c['frozenSource']['frozenTreeSHA256'],sourceRevision=revision,proof=output.PROOF,sitemapRoutes=output.ROUTES,htmlFiles=2,notFoundRobots='noindex,follow',notFoundStatus=404,publicHttpVerified=False,indexNowSubmitted=False,boundedContractSha256=hashlib.sha256(contract.read_bytes()).hexdigest(),coreHubLaunchStatus='NOT_ASSESSED',fullLaunchStatus='NOT_ASSESSED',approvals=dict(publication=True,hostBinding=True,indexNowProof=True),authorizationEvidence='https://github.com/joseungil-kr/fwith-site-factory/blob/'+('c'*40)+'/docs/direct-gokseong/production-authorization-20261016.json',sourceContractSha256='d'*64)

def copy_source(destination):
 destination=Path(destination);rows=adapter.frozen_source()
 for row in rows:
  target=destination/row['path'];target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((S/row['path']).read_bytes())
 shutil.copytree(A,destination/'release-adapter',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
 return destination

def fixture_environment(root,binding):
 binding=Path(binding);binding.write_text(json.dumps(production_binding(root),sort_keys=True)+'\n')
 return dict(adapter.private_environment(),PYTHONDONTWRITEBYTECODE='1',SITE_RELEASE_MODE='production',SITE_INDEXABLE='true',SITE_URL=output.ORIGIN,SITE_FACTORY_REVISION=TEST_REVISION,SITE_RELEASE_BINDING_PATH=str(binding),SITE_RELEASE_BINDING_SHA256=hashlib.sha256(binding.read_bytes()).hexdigest())

@contextmanager
def synthetic_production_output(edit=None):
 with tempfile.TemporaryDirectory(prefix='gokseong-LOCAL-SYNTHETIC-production-') as tmp:
  temporary=Path(tmp);root=copy_source(temporary/'source');adapter.verify_private_dist(S/'candidate/dist');shutil.copytree(S/'candidate/dist',root/'candidate/dist')
  env=fixture_environment(root,temporary/'production-binding.json')
  if edit:edit(root,env)
  run=subprocess.run(['node',str(root/'release-adapter/scripts/write_gokseong_release_files.mjs')],cwd=root/'candidate',env=env,text=True,capture_output=True)
  assert run.returncode==0,run.stdout+run.stderr
  yield root/'candidate/dist',dict(mode='production',indexable=True,origin=output.ORIGIN,revision=TEST_REVISION)
