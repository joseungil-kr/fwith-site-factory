"""Read-only source-C evidence. Fixed production metadata; no deployment capability."""
import hashlib,json,os,pathlib,subprocess,sys
ROOT=pathlib.Path('site-factory/hwaseong-flower')
OUT=pathlib.Path('hwaseong-source-c-evidence')
BASELINE='d7d7f47ecafc9bd9e3a75511379d430cd00e8510'
PREVIOUS='3ffc1443558ae6b375a472b2224c0c0125b5ebea'
QA='3225fcf46b31d511a15ce865cddad690f2dd4480'
def sha(b):return hashlib.sha256(b).hexdigest()
def compact(v):return json.dumps(v,sort_keys=True,separators=(',',':')).encode()
def git(*args):return subprocess.check_output(['git',*args])
def artifacts():
 out={};total=0
 for p in sorted((ROOT/'dist').rglob('*')):
  assert not p.is_symlink(),str(p)
  if p.is_file():
   b=p.read_bytes();out[str(p.relative_to(ROOT/'dist'))]=sha(b);total+=len(b)
 assert len(out)==87,'Unexpected artifact inventory'
 assert sum(n.endswith('.html') for n in out)==66,'Incomplete 58 article + 7 hub + 404 inventory'
 assert total<24*1024*1024,'Artifact exceeds bounded download size'
 return out
def main():
 assert os.environ['GITHUB_REF']=='refs/heads/manual-hwaseong-supplement-artifacts-20261008'
 assert os.environ['SITE_URL']=='https://hwaseong.fwith.kr'
 assert os.environ['SITE_INDEXABLE']=='true' and os.environ['MANUAL_PREVIEW']=='false'
 revision=os.environ['GITHUB_SHA'];assert git('rev-parse','HEAD').decode().strip()==revision
 for ancestor in [BASELINE,PREVIOUS,QA]:subprocess.run(['git','merge-base','--is-ancestor',ancestor,revision],check=True)
 assert json.loads((ROOT/'src/data/build-revision.json').read_bytes())=={'sha':revision}
 sources={}
 for row in git('ls-tree','-rz',revision,'--',str(ROOT)).split(b'\0'):
  if not row:continue
  meta,name=row.split(b'\t');mode,kind,blob=meta.split();assert kind==b'blob' and mode in (b'100644',b'100755')
  name=name.decode();b=git('cat-file','blob',blob.decode());sources[name]=sha(b)
  p=pathlib.Path(name);assert p.is_file() and not p.is_symlink()
  if name==str(ROOT/'src/data/build-revision.json'):assert json.loads(p.read_bytes())=={'sha':revision}
  else:assert sha(p.read_bytes())==sources[name],name
 actual=artifacts();OUT.mkdir(exist_ok=True)
 if sys.argv[1]=='record':
  (OUT/'production-artifact-manifest.json').write_bytes(compact(actual))
  (OUT/'production-source-manifest.json').write_bytes(compact(sources))
 elif sys.argv[1]=='verify':
  assert sources==json.loads((OUT/'production-source-manifest.json').read_bytes()),'Source changed across builds'
  assert actual==json.loads((OUT/'production-artifact-manifest.json').read_bytes()),'Non-deterministic artifact rebuild'
  delta=git('diff','--binary','--full-index',BASELINE,revision,'--',str(ROOT))
  report={'revision':revision,'baselineRevision':BASELINE,'previousBranchRevision':PREVIOUS,'reviewedQaRevision':QA,'deltaSha256':sha(delta),'artifactManifestSha256':sha(compact(actual)),'sourceManifestSha256':sha(compact(sources)),'artifactCount':len(actual),'htmlCount':66,'sourceCount':len(sources),'twoBuildsByteIdentical':True,'productionOrigin':'https://hwaseong.fwith.kr','pixelTransport':'http://127.0.0.1:8935','deploymentPerformed':False}
  (OUT/'production-artifact-verification.json').write_text(json.dumps(report,indent=2)+'\n')
 else:raise ValueError('Unknown mode')
if __name__=='__main__':main()

