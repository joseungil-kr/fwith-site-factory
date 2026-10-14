// Preserve frozen historical provenance and verify explicitly bounded technical successors.
import {readFileSync,lstatSync} from 'node:fs';
import {resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
const SUCCESSOR_PIN='9a96ffe752ba1727d31a20437bbb16be53ecbd6412fe51ba2563cdd3616d208e',HISTORY_PIN='2169b21207d4e4b4957a1f3bb90c4e35511e4db69a572cc741249d01448e67cc';
const sha=b=>createHash('sha256').update(b).digest('hex');
export function verifyReuse(root=new URL('../',import.meta.url)){
 const base=root instanceof URL?root:new URL(`file://${resolve(root)}/`);
 const read=p=>{if(p.startsWith('/')||p.includes('..'))throw new Error('Unsafe reuse provenance path');const f=new URL(p,base);if(!lstatSync(f).isFile()||lstatSync(f).isSymbolicLink())throw new Error('Regular provenance source required');return readFileSync(f)};
 const historical=read('src/data/template-provenance.json'),successor=read('release/successor-provenance.json');
 if(sha(historical)!==HISTORY_PIN||sha(successor)!==SUCCESSOR_PIN)throw new Error('Stale reuse provenance: manifest');
 const provenance=JSON.parse(historical),technical=JSON.parse(successor);
 const transitions=new Map(technical.transitions.map(r=>[r.path,r]));
 if(transitions.size!==technical.transitions.length)throw new Error('Duplicate transition');
 const rows=[...provenance.reusedUnchanged.map(r=>({path:r.path,sha256:r.sha256})),...provenance.adaptedFrom.map(r=>({path:r.path,sha256:r.currentSHA256}))];
 if(!rows.length||new Set(rows.map(r=>r.path)).size!==rows.length)throw new Error('Invalid reuse provenance rows');
 for(const row of rows){
  const bytes=read(row.path),change=transitions.get(row.path);
  if(!change){if(sha(bytes)!==row.sha256)throw new Error(`Stale reuse provenance: ${row.path}`);continue}
  if(change.originalSha256!==row.sha256||sha(bytes)!==change.currentSha256)throw new Error(`Stale reuse provenance: ${row.path}`);
  let restored=bytes.toString();
  for(const part of [...change.transformations].reverse()){if(restored.slice(part.currentStart,part.currentStart+part.replacement.length)!==part.replacement)throw new Error('Transition mismatch');restored=restored.slice(0,part.currentStart)+part.original+restored.slice(part.currentStart+part.replacement.length)}
  if(sha(restored)!==row.sha256)throw new Error('Historical restoration mismatch');
  let applied=restored;
  for(const part of [...change.transformations].reverse()){if(applied.slice(part.originalStart,part.originalStart+part.original.length)!==part.original)throw new Error('Original transition mismatch');applied=applied.slice(0,part.originalStart)+part.replacement+applied.slice(part.originalStart+part.original.length)}
  if(applied!==bytes.toString())throw new Error('Successor reconstruction mismatch');
 }
 if([...transitions.keys()].some(p=>!rows.some(r=>r.path===p)))throw new Error('Unknown legacy transition');
 return {unchanged:rows.length-transitions.size,adapted:transitions.size,historicalRows:rows.length,successorManifestSha256:SUCCESSOR_PIN};
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url))console.log(JSON.stringify(verifyReuse()));
