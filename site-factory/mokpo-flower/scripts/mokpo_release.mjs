// Separate, fail-closed technical successor. The private runtime and QA are preserved byte-for-byte.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {isDeepStrictEqual} from 'node:util';
import {assertBoundary,verifyFrozenInputs,REVIEWED_SPEC_SHA256} from '../src/lib/mokpo-runtime.mjs';
export const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
export const HOSTNAME='mokpo.fwith.kr',ORIGIN='https://'+HOSTNAME,WORKER='mokpo-flower-guide';
export const ROUTES=['/','/regions/hankook-hospital-funeral-wreath/'];
export const HTML_ROUTES=['/','/regions/',ROUTES[1],'/404.html'];
export const PROOF={origin:ORIGIN,path:'/39c4ed924bc6084c670a963c26d9f018.txt',sha256:'5da3864d5327c6e4e41e6eef12510004b2302f55c3bc61593d7d49c1797739b5'};
export const PRIVATE_TREE_SHA='271e834444f31e479024764d3ae9f30fbb6816f89a90ce41458a654e31877311';
export const sha=b=>createHash('sha256').update(b).digest('hex');
export const require=(ok,reason)=>{if(!ok)throw new Error(reason)};
const same=isDeepStrictEqual;
export function read(p){const s=fs.lstatSync(p);require(s.isFile()&&!s.isSymbolicLink(),'regular_file_required');return fs.readFileSync(p)}
export function frozenSource(root=ROOT){
 const raw=read(path.join(root,'release/private-source-manifest.json')),rows=JSON.parse(raw);
 require(rows.length===71,'frozen_source_denominator');
 // Canonical byte ordering must agree with the original Python-generated source inventory.
 const sorted=rows.slice().sort((a,b)=>a.path<b.path?-1:a.path>b.path?1:0).map(r=>`${r.sha256}  ${r.path}\n`).join('');
 require(sha(sorted)===PRIVATE_TREE_SHA,'frozen_manifest_changed');
 for(const row of rows){
  require(typeof row.path==='string'&&!path.isAbsolute(row.path)&&!row.path.split('/').includes('..'),'unsafe_manifest_path');
  if(row.path==='package.json')continue;
  const bytes=read(path.join(root,row.path));require(sha(bytes)===row.sha256&&bytes.length===row.bytes,'frozen_source_changed:'+row.path);
 }
 const pkg=JSON.parse(read(path.join(root,'package.json')));
 require(same(pkg,{"dependencies":{"@astrojs/sitemap":"^3.0.0","astro":"^7.3.5"},"devDependencies":{"@astrojs/check":"^0.9.0","typescript":"^5.9.0"},"name":"flower-direct-static-mokpo-private","private":true,"scripts":{"build":"node scripts/build_mokpo_release.mjs","build:private":"node scripts/verify_reuse_provenance.mjs && node scripts/assert_preview_boundary.mjs && astro check && astro build && python3 scripts/qa_mokpo.py","qa":"python3 scripts/qa_mokpo.py","test":"node scripts/verify_reuse_provenance.mjs && node --test tests/*.test.mjs && python3 scripts/test_mokpo.py","test:production":"node --test release-tests/*.test.mjs && python3 scripts/test_mokpo_release_output.py","typecheck":"astro check"},"type":"module"}),'package_contract_changed');
 require(pkg.scripts['build:private']==='node scripts/verify_reuse_provenance.mjs && node scripts/assert_preview_boundary.mjs && astro check && astro build && python3 scripts/qa_mokpo.py','private_build_changed');
 require(pkg.scripts.test==='node scripts/verify_reuse_provenance.mjs && node --test tests/*.test.mjs && python3 scripts/test_mokpo.py','private_tests_changed');
 verifyFrozenInputs();return true;
}
export function robotsForRoute(route){require(HTML_ROUTES.includes(route),'unknown_html_route');return ROUTES.includes(route)?'index,follow':'noindex,follow'}
export function validateBinding(b,env,contractSha){
 const expected={schemaVersion:1,state:'approved',repository:'joseungil-kr/fwith-site-factory',sourceRoot:'site-factory/mokpo-flower',siteKey:'mokpo-flower-direct',hostname:HOSTNAME,origin:ORIGIN,worker:WORKER,frozenInputSha256:REVIEWED_SPEC_SHA256,frozenPrivateTreeSha256:PRIVATE_TREE_SHA,sourceRevision:env.SITE_FACTORY_REVISION,proof:PROOF,sitemapRoutes:ROUTES,htmlFiles:4,directoryRobots:'noindex,follow',notFoundStatus:404,publicHttpVerified:false,indexNowSubmitted:false,boundedContractSha256:contractSha,coreHubLaunchStatus:'NOT_ASSESSED',fullLaunchStatus:'NOT_ASSESSED'};
 for(const [k,v] of Object.entries(expected))require(same(b[k],v),'binding_mismatch:'+k);
 require(/^[0-9a-f]{40}$/.test(b.sourceRevision||'')&&/^[0-9a-f]{40}$/.test(b.previewSourceRevision||'')&&b.sourceRevision!==b.previewSourceRevision,'production_successor_required');
 require(same(b.approvals,{publication:true,hostBinding:true,indexNowProof:true}),'explicit_approvals_required');
 require(typeof b.authorizationEvidence==='string'&&/^https:\/\/github\.com\/joseungil-kr\/fwith-site-factory\/blob\/[0-9a-f]{40}\/docs\/direct-mokpo\/production-authorization-20261015\.json$/.test(b.authorizationEvidence),'auditable_approval_reference_required');
 require(/^[0-9a-f]{64}$/.test(b.sourceContractSha256||''),'source_contract_digest_required');
 require(Object.keys(b).sort().join('|')===[...Object.keys(expected),'previewSourceRevision','approvals','authorizationEvidence','sourceContractSha256'].sort().join('|'),'binding_schema_mismatch');
 require(env.SITE_RELEASE_MODE==='production'&&env.SITE_INDEXABLE==='true'&&env.SITE_URL===ORIGIN,'production_environment_mismatch');
 return {mode:'production',indexable:true,origin:ORIGIN,revision:b.sourceRevision,worker:WORKER};
}
export function resolveMokpoRelease(env=process.env,root=ROOT){
 frozenSource(root);
 require(!env.CLOUDFLARE_API_TOKEN&&!env.CLOUDFLARE_ACCOUNT_ID,'provider_credentials_forbidden_during_build');
 for(const key of ['PRODUCTION_APPROVED','OWNERSHIP_VERIFIED','INDEXNOW_ENABLED','PUBLIC_APPROVED'])require(!env[key]||env[key]==='false','unbound_approval_flag:'+key);
 const mode=env.SITE_RELEASE_MODE||'preview';require(['preview','production'].includes(mode),'unknown_release_mode');
 if(mode==='preview'){
  assertBoundary(undefined,env);require(!env.SITE_RELEASE_BINDING_PATH&&!env.SITE_RELEASE_BINDING_SHA256&&(!env.SITE_INDEXABLE||env.SITE_INDEXABLE==='false'),'preview_binding_or_indexing_forbidden');
  return {mode,indexable:false,origin:null,revision:env.SITE_FACTORY_REVISION||'local',worker:null};
 }
 const bindingPath=env.SITE_RELEASE_BINDING_PATH;
 require(typeof bindingPath==='string'&&path.isAbsolute(bindingPath)&&path.basename(bindingPath)==='production-binding.json','control_binding_path_required');
 const realRoot=fs.realpathSync(root),realBinding=fs.realpathSync(bindingPath);
 require(!realBinding.startsWith(realRoot+path.sep),'source_internal_binding_forbidden');
 const raw=read(bindingPath);require(/^[0-9a-f]{64}$/.test(env.SITE_RELEASE_BINDING_SHA256||'')&&sha(raw)===env.SITE_RELEASE_BINDING_SHA256,'binding_digest_mismatch');
 const result=validateBinding(JSON.parse(raw),env,sha(read(path.join(root,'release/bounded-contract.json'))));
 const proof=read(path.join(root,'release/existing-indexnow-proof.txt'));
 require(sha(proof)===PROOF.sha256&&proof.toString()===path.basename(PROOF.path,'.txt')+'\n','existing_proof_bytes_required');
 return result;
}
export function privateBuildEnvironment(env=process.env){
 const release=resolveMokpoRelease(env),child={...env};
 // This explicit projection runs the unchanged private build first; it never presents production as private verification.
 for(const key of ['SITE_RELEASE_MODE','SITE_INDEXABLE','SITE_URL','SITE_RELEASE_BINDING_PATH','SITE_RELEASE_BINDING_SHA256'])delete child[key];
 assertBoundary(undefined,child);return {release,env:child};
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url))console.log(JSON.stringify(resolveMokpoRelease()));
