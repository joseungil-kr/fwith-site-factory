import fs from 'node:fs';
import assert from 'node:assert/strict';
import {sha256} from '../src/lib/mokpo-runtime.mjs';
const root=new URL('../',import.meta.url);
const manifest=JSON.parse(fs.readFileSync(new URL('src/data/reuse-provenance.json',root),'utf8'));
for(const item of manifest){
 const file=fs.readFileSync(new URL(item.destination,root));
 assert.equal(sha256(file),item.destinationSHA256??item.sha256,`Reuse digest mismatch: ${item.destination}`);
 assert.equal(file.length,item.destinationBytes??item.bytes,`Reuse bytes mismatch: ${item.destination}`);
}
const old=JSON.parse(fs.readFileSync(new URL('src/data/frozen/template-package-lock.json',root),'utf8'));
const current=JSON.parse(fs.readFileSync(new URL('package-lock.json',root),'utf8'));
assert.equal(current.name,'flower-direct-static-mokpo-private');assert.equal(current.packages[''].name,current.name);
current.name=old.name;current.packages[''].name=old.packages[''].name;
assert.deepEqual(current,old,'Only two project name fields may change in reused lockfile');
console.log(`Verified ${manifest.length} reused input paths; lockfile dependencies unchanged.`);
