import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {verifyReuse} from '../scripts/verify_reuse_provenance.mjs';
const root=new URL('../',import.meta.url);
function fixture(){
 const dir=fs.mkdtempSync(path.join(os.tmpdir(),'gangdong-successor-'));
 const historical=JSON.parse(fs.readFileSync(new URL('src/data/template-provenance.json',root),'utf8'));
 for(const row of [...historical.reusedUnchanged,...historical.adaptedFrom,{path:'src/data/template-provenance.json'},{path:'release/successor-provenance.json'}]){
  const target=path.join(dir,row.path);fs.mkdirSync(path.dirname(target),{recursive:true});fs.copyFileSync(new URL(row.path,root),target);
 }
 return dir;
}
test('exact reversible technical transitions preserve all historical provenance rows',()=>{
 const result=verifyReuse(root);assert.equal(result.historicalRows,47);assert.equal(result.adapted,7);assert.equal(result.unchanged,40);
});
for(const file of ['src/layouts/BaseLayout.astro','src/styles/global.css','release/successor-provenance.json','src/data/template-provenance.json'])test('reject successor mutation '+file,()=>{
 const dir=fixture();try{assert.doesNotThrow(()=>verifyReuse(dir));fs.appendFileSync(path.join(dir,file),' ');assert.throws(()=>verifyReuse(dir),/Stale reuse provenance/);}finally{fs.rmSync(dir,{recursive:true,force:true});}
});
