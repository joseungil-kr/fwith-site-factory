#!/usr/bin/env python3
"""Hash local source, generated files and actual test logs without touching remote state."""
from pathlib import Path
import hashlib,json,re,sys
C=Path(__file__).resolve().parents[1];R=C.parent;E=R/'evidence'
sha=lambda data:hashlib.sha256(data).hexdigest()
def dump(name,data):
 p=E/name;p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n');return {'path':str(p.relative_to(R)),'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size}
def inventory(root,exclude=()):
 rows=[]
 for p in sorted(root.rglob('*')):
  rel=p.relative_to(root)
  if any(part in exclude for part in rel.parts) or not p.is_file() or p.is_symlink():continue
  rows.append({'path':str(rel),'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size})
 canonical=''.join(f"{r['sha256']}  {r['path']}\n" for r in rows)
 return {'algorithm':'SHA256 of concatenated sorted SHA256 + two spaces + POSIX relative path + LF lines','treeSHA256':sha(canonical.encode()),'files':rows}
source=inventory(C,('node_modules','dist','.astro','evidence','__pycache__'))
outputs=inventory(C/'dist')
source_ref=dump('source-manifest.json',source);output_ref=dump('output-manifest.json',outputs)
source_by_path={f['path']:f for f in source['files']};test_source=[f for f in source['files'] if f['path'].startswith(('scripts/','tests/'))]
# Re-evaluate actual static output; hash logs only after their known command runs have completed.
from qa_mokpo import check
static=check();build=(E/'build-final.log').read_text();tests=(E/'tests-final.log').read_text()
assert '0 errors' in build and '4 page(s) built' in build and 'PASS_PRIVATE_STATIC_ONLY' in build
assert 'tests 30' in tests and 'pass 30' in tests and 'fail 0' in tests and 'Ran 29 tests' in tests and re.search(r'\nOK\s*$',tests)
log_refs=[]
for p in [E/'build-final.log',E/'tests-final.log',E/'toolchain.json',E/'current-product-binding.json',E/'original-input-integrity.json',E/'browser-and-http-blocker.json',E/'browser-first.log',C/'evidence/static-qa.json']:
 log_refs.append({'path':str(p.relative_to(R)),'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size})
binding={'status':'LOCAL_IMPLEMENTATION_BUILT_STATIC_VERIFIED_BROWSER_BLOCKED','origin':None,'productionEnabled':False,'coreHubLaunchStatus':'NOT_ASSESSED','fullLaunchStatus':'NOT_ASSESSED','previewIndexableCount':0,'reviewedSpecSHA256':static['boundSpecSHA256'],'sourceManifest':source_ref,'outputManifest':output_ref,'sourceTreeSHA256':source['treeSHA256'],'outputTreeSHA256':outputs['treeSHA256'],'sourceCommit':{'branch':'main','sha':'693f53f2d2f802e3cfcf0be3e3ec40efc658a32a','scope':'Parent-reported retained upstream context; this local candidate is not committed and no remote operation occurred.'},'checks':{'typecheck':'0 errors, 0 warnings, 0 hints','build':'4 static HTML files','nodeTests':{'passed':30,'failed':0},'pythonTests':{'passed':29,'failed':0},'staticQa':static['status'],'browser':'BLOCKED_BEFORE_PAGE_OPEN','screenshots':0,'loopbackHTTP':'NOT_VERIFIED; curl exit7/status000','unknownPath404':'NOT_VERIFIED','node22Parity':'NOT_VERIFIED','cleanDependencyInstall':'NOT_RUN','coreProductionGates':'NOT_ASSESSED'},'testSources':test_source,'executionEvidence':log_refs,'counts':{'sourceFiles':len(source['files']),'distFiles':len(outputs['files']),'htmlFiles':len([p for p in outputs['files'] if p['path'].endswith('.html')])}}
dump('test-output-binding.json',binding)
print(json.dumps({k:binding[k] for k in ('status','sourceTreeSHA256','outputTreeSHA256','counts')},indent=2))
