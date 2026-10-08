"""Exact supplemental source/artifact approval; immutable M2 hashing helpers reused."""
import hashlib,importlib.util,json,os,re,subprocess,sys
from pathlib import Path
CONTROL='657b9ce62b1a519ba606f9fb0110aa3679d0931c'
BASELINE='aeb04a9ed1f9f36692fd3e679e6e71c5c065224d'
ROOT='site-factory/ansan-flower'
FILES=['.github/workflows/ansan-cloudflare-production-deploy.yml', '.github/workflows/ansan-indexnow-production.yml', '.github/workflows/ansan-live-qa.yml', '.github/workflows/ansan-manual-preview-qa.yml', '.github/workflows/ansan-site-build-test.yml', '.github/workflows/sync-flower-product-images.yml', '.github/scripts/ansan-supplemental-gate.py', '.github/workflows/ansan-supplemental-production-artifacts.yml', '.github/scripts/ansan-supplemental-production-capture.mjs', '.github/scripts/ansan-manual-preview.mjs']
CHECKS=['sourceReview','immutableBaseline','nativeGates','routes','assets','cta','catalog','canonicalGraph','pixelQA','productionIndexableBuild','productionArtifactReview','unreleasedDeltaReconciled']
def validate(a,revision,source,execution,delta,artifact=None):
 def require(ok,msg):
  if not ok:raise ValueError(msg)
 require(a['status']=='passed','Independent approval pending')
 require(a['revision']==revision and a['baselineRevision']==BASELINE,'Wrong release/baseline')
 require(a['productionOrigin']=='https://ansan.fwith.kr','Wrong origin')
 require(a['sourceFiles']==source and bool(source),'Source manifest mismatch')
 require(a['executionFiles']==execution and set(execution)==set(FILES),'Execution manifest mismatch')
 require(a['deltaSha256']==delta,'Baseline delta mismatch')
 require(a['controlRevision']==CONTROL,'Wrong M2 control')
 require(a['author'].strip() and a['reviewer'].strip() and a['author'].strip().casefold()!=a['reviewer'].strip().casefold(),'Independent roles required')
 require(all(a['checks'].get(k) is True for k in CHECKS),'Missing independent review')
 require(a['pixelEvidenceMode']=='production-origin-loopback','Wrong pixel phase')
 require(re.fullmatch('[0-9a-f]{64}',a['artifactManifestSha256'] or '') is not None,'Missing artifact hash')
 require(re.fullmatch('[0-9a-f]{40}',revision) is not None,'Full source SHA required')
 e=a['reviewEvidence']
 require(e['siteKey']=='ansan-flower-test' and e['phase']=='production-artifact' and e['status']=='passed','Wrong review phase/site/status')
 require(e['author']==a['author'] and e['reviewer']==a['reviewer'],'Wrong review assignments')
 require(e['executionRevision']==revision and isinstance(e['runId'],int) and e['runId']>0 and isinstance(e['runAttempt'],int) and e['runAttempt']>=1,'Wrong exact artifact execution identity')
 require(e['sourceManifestSha256']==hashlib.sha256(json.dumps(source,sort_keys=True,separators=(',',':')).encode()).hexdigest(),'Wrong reviewed source manifest')
 require(e['checks']==a['checks'],'Review check record differs')
 require(hashlib.sha256(json.dumps(e,sort_keys=True,separators=(',',':')).encode()).hexdigest()==a['reviewEvidenceSha256'],'Review record bytes changed')
 require(all(isinstance(v,str) and v.strip() for v in e['observations']),'Invalid pixel observations')
 require(a['reviewEvidence']['revision']==revision and a['reviewEvidence']['artifactManifestSha256']==a['artifactManifestSha256'],'Wrong review binding')
 require(a['reviewEvidence']['reviewer']==a['reviewer'] and a['reviewEvidence']['pixelStatus']=='passed','Missing actual pixel review')
 require(bool(a['reviewEvidence']['artifacts']) and bool(a['reviewEvidence']['observations']),'Missing artifact receipts/pixel observations')
 for artifact_receipt in a['reviewEvidence']['artifacts']:
  require(isinstance(artifact_receipt['id'],int) and artifact_receipt['id']>0 and re.fullmatch('[0-9a-f]{64}',artifact_receipt['sha256']) is not None,'Invalid official artifact identity')
 if artifact is not None:require(artifact==a['artifactManifestSha256'],'Built artifact differs from reviewed bytes')

