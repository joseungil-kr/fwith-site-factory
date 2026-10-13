import fs from 'node:fs';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const EXPECTED_APPROVAL_SHA='0873b3ffcf00bc7f43c07afaf242c3df1e93e19fbbffff539a55a73eedc047f1';
const HISTORICAL_APPROVAL_SHA='655577a5da36019a2c16b9974e3315995870a85d2ce546ade36cee3a0c17d6eb';
const OVERLAY_PATH='src/data/shared-banner-requested-change.json';
const APPROVED_REPLACEMENTS=["public/images/shared-banners/flower-budget.webp", "public/images/shared-banners/flower-consultation.webp", "public/images/shared-banners/flower-message.webp", "src/components/SharedFlowerBanner.astro", "src/data/shared-banner-manifest.json"];
const APPROVED_ORIGIN='https://seoul-dongjak.fwith.kr';
export function validateRelease(read) {
 const raw=read('src/data/release-approval.json');
 assert.equal(sha(raw),EXPECTED_APPROVAL_SHA,'Release approval bytes changed');
 const a=JSON.parse(raw),c=JSON.parse(read('src/data/site-config.json')),m=JSON.parse(read('src/data/publish-manifest.json'));
 assert.equal(a.publicationAuthorized,true);assert.equal(a.hostBindingApproved,true,'Host binding approval pending');assert.equal(a.proofFileApproved,true);
 assert.equal(a.publicReleaseVerified,false);assert.equal(c.productionApproved,true);assert.equal(c.hostnameOwnershipVerified,false);
 assert.equal(sha(read('src/data/site-config.json')),a.approvedConfigSha256);assert.equal(sha(read('src/data/publish-manifest.json')),a.candidateManifestSha256);
 assert.equal(sha(read('tests/reference/release-baseline/site-config.json')),a.priorConfigSha256);assert.equal(sha(read('tests/reference/release-baseline/publish-manifest.json')),a.priorManifestSha256);
 assert.equal(sha(read('public/40ce75e866dc2c92254e7d1ad474326f.txt')),a.proofSha256);
 // Preserve the original content seal and allow only the exact requested five-file overlay.
 assert.equal(a.requestedCustomerContentOverlay.path,OVERLAY_PATH);
 const overlayRaw=read(OVERLAY_PATH);assert.equal(sha(overlayRaw),a.requestedCustomerContentOverlay.sha256,'Requested-change overlay bytes changed');
 const overlay=JSON.parse(overlayRaw);assert.equal(overlay.schemaVersion,1);assert.equal(overlay.changeId,'shared-banner-phone-20261013');
 assert.equal(overlay.sourceRevisionBeforeChange,'bdfb4ae78640a95aa6001581da552a7329fb4775');
 assert.equal(overlay.historicalApproval.path,'tests/reference/release-baseline/release-approval.before-banner-phone.json');
 assert.equal(overlay.historicalApproval.sha256,HISTORICAL_APPROVAL_SHA);
 const historicalRaw=read(overlay.historicalApproval.path);assert.equal(sha(historicalRaw),HISTORICAL_APPROVAL_SHA,'Historical approval seal changed');
 const historical=JSON.parse(historicalRaw);assert.deepEqual(a.unchangedCustomerContent,historical.unchangedCustomerContent,'Historical content map changed');
 assert.deepEqual(Object.keys(overlay.replacements).sort(),APPROVED_REPLACEMENTS,'Requested change scope expanded');
 for(const [path,replacement] of Object.entries(overlay.replacements)){
  assert.equal(replacement.beforeSha256,historical.unchangedCustomerContent[path],'Replacement baseline changed: '+path);
  assert.match(replacement.afterSha256,/^[0-9a-f]{64}$/);assert.notEqual(replacement.beforeSha256,replacement.afterSha256);
 }
 for (const [path,digest] of Object.entries(a.unchangedCustomerContent)) assert.equal(sha(read(path)),overlay.replacements[path]?.afterSha256||digest,path);
 assert.equal(m.directRelease.publicationAuthorized,true);assert.equal(m.directRelease.plannedOriginalCount,a.originalPlanN);assert.deepEqual(m.directRelease.publishedCoverage,a.publishedCoverage);
 return true;
}
export function validateCurrentRelease() {
 if(process.env.SITE_URL)assert.equal(process.env.SITE_URL,APPROVED_ORIGIN,'Production origin override');
 if(process.env.SITE_INDEXABLE==='true')assert.match(process.env.SITE_FACTORY_REVISION||'',/^[0-9a-f]{40}$/,'Exact revision required');
 const read=p=>{const f=new URL('../'+p,import.meta.url);assert.ok(!fs.lstatSync(f).isSymbolicLink(),'Source symlink forbidden');return fs.readFileSync(f);};
 return validateRelease(read);
}
