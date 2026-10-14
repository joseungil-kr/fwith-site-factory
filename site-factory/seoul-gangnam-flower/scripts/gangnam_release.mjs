// Gangnam-only build contract. No provider access and no historical release_mode import.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
export const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
export const HOSTNAME='seoul-gangnam.fwith.kr', ORIGIN='https://'+HOSTNAME;
export const PREVIEW='https://seoul-gangnam.local.invalid', WORKER='seoul-gangnam-flower-guide';
export const PREDECESSOR='0952966db104f562467d26fdc91ab13c46c0366a';
export const ROUTES=['/','/regions/','/regions/gangnam-funeral-wreath/','/regions/gangnam-wedding-wreath/','/regions/gangnam-event-wreath/'];
export const PROOF={origin:ORIGIN,path:'/39c4ed924bc6084c670a963c26d9f018.txt',sha256:'5da3864d5327c6e4e41e6eef12510004b2302f55c3bc61593d7d49c1797739b5'};
export const COPY_SHA='b442c6ab713453dc4651ea27f1586f777cd5f9915c5b9dd932d6f09da761990b';
export const UI_SHA='5834b9cabf57f394d83ba3744df7691d7b9d6167a95ba8d04aee1a94eeaa5a5a';
const sha=b=>createHash('sha256').update(b).digest('hex');
const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const require=(ok,reason)=>{if(!ok)throw new Error(reason)};
const read=p=>{require(fs.lstatSync(p).isFile()&&!fs.lstatSync(p).isSymbolicLink(),'regular_file_required');return fs.readFileSync(p)};
export function validateBinding(binding,env){
 const expected={schemaVersion:1,state:'approved',repository:'joseungil-kr/fwith-site-factory',sourceRoot:'site-factory/seoul-gangnam-flower',siteKey:'seoul-gangnam-flower-direct',hostname:HOSTNAME,origin:ORIGIN,worker:WORKER,previewSourceRevision:PREDECESSOR,customerCopySha256:COPY_SHA,uiCopySha256:UI_SHA,sourceRevision:env.SITE_FACTORY_REVISION,proof:PROOF,sitemapRoutes:ROUTES,htmlFiles:6,directoryRobots:'index,follow',notFoundStatus:404,publicHttpVerified:false,indexNowSubmitted:false};
 for(const [k,v] of Object.entries(expected))require(same(binding[k],v),'binding_mismatch:'+k);
 require(/^[0-9a-f]{40}$/.test(binding.sourceRevision)&&binding.sourceRevision!==PREDECESSOR,'production_successor_required');
 require(same(binding.approvals,{publication:true,hostBinding:true,indexNowProof:true}),'explicit_approvals_required');
 require(typeof binding.authorizationEvidence==='string'&&/^https:\/\/github\.com\/joseungil-kr\/fwith-site-factory\/blob\/[0-9a-f]{40}\/docs\/direct-seoul-gangnam\/[A-Za-z0-9._-]+\.json$/.test(binding.authorizationEvidence),'auditable_approval_reference_required');
 require(/^[0-9a-f]{64}$/.test(binding.sourceContractSha256||''),'source_contract_digest_required');
 require(Object.keys(binding).sort().join('|')===[...Object.keys(expected),'approvals','authorizationEvidence','sourceContractSha256'].sort().join('|'),'binding_schema_mismatch');
 require(env.SITE_RELEASE_MODE==='production'&&env.SITE_INDEXABLE==='true'&&env.SITE_URL===ORIGIN,'production_environment_mismatch');
 return {mode:'production',indexable:true,origin:ORIGIN,revision:binding.sourceRevision,worker:WORKER};
}
export function resolveGangnamRelease(env=process.env,root=ROOT){
 const config=JSON.parse(read(path.join(root,'src/data/site-config.json')));
 require(config.siteKey==='seoul-gangnam-flower-direct'&&config.previewUrl===PREVIEW,'gangnam_source_identity_required');
 require(config.productionApproved===false&&config.hostnameOwnershipVerified===false&&config.publicHttpVerified===false&&config.indexNowSubmitted===false&&config.worker===null&&config.canonicalHostname===null&&config.sourceCommit===null,'frozen_preview_record_changed');
 require(sha(read(path.join(root,'src/data/gangnam-copy.json')))===COPY_SHA&&sha(read(path.join(root,'src/data/gangnam-ui-copy.json')))===UI_SHA,'approved_copy_bytes_changed');
 const mode=env.SITE_RELEASE_MODE||'preview';
 require(mode==='preview'||mode==='production','unknown_release_mode');
 require(!env.CLOUDFLARE_API_TOKEN&&!env.CLOUDFLARE_ACCOUNT_ID,'provider_credentials_forbidden_during_build');
 if(mode==='preview'){
  require(!env.SITE_INDEXABLE||env.SITE_INDEXABLE==='false','preview_indexing_forbidden');
  require(!env.SITE_URL||env.SITE_URL===PREVIEW,'preview_origin_mismatch');
  require(!env.SITE_RELEASE_BINDING_PATH&&!env.SITE_RELEASE_BINDING_SHA256,'preview_binding_forbidden');
  return {mode,indexable:false,origin:PREVIEW,revision:env.SITE_FACTORY_REVISION||'local',worker:null};
 }
 require(typeof env.SITE_RELEASE_BINDING_PATH==='string'&&path.isAbsolute(env.SITE_RELEASE_BINDING_PATH)&&path.basename(env.SITE_RELEASE_BINDING_PATH)==='production-binding.json','control_binding_path_required');
 const realRoot=fs.realpathSync(root), realBinding=fs.realpathSync(env.SITE_RELEASE_BINDING_PATH);
 require(!realBinding.startsWith(realRoot+path.sep),'source_internal_binding_forbidden');
 const raw=read(env.SITE_RELEASE_BINDING_PATH);
 require(/^[0-9a-f]{64}$/.test(env.SITE_RELEASE_BINDING_SHA256||'')&&sha(raw)===env.SITE_RELEASE_BINDING_SHA256,'binding_digest_mismatch');
 const modeResult=validateBinding(JSON.parse(raw),env);
 const proof=read(path.join(root,'public'+PROOF.path));
 require(sha(proof)===PROOF.sha256&&proof.toString()===path.basename(PROOF.path,'.txt')+'\n','existing_proof_bytes_required');
 return modeResult;
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 const rootIndex=process.argv.indexOf('--root');
 const mode=resolveGangnamRelease(process.env,rootIndex<0?ROOT:path.resolve(process.argv[rootIndex+1]));
 console.log(process.argv.includes('--json')?JSON.stringify(mode):'Gangnam '+mode.mode+' build boundary verified; no publication performed');
}
