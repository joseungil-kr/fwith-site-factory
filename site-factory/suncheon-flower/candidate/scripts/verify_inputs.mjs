import fs from 'node:fs';
import {validateRuntime,pageMap} from '../src/lib/suncheon-runtime.mjs';
validateRuntime();
fs.writeFileSync(new URL('../src/data/page-map.json',import.meta.url),JSON.stringify(pageMap,null,2)+'\n');
console.log(JSON.stringify({status:'PASS_REQUIRED_BYTES_PRIVATE_BOUNDARY',origin:null,productionEnabled:false,renderSource:'JSON_ONLY',htmlCount:4}));
