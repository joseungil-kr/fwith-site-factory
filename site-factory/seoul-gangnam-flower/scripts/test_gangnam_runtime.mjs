/** Current generic/Gangnam tests plus unchanged Gwanak adapter assertions in a
 * separate frozen-input fixture. Historical UI regexes are not Gangnam UI evidence.
 */
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {spawnSync} from 'node:child_process';
const excluded=new Set(['gwanak-grouped.test.mjs','gwanak-surface.test.mjs','yeongdeungpo-grouped.test.mjs']);
const historicalOnly=[
 'component receives the independently retained hero answer without raw HTML or CSS changes',
 'source cards use H3 beneath one source-section H2',
 'renderer uses escaped expressions, accessible source links and existing stacked cards',
 // The shared validator deliberately rejects Gangnam's two reviewed HTTP sources.
 // Its frozen-source assertion runs unchanged against the HTTPS-only Gwanak fixture below.
 'every frozen source is retained in reviewed order without mutation'
];
const run=(args,cwd=process.cwd())=>{const result=spawnSync(process.execPath,args,{cwd,stdio:'inherit'});if(result.status!==0)throw new Error('Gangnam native regression failed: '+args.join(' '));};
const files=fs.readdirSync('tests').filter(name=>name.endsWith('.test.mjs')&&!excluded.has(name)).map(name=>'tests/'+name);
console.log('CURRENT GANGNAM: generic algorithms, unchanged adapter compatibility and new frozen Gangnam contract. Historical UI assertions are excluded from this current-UI run.');
run(['--test','--test-skip-pattern='+historicalOnly.join('|'),...files]);
const root=fs.mkdtempSync(path.join(os.tmpdir(),'gangnam-gwanak-regression-'));
try{
 for(const name of ['src/lib','src/data','public'])fs.cpSync(name,path.join(root,name),{recursive:true});
 fs.mkdirSync(path.join(root,'scripts'),{recursive:true});fs.mkdirSync(path.join(root,'tests'),{recursive:true});
 fs.copyFileSync('scripts/generate_gwanak_runtime.mjs',path.join(root,'scripts/generate_gwanak_runtime.mjs'));
 for(const name of ['gwanak-grouped.test.mjs','sources.test.mjs'])fs.copyFileSync('tests/'+name,path.join(root,'tests/'+name));
 const frozen=JSON.parse(fs.readFileSync('src/data/gwanak-plan-binding.json','utf8'));
 for(const [name,value] of [['region-coverage',frozen.coverage],['region-policy',frozen.policy]])fs.writeFileSync(path.join(root,'src/data',name+'.json'),JSON.stringify(value,null,2)+'\n');
 console.log('ORIGINAL GWANAK N2 ADAPTER ASSERTIONS: isolated original frozen plan/copy fixture through the current additive dispatcher; no publication.');
 run(['scripts/generate_gwanak_runtime.mjs'],root);
 run(['--test','--test-skip-pattern=renderer uses escaped expressions, accessible source links and existing stacked cards','tests/gwanak-grouped.test.mjs','tests/sources.test.mjs'],root);
}finally{fs.rmSync(root,{recursive:true,force:true});}
