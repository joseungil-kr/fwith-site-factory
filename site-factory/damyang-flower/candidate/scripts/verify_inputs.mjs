import fs from 'node:fs';
import {pageMap,validateRuntime} from '../src/lib/damyang-runtime.mjs';
validateRuntime();
fs.writeFileSync('src/data/page-map.json',JSON.stringify(pageMap,null,2)+'\n');
console.log('Verified exact Damyang five-key copy, original manuscript-only review and seven image inputs.');
