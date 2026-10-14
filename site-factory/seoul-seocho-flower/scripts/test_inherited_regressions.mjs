/** Original regional assertions run unchanged against the additive current dispatcher. */
import fs from 'node:fs';import os from 'node:os';import path from 'node:path';import {spawnSync} from 'node:child_process';
for(const region of ['guro','geumcheon']){
 const root=fs.mkdtempSync(path.join(os.tmpdir(),'yeongdeungpo-'+region+'-regression-'));
 try {
  fs.cpSync('tests/reference/'+region+'-runtime',root,{recursive:true});
  fs.cpSync('src/lib',path.join(root,'src/lib'),{recursive:true});
  for(const name of ['guro-plan-binding','geumcheon-plan-binding','yeongdeungpo-plan-binding','yeongdeungpo-copy','gwanak-plan-binding','seocho-plan-binding'])fs.copyFileSync('src/data/'+name+'.json',path.join(root,'src/data/'+name+'.json'));
  const files=fs.readdirSync(path.join(root,'tests')).filter(f=>f.endsWith('.test.mjs')).map(f=>'tests/'+f);
  console.log('ORIGINAL '+region.toUpperCase()+' ASSERTIONS WITH CURRENT ADDITIVE DISPATCHER');
  const result=spawnSync(process.execPath,['--test',...files],{cwd:root,stdio:'inherit'});if(result.status!==0)throw new Error('Original '+region+' regression failed');
 }finally{fs.rmSync(root,{recursive:true,force:true});}
}