def artifact_digest(dist,m2):
 m2.require(dist.is_dir() and not dist.is_symlink(),'Missing/symlink artifact root')
 m2.require(not any(p.is_symlink() for p in dist.rglob('*')),'Artifact symlink forbidden')
 files=m2.artifacts(dist);m2.require(bool(files),'Empty artifact')
 return m2.digest(m2.compact(files))

def main():
 source=Path(sys.argv[1]).resolve();authority=Path(sys.argv[2]).resolve();control=Path(sys.argv[3]).resolve();phase=sys.argv[4]
 if phase not in ['source','artifact']:raise ValueError('Wrong phase')
 spec=importlib.util.spec_from_file_location('m2',control/'scripts/manual-release-20261007/gate.py');m2=importlib.util.module_from_spec(spec);spec.loader.exec_module(m2)
 revision=m2.git(source,'rev-parse','HEAD').decode().strip()
 m2.require(m2.git(control,'rev-parse','HEAD').decode().strip()==CONTROL,'Control moved')
 m2.require(os.environ['GITHUB_REF']=='refs/heads/site-factory-ansan-v1','Wrong production branch')
 for checkout,branch,expected in [(source,'site-factory-ansan-v1',revision),(authority,'main',m2.git(authority,'rev-parse','HEAD').decode().strip())]:
  remote=m2.git(checkout,'ls-remote','--heads','origin','refs/heads/'+branch).decode().split()
  m2.require(len(remote)==2 and remote[0]==expected,'Source/main moved during upload gate')
 a=json.loads((authority/'.github/supplemental-release-20261007/ansan.approval.json').read_text())
 subprocess.run(['git','-C',str(source),'merge-base','--is-ancestor',BASELINE,revision],check=True)
 files=m2.tracked_files(source,ROOT,revision)
 execution={f:m2.digest(m2.git(source,'show',revision+':'+f)) for f in FILES}
 delta=m2.digest(m2.git(source,'diff','--binary','--full-index',BASELINE,revision,'--',ROOT,*FILES))
 artifact=artifact_digest(source/ROOT/'dist',m2) if phase=='artifact' else None
 validate(a,revision,files,execution,delta,artifact)
 registry=json.loads((authority/'.github/site-factory-sites.json').read_text())['sites']['ansan-flower-test']
 m2.require(registry['approvedRevision']==revision and registry['approvalEvidenceUrl']==a['evidenceUrl'],'Registry approval mismatch')
 # Freeze original article lineage and region/provider behavior; manual additions remain explicit.
 for frozen_root in [ROOT+'/src/content/articles',ROOT+'/src/data/architecture.json',ROOT+'/src/data/page-map.json',ROOT+'/src/data/publish-manifest.json',ROOT+'/src/data/region-policy.json']:
  m2.require(m2.tracked_files(source,frozen_root,BASELINE)==m2.tracked_files(source,frozen_root,revision),'Frozen original lineage changed')
 old_manual=m2.tracked_files(source,ROOT+'/src/content/manual',BASELINE)
 for name,h in old_manual.items():m2.require(files.get(name)==h,'Original manual content changed')
 for preserved in [ROOT+'/wrangler.jsonc',ROOT+'/product-image-sync.trigger',ROOT+'/scripts/submit_indexnow.mjs',ROOT+'/scripts/select_indexnow_urls.mjs']:
  m2.require(m2.git(source,'show',BASELINE+':'+preserved)==m2.git(source,'show',revision+':'+preserved),'Provider/sender/image trigger changed')
 m2.worktree(source,files,ROOT,revision,phase=='artifact','sha')
 for f,h in execution.items():m2.require(m2.digest((source/f).read_bytes())==h,'Execution worktree changed')
 print('Exact supplemental source/artifact approval verified; no submission performed')
if __name__=='__main__':main()
