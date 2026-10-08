"""Read-only source-C evidence. Fixed production metadata; no deployment capability."""
import hashlib,json,os,pathlib,subprocess,sys
ROOT=pathlib.Path('site-factory/seongnam-flower')
PHASE=os.environ['MANUAL_QA_PHASE']
assert PHASE in ('preview','production')
ORIGIN='https://seongnam-flower-guide-qa.joseungil.workers.dev' if PHASE=='preview' else 'https://seongnam.fwith.kr'
OUT=pathlib.Path('seongnam-'+PHASE+'-evidence/logs')
BASELINE='06f4049c2c8e818ef7474e628031c5f901b4ecab'
def sha(b):return hashlib.sha256(b).hexdigest()
def compact(v):return json.dumps(v,sort_keys=True,separators=(',',':')).encode()
def git(*args):return subprocess.check_output(['git',*args])
def artifacts():
 out={};total=0
 for p in sorted((ROOT/'dist').rglob('*')):
  assert not p.is_symlink(),str(p)
  if p.is_file():
   b=p.read_bytes();out[str(p.relative_to(ROOT/'dist'))]=sha(b);total+=len(b)
 assert len(out)==64,'Unexpected artifact inventory'
 assert sum(n.endswith('.html') for n in out)==36,'Incomplete 30 article + 5 hub + 404 inventory'
 assert total<24*1024*1024,'Artifact exceeds bounded download size'
 return out
def main():
 assert os.environ['GITHUB_REF']=='refs/heads/manual-seongnam-supplement-artifacts-20261008'
 assert os.environ['SITE_URL']==os.environ['SITE_ORIGIN']==ORIGIN
 assert os.environ['SITE_INDEXABLE']==('false' if PHASE=='preview' else 'true')
 revision=os.environ['GITHUB_SHA'];assert git('rev-parse','HEAD').decode().strip()==revision
 for ancestor in [BASELINE]:subprocess.run(['git','merge-base','--is-ancestor',ancestor,revision],check=True)
 assert json.loads((ROOT/'src/data/build-revision.json').read_bytes())=={'revision':revision}
 sources={}
 for row in git('ls-tree','-rz',revision,'--',str(ROOT)).split(b'\0'):
  if not row:continue
  meta,name=row.split(b'\t');mode,kind,blob=meta.split();assert kind==b'blob' and mode in (b'100644',b'100755')
  name=name.decode();b=git('cat-file','blob',blob.decode());sources[name]=sha(b)
  p=pathlib.Path(name);assert p.is_file() and not p.is_symlink()
  if name==str(ROOT/'src/data/build-revision.json'):assert json.loads(p.read_bytes())=={'revision':revision}
  else:assert sha(p.read_bytes())==sources[name],name
 actual=artifacts();OUT.mkdir(exist_ok=True)
 if sys.argv[1]=='record':
  (OUT/'production-artifact-manifest.json').write_bytes(compact(actual))
  (OUT/'production-source-manifest.json').write_bytes(compact(sources))
 elif sys.argv[1]=='verify':
  assert sources==json.loads((OUT/'production-source-manifest.json').read_bytes()),'Source changed across builds'
  assert actual==json.loads((OUT/'production-artifact-manifest.json').read_bytes()),'Non-deterministic artifact rebuild'
  delta=git('diff','--binary','--full-index',BASELINE,revision,'--',str(ROOT))
  report={'revision':revision,'baselineRevision':BASELINE,'phase':PHASE,'deltaSha256':sha(delta),'artifactManifestSha256':sha(compact(actual)),'sourceManifestSha256':sha(compact(sources)),'artifactCount':len(actual),'htmlCount':36,'sourceCount':len(sources),'twoBuildsByteIdentical':True,'canonicalOrigin':ORIGIN,'pixelTransport':'http://127.0.0.1:8936','deploymentPerformed':False}
  (OUT/'production-artifact-verification.json').write_text(json.dumps(report,indent=2)+'\n')
 else:raise ValueError('Unknown mode')
if __name__=='__main__':main()

