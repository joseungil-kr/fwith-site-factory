// Gangdong-only technical release layer, reused from Songpa production. No provider access.
// Frozen preview projection and its fail-closed validator remain unchanged.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {assertBoundary,validateRuntime,INPUT_PIN,canonical} from '../src/lib/gangdong-runtime.mjs';
export const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
export const HOSTNAME='seoul-gangdong.fwith.kr', ORIGIN='https://'+HOSTNAME;
export const PREVIEW='https://seoul-gangdong.local.invalid', WORKER='seoul-gangdong-flower-guide';
export const PREDECESSOR='9c044584505eec60c71f2bc7add497f0902f5424';
export const ROUTES=['/','/regions/gangdong-condolence-wreath/','/regions/gangdong-wedding-wreath/'];
export const HTML_ROUTES=['/','/regions/',...ROUTES.slice(1),'/404.html'];
export const PROOF={origin:ORIGIN,path:'/39c4ed924bc6084c670a963c26d9f018.txt',sha256:'5da3864d5327c6e4e41e6eef12510004b2302f55c3bc61593d7d49c1797739b5'};
export const RUNTIME_SHA='91de4df55bcafc061c79ca4b02499415ebb79c23e8a9b2a09e9e173df14c5e42';
export const RUNTIME_VALIDATOR_SHA='1daa80415320b88f3b819136bfbcce730efb7dc7ae6f02a0fc60d9ebcc8b6743';
const sha=b=>createHash('sha256').update(b).digest('hex');
const same=(a,b)=>canonical(a)===canonical(b);
const require=(ok,reason)=>{if(!ok)throw new Error(reason)};
const read=p=>{require(fs.lstatSync(p).isFile()&&!fs.lstatSync(p).isSymbolicLink(),'regular_file_required');return fs.readFileSync(p)};
export function robotsForRoute(route,release){
 require(HTML_ROUTES.includes(route),'unknown_html_route');
 return release.mode==='production'?(['/404.html','/regions/'].includes(route)?'noindex,follow':'index,follow'):'noindex,nofollow,noarchive';
}
export function validateBinding(binding,env){
 const expected={schemaVersion:1,state:'approved',repository:'joseungil-kr/fwith-site-factory',sourceRoot:'site-factory/seoul-gangdong-flower',siteKey:'seoul-gangdong-flower-direct',hostname:HOSTNAME,origin:ORIGIN,worker:WORKER,previewSourceRevision:PREDECESSOR,frozenInputSha256:INPUT_PIN,frozenRuntimeSha256:RUNTIME_SHA,sourceRevision:env.SITE_FACTORY_REVISION,proof:PROOF,sitemapRoutes:ROUTES,htmlFiles:5,directoryRobots:'noindex,follow',notFoundStatus:404,publicHttpVerified:false,indexNowSubmitted:false};
 for(const [k,v] of Object.entries(expected))require(same(binding[k],v),'binding_mismatch:'+k);
 require(/^[0-9a-f]{40}$/.test(binding.sourceRevision)&&binding.sourceRevision!==PREDECESSOR,'production_successor_required');
 require(same(binding.approvals,{publication:true,hostBinding:true,indexNowProof:true}),'explicit_approvals_required');
 require(typeof binding.authorizationEvidence==='string'&&/^https:\/\/github\.com\/joseungil-kr\/fwith-site-factory\/blob\/[0-9a-f]{40}\/docs\/direct-seoul-gangdong\/[A-Za-z0-9._-]+\.json$/.test(binding.authorizationEvidence),'auditable_approval_reference_required');
 require(/^[0-9a-f]{64}$/.test(binding.sourceContractSha256||''),'source_contract_digest_required');
 require(Object.keys(binding).sort().join('|')===[...Object.keys(expected),'approvals','authorizationEvidence','sourceContractSha256'].sort().join('|'),'binding_schema_mismatch');
 require(env.SITE_RELEASE_MODE==='production'&&env.SITE_INDEXABLE==='true'&&env.SITE_URL===ORIGIN,'production_environment_mismatch');
 return {mode:'production',indexable:true,origin:ORIGIN,revision:binding.sourceRevision,worker:WORKER};
}
export function resolveGangdongRelease(env=process.env,root=ROOT){
 require(sha(read(path.join(root,'src/data/gangdong-runtime.json')))===RUNTIME_SHA&&sha(read(path.join(root,'src/lib/gangdong-runtime.mjs')))===RUNTIME_VALIDATOR_SHA,'frozen_preview_bytes_changed');
 const runtime=JSON.parse(read(path.join(root,'src/data/gangdong-runtime.json')));
 validateRuntime(runtime,root);
 const intended=runtime.futurePublicContract.routes,presentation=runtime.presentation.paths;
 require(same(presentation,{primary:ROUTES,supportNoindexFollow:['/regions/'],error404:'/404.html'}),'frozen_presentation_mismatch');
 require(intended.length===5&&same(intended.map(r=>r.path),[...ROUTES,'/regions/','/404.html'])&&intended.every(r=>r.productionRobots===(ROUTES.includes(r.path)?'index,follow':'noindex,follow')&&r.inProductionSitemap===ROUTES.includes(r.path)),'frozen_public_contract_mismatch');
 const mode=env.SITE_RELEASE_MODE||'preview';
 require(mode==='preview'||mode==='production','unknown_release_mode');
 require(!env.CLOUDFLARE_API_TOKEN&&!env.CLOUDFLARE_ACCOUNT_ID,'provider_credentials_forbidden_during_build');
 for(const name of ['PRODUCTION_APPROVED','OWNERSHIP_VERIFIED','INDEXNOW_ENABLED','PUBLIC_APPROVED'])require(env[name]==null||env[name]==='false','unbound_approval_flag:'+name);
 if(mode==='preview'){
  assertBoundary(env);
  require(!env.SITE_RELEASE_BINDING_PATH&&!env.SITE_RELEASE_BINDING_SHA256,'preview_binding_forbidden');
  return {mode,indexable:false,origin:PREVIEW,revision:env.SITE_FACTORY_REVISION||'local',worker:null};
 }
 require(typeof env.SITE_RELEASE_BINDING_PATH==='string'&&path.isAbsolute(env.SITE_RELEASE_BINDING_PATH)&&path.basename(env.SITE_RELEASE_BINDING_PATH)==='production-binding.json','control_binding_path_required');
 const realRoot=fs.realpathSync(root),realBinding=fs.realpathSync(env.SITE_RELEASE_BINDING_PATH);
 require(!realBinding.startsWith(realRoot+path.sep),'source_internal_binding_forbidden');
 const raw=read(env.SITE_RELEASE_BINDING_PATH);
 require(/^[0-9a-f]{64}$/.test(env.SITE_RELEASE_BINDING_SHA256||'')&&sha(raw)===env.SITE_RELEASE_BINDING_SHA256,'binding_digest_mismatch');
 const result=validateBinding(JSON.parse(raw),env),proof=read(path.join(root,'public'+PROOF.path));
 require(sha(proof)===PROOF.sha256&&proof.toString()===path.basename(PROOF.path,'.txt')+'\n','existing_proof_bytes_required');
 return result;
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 const rootIndex=process.argv.indexOf('--root');
 const mode=resolveGangdongRelease(process.env,rootIndex<0?ROOT:path.resolve(process.argv[rootIndex+1]));
 console.log(process.argv.includes('--json')?JSON.stringify(mode):'Gangdong '+mode.mode+' build boundary verified; no publication performed');
}
