import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';import crypto from 'node:crypto';
import {fixturePath,assertCurrentBannerAmendment,assertAmendedBytes,applyReviewedAmendment} from './shared-banner-amendment.mjs';
const digest=b=>crypto.createHash('sha256').update(b).digest('hex');
const expectedFixtureSha256='bd30ee96b7c3e5472189bdea753bab2cde8815fe1ba6d0671d6da6bebb4f1934';
const fixture=JSON.parse(fs.readFileSync(fixturePath,'utf8'));
test('banner amendment fixture remains bound to the exact reviewed source and additions',()=>{assert.equal(digest(fs.readFileSync(fixturePath)),expectedFixtureSha256);assertCurrentBannerAmendment();});
test('historical archive and current source tampering both fail instead of refreshing old pins',()=>{
 for(const [file,row] of Object.entries(fixture.files)){
  const correct=Buffer.from(applyReviewedAmendment(file,row.beforeUtf8));assertAmendedBytes(file,correct,row);
  assert.throws(()=>assertAmendedBytes(file,Buffer.concat([correct,Buffer.from('changed')]),row));
  assert.throws(()=>assertAmendedBytes(file,correct,{...row,beforeUtf8:row.beforeUtf8+'changed'}));
  const tampered=Buffer.concat([correct,Buffer.from('changed')]);assert.throws(()=>assertAmendedBytes(file,tampered,{...row,afterSha256:digest(tampered)}),/Non-banner changes/);
 }
});
test('amendment does not claim new content approval or authorize any unrelated source change',()=>{assert.equal(fixture.productionApprovalGranted,false);assert.equal(fixture.historicalPinsPreserved,true);assert.throws(()=>applyReviewedAmendment('src/data/pages.json','{}'),/outside reviewed/);});
