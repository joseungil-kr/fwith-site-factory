import fs from 'node:fs';
import {pageMap,validateRuntime} from '../src/lib/gokseong-runtime.mjs';
validateRuntime();
fs.writeFileSync('src/data/page-map.json',JSON.stringify(pageMap,null,2)+'\n');
console.log('Verified exact Gokseong five-key copy, original manuscript-only review and seven unchanged customer image inputs; seven historical policy crops are pinned references, not packaged bytes.');
