import assert from 'node:assert/strict';import crypto from 'node:crypto';import fs from 'node:fs';import path from 'node:path';
export const digest=b=>crypto.createHash('sha256').update(b).digest('hex');
export const releaseDigest=bindings=>digest(JSON.stringify(Object.entries(bindings).sort(([a],[b])=>a.localeCompare(b))));
export const RULE_REVISION='8986a1936615cd0d814b816db7816488e40bacc1';
export const EXPECTED_REVIEWER='supplement-guide-review-89bc7a8013c04401';
export const PINNED_RULE_HASHES={
 'quality/rules/sources/site_factory_query_first_v1_1_test.md':'2a5ccd0a033f832df02f172cc3f09445f03c7d18b44af722264fad275d46488f',
 'quality/rules/sources/site_factory_rules_v1.md':'571e445716658eaf79e9583c54ee1e0c3204cdaa9c400f1eb67dd2816769db3d',
 'quality/rules/sources/site_factory_rules_v1_2.md':'b2d3cb57480c809d22b943b30e83fcd21c8767ff4df109603bc10476b38190ff',
 'quality/rules/COMBINED_RULES.md':'356666a7067218942a115ca8115823b6276d4526f3f8795cbbed8dc7546007bf',
 'quality/rules/PRECEDENCE_AND_COVERAGE.md':'c1663ca7fa0b99a10adf484bfa73ab5a563e9a19aa4a2161d81585c9d1984cd4'
};
export function discoverReleaseFiles(root='.'){
 const out=[];const skip=new Set(['node_modules','dist','.astro','.git']);
 function walk(dir){for(const ent of fs.readdirSync(path.join(root,dir),{withFileTypes:true})){if(skip.has(ent.name))continue;const rel=path.posix.join(dir,ent.name);if(ent.isDirectory()){if(rel==='quality/reviews')continue;walk(rel);}else if(ent.isFile()&&!['src/data/manual-provenance.json','src/data/build-revision.json'].includes(rel))out.push(rel);}}
 walk('');return out.sort();
}
const validDate=d=>typeof d==='string'&&/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/.test(d)&&Number.isFinite(Date.parse(d))&&new Date(d).toISOString()===d&&Date.parse(d)<=Date.now()+300000;
export function validateManualContract(manifest,proof,observed,{preview=false,indexable=false,evidence=null,inventory=null}={}){
 assert.equal(proof.publicationMode,'manual-user-request');assert(proof.writerId,'Missing writer identity');assert.equal(proof.expectedReviewerId,EXPECTED_REVIEWER,'Unexpected reviewer identity');assert.notEqual(proof.writerId,proof.expectedReviewerId,'Writer cannot review');
 assert(proof.bindings&&Object.keys(proof.bindings).length,'Missing file hashes');assert.equal(proof.releaseHash,releaseDigest(proof.bindings),'Release hash drift');assert.equal(manifest.manualReleaseId,proof.manualReleaseId,'Release identity mismatch');
 assert(inventory,'Missing discovered runtime inventory');assert.deepEqual([...inventory].sort(),Object.keys(proof.bindings).sort(),'Unbound or missing runtime files');assert.deepEqual(Object.keys(observed).sort(),Object.keys(proof.bindings).sort(),'Observed inventory mismatch');
 for(const [file,hash] of Object.entries(proof.bindings)){assert.match(hash,/^[a-f0-9]{64}$/,'Invalid file hash');assert.equal(observed[file],hash,'Content/metadata/catalog/asset hash drift: '+file);}
 const discoveredManual=inventory.filter(f=>f.startsWith('src/content/manual-articles/')&&f.endsWith('.md')).sort();assert.deepEqual(discoveredManual,manifest.pages.map(p=>p.file).sort(),'Manual collection inventory mismatch');
 assert.equal(proof.ruleRevision,RULE_REVISION,'Wrong rule revision');for(const [file,hash] of Object.entries(PINNED_RULE_HASHES))assert.equal(proof.ruleHashes?.[file],hash,'Pinned rule hash mismatch');assert(proof.ruleHashes&&Object.keys(proof.ruleHashes).length>=5,'Missing rule hashes');for(const [file,hash]of Object.entries(proof.ruleHashes))assert.equal(proof.bindings[file],hash,'Rule file not bound');
 for(const p of manifest.pages){assert.equal(p.publicationMode,'manual-user-request');assert.match(p.manualPublicationId,/^mp-[a-f0-9]{20}$/);for(const f of ['snapshotId','snapshotHash','sourceDraftKey','sourceRecordId','approvalVerified'])assert.equal(p[f],undefined,'Fabricated frozen provenance');assert(proof.bindings[p.file],'Unbound manual content');}
 if(preview){assert.equal(indexable,false,'Manual preview cannot be indexable');return true;}
 const r=proof.independentReview;assert.equal(r?.status,'approved','Independent review pending');assert(r.reviewerId&&r.reviewerId!==proof.writerId,'Writer cannot approve own content');assert.equal(r.reviewerId,EXPECTED_REVIEWER,'Unexpected reviewer');assert.equal(r.releaseHash,proof.releaseHash,'Review does not bind release');assert(r.evidencePath,'Missing review evidence reference');assert(validDate(r.reviewedAt),'Invalid review date');
 assert(evidence,'Missing independent evidence document');assert.equal(evidence.status,'approved','Evidence not approved');assert.equal(evidence.fullBodiesRead,true,'Full bodies not reviewed');assert.equal(evidence.ruleRevision,RULE_REVISION,'Evidence rule revision mismatch');assert.deepEqual(evidence.ruleHashes,proof.ruleHashes,'Evidence rule hashes mismatch');assert.equal(evidence.reviewedAt,r.reviewedAt,'Review timestamp mismatch');assert(validDate(evidence.reviewedAt),'Invalid evidence date');
 for(const f of ['contentQa','codeQa','catalogAndAssetsQa','visualQa'])assert.equal(evidence[f],'PASS','Release QA incomplete: '+f);
 for(const[k,v]of Object.entries({releaseHash:proof.releaseHash,writerId:proof.writerId,reviewerId:r.reviewerId,manualReleaseId:proof.manualReleaseId}))assert.equal(evidence[k],v,'Evidence mismatch: '+k);
 assert(Array.isArray(evidence.pages),'Missing per-page decisions');assert.deepEqual(evidence.pages.map(p=>p.pageKey).sort(),manifest.pages.map(p=>p.pageKey).sort(),'Per-page inventory mismatch');
 for(const p of manifest.pages){const e=evidence.pages.find(e=>e.pageKey===p.pageKey);assert.equal(e.decision,'PASS','Page not approved: '+p.pageKey);assert.equal(e.fullBodyRead,true,'Page full body not read');assert.equal(e.contentSha256,proof.bindings[p.file],'Page content digest mismatch');assert.equal(e.metadataSha256,digest(JSON.stringify(p)),'Page metadata digest mismatch');}
 assert.equal(digest(JSON.stringify(evidence)),r.evidenceHash,'Evidence hash mismatch');return true;
}
