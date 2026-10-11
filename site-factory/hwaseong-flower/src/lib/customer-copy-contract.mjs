import fs from 'node:fs';import path from 'node:path';import crypto from 'node:crypto';import assert from 'node:assert/strict';
const hash=x=>crypto.createHash('sha256').update(x).digest('hex');
export function validateCustomerCopyRevision(root='.'){
 const read=f=>JSON.parse(fs.readFileSync(path.join(root,f)));const r=read('src/data/customer-copy-revision-20261011.json');assert.equal(r.revisionId,'hwaseong-customer-copy-20261011');assert.equal(r.integrationWriter,'/root/integrate_reviewed_legacy_copy');assert.equal(r.expectedIndependentReviewer,'/root');assert.equal(r.articles.length,58);
 for(const e of [r.history,...r.copyReviewEvidence,...r.surfaces])assert.equal(hash(fs.readFileSync(path.join(root,e.file))),e.sha256,'Reviewed evidence/common copy drift '+e.file);
 for(const e of r.articles){const raw=fs.readFileSync(path.join(root,e.file)),text=raw.toString('utf8'),regex=new RegExp('^'+e.identityField+':.*$','m');assert.equal(hash(raw),e.currentFileSha256,'Reviewed article drift '+e.pageKey);assert.equal(hash(text.replace(regex,e.originalIdentityLine)),e.approvedSha256,'Exact approved Markdown drift '+e.pageKey);assert.equal(hash(text.split('---').slice(2).join('---')),e.bodySha256);assert.notEqual(e.currentIdentity,e.parentIdentity);const identity=text.match(regex)?.[0];assert.equal(identity,e.identityField+': '+JSON.stringify(e.currentIdentity));assert.equal(hash(text.replace(new RegExp('^'+e.identityField+':.*\\n','m'),'')),e.normalizedIdentitySha256);}
 return r;
}
