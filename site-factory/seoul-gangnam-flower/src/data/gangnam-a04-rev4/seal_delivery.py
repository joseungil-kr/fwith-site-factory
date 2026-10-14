from pathlib import Path
import json,hashlib,datetime,zipfile
O=Path(__file__).parent;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
excluded={'delivery-manifest.json','SHA256SUMS.txt','delivery-verification.json'}
files=[]
for p in sorted(O.rglob('*')):
 if p.is_file() and '__pycache__' not in p.parts and p.name not in excluded and p.suffix!='.zip':files.append({'path':str(p.relative_to(O)),'bytes':p.stat().st_size,'sha256':sha(p)})
m={'createdAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Separate local A04 addendum and rev4 overlay inputs; includes preserved original failure, frozen method, independent reviews and final readback. Original bundle/source are external immutable references, not repackaged or overwritten.','fileCount':len(files),'files':files,'exclusions':['This manifest and SHA256SUMS wrapper','ZIP wrapper','delivery-verification.json receipt','Python __pycache__ generated files'],'originalBundleManifestSha256':'2af6d2b07e668177bd271b9b4cfc6cb751ffdedfd96ae8d975e5d3dd83979214','productionReady':False}
mp=O/'delivery-manifest.json';mp.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
(O/'SHA256SUMS.txt').write_text(''.join(q['sha256']+'  '+q['path']+'\n' for q in files)+sha(mp)+'  delivery-manifest.json\n')
zp=O/'gangnam-a04-rev4-local-handoff-20261013.zip'
with zipfile.ZipFile(zp,'w',zipfile.ZIP_DEFLATED) as z:
 for q in files:z.write(O/q['path'],q['path'])
 z.write(mp,'delivery-manifest.json');z.write(O/'SHA256SUMS.txt','SHA256SUMS.txt')
errors=[]
for q in files:
 if sha(O/q['path'])!=q['sha256'] or (O/q['path']).stat().st_size!=q['bytes']:errors.append(q['path'])
with zipfile.ZipFile(zp) as z:
 for q in files:
  if hashlib.sha256(z.read(q['path'])).hexdigest()!=q['sha256']:errors.append('ZIP:'+q['path'])
 ck=z.testzip();entries=len(z.namelist())
receipt={'verifiedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'classification':'직접 확인: directory and ZIP readback','manifestSha256':sha(mp),'fileCount':len(files),'directoryMismatches':errors,'zip':{'path':str(zp),'bytes':zp.stat().st_size,'sha256':sha(zp),'entryCount':entries,'crcError':ck},'acceptanceSha256':sha(O/'revised-input/acceptance.rev4.json'),'inputManifestSha256':sha(O/'revised-input/input-manifest.rev4.json'),'success':not errors and ck is None,'boundary':'Local wrapper integrity only. No implementation or public deployment claim.'}
(O/'delivery-verification.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n');print(json.dumps(receipt,ensure_ascii=False,indent=2))
