import copyRevision from '../data/customer-copy-revision-20261011.json' with {type:'json'};
import fs from 'node:fs';import path from 'node:path';import crypto from 'node:crypto';import assert from 'node:assert/strict';
const hash=x=>crypto.createHash('sha256').update(x).digest('hex');
export function canonical(v){return JSON.stringify(v,(_,x)=>x&&typeof x==='object'&&!Array.isArray(x)?Object.fromEntries(Object.entries(x).sort(([a],[b])=>a<b?-1:a>b?1:0)):x);}
export function validateCustomerCopyRevision(root='.'){
 const read=f=>JSON.parse(fs.readFileSync(path.join(root,f)));const r=read('src/data/customer-copy-revision-20261011.json');assert.equal(r.revisionId,'seongnam-customer-copy-20261011');assert.equal(r.integrationWriter,'/root/integrate_reviewed_legacy_copy');assert.equal(r.expectedIndependentReviewer,'/root');assert.equal(r.articles.length,30);
 for(const e of [r.history,...r.copyReviewEvidence,...r.surfaces])assert.equal(hash(fs.readFileSync(path.join(root,e.file))),e.sha256,'Reviewed evidence/common copy drift '+e.file);
 const data={'pages.json':read('src/data/pages.json'),'manual-pages.json':read('src/data/manual-pages.json')};
 for(const e of r.articles){const bytes=fs.readFileSync(path.join(root,e.approvedFile));assert.equal(hash(bytes),e.approvedSha256);const approved=JSON.parse(bytes),p=data[e.collection].find(x=>x.pageKey===e.pageKey);assert(p);assert.equal(hash(canonical(p)),e.currentObjectSha256,'Reviewed article drift '+e.pageKey);for(const k of new Set([...Object.keys(p),...Object.keys(approved)]))if(!r.operationalFields.includes(k))assert.deepEqual(p[k],approved[k],'Exact approved copy '+e.pageKey+':'+k);if(e.kind!=='manual'){assert.notEqual(p.snapshotId,p.parentSnapshotId);assert.equal(p.snapshotHash,hash(canonical(Object.fromEntries(Object.entries(approved).filter(([k])=>!r.operationalFields.includes(k))))));}}
 return r;
}

// User-authorized screen-review deferral is explicit evidence, never a visual PASS.
export function assertVisualQa(evidence){
 if(evidence.visualQa==='PASS')return true;
 assert.equal(evidence.visualQa,'DEFERRED_NOT_PASS','Actual rendered-screen review or explicit authorized deferral is required');
 const d=evidence.visualDeferral;assert(d,'Missing visual deferral evidence');
 assert.equal(d.status,'DEFERRED_NOT_PASS');assert.equal(d.criterion,'visualQa');
 assert.equal(d.authorization,'user-requested-batch-deferral');
 assert.equal(d.authorizationReference,"User instruction dated 2026-10-10, restated in scheduled request 2026-10-11T16:00:00Z",'Missing verified visual-deferral authority');
 assert(typeof d.reason==='string'&&d.reason.trim(),'Missing deferral reason');
 assert.deepEqual(d.pendingChecks,['desktop-actual-screen','narrow-actual-screen']);
 assert(Array.isArray(d.pendingPageKeys));assert.equal(new Set(d.pendingPageKeys).size,d.pendingPageKeys.length);
 assert.deepEqual(d.pendingPageKeys.slice().sort(),copyRevision.articles.map(p=>p.pageKey).sort(),'Visual deferral scope differs from exact current articles');
 assert.equal(d.noVisualPassClaim,true);return true;
}
