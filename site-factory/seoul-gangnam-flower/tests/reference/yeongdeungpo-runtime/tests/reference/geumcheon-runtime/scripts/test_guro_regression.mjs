/** Run the exact original Guro test suite against current shared adapters, without rewriting N3 expectations. */
import fs from 'node:fs';import os from 'node:os';import path from 'node:path';import {spawnSync} from 'node:child_process';
const root=fs.mkdtempSync(path.join(os.tmpdir(),'geumcheon-guro-regression-'));
try {
 fs.cpSync('tests/reference/guro-runtime',root,{recursive:true});
 fs.cpSync('src/lib',path.join(root,'src/lib'),{recursive:true});fs.copyFileSync('src/data/geumcheon-plan-binding.json',path.join(root,'src/data/geumcheon-plan-binding.json'));
 const files=fs.readdirSync(path.join(root,'tests')).filter(f=>f.endsWith('.test.mjs')).map(f=>'tests/'+f);
 const test=spawnSync(process.execPath,['--test',...files],{cwd:root,stdio:'inherit'});if(test.status!==0)throw new Error('Original Guro regression failed');
}finally {fs.rmSync(root,{recursive:true,force:true});}
