#!/usr/bin/env python3
"""Bind actual local sources, original bytes, outputs and completed test logs."""
from pathlib import Path
import hashlib,json,re,datetime,difflib
from qa_yeosu import check,C,W
R=C.parent;E=R/'evidence'
sha=lambda b:hashlib.sha256(b).hexdigest()
def dump(name,data):
 p=E/name;p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n');return {'path':str(p.relative_to(R)),'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())}
def tree(root,excluded=()):
 files=[]
 for p in sorted(root.rglob('*')):
  rel=p.relative_to(root)
  if p.is_file() and not p.is_symlink() and not any(part in excluded for part in rel.parts):files.append({'path':rel.as_posix(),'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())})
 return {'algorithm':'sha256(sorted sha256 + two spaces + POSIX path + LF)','treeSHA256':sha(''.join(f"{x['sha256']}  {x['path']}\n" for x in files).encode()),'files':files}
static=check();baseline=json.loads((E/'original-input-baseline.json').read_text());changed=[]
for item in baseline:
 p=W/item['path']
 if not p.is_file() or p.stat().st_size!=item['bytes'] or sha(p.read_bytes())!=item['sha256']:changed.append(item['path'])
assert not changed,changed
original=dump('original-input-integrity.json',{'checkedFileCount':len(baseline),'changedFiles':changed,'baselineSHA256':sha((E/'original-input-baseline.json').read_bytes()),'sourceDirectories':['yeosu-customer-copy-20261014','yeosu-page-spec-addendum-20261015','yeosu-research-preparation-20261014','mokpo-local-implementation-20261015']})
build=(E/'build-final.log').read_text();tests=(E/'tests-final.log').read_text()
assert '0 errors' in build and '0 warnings' in build and '4 page(s) built' in build and 'PASS_PRIVATE_STATIC_ONLY' in build
assert re.search(r'tests 34\b',tests) and re.search(r'pass 34\b',tests) and re.search(r'fail 0\b',tests)
python=re.search(r'Ran (\d+) tests',tests);assert python and re.search(r'^OK\s*$',tests,re.M) and 'FAILED (' not in tests
# Evidence diff is a local comparison, not a claim of Git changes or original deletions.
T=W/'mokpo-local-implementation-20261015/candidate';diff=''
for rel in ['astro.config.mjs','package.json','src/components/CopyPage.astro','src/components/DraftBlocks.astro','src/components/SharedFlowerBanner.astro','src/layouts/BaseLayout.astro']:
 diff+=''.join(difflib.unified_diff((T/rel).read_text().splitlines(True),(C/rel).read_text().splitlines(True),fromfile='approved-template/'+rel,tofile='yeosu-candidate/'+rel))
for rel in ['src/lib/yeosu-runtime.mjs','src/components/InlineCopy.astro','src/styles/yeosu.css','scripts/qa_yeosu.py','scripts/test_yeosu.py','tests/yeosu-runtime.test.mjs']:
 diff+=''.join(difflib.unified_diff([],(C/rel).read_text().splitlines(True),fromfile='/dev/null',tofile='yeosu-candidate/'+rel))
(E/'local-code.diff').write_text(diff)
source=tree(C,('node_modules','dist','.astro','evidence','__pycache__'));output=tree(C/'dist')
sourceRef=dump('source-manifest.json',source);outputRef=dump('output-manifest.json',output)
logs=[]
for p in [E/'build-final.log',E/'tests-final.log',E/'toolchain.json',E/'verification-limitations.json',E/'failure-recovery.json',E/'local-code.diff',C/'evidence/static-qa.json']:
 logs.append({'path':str(p.relative_to(R)),'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size})
binding={'status':'IMPLEMENTED_BUILT_AND_STATIC_VERIFIED_ONLY','createdUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sourceTreeSHA256':source['treeSHA256'],'outputTreeSHA256':output['treeSHA256'],'sourceManifest':sourceRef,'outputManifest':outputRef,'originalIntegrity':original,'sourceCommit':None,'remoteWritesPerformed':False,'origin':None,'productionEnabled':False,'specSHA256':static['specSHA256'],'checks':{'typecheck':'0 errors, 0 warnings, 0 hints','staticHTML':4,'nodeTests':34,'pythonTests':int(python[1]),'staticQA':static['status'],'browser':'NOT_RETRIED_PRIOR_DENIAL','http404':'NOT_VERIFIED','publicHTTP':'NOT_RUN','productionLaunch':'NOT_ASSESSED'},'counts':{'sourceFiles':len(source['files']),'outputFiles':len(output['files']),'HTML':4,'homeProducts':0,'articleProducts':4,'articleFAQPairs':3,'primaryBannersEach':3,'supportChildren':1,'sitemapURLs':0},'executionEvidence':logs}
dump('test-output-binding.json',binding)
print(json.dumps({k:binding[k] for k in ['status','sourceTreeSHA256','outputTreeSHA256','counts','checks']},indent=2))
