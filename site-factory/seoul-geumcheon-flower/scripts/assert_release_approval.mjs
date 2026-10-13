import fs from 'node:fs';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const EXPECTED_APPROVAL_SHA='f252c7e631b202c330a25f1f3774734c56b1fad410b326452c5145ba2932c74a';
const APPROVED_ORIGIN='https://seoul-geumcheon.fwith.kr';
export function validateRelease(read) {
 const raw=read('src/data/release-approval.json');
 assert.equal(sha(raw),EXPECTED_APPROVAL_SHA,'Release approval bytes changed');
 const a=JSON.parse(raw),c=JSON.parse(read('src/data/site-config.json')),m=JSON.parse(read('src/data/publish-manifest.json'));
 assert.equal(a.publicationAuthorized,true);assert.equal(a.hostBindingApproved,true,'Host binding approval pending');assert.equal(a.proofFileApproved,true);
 assert.equal(a.publicReleaseVerified,false);assert.equal(c.productionApproved,true);assert.equal(c.hostnameOwnershipVerified,false);
 assert.equal(sha(read('src/data/site-config.json')),a.approvedConfigSha256);assert.equal(sha(read('src/data/publish-manifest.json')),a.candidateManifestSha256);
 assert.equal(sha(read('tests/reference/release-baseline/site-config.json')),a.priorConfigSha256);assert.equal(sha(read('tests/reference/release-baseline/publish-manifest.json')),a.priorManifestSha256);
 assert.equal(sha(read('public/40ce75e866dc2c92254e7d1ad474326f.txt')),a.proofSha256);
 for (const [path,digest] of Object.entries(a.unchangedCustomerContent)) assert.equal(sha(read(path)),digest,path);
 assert.equal(m.directRelease.publicationAuthorized,true);assert.equal(m.directRelease.plannedOriginalCount,a.originalPlanN);assert.deepEqual(m.directRelease.publishedCoverage,a.publishedCoverage);
 return true;
}
export function validateCurrentRelease() {
 if(process.env.SITE_URL)assert.equal(process.env.SITE_URL,APPROVED_ORIGIN,'Production origin override');
 if(process.env.SITE_INDEXABLE==='true')assert.match(process.env.SITE_FACTORY_REVISION||'',/^[0-9a-f]{40}$/,'Exact revision required');
 const read=p=>{const f=new URL('../'+p,import.meta.url);assert.ok(!fs.lstatSync(f).isSymbolicLink(),'Source symlink forbidden');return fs.readFileSync(f);};
 return validateRelease(read);
}
