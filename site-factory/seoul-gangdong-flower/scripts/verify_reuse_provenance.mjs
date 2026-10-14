import {readFileSync,lstatSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
export function verifyReuse(root=new URL('../',import.meta.url)){
 const base=root instanceof URL?root:new URL(`file://${resolve(root)}/`);
 const provenance=JSON.parse(readFileSync(new URL('src/data/template-provenance.json',base),'utf8'));
 const rows=[...provenance.reusedUnchanged.map(r=>({path:r.path,sha256:r.sha256})),...provenance.adaptedFrom.map(r=>({path:r.path,sha256:r.currentSHA256}))];
 if(!rows.length||new Set(rows.map(r=>r.path)).size!==rows.length)throw new Error('Invalid reuse provenance rows');
 for(const row of rows){
  if(row.path.startsWith('/')||row.path.includes('..'))throw new Error('Unsafe reuse provenance path');
  const file=new URL(row.path,base);
  if(!lstatSync(file).isFile()||createHash('sha256').update(readFileSync(file)).digest('hex')!==row.sha256)throw new Error(`Stale reuse provenance: ${row.path}`);
 }
 return {unchanged:provenance.reusedUnchanged.length,adapted:provenance.adaptedFrom.length};
}
