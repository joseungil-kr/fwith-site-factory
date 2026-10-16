import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {validateAuthor,validateReview,validateAssets,assertBoundary,regularRead,author,reviewer,blocks,validateProjectionData} from '../src/lib/gurye-runtime.mjs';
test('nine packaged author files, historical reviews and seven assets bind',()=>{assert.equal(validateAuthor(),9);validateReview();validateAssets();});
test('all production/provider environment flags fail closed',()=>{for(const key of ['SITE_ORIGIN','SITE_URL','PUBLIC_SITE_URL','PRODUCTION_ORIGIN','DEPLOY_ENV','DEPLOY_TARGET','ALLOW_PRODUCTION','SITE_RELEASE_MODE','SITE_INDEXABLE','SITE_RELEASE_BINDING_PATH','SITE_RELEASE_BINDING_SHA','CLOUDFLARE_API_TOKEN','CLOUDFLARE_ACCOUNT_ID','PRODUCTION_APPROVED','OWNERSHIP_VERIFIED','INDEXNOW_ENABLED','PUBLIC_APPROVED'])assert.throws(()=>assertBoundary({[key]:'test-fixture-only'}),/Private-only/);});
test('reject altered author source and path traversal',()=>{const d=fs.mkdtempSync(path.join(os.tmpdir(),'gurye-test-'));try{fs.cpSync(author,d,{recursive:true});fs.appendFileSync(path.join(d,'draft-home.ko.md'),' ');assert.throws(()=>validateAuthor(d),/Bound source changed/);assert.throws(()=>regularRead(author,'../package.json'),/Unsafe/);}finally{fs.rmSync(d,{recursive:true});}});
test('reject altered independent review',()=>{const d=fs.mkdtempSync(path.join(os.tmpdir(),'gurye-review-'));try{fs.cpSync(reviewer,d,{recursive:true});fs.appendFileSync(path.join(d,'R2-RESULT.json'),' ');assert.throws(()=>validateReview(d),/review changed/);}finally{fs.rmSync(d,{recursive:true});}});
test('reject symlinked input files without following them',()=>{const d=fs.mkdtempSync(path.join(os.tmpdir(),'gurye-link-'));try{fs.symlinkSync(path.join(author,'draft-home.ko.md'),path.join(d,'draft.md'));assert.throws(()=>regularRead(d,'draft.md'),/Symlink/);}finally{fs.rmSync(d,{recursive:true});}});
test('renderer preserves paragraph/list transition and refuses embedded headings',()=>{assert.deepEqual(blocks('상담 내용\n- 상품\n- 날짜\n\n연락처'),[{type:'p',text:'상담 내용'},{type:'ul',items:['상품','날짜']},{type:'p',text:'연락처'}]);assert.throws(()=>blocks('### heading'),/Heading/);});

const projected=JSON.parse(fs.readFileSync(path.resolve(author,'../source-projection.json')));
const historical=JSON.parse(fs.readFileSync(path.join(author,'AUTHOR-MANIFEST.json')));
test('projection validates nine included author files and 124 archived references separately',()=>assert.equal(validateProjectionData(projected,historical),true));
for(const [name,mutate] of [
 ['archive missing',p=>p.archivedHistoricalEntries.pop()],['archive duplicate',p=>p.archivedHistoricalEntries[1]=p.archivedHistoricalEntries[0]],['archive hash',p=>p.archivedHistoricalEntries[0].sha256='0'.repeat(64)],['archive bytes',p=>p.archivedHistoricalEntries[0].bytes++],['archive claims bytes packaged',p=>p.archivedHistoricalEntries[0].mode='BYTES_VERIFIED'],['included missing',p=>p.packagedAuthorFiles.pop()],['included duplicate',p=>p.packagedAuthorFiles[1]=p.packagedAuthorFiles[0]],['network promoted',p=>p.buildNetworkRequests=true],['raw images promoted',p=>p.rawPolicyImagesPackaged=true],['crops promoted',p=>p.cropImagesPackaged=true],['new binary',p=>p.newBinaryBlobs=1],['customer changes allowed',p=>p.customerOutputChangesAllowed=true],['publication promoted',p=>p.publicationEligible=true],['source revision invented',p=>p.sourceCommit='a'.repeat(40)],['proof invented',p=>p.proof='fixture'],['historical result changed',p=>p.historicalImplementation.independentReviewResultUTF8+=' '],['review manifest changed',p=>p.historicalImplementation.independentReviewManifestSHA256='0'.repeat(64)],['unexpected payload',p=>p.rawImageBase64='not-allowed']
])test('reject reference projection mutation: '+name,()=>{const p=structuredClone(projected);mutate(p);assert.throws(()=>validateProjectionData(p,historical));});
for(const [name,mutate] of [
 ['original URL',p=>p.publicOriginalObservations[0].url='https://example.invalid/fixture'],
 ['original SHA',p=>p.publicOriginalObservations[0].sha256='0'.repeat(64)],
 ['historical GET time',p=>p.publicOriginalObservations[0].archivedAtUTC='2099-01-01T00:00:00Z'],
 ['original bytes',p=>p.publicOriginalObservations[0].bytes++],
 ['policy coordinate',p=>p.policyImageCoordinates[0].coordinateRect[1]++],
 ['policy source hash',p=>p.policyImageCoordinates[0].originalSHA256='0'.repeat(64)],
 ['policy pixel claim',p=>p.policyImageCoordinates[0].decodedPixelsMatchOriginalRectangle=false]
])test('pinned projection byte validation rejects '+name,()=>{
 const d=fs.mkdtempSync(path.join(os.tmpdir(),'gurye-project-'));
 try{const a=path.join(d,'author');fs.cpSync(author,a,{recursive:true});const fixture=structuredClone(projected);mutate(fixture);fs.writeFileSync(path.join(d,'source-projection.json'),JSON.stringify(fixture));assert.throws(()=>validateAuthor(a),/Projection bytes changed/);}
 finally{fs.rmSync(d,{recursive:true});}
});
test('unexpected archived image cannot masquerade as a packaged source',()=>{
 const d=fs.mkdtempSync(path.join(os.tmpdir(),'gurye-extra-'));
 try{const a=path.join(d,'author');fs.cpSync(author,a,{recursive:true});fs.copyFileSync(path.resolve(author,'../source-projection.json'),path.join(d,'source-projection.json'));fs.mkdirSync(path.join(a,'evidence'));fs.writeFileSync(path.join(a,'evidence','fixture.bin'),'non-secret fixture');assert.throws(()=>validateAuthor(a),/Only nine/);}
 finally{fs.rmSync(d,{recursive:true});}
});
