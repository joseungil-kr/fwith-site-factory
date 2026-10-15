import {validateRuntime,pageMap} from '../src/lib/mokpo-runtime.mjs';
import fs from 'node:fs';
validateRuntime();
fs.writeFileSync(new URL('../src/data/page-map.json',import.meta.url),JSON.stringify(pageMap,null,2)+'\n');
console.log('Preview boundary verified: origin=null, 4 HTML paths, core/full launch NOT_ASSESSED.');
