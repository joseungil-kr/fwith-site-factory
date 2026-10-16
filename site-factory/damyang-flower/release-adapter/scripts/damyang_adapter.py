"""Offline preparation adapter. Never authorizes, packages or publishes a release.

The original private application and reviewed inputs stay byte-identical.
Inspection output is separate from private dist. Production execution is fail-closed
until a subsequent actual-source/control/runner binding is independently reviewed.
"""
from pathlib import Path
import argparse,hashlib,json,os,re,shutil,subprocess
import damyang_release_output as output
ADAPTER=Path(__file__).resolve().parents[1]
SOURCE=ADAPTER.parent
CANDIDATE=SOURCE/'candidate'
PREVIEW_SHA='local-inspection'
PRIVATE_FILE_COUNT=65 # Set by final local source freeze.
MANIFEST_SHA='33028f8fefb57c023d13eb99869626a0134538019d9e574c3c176bd5ca10baaf'
TREE_SHA='b2ada80b598aa383a4da56bfe547722e5894a0fc9658a3f10d9e0f127a3a5b73'
CONTRACT_SHA='8b62c4bb7ee96c05c7a612c3a24582a7eda26ae380a781221bf8a314ab3e5544'
BOUNDARY=['SITE_ORIGIN','SITE_URL','PUBLIC_SITE_URL','PRODUCTION_ORIGIN','DEPLOY_ENV','DEPLOY_TARGET','ALLOW_PRODUCTION','SITE_RELEASE_MODE','SITE_INDEXABLE','SITE_RELEASE_BINDING_PATH','SITE_RELEASE_BINDING_SHA256','CLOUDFLARE_API_TOKEN','CLOUDFLARE_ACCOUNT_ID','PRODUCTION_APPROVED','OWNERSHIP_VERIFIED','INDEXNOW_ENABLED','PUBLIC_APPROVED']
def require(ok,reason):
 if not ok:raise ValueError(reason)
def sha(data):return hashlib.sha256(data).hexdigest()
def read(p):
 p=Path(p);require(p.is_file() and not p.is_symlink(),'regular_file_required:'+str(p));return p.read_bytes()
def save(p,v):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
IGNORED_PRIVATE_OUTPUTS={'candidate/node_modules','candidate/.astro','candidate/dist','candidate/evidence','candidate/scripts/__pycache__'}
def private_inventory(root):
 root=Path(root);result=set()
 def visit(directory):
  for entry in directory.iterdir():
   rel=entry.relative_to(root).as_posix()
   if rel in IGNORED_PRIVATE_OUTPUTS or rel=='release-adapter':continue
   require(not entry.is_symlink(),'regular_file_required:symlink')
   require(not entry.name.startswith('.'),'hidden_source_forbidden')
   if entry.is_dir():visit(entry)
   elif entry.is_file():result.add(rel)
   else:raise ValueError('regular_file_required:'+str(entry))
 visit(root);return result

def frozen_source(root=SOURCE):
 raw=read(ADAPTER/'release/private-source-manifest.json');require(sha(raw)==MANIFEST_SHA,'frozen_manifest_changed');rows=json.loads(raw)
 require(PRIVATE_FILE_COUNT>0 and len(rows)==PRIVATE_FILE_COUNT and len({r['path'] for r in rows})==PRIVATE_FILE_COUNT,'frozen_denominator_changed')
 require(sha(''.join(f"{r['sha256']}  {r['path']}\n" for r in sorted(rows,key=lambda r:r['path'])).encode())==TREE_SHA,'frozen_tree_changed')
 root=Path(root).resolve()
 for row in rows:
  p=Path(row['path']);require(not p.is_absolute() and not any(part in {'.','..'} or part.startswith('.') for part in p.parts),'unsafe_manifest_path')
  target=root/p;require(target.resolve().is_relative_to(root),'manifest_escape');require(not any(x.is_symlink() for x in [target,*list(target.parents)[:len(p.parts)-1]]),'regular_file_required:symlink_path');raw=read(target)
  require(len(raw)==row['bytes'] and sha(raw)==row['sha256'],'frozen_file_changed:'+str(p))
 require(private_inventory(root)=={r['path'] for r in rows},'unexpected_or_missing_private_source_file')
 require(sha(read(ADAPTER/'release/bounded-contract.json'))==CONTRACT_SHA,'bounded_contract_changed')
 return rows

def private_environment(env=None):
 env=dict(os.environ if env is None else env)
 for name in BOUNDARY:require(not env.get(name),'unexpected_release_or_provider_environment:'+name)
 env['ASTRO_TELEMETRY_DISABLED']='1';return env

