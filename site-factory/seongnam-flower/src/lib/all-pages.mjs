import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import original from '../data/pages.json' with {type:'json'};
import manual from '../data/manual-pages.json' with {type:'json'};
import manualMap from '../data/manual-page-map.json' with {type:'json'};
import originalArchitecture from '../data/architecture.json' with {type:'json'};
import originalManifest from '../data/publish-manifest.json' with {type:'json'};
import originalMap from '../data/page-map.json' with {type:'json'};
export const frozenPages=original,manualPages=manual;
export const hash=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');
export function canonical(v){if(Array.isArray(v))return '['+v.map(canonical).join(',')+']';if(v&&typeof v==='object')return '{'+Object.keys(v).sort().map(k=>JSON.stringify(k)+':'+canonical(v[k])).join(',')+'}';return JSON.stringify(v);}
export const digest=value=>hash(canonical(value));
export function assemble(frozen, authored){
 const rows=[...frozen,...authored],keys=new Set(),urls=new Set();
 for(const p of rows){if(keys.has(p.pageKey)||urls.has(p.url))throw Error('Duplicate active page identity');keys.add(p.pageKey);urls.add(p.url);}
 for(const p of authored){
  if(p.sourceType!=='manual-authored'||p.publicationMode!=='manual-user-request'||!p.revisionId||!p.manualReleaseId)throw Error('Missing manual lineage');
  for(const field of ['snapshotId','snapshotHash','approvalVerified','publishQueueRecordId','sourceRecordId','status'])if(field in p)throw Error('Manual page masquerades as frozen approval');
  const record={...p};delete record.contentSha256;if(digest(record)!==p.contentSha256)throw Error('Manual content hash changed');
 }
 return rows;
}
export const effectiveArchitecture={...originalArchitecture,pages:[...originalArchitecture.pages,...manualMap.pages],hubs:originalArchitecture.hubs.map(h=>({...h,children:[...original,...manual].filter(p=>p.category===h.category).length}))};
export const effectiveManifest={...originalManifest,pages:[...originalManifest.pages,...manualMap.pages]};
export const effectiveMap={...originalMap,pages:[...originalMap.pages,...manualMap.pages]};
// Standard package builds execute from the package root. Astro rebases import.meta.url
// into prerender chunks, so filesystem-backed review evidence must use this stable root.
export function assertProductionReview(packageRoot=process.cwd()) {
 const root=path.resolve(packageRoot);
 const provenance=JSON.parse(fs.readFileSync(path.join(root,'src/data/manual-provenance.json')));
 if(provenance.independentReview.status!=='passed')throw Error('Manual independent review is pending');
 const evidencePath=provenance.independentReview.evidencePath;
 if(typeof evidencePath!=='string'||!/^reviews\/[a-z0-9-]+\.json$/.test(evidencePath))throw Error('Manual independent review evidence is absent or unsafe');
 const evidence=JSON.parse(fs.readFileSync(path.join(root,evidencePath)));
 if(evidence.reviewerId===provenance.authorId||evidence.reviewerId!==provenance.expectedReviewerId||evidence.decision!=='PASS'||evidence.scopeDigest!==provenance.scopeDigest||evidence.visualQa!=='PASS'||evidence.fullBodiesRead!==true)throw Error('Invalid independent manual review');
 if(digest(provenance.scopeFileHashes)!==provenance.scopeDigest)throw Error('Invalid manual scope digest');
 for(const [file,sha] of Object.entries(provenance.scopeFileHashes)){
  if(path.isAbsolute(file)||file.split(/[\\/]/).includes('..'))throw Error('Unsafe manual scope path');
  if(hash(fs.readFileSync(path.join(root,file)))!==sha)throw Error('Reviewed source scope changed: '+file);
 }
 return true;
}
// Direct Astro builds cannot bypass the same pending/reviewed-scope checks.
if(process.env.SITE_INDEXABLE==='true')assertProductionReview();
export default assemble(original,manual);
