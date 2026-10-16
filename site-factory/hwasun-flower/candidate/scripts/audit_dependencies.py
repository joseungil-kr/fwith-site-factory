from pathlib import Path
import json,hashlib,datetime,subprocess
C=Path(__file__).resolve().parents[1];(C/'evidence').mkdir(parents=True,exist_ok=True);lock=json.loads((C/'package-lock.json').read_text());present=[];missing=[];bad=[]
for rel,meta in lock['packages'].items():
 if not rel:continue
 p=C/rel/'package.json'
 if p.exists():
  installed=json.loads(p.read_text());row={'path':rel,'expected':meta['version'],'actual':installed['version']};present.append(row)
  if row['expected']!=row['actual']:bad.append(row)
 else:missing.append({'path':rel,'optional':meta.get('optional',False),'os':meta.get('os'),'cpu':meta.get('cpu')})
assert not bad,bad
assert all(m['optional'] for m in missing),[m for m in missing if not m['optional']]
r={'checkedAtUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'method':'Reused pre-existing local dependency cache; compared each installed package version to unchanged reused package-lock. No network install or full package-byte integrity audit claimed.','node':subprocess.check_output(['node','--version'],text=True).strip(),'cache':str((C/'node_modules').resolve()),'lockSHA256':hashlib.sha256((C/'package-lock.json').read_bytes()).hexdigest(),'installedMatching':len(present),'missingOptionalPlatformPackages':len(missing),'versionMismatches':bad,'packages':present,'missing':missing,'npmInstallPerformed':False}
(C/'evidence/dependency-cache-verification.json').write_text(json.dumps(r,indent=2)+'\n');print({k:r[k] for k in ['node','installedMatching','missingOptionalPlatformPackages','versionMismatches','npmInstallPerformed']})
