"""Read-only source-C evidence; fixed site and no deployment capability."""
import hashlib,json,os,pathlib,subprocess,sys
ROOT=pathlib.Path('site-factory/goyang-flower')
OUT=pathlib.Path('goyang-preview-evidence')
def sha(b):return hashlib.sha256(b).hexdigest()
def compact(v):return json.dumps(v,sort_keys=True,separators=(',',':')).encode()
def artifacts():
 out={}
 for p in sorted((ROOT/'dist').rglob('*')):
  assert not p.is_symlink(),str(p)
  if p.is_file():out[str(p.relative_to(ROOT/'dist'))]=sha(p.read_bytes())
 assert len(out)==92,'Unexpected production artifact inventory'
 assert sum(p.stat().st_size for p in (ROOT/'dist').rglob('*') if p.is_file())<24*1024*1024
 return out
def main():
 assert os.environ['GITHUB_REF']=='refs/heads/manual-goyang-source-c-20261007'
 assert os.environ['SITE_URL']==os.environ['SITE_ORIGIN']=='https://goyang.fwith.kr'
 assert os.environ['SITE_INDEXABLE']=='true'
 revision=os.environ['GITHUB_SHA'];assert subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==revision
 subprocess.run(['git','merge-base','--is-ancestor','95dc6bd67cff7318e880072bea1cec51cdd9d6fb',revision],check=True)
 assert json.loads((ROOT/'src/data/build-revision.json').read_bytes())=={'revision':revision}
 sources={}
 for row in subprocess.check_output(['git','ls-tree','-rz',revision,'--',str(ROOT)]).split(b'\0'):
  if not row:continue
  meta,name=row.split(b'\t');mode,kind,blob=meta.split();assert kind==b'blob' and mode in (b'100644',b'100755')
  name=name.decode();b=subprocess.check_output(['git','cat-file','blob',blob.decode()]);sources[name]=sha(b)
  p=pathlib.Path(name);assert p.is_file() and not p.is_symlink()
  if name==str(ROOT/'src/data/build-revision.json'):assert json.loads(p.read_bytes())=={'revision':revision}
  else:assert sha(p.read_bytes())==sources[name],name
 actual=artifacts();OUT.mkdir(exist_ok=True)
 if sys.argv[1]=='record':
  (OUT/'production-artifact-manifest.json').write_bytes(compact(actual))
  (OUT/'production-source-manifest.json').write_bytes(compact(sources))
 elif sys.argv[1]=='verify':
  assert actual==json.loads((OUT/'production-artifact-manifest.json').read_bytes()),'Non-deterministic artifact rebuild'
  report={'revision':revision,'baselineRevision':'95dc6bd67cff7318e880072bea1cec51cdd9d6fb','artifactManifestSha256':sha(compact(actual)),'sourceManifestSha256':sha(compact(sources)),'artifactCount':len(actual),'sourceCount':len(sources),'twoBuildsByteIdentical':True,'productionOrigin':'https://goyang.fwith.kr','pixelTransport':'http://127.0.0.1:8936','deploymentPerformed':False}
  (OUT/'production-artifact-verification.json').write_text(json.dumps(report,indent=2)+'\n')
 else:raise ValueError('Unknown mode')
if __name__=='__main__':main()
