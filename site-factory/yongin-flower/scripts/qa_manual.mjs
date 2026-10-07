import fs from 'node:fs';import crypto from 'node:crypto';
import {effectiveManifest,manual} from '../src/lib/manual-source.mjs';
import {assertManualProductionReady,artifactDigest} from '../src/lib/manual-release-gate.mjs';
const hash=s=>crypto.createHash('sha256').update(s).digest('hex');
assertManualProductionReady();
const architecture=JSON.parse(fs.readFileSync('src/data/architecture.json','utf8'));
const map=JSON.parse(fs.readFileSync('src/data/manual-page-map.json','utf8'));
const intents=JSON.parse(fs.readFileSync('src/data/manual-intents.json','utf8'));
const coverage=JSON.parse(fs.readFileSync('src/data/manual-coverage.json','utf8'));
const urls=new Set(),keys=new Set();
for(const p of effectiveManifest.pages){if(urls.has(p.url)||keys.has(p.pageKey))throw Error('Duplicate active identity');urls.add(p.url);keys.add(p.pageKey);}
for(const p of manual.pages){
 const text=fs.readFileSync(p.file,'utf8');
 if(hash(text)!==p.contentSha256)throw Error('Manual content hash mismatch '+p.pageKey);
 if(p.sourceType!=='manual-authored'||p.status||p.sourceRecordId||p.snapshotId||/^draftStatus:/m.test(text))throw Error('Manual source masquerading as frozen/approved record');
 if(p.originalFile&&hash(fs.readFileSync(p.originalFile))!==p.originalSha256)throw Error('Frozen original changed');
 if(!architecture.pages.some(a=>a.pageKey===p.pageKey&&a.url===p.url))throw Error('Missing architecture');
 if(!map.pages.some(a=>a.pageKey===p.pageKey&&a.revisionId===p.revisionId&&a.contentSha256===p.contentSha256&&a.url===p.url))throw Error('Manual map differs');
 const intent=intents.pages.find(i=>i.pageKey===p.pageKey);
 if(!intent||intent.contentSha256!==p.contentSha256||intent.queryClass!=='local-commercial'||!intent.primaryKeyword||!intent.intentKey||!intent.clusterId||intent.contentRole!=='commercial-landing'||!intent.queryEvidence?.sources?.length)throw Error('Manual intent contract mismatch');
 if(!text.includes('tel:18440644')||!text.includes('https://fwith.co.kr'))throw Error('Missing real order action');
}
if(coverage.places.length!==42||new Set(coverage.places.map(p=>p.name)).size!==42)throw Error('Incomplete crosswalk');
for(const p of coverage.places)if(!urls.has(p.url))throw Error('Crosswalk dead URL');
console.log(JSON.stringify({manualIntegrity:'PASS',manualRows:manual.pages.length,activeArticles:effectiveManifest.pages.length,crosswalkNames:42,localCompleteness:'NOT_CLAIMED',artifactDigest:artifactDigest(),reviewState:JSON.parse(fs.readFileSync('src/data/manual-release-review.json','utf8')).decision}));
