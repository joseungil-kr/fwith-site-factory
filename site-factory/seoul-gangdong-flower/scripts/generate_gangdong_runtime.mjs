import {readFileSync,writeFileSync} from 'node:fs';
import {generateRuntime} from '../src/lib/gangdong-runtime.mjs';
const root=new URL('../',import.meta.url);const data=JSON.stringify(generateRuntime(root),null,2)+'\n';const target=new URL('src/data/gangdong-runtime.json',root);
if(process.argv.includes('--check')){if(readFileSync(target,'utf8')!==data)throw new Error('Generated runtime is stale');console.log('Exact frozen Gangdong projection verified');}else{writeFileSync(target,data);console.log('Generated exact Gangdong local runtime');}
