import crypto from 'node:crypto';
import fs from 'node:fs';
import {assertIndependentReview,assertScopeFiles} from './manual-review-contract.mjs';
import provenance from '../data/manual-provenance.json' with {type:'json'};
import original from '../data/pages.json' with {type:'json'};
import manual from '../data/manual-pages.json' with {type:'json'};
import revisions from '../data/manual-revisions.json' with {type:'json'};
export const frozenPages=original;
export const manualPages=manual;
export const manualRevisions=revisions;
export function canonical(value){if(Array.isArray(value))return '['+value.map(canonical).join(',')+']';if(value&&typeof value==='object')return '{'+Object.keys(value).sort().map(k=>JSON.stringify(k)+':'+canonical(value[k])).join(',')+'}';return JSON.stringify(value);}
export function digest(value){return crypto.createHash('sha256').update(canonical(value)).digest('hex');}
export function assemble(original,manual,revisions){
 const keys=new Set(),urls=new Set();
 for(const p of [...original,...manual]){if(keys.has(p.pageKey)||urls.has(p.url))throw new Error('Duplicate content identity');keys.add(p.pageKey);urls.add(p.url);}
 for(const p of manual){if(p.publicationMode!=='manual-user-request'||!p.manualReleaseId||!p.contentRevision)throw new Error('Missing manual provenance');for(const key of ['snapshotId','snapshotHash','approvalVerified','publishQueueRecordId','sourceRecordId'])if(key in p)throw new Error('Manual page claims frozen approval');if(!p.sources?.length||!p.sections?.length||!p.firstAnswer)throw new Error('Incomplete manual content');}
 const revisionKeys=new Set();
 const augmented=original.map(p=>{const r=revisions.find(r=>r.pageKey===p.pageKey);if(!r)return p;if(revisionKeys.has(r.pageKey))throw new Error('Duplicate revision');revisionKeys.add(r.pageKey);if(r.url!==p.url||r.baseContentSha256!==digest(p))throw new Error('Original revision hash mismatch');if(r.sectionsSha256!==digest(r.sectionsToAppend))throw new Error('Addendum digest mismatch');if(!r.revisionId||r.publicationMode!=='manual-user-request')throw new Error('Missing revision provenance');return {...p,manualAddendum:r};});
 if(revisionKeys.size!==revisions.length)throw new Error('Unknown or duplicate revision target');
 return [...augmented,...manual];
}
// The renderer itself enforces the gate, including direct astro builds that omit npm scripts.
if(process.env.SITE_INDEXABLE==='true'){
 const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
 assertScopeFiles(provenance.scopeFileHashes,file=>hash(fs.readFileSync(file)));
 if(digest(provenance.scopeFileHashes)!==provenance.scopeDigest)throw new Error('Invalid release scope');
 const path=provenance.independentReview.evidencePath;
 if(typeof path!=='string'||!/^reviews\/[a-z0-9-]+\.json$/.test(path))throw new Error('Independent evidence missing');
 const bytes=fs.readFileSync(path);assertIndependentReview(provenance,JSON.parse(bytes),hash(bytes));
}
export default assemble(original,manual,revisions);
