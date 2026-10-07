import test from 'node:test';
import assert from 'node:assert/strict';
import {assertIndependentReview,assertScopeFiles} from '../src/lib/manual-review-contract.mjs';
const author='11111111-1111-4111-8111-111111111111',reviewer='22222222-2222-4222-8222-222222222222';
const p={authorId:author,expectedReviewerId:reviewer,releaseId:'fixture-only',scopeDigest:'scope',manualPagesSha256:'pages',manualRevisionsSha256:'addenda',independentReview:{status:'passed',reviewerId:reviewer,evidenceSha256:'evidence'}};
const e={authorId:author,reviewerId:reviewer,releaseId:'fixture-only',scopeDigest:'scope',manualPagesSha256:'pages',manualRevisionsSha256:'addenda',decision:'PASS',fullBodiesRead:true,contentQa:'PASS',codeQa:'PASS',catalogAndAssetsQa:'PASS',visualQa:'PASS',reviewedAt:'2026-10-07T00:00:00Z'};
test('same writer/reviewer cannot pass with otherwise correct hashes',()=>{const x=structuredClone(p),y=structuredClone(e);x.expectedReviewerId=author;x.independentReview.reviewerId=author;y.reviewerId=author;assert.throws(()=>assertIndependentReview(x,y,'evidence'),/Writer/);});
test('missing actual evidence or wrong reviewer fails',()=>{assert.throws(()=>assertIndependentReview(p,{},'evidence'));assert.throws(()=>assertIndependentReview(p,{...e,reviewerId:author},'evidence'));});
test('changed content code asset catalog scope or review file fails',()=>{for(const key of ['scopeDigest','manualPagesSha256','manualRevisionsSha256'])assert.throws(()=>assertIndependentReview(p,{...e,[key]:'changed'},'evidence'));assert.throws(()=>assertIndependentReview(p,e,'tampered'));});
test('pending partial and nonvisual review cannot authorize production',()=>{for(const changes of [{decision:'REVISE'},{fullBodiesRead:false},{visualQa:'UNVERIFIED'},{catalogAndAssetsQa:'pending'}])assert.throws(()=>assertIndependentReview(p,{...e,...changes},'evidence'));const q=structuredClone(p);q.independentReview.status='pending';assert.throws(()=>assertIndependentReview(q,e,'evidence'));});
test('complete independently bound fixture is accepted only when every requirement holds',()=>{assert.equal(assertIndependentReview(p,e,'evidence'),true);});

test('code product-catalog and asset bytes are validated against the exact scope',()=>{const files={'src/lib/catalog.mjs':'code','src/data/products.json':'catalog','public/images/a.jpg':'asset'};assert.equal(assertScopeFiles(files,f=>files[f]),true);for(const target of Object.keys(files))assert.throws(()=>assertScopeFiles(files,f=>f===target?'changed':files[f]),/scope changed/);});
