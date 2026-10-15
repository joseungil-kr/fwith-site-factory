import fs from 'node:fs';
import {pageMap,validateRuntime} from '../src/lib/donggu-runtime.mjs';
validateRuntime();
fs.writeFileSync('src/data/page-map.json',JSON.stringify(pageMap,null,2)+'\n');
console.log('Verified exact final Donggu copy, review and seven image inputs.');
