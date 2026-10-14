import {test} from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {ROOT,HOSTNAME,ORIGIN,PREVIEW,WORKER,PREDECESSOR,ROUTES,PROOF,RUNTIME_SHA,RUNTIME_VALIDATOR_SHA,validateBinding,resolveSongpaRelease} from '../scripts/songpa_release.mjs';
import {INPUT_PIN} from '../src/lib/songpa-runtime.mjs';
const env={SITE_RELEASE_MODE:'production',SITE_INDEXABLE:'true',SITE_URL:ORIGIN,SITE_FACTORY_REVISION:'a'.repeat(40)};
const binding=()=>({schemaVersion:1,state:'approved',repository:'joseungil-kr/fwith-site-factory',sourceRoot:'site-factory/seoul-songpa-flower',siteKey:'seoul-songpa-flower-direct',hostname:HOSTNAME,origin:ORIGIN,worker:WORKER,previewSourceRevision:PREDECESSOR,frozenInputSha256:INPUT_PIN,frozenRuntimeSha256:RUNTIME_SHA,sourceRevision:env.SITE_FACTORY_REVISION,proof:PROOF,sitemapRoutes:ROUTES,htmlFiles:5,directoryRobots:'noindex,follow',notFoundStatus:404,publicHttpVerified:false,indexNowSubmitted:false,approvals:{publication:true,hostBinding:true,indexNowProof:true},authorizationEvidence:'https://github.com/joseungil-kr/fwith-site-factory/blob/'+('b'.repeat(40))+'/docs/direct-seoul-songpa/production-authorization-20261014.json',sourceContractSha256:'c'.repeat(64)});
test('exact Songpa identity and three indexable routes',()=>assert.deepEqual(validateBinding(binding(),env),{mode:'production',indexable:true,origin:ORIGIN,revision:env.SITE_FACTORY_REVISION,worker:WORKER}));
for(const [key,value] of [['worker','seoul-gwanak-flower-guide'],['worker','seoul-seocho-flower-guide'],['hostname','seoul-gwanak.fwith.kr'],['origin','https://seoul-gwanak.fwith.kr'],['siteKey','seoul-gwanak-flower-direct'],['sourceRoot','site-factory/seoul-gwanak-flower'],['sitemapRoutes',['/','/regions/gwanak-funeral-wreath/']],['sitemapRoutes',[...ROUTES,'/regions/']],['directoryRobots','index,follow'],['htmlFiles',6],['sourceRevision',PREDECESSOR],['frozenInputSha256','0'.repeat(64)],['frozenRuntimeSha256','0'.repeat(64)],['publicHttpVerified',true],['indexNowSubmitted',true],['extra',true],['authorizationEvidence','unverified'],['sourceContractSha256','short'],['proof',{...PROOF,origin:'https://seoul-gwanak.fwith.kr'}],['approvals',{publication:true,hostBinding:false,indexNowProof:true}]]){
 test('reject wrong binding '+key+' '+JSON.stringify(value),()=>assert.throws(()=>validateBinding({...binding(),[key]:value},env)));
}
for(const [key,value] of [['SITE_RELEASE_MODE','preview'],['SITE_INDEXABLE','false'],['SITE_URL','https://seoul-gwanak.fwith.kr'],['SITE_FACTORY_REVISION','d'.repeat(40)]])test('reject wrong production environment '+key,()=>assert.throws(()=>validateBinding(binding(),{...env,[key]:value})));
test('default preview remains unpublished',()=>assert.deepEqual(resolveSongpaRelease({}),{mode:'preview',indexable:false,origin:PREVIEW,revision:'local',worker:null}));
for(const bad of [{SITE_INDEXABLE:'true'},{SITE_URL:ORIGIN},{SITE_RELEASE_MODE:'other'},{SITE_RELEASE_BINDING_PATH:'/tmp/production-binding.json'},{CLOUDFLARE_API_TOKEN:'TEST_ONLY'},{CLOUDFLARE_ACCOUNT_ID:'TEST_ONLY'}])test('preview refuses partial activation '+JSON.stringify(bad),()=>assert.throws(()=>resolveSongpaRelease(bad)));
test('production requires exact control binding digest and existing proof',()=>{
 const dir=fs.mkdtempSync(path.join(os.tmpdir(),'songpa-release-'));
 try{const file=path.join(dir,'production-binding.json'),raw=JSON.stringify(binding());fs.writeFileSync(file,raw);const runtime={...env,SITE_RELEASE_BINDING_PATH:file,SITE_RELEASE_BINDING_SHA256:createHash('sha256').update(raw).digest('hex')};assert.equal(resolveSongpaRelease(runtime).worker,WORKER);assert.throws(()=>resolveSongpaRelease({...runtime,SITE_RELEASE_BINDING_SHA256:'0'.repeat(64)}));}finally{fs.rmSync(dir,{recursive:true});}
});
test('frozen runtime mutation is rejected',()=>{
 const dir=fs.mkdtempSync(path.join(os.tmpdir(),'songpa-copy-'));
 try{fs.mkdirSync(path.join(dir,'src/data'),{recursive:true});fs.mkdirSync(path.join(dir,'src/lib'),{recursive:true});for(const name of ['src/data/songpa-runtime.json','src/lib/songpa-runtime.mjs'])fs.copyFileSync(path.join(ROOT,name),path.join(dir,name));fs.appendFileSync(path.join(dir,'src/data/songpa-runtime.json'),' ');assert.throws(()=>resolveSongpaRelease({},dir),/frozen_preview_bytes_changed/);}finally{fs.rmSync(dir,{recursive:true});}
});

test('source-internal control binding is rejected',()=>{
 const dir=fs.mkdtempSync(path.join(ROOT,'.binding-test-'));
 try{const file=path.join(dir,'production-binding.json'),raw=JSON.stringify(binding());fs.writeFileSync(file,raw);assert.throws(()=>resolveSongpaRelease({...env,SITE_RELEASE_BINDING_PATH:file,SITE_RELEASE_BINDING_SHA256:createHash('sha256').update(raw).digest('hex')}),/source_internal_binding_forbidden/);}finally{fs.rmSync(dir,{recursive:true});}
});

test('separate public layer never relaxes the frozen validator',async()=>{const {assertBoundary}=await import('../src/lib/songpa-runtime.mjs');assert.throws(()=>assertBoundary(env));});

test('JSON object field order does not change an exact binding',()=>{const b=binding();b.approvals={hostBinding:true,indexNowProof:true,publication:true};b.proof={sha256:PROOF.sha256,path:PROOF.path,origin:PROOF.origin};assert.equal(validateBinding(b,env).mode,'production');});
