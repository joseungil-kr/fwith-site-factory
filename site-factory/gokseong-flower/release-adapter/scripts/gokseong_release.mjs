// Separate, fail-closed technical successor. Customer content is preserved; the reference-only input runtime and QA are separately versioned.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {isDeepStrictEqual} from 'node:util';
export const REVIEWED_SPEC_SHA256='d9e4e75f99370c51201bf411f613b58ef1af6aa3be182a10a043741c0fcfb3dd';
function assertBoundary(_config,env){for(const key of ['SITE_ORIGIN','SITE_URL','PUBLIC_SITE_URL','PRODUCTION_ORIGIN','DEPLOY_ENV','DEPLOY_TARGET','ALLOW_PRODUCTION'])if(env[key])throw new Error('Gokseong private boundary: '+key+' must not be set')}
export const ADAPTER_ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
export const SOURCE_ROOT=path.resolve(ADAPTER_ROOT,'..');
export const ROOT=path.join(SOURCE_ROOT,'candidate');
export const HOSTNAME='gokseong.fwith.kr',ORIGIN='https://'+HOSTNAME,WORKER='gokseong-flower-guide';
export const ROUTES=['/'];
export const HTML_ROUTES=['/','/404.html'];
export const PROOF=null; // Dedicated Gokseong verification key requires separate approval and a reviewed successor.
export const EQUIVALENCE_SHA256='c337efd945a3090f5f48ea69c4f79c5866065bfaf7e76fd60c010b154e45338e';
export const PRIVATE_FILE_COUNT=73; // Set by final local source freeze, never inferred during validation.
export const PRIVATE_TREE_SHA='d37ad2fa7bdcedc33dd0a223fc8434e83b404167a07a8e056046c0c58caa3dbb';
export const sha=b=>createHash('sha256').update(b).digest('hex');
export const require=(ok,reason)=>{if(!ok)throw new Error(reason)};
const same=isDeepStrictEqual;
export function read(p){const s=fs.lstatSync(p);require(s.isFile()&&!s.isSymbolicLink(),'regular_file_required');return fs.readFileSync(p)}
export function frozenSource(root=SOURCE_ROOT){
 const raw=read(path.join(ADAPTER_ROOT,'release/private-source-manifest.json')),rows=JSON.parse(raw);
 require(PRIVATE_FILE_COUNT>0&&rows.length===PRIVATE_FILE_COUNT,'frozen_source_denominator');
 const sorted=rows.slice().sort((a,b)=>a.path<b.path?-1:a.path>b.path?1:0).map(r=>`${r.sha256}  ${r.path}\n`).join('');
 require(sha(sorted)===PRIVATE_TREE_SHA,'frozen_manifest_changed');
 require(new Set(rows.map(r=>r.path)).size===PRIVATE_FILE_COUNT,'duplicate_frozen_path');
 for(const row of rows){
  require(typeof row.path==='string'&&(row.path==='SOURCE-SAVE.ko.md'||row.path.startsWith('candidate/')||row.path.startsWith('inputs/'))&&!path.isAbsolute(row.path)&&!row.path.split('/').some(part=>part==='..'||part==='.'||part.startsWith('.')),'unsafe_manifest_path');
  const target=path.join(root,row.path);let cursor=root;for(const part of row.path.split('/')){cursor=path.join(cursor,part);require(!fs.lstatSync(cursor).isSymbolicLink(),'source_symlink_forbidden');}const bytes=read(target);require(sha(bytes)===row.sha256&&bytes.length===row.bytes,'frozen_source_changed:'+row.path);
 }
 const excluded=new Set(['candidate/node_modules','candidate/.astro','candidate/dist','candidate/evidence','candidate/scripts/__pycache__']);const inventory=[];function visit(dir){for(const d of fs.readdirSync(dir,{withFileTypes:true})){const file=path.join(dir,d.name),rel=path.relative(root,file).split(path.sep).join('/');if(excluded.has(rel)||rel==='release-adapter')continue;require(!d.name.startsWith('.')&&!d.isSymbolicLink(),'hidden_or_symlink_source_forbidden');if(d.isDirectory())visit(file);else{require(d.isFile(),'source_regular_file_required');inventory.push(rel);}}}visit(root);require(same(inventory.sort(),rows.map(r=>r.path).sort()),'unexpected_or_missing_private_source_file');
 return true;
}
export function robotsForRoute(route){require(HTML_ROUTES.includes(route),'unknown_html_route');return ROUTES.includes(route)?'index,follow':'noindex,follow'}
export function validateBinding(b,env,contractSha){
 const expected={schemaVersion:1,state:'approved',repository:'joseungil-kr/fwith-site-factory',sourceRoot:'site-factory/gokseong-flower',siteKey:'gokseong-flower-direct',hostname:HOSTNAME,origin:ORIGIN,worker:WORKER,frozenInputSha256:REVIEWED_SPEC_SHA256,frozenPrivateTreeSha256:PRIVATE_TREE_SHA,sourceRevision:env.SITE_FACTORY_REVISION,proof:PROOF,sitemapRoutes:ROUTES,htmlFiles:2,notFoundRobots:'noindex,follow',notFoundStatus:404,publicHttpVerified:false,indexNowSubmitted:false,boundedContractSha256:contractSha,coreHubLaunchStatus:'NOT_ASSESSED',fullLaunchStatus:'NOT_ASSESSED'};
 for(const [k,v] of Object.entries(expected))require(same(b[k],v),'binding_mismatch:'+k);
 require(/^[0-9a-f]{40}$/.test(b.sourceRevision||''),'actual_source_revision_required');
 require(same(b.approvals,{publication:true,hostBinding:true,indexNowProof:true}),'explicit_approvals_required');
 require(typeof b.authorizationEvidence==='string'&&/^https:\/\/github\.com\/joseungil-kr\/fwith-site-factory\/blob\/[0-9a-f]{40}\/docs\/direct-gokseong\/production-authorization-20261016\.json$/.test(b.authorizationEvidence),'auditable_approval_reference_required');
 require(/^[0-9a-f]{64}$/.test(b.sourceContractSha256||''),'source_contract_digest_required');
 require(Object.keys(b).sort().join('|')===[...Object.keys(expected),'approvals','authorizationEvidence','sourceContractSha256'].sort().join('|'),'binding_schema_mismatch');
 require(env.SITE_RELEASE_MODE==='production'&&env.SITE_INDEXABLE==='true'&&env.SITE_URL===ORIGIN,'production_environment_mismatch');
 require(PROOF!==null,'site_specific_indexnow_proof_pending_no_production_mode');
 return {mode:'production',indexable:true,origin:ORIGIN,revision:b.sourceRevision,worker:WORKER};
}
export function resolveGokseongRelease(env=process.env,root=ROOT){
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
 return result;
}
export function privateBuildEnvironment(env=process.env){
 const release=resolveGokseongRelease(env),child={...env};
 // This explicit projection runs the reviewed private build first; it never presents production as private verification.
 for(const key of ['SITE_RELEASE_MODE','SITE_INDEXABLE','SITE_URL','SITE_RELEASE_BINDING_PATH','SITE_RELEASE_BINDING_SHA256','PRODUCTION_APPROVED','OWNERSHIP_VERIFIED','INDEXNOW_ENABLED','PUBLIC_APPROVED'])delete child[key];
 assertBoundary(undefined,child);return {release,env:child};
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url))console.log(JSON.stringify(resolveGokseongRelease()));
