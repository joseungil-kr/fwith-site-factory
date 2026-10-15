// Separate, fail-closed technical successor. The private runtime and QA are preserved byte-for-byte.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {isDeepStrictEqual} from 'node:util';
const REVIEWED_SPEC_SHA256='b7fd276f969d473b60619cafca6ed160a442fdf5feb36b1bb1addccdaeb96b1f';
function assertBoundary(_config,env){for(const key of ['SITE_ORIGIN','SITE_URL','PUBLIC_SITE_URL','PRODUCTION_ORIGIN','DEPLOY_ENV','DEPLOY_TARGET','ALLOW_PRODUCTION'])if(env[key])throw new Error('Yeosu private boundary: '+key+' must not be set')}
export const ADAPTER_ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
export const SOURCE_ROOT=path.resolve(ADAPTER_ROOT,'..');
export const ROOT=path.join(SOURCE_ROOT,'portable/yeosu-portable-build-inputs-20261015/yeosu-local-implementation-20261015/candidate');
export const HOSTNAME='yeosu.fwith.kr',ORIGIN='https://'+HOSTNAME,WORKER='yeosu-flower-guide';
export const ROUTES=['/','/regions/yeosu-jeonnam-hospital-funeral-wreath/'];
export const HTML_ROUTES=['/','/regions/',ROUTES[1],'/404.html'];
export const PROOF={origin:ORIGIN,path:'/39c4ed924bc6084c670a963c26d9f018.txt',sha256:'5da3864d5327c6e4e41e6eef12510004b2302f55c3bc61593d7d49c1797739b5'};
export const PRIVATE_TREE_SHA='86e99ad5449f1b7aff5338e1e8ce41f6c95b12bba9b295bb4c1e05a5b3ddb336';
export const sha=b=>createHash('sha256').update(b).digest('hex');
export const require=(ok,reason)=>{if(!ok)throw new Error(reason)};
const same=isDeepStrictEqual;
export function read(p){const s=fs.lstatSync(p);require(s.isFile()&&!s.isSymbolicLink(),'regular_file_required');return fs.readFileSync(p)}
export function frozenSource(root=SOURCE_ROOT){
 const raw=read(path.join(ADAPTER_ROOT,'release/private-source-manifest.json')),rows=JSON.parse(raw);
 require(rows.length===75,'frozen_source_denominator');
 const sorted=rows.slice().sort((a,b)=>a.path<b.path?-1:a.path>b.path?1:0).map(r=>`${r.sha256}  ${r.path}\n`).join('');
 require(sha(sorted)===PRIVATE_TREE_SHA,'frozen_manifest_changed');
 require(new Set(rows.map(r=>r.path)).size===75,'duplicate_frozen_path');
 for(const row of rows){
  require(typeof row.path==='string'&&row.path.startsWith('portable/yeosu-portable-build-inputs-20261015/')&&!path.isAbsolute(row.path)&&!row.path.split('/').includes('..'),'unsafe_manifest_path');
  const bytes=read(path.join(root,row.path));require(sha(bytes)===row.sha256&&bytes.length===row.bytes,'frozen_source_changed:'+row.path);
 }
 return true;
}
export function robotsForRoute(route){require(HTML_ROUTES.includes(route),'unknown_html_route');return ROUTES.includes(route)?'index,follow':'noindex,follow'}
export function validateBinding(b,env,contractSha){
 const expected={schemaVersion:1,state:'approved',repository:'joseungil-kr/fwith-site-factory',sourceRoot:'site-factory/yeosu-flower',siteKey:'yeosu-flower-direct',hostname:HOSTNAME,origin:ORIGIN,worker:WORKER,frozenInputSha256:REVIEWED_SPEC_SHA256,frozenPrivateTreeSha256:PRIVATE_TREE_SHA,sourceRevision:env.SITE_FACTORY_REVISION,proof:PROOF,sitemapRoutes:ROUTES,htmlFiles:4,directoryRobots:'noindex,follow',notFoundStatus:404,publicHttpVerified:false,indexNowSubmitted:false,boundedContractSha256:contractSha,coreHubLaunchStatus:'NOT_ASSESSED',fullLaunchStatus:'NOT_ASSESSED'};
 for(const [k,v] of Object.entries(expected))require(same(b[k],v),'binding_mismatch:'+k);
 require(/^[0-9a-f]{40}$/.test(b.sourceRevision||'')&&/^[0-9a-f]{40}$/.test(b.previewSourceRevision||'')&&b.sourceRevision!==b.previewSourceRevision,'production_successor_required');
 require(same(b.approvals,{publication:true,hostBinding:true,indexNowProof:true}),'explicit_approvals_required');
 require(typeof b.authorizationEvidence==='string'&&/^https:\/\/github\.com\/joseungil-kr\/fwith-site-factory\/blob\/[0-9a-f]{40}\/docs\/direct-yeosu\/production-authorization-20261015\.json$/.test(b.authorizationEvidence),'auditable_approval_reference_required');
 require(/^[0-9a-f]{64}$/.test(b.sourceContractSha256||''),'source_contract_digest_required');
 require(Object.keys(b).sort().join('|')===[...Object.keys(expected),'previewSourceRevision','approvals','authorizationEvidence','sourceContractSha256'].sort().join('|'),'binding_schema_mismatch');
 require(env.SITE_RELEASE_MODE==='production'&&env.SITE_INDEXABLE==='true'&&env.SITE_URL===ORIGIN,'production_environment_mismatch');
 return {mode:'production',indexable:true,origin:ORIGIN,revision:b.sourceRevision,worker:WORKER};
}
export function resolveYeosuRelease(env=process.env,root=ROOT){
 frozenSource();
 require(!env.CLOUDFLARE_API_TOKEN&&!env.CLOUDFLARE_ACCOUNT_ID,'provider_credentials_forbidden_during_build');
 for(const key of ['PRODUCTION_APPROVED','OWNERSHIP_VERIFIED','INDEXNOW_ENABLED','PUBLIC_APPROVED'])require(!env[key]||env[key]==='false','unbound_approval_flag:'+key);
 const mode=env.SITE_RELEASE_MODE||'preview';require(['preview','production'].includes(mode),'unknown_release_mode');
 if(mode==='preview'){
  assertBoundary(undefined,env);require(!env.SITE_RELEASE_BINDING_PATH&&!env.SITE_RELEASE_BINDING_SHA256&&(!env.SITE_INDEXABLE||env.SITE_INDEXABLE==='false'),'preview_binding_or_indexing_forbidden');
  return {mode,indexable:false,origin:null,revision:env.SITE_FACTORY_REVISION||'local',worker:null};
 }
 const bindingPath=env.SITE_RELEASE_BINDING_PATH;
 require(typeof bindingPath==='string'&&path.isAbsolute(bindingPath)&&path.basename(bindingPath)==='production-binding.json','control_binding_path_required');
 const realRoot=fs.realpathSync(SOURCE_ROOT),realBinding=fs.realpathSync(bindingPath);
 require(!realBinding.startsWith(realRoot+path.sep),'source_internal_binding_forbidden');
 const raw=read(bindingPath);require(/^[0-9a-f]{64}$/.test(env.SITE_RELEASE_BINDING_SHA256||'')&&sha(raw)===env.SITE_RELEASE_BINDING_SHA256,'binding_digest_mismatch');
 const result=validateBinding(JSON.parse(raw),env,sha(read(path.join(ADAPTER_ROOT,'release/bounded-contract.json'))));
 const proof=read(path.join(ADAPTER_ROOT,'release/existing-indexnow-proof.txt'));
 require(sha(proof)===PROOF.sha256&&proof.toString()===path.basename(PROOF.path,'.txt')+'\n','existing_proof_bytes_required');
 return result;
}
export function privateBuildEnvironment(env=process.env){
 const release=resolveYeosuRelease(env),child={...env};
 // This explicit projection runs the unchanged private build first; it never presents production as private verification.
 for(const key of ['SITE_RELEASE_MODE','SITE_INDEXABLE','SITE_URL','SITE_RELEASE_BINDING_PATH','SITE_RELEASE_BINDING_SHA256'])delete child[key];
 assertBoundary(undefined,child);return {release,env:child};
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url))console.log(JSON.stringify(resolveYeosuRelease()));
