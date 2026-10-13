// Exact QA-only successor. Historical fixture, tests and helper archive remain sealed.
import fs from 'node:fs';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
const digest=b=>crypto.createHash('sha256').update(b).digest('hex');
export const expectedSuccessorSha256='0c78119522069a313cf7be46e5ac4cb34ea58465c70e4c80fb25245722e1317b';
const raw=fs.readFileSync(new URL('./fixtures/shared-banner-phone-successor.json',import.meta.url));
assert.equal(digest(raw),expectedSuccessorSha256,'Phone successor fixture changed');
export const successor=JSON.parse(raw);
const historicalRaw=fs.readFileSync(new URL('./fixtures/shared-banner-amendment.json',import.meta.url));
assert.equal(digest(historicalRaw),successor.historicalFixtureSha256,'Historical fixture changed');
const historical=JSON.parse(historicalRaw);
assert.equal(digest(fs.readFileSync(new URL('./historical/shared-banner-amendment.original.mjs',import.meta.url))),successor.historicalHelperSha256,'Historical helper archive changed');
const expectedPaths=["public/images/shared-banners/flower-budget.webp", "public/images/shared-banners/flower-consultation.webp", "public/images/shared-banners/flower-message.webp", "scripts/qa_shared_banners.py", "scripts/test_shared_banners.py", "src/components/SharedFlowerBanner.astro", "src/data/shared-banner-manifest.json", "tests/shared-banner-amendment.mjs"];
assert.deepEqual(Object.keys(successor.replacements).sort(),expectedPaths,'Only seven phone paths and the exact successor adapter are permitted');
assert.equal(successor.historicalPinsPreserved,true);assert.equal(successor.productionApprovalGranted,false);
for(const [file,row] of Object.entries(successor.replacements)){assert.equal(row.beforeSha256,historical.additions[file],'Historical addition pin changed');assert.match(row.afterSha256,/^[0-9a-f]{64}$/);assert.notEqual(row.beforeSha256,row.afterSha256);}
export function assertExactPhoneSuccessor(value=successor){assert.deepEqual(value,successor,'Unreviewed phone successor');return true;}
export function currentExpectedSha(file,historicalExpected){
 const row=successor.replacements[file];
 if(!row)return historicalExpected;
 assert.equal(historicalExpected,row.beforeSha256,'Historical pin mismatch for phone successor: '+file);
 return row.afterSha256;
}
export function assertCurrentPhoneBytes(file,bytes,historicalExpected){assert.equal(digest(bytes),currentExpectedSha(file,historicalExpected),'Current phone bytes changed: '+file);return true;}
