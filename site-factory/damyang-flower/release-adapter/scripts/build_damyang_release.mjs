import fs from 'node:fs';
import path from 'node:path';
import {spawnSync} from 'node:child_process';
import {privateBuildEnvironment,ROOT,ADAPTER_ROOT} from './damyang_release.mjs';
const selected=privateBuildEnvironment();
fs.mkdirSync(path.join(ROOT,'evidence'),{recursive:true});
for(const [bin,args] of [[process.execPath,['scripts/verify_inputs.mjs']],[process.execPath,['node_modules/astro/bin/astro.mjs','check']],[process.execPath,['node_modules/astro/bin/astro.mjs','build']],['python3',['scripts/qa_damyang.py']]]){
 const run=spawnSync(bin,args,{cwd:ROOT,env:selected.env,stdio:'inherit'});if(run.status!==0)process.exit(run.status??1);
}
if(selected.release.mode==='production'){
 const write=spawnSync(process.execPath,[path.join(ADAPTER_ROOT,'scripts/write_damyang_release_files.mjs')],{cwd:ROOT,env:process.env,stdio:'inherit'});
 if(write.status!==0)process.exit(write.status??1);
 const qa=spawnSync('python3',[path.join(ADAPTER_ROOT,'scripts/damyang_release_output.py'),'--dist','dist','--revision',selected.release.revision],{cwd:ROOT,env:process.env,stdio:'inherit'});
 if(qa.status!==0)process.exit(qa.status??1);
}
console.log('Verified '+selected.release.mode+' build only; production launch/pixels/provider/public HTTP remain separate gates.');
