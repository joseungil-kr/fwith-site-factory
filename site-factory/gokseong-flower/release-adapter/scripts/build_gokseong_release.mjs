// Private output regression must complete under the private environment before any transform.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {spawnSync} from 'node:child_process';
import {privateBuildEnvironment,ROOT,ADAPTER_ROOT} from './gokseong_release.mjs';
export function runBuild(selected,spawn=spawnSync,outerEnvironment=process.env){
 for(const key of ['SITE_ORIGIN','SITE_URL','PUBLIC_SITE_URL','PRODUCTION_ORIGIN','DEPLOY_ENV','DEPLOY_TARGET','ALLOW_PRODUCTION','SITE_RELEASE_MODE','SITE_INDEXABLE','SITE_RELEASE_BINDING_PATH','SITE_RELEASE_BINDING_SHA256','CLOUDFLARE_API_TOKEN','CLOUDFLARE_ACCOUNT_ID','PRODUCTION_APPROVED','OWNERSHIP_VERIFIED','INDEXNOW_ENABLED','PUBLIC_APPROVED'])if(selected.env[key])throw new Error('Private regression environment contaminated: '+key);
 const commands=[
  [process.execPath,['scripts/verify_inputs.mjs']],
  [process.execPath,['node_modules/astro/bin/astro.mjs','check']],
  [process.execPath,['node_modules/astro/bin/astro.mjs','build']],
  ['python3',['scripts/qa_gokseong.py']],
  [process.execPath,['--test','tests/gokseong-runtime.test.mjs']],
  ['python3',['scripts/test_gokseong.py']],
  ['python3',[path.join(ADAPTER_ROOT,'scripts/test_gokseong_runner_output.py')]],
  ['python3',[path.join(ADAPTER_ROOT,'scripts/test_gokseong_occurrences.py')]]
 ];
 for(const [bin,args] of commands){const run=spawn(bin,args,{cwd:ROOT,env:selected.env,stdio:'inherit'});if(run.status!==0)throw new Error('Private build/regression failed before transform: '+args.join(' '));}
 if(selected.release.mode==='production'){
  const write=spawn(process.execPath,[path.join(ADAPTER_ROOT,'scripts/write_gokseong_release_files.mjs')],{cwd:ROOT,env:outerEnvironment,stdio:'inherit'});if(write.status!==0)throw new Error('Production head transform failed');
  const qa=spawn('python3',[path.join(ADAPTER_ROOT,'scripts/gokseong_release_output.py'),'--dist','dist','--revision',selected.release.revision],{cwd:ROOT,env:outerEnvironment,stdio:'inherit'});if(qa.status!==0)throw new Error('Production output verification failed');
 }
 return true;
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 const selected=privateBuildEnvironment();fs.mkdirSync(path.join(ROOT,'evidence'),{recursive:true});runBuild(selected);
 console.log('Verified '+selected.release.mode+' build only; public source/ownership/browser/HTTP/receipt gates are separate.');
}
