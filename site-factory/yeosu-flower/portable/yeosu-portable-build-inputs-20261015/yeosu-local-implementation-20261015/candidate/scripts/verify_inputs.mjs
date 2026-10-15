import fs from 'node:fs';
import {validateRuntime,pageMap,workspace,sha256} from '../src/lib/yeosu-runtime.mjs';
validateRuntime();
const candidate=new URL('../',import.meta.url);
const baseline=JSON.parse(fs.readFileSync(new URL('../../evidence/original-input-baseline.json',import.meta.url)));
for(const b of baseline){const bytes=fs.readFileSync(new URL(b.path,workspace));if(bytes.length!==b.bytes||sha256(bytes)!==b.sha256)throw new Error(`Original input modified: ${b.path}`);}
const reused=JSON.parse(fs.readFileSync(new URL('../src/data/reuse-provenance.json',import.meta.url)));
for(const b of reused){if(b.destination==='package-lock.json'){if(sha256(fs.readFileSync(new URL(b.destination,candidate)))!==b.destinationSHA256||sha256(fs.readFileSync(new URL(b.source,workspace)))!==b.sourceSHA256||b.kind!=='project-name-only-modified')throw new Error('Lockfile provenance mismatch');continue;}if(sha256(fs.readFileSync(new URL(b.destination,candidate)))!==b.sha256||sha256(fs.readFileSync(new URL(b.source,workspace)))!==b.sha256)throw new Error(`Reuse mismatch: ${b.destination}`);}
const a=JSON.parse(fs.readFileSync(new URL('mokpo-local-implementation-20261015/candidate/package-lock.json',workspace)));const b=JSON.parse(fs.readFileSync(new URL('../package-lock.json',import.meta.url)));a.name=b.name;a.packages[''].name=b.packages[''].name;if(JSON.stringify(a)!==JSON.stringify(b))throw new Error('Dependency lock changed beyond project names');
fs.writeFileSync(new URL('../src/data/page-map.json',import.meta.url),JSON.stringify(pageMap,null,2)+'\n');
console.log(JSON.stringify({status:'PASS_INPUT_BYTES_PRIVATE_BOUNDARY',originalFiles:baseline.length,reusedFiles:reused.length,lockVersionsAndIntegrityUnchanged:true,origin:null,productionEnabled:false}));
