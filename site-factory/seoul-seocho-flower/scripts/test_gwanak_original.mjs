/** Original Gwanak grouped assertions, unchanged, run on the current additive dispatcher with original data. */
import fs from 'node:fs';import os from 'node:os';import path from 'node:path';import {spawnSync} from 'node:child_process';import crypto from 'node:crypto';
const source='tests/reference/gwanak-runtime';
for(const f of JSON.parse(fs.readFileSync(source+'/source-inventory.json','utf8')))if(crypto.createHash('sha256').update(fs.readFileSync(source+'/'+f.path)).digest('hex')!==f.sha256)throw new Error('Original Gwanak fixture changed: '+f.path);
const temp=fs.mkdtempSync(path.join(os.tmpdir(),'seocho-gwanak-regression-'));
try{
 fs.cpSync(source,temp,{recursive:true});fs.cpSync('src/lib',temp+'/src/lib',{recursive:true});
 fs.copyFileSync('src/data/seocho-plan-binding.json',temp+'/src/data/seocho-plan-binding.json');
 const run=spawnSync(process.execPath,['--test','tests/gwanak-grouped.test.mjs'],{cwd:temp,stdio:'inherit'});
 if(run.status!==0)throw new Error('Original Gwanak adapter assertions failed against current dispatcher');
}finally{fs.rmSync(temp,{recursive:true,force:true});}
