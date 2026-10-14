/** Verify and run unchanged Yeongdeungpo ca5 source contracts in their original fixture. */
import fs from 'node:fs';import path from 'node:path';import {spawnSync} from 'node:child_process';import crypto from 'node:crypto';
const root='tests/reference/yeongdeungpo-runtime';
const inventory=JSON.parse(fs.readFileSync(root+'/source-inventory.json','utf8'));
for(const file of inventory){const b=fs.readFileSync(path.join(root,file.path));if(crypto.createHash('sha256').update(b).digest('hex')!==file.sha256)throw new Error('Original template fixture drift: '+file.path);}
const files=fs.readdirSync(root+'/tests').filter(f=>f.endsWith('.test.mjs')).map(f=>'tests/'+f);
console.log('ORIGINAL YEONGDEUNGPO ca5 TEMPLATE: unchanged120tests, including3historical UI source contracts.');
const run=spawnSync(process.execPath,['--test',...files],{cwd:root,stdio:'inherit'});if(run.status!==0)throw new Error('Original Yeongdeungpo fixture failed');
