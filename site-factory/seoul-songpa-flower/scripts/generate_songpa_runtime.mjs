import {readFileSync,writeFileSync} from 'node:fs';
import {generateRuntime} from '../src/lib/songpa-runtime.mjs';
const root=new URL('../',import.meta.url);const data=JSON.stringify(generateRuntime(root),null,2)+'\n';const target=new URL('src/data/songpa-runtime.json',root);
if(process.argv.includes('--check')){if(readFileSync(target,'utf8')!==data)throw new Error('Generated runtime is stale');console.log('Exact frozen Songpa projection verified');}else{writeFileSync(target,data);console.log('Generated exact Songpa local runtime');}
