import crypto from 'node:crypto';
import fs from 'node:fs';
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
// Direct Astro builds also fail closed while independent review is pending.
if(process.env.SITE_INDEXABLE==='true'){
 const provenance=JSON.parse(fs.readFileSync(new URL('../data/manual-provenance.json',import.meta.url)));
 if(provenance.independentReview.status!=='passed')throw Error('Manual independent review is pending');
 if(!provenance.independentReview.evidencePath)throw Error('Manual independent review evidence is absent');
 const evidence=JSON.parse(fs.readFileSync(new URL('../../'+provenance.independentReview.evidencePath,import.meta.url)));
 if(evidence.reviewerId===provenance.authorId||evidence.reviewerId!==provenance.expectedReviewerId||evidence.decision!=='PASS'||evidence.scopeDigest!==provenance.scopeDigest||evidence.visualQa!=='PASS'||evidence.fullBodiesRead!==true)throw Error('Invalid independent manual review');
 for(const [file,sha] of Object.entries(provenance.scopeFileHashes))if(hash(fs.readFileSync(new URL('../../'+file,import.meta.url)))!==sha)throw Error('Reviewed source scope changed: '+file);
}
export default assemble(original,manual);