def verify_private_dist(dist):
 dist=Path(dist);b=output.baseline();names={p.relative_to(dist).as_posix() for p in dist.rglob('*') if p.is_file()}
 expected=set(b['htmlBodies'])|set(b['staticAssets'])|{'robots.txt','_headers','sitemap.xml'}
 require(names==expected and len(names)==14,'private_output_inventory')
 require(not any(p.is_symlink() for p in dist.rglob('*')),'private_output_symlink')
 for name in b['htmlBodies']:
  raw=read(dist/name);start=raw.find(b'<body');require(start>=0 and sha(raw[start:])==b['htmlBodies'][name] and raw[:start].decode()==b['htmlPrefixes'][name],'private_html_not_exact:'+name)
 for name,digest in b['staticAssets'].items():require(sha(read(dist/name))==digest,'private_asset_changed:'+name)
 for name in ['robots.txt','_headers','sitemap.xml']:require(read(dist/name)==read(CANDIDATE/'public'/name),'private_control_changed:'+name)
 return True

def inspect_output(private_dist,destination):
 frozen_source();private_environment();private_dist=Path(private_dist).resolve();destination=Path(destination).resolve()
 require(not destination.exists(),'inspection_destination_already_exists')
 require(not destination.is_relative_to(SOURCE) and not SOURCE.is_relative_to(destination),'inspection_output_must_be_outside_source')
 verify_private_dist(private_dist)
 shutil.copytree(private_dist,destination)
 for filename,route in output.FILES.items():
  p=destination/filename;raw=p.read_bytes();start=raw.find(b'<body');head=output.transformed_prefix(raw[:start].decode(),route,PREVIEW_SHA).encode();p.write_bytes(head+raw[start:])
 (destination/'robots.txt').write_text('User-agent: *\nAllow: /\nSitemap: '+output.ORIGIN+'/sitemap-index.xml\n')
 (destination/'_headers').write_text('/*\n');(destination/'sitemap.xml').unlink()
 (destination/'sitemap-index.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><sitemap><loc>'+output.ORIGIN+'/sitemap-0.xml</loc></sitemap></sitemapindex>\n')
 (destination/'sitemap-0.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join('<url><loc>'+output.ORIGIN+r+'</loc></url>' for r in output.ROUTES)+'</urlset>\n')
 proof=read(ADAPTER/'release/existing-indexnow-proof.txt');require(sha(proof)==output.PROOF['sha256'] and proof==(Path(output.PROOF['path']).stem+'\n').encode(),'existing_proof_bytes_required');(destination/Path(output.PROOF['path']).name).write_bytes(proof)
 result=output.inspect_dist(destination,dict(mode='offline-inspection',indexable=True,origin=output.ORIGIN,revision=PREVIEW_SHA))
 result.update(state='OFFLINE_METADATA_INSPECTION_ONLY',sourceRevision=None,sourceRevisionRole='pending-real-remote-save; local-inspection marker only',productionBindingUsed=False,productionRunnerExecuted=False,publishableArtifact=False,releaseManifestCreated=False,providerCredentialsUsed=False,publicationExecuted=False,indexNowSubmitted=False)
 frozen_source();return result

def build_private(log_dir):
 frozen_source();env=private_environment();log_dir=Path(log_dir);log_dir.mkdir(parents=True,exist_ok=True)
 for command,name in [(['node','scripts/verify_inputs.mjs'],'verify-inputs.log'),(['node','node_modules/astro/bin/astro.mjs','check'],'typecheck.log'),(['node','node_modules/astro/bin/astro.mjs','build'],'private-build.log'),(['python3','scripts/qa_damyang.py'],'private-qa.log'),(['node','--test','tests/damyang-runtime.test.mjs'],'private-node-tests.log'),(['python3','scripts/test_damyang.py'],'private-python-tests.log')]:
  with (log_dir/name).open('wb') as log:run=subprocess.run(command,cwd=CANDIDATE,env=env,stdout=log,stderr=subprocess.STDOUT)
  require(run.returncode==0,'private_regression_failed:'+name)
 frozen_source();verify_private_dist(CANDIDATE/'dist')

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('mode',choices=['verify-source','inspect','production']);p.add_argument('--destination');p.add_argument('--evidence');args=p.parse_args()
 if args.mode=='production':raise SystemExit('BLOCKED: local preparation only; actual source/control/runner/browser/host approval gates remain pending')
 if args.mode=='verify-source':print(json.dumps({'immutableFiles':len(frozen_source()),'previewSourceRevision':PREVIEW_SHA}));raise SystemExit(0)
 require(args.destination and args.evidence,'inspection_destination_and_evidence_required');build_private(args.evidence);result=inspect_output(CANDIDATE/'dist',args.destination);save(Path(args.evidence)/'inspection-result.json',result);print(json.dumps({k:v for k,v in result.items() if k!='files'},ensure_ascii=False))
