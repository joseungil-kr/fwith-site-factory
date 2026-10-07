import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {manualBuildMode,manualDigests,validateManual,digest} from '../src/lib/manual-contract.mjs';
const root=path.resolve(new URL('..',import.meta.url).pathname);
const preview={MANUAL_PREVIEW:'1',SITE_INDEXABLE:'false',SITE_URL:'http://127.0.0.1:8934'};
const read=(r,p)=>JSON.parse(fs.readFileSync(path.join(r,p),'utf8'));
const write=(r,p,x)=>fs.writeFileSync(path.join(r,p),JSON.stringify(x,null,2)+'\n');
function refresh(r){const p=read(r,'src/data/manual-provenance.json');Object.assign(p,Object.fromEntries(Object.entries(manualDigests(r)).filter(([k])=>k.endsWith('Hash'))));write(r,'src/data/manual-provenance.json',p);return p;}
function fixture(fn){const r=fs.mkdtempSync(path.join(os.tmpdir(),'ansan-manual-contract-'));try{for(const d of ['src','scripts','tests','public'])fs.cpSync(path.join(root,d),path.join(r,d),{recursive:true});for(const f of ['package.json','astro.config.mjs'])fs.copyFileSync(path.join(root,f),path.join(r,f));return fn(r);}finally{fs.rmSync(r,{recursive:true,force:true});}}
function receipt(r,overrides={}){const p=refresh(r),reviewerId=p.expectedReviewerId;const proof={kind:'independent-manual-content-review',status:'approved',reviewerId,writerId:p.writerId,checkedCustomerFields:true,checkedSources:true,checkedRenderer:true,...Object.fromEntries(Object.entries(p).filter(([k])=>k.endsWith('Hash'))),pageIds:read(r,'src/data/manual-page-map.json').pages.map(p=>p.pageKey),...overrides};write(r,'src/data/manual-review-evidence.json',proof);const review={...proof,reviewedAt:'2026-10-07T00:00:00Z',evidenceFile:'src/data/manual-review-evidence.json',evidenceSha256:digest(fs.readFileSync(path.join(r,'src/data/manual-review-evidence.json')))};write(r,'src/data/manual-review.json',review);return {proof,review};}
test('pending manual candidates render only through explicit local noindex preview',()=>{assert.equal(validateManual(root,preview).pages.length,20);assert.throws(()=>validateManual(root,{}),/pending/);});
for(const env of [{SITE_INDEXABLE:'false'},{SITE_URL:'https://ansan.fwith.kr',SITE_INDEXABLE:'false'},{SITE_URL:'http://localhost:8934',SITE_INDEXABLE:'false'},{MANUAL_PUBLISH:'true'}])test('no environment flag turns an unreviewed production target into approval '+JSON.stringify(env),()=>assert.throws(()=>validateManual(root,env),/pending/));
for(const SITE_URL of ['https://ansan.fwith.kr','http://localhost.example.com','https://127.0.0.1:8934','http://user:pass@localhost:8934'])test('preview rejects nonlocal or ambiguous target '+SITE_URL,()=>assert.throws(()=>manualBuildMode({...preview,SITE_URL}),/preview/));
test('exact independent fixture receipt admits production while actual source stays pending',()=>fixture(r=>{receipt(r);assert.equal(validateManual(r,{}).production,true);assert.equal(read(root,'src/data/manual-review.json').status,'pending');}));
test('self-approval is rejected',()=>fixture(r=>{receipt(r,{reviewerId:read(r,'src/data/manual-provenance.json').writerId});assert.throws(()=>validateManual(r,{}),/Writer cannot/);}));
test('partial customer/source/renderer review fails closed',()=>fixture(r=>{receipt(r,{checkedSources:false});assert.throws(()=>validateManual(r,{}),/Incomplete/);}));
test('changed receipt bytes fail independently of declared hashes',()=>fixture(r=>{receipt(r);fs.appendFileSync(path.join(r,'src/data/manual-review-evidence.json'),' ');assert.throws(()=>validateManual(r,{}),/evidence bytes/);}));
test('content drift invalidates review and provenance',()=>fixture(r=>{receipt(r);const f=read(r,'src/data/manual-page-map.json').pages[0].file;fs.appendFileSync(path.join(r,f),'\nChanged customer text.\n');assert.throws(()=>validateManual(r,{}),/contentHash drift/);refresh(r);assert.throws(()=>validateManual(r,{}),/digest drift/);}));
test('catalog or Truth drift invalidates the exact approval',()=>fixture(r=>{receipt(r);const f='src/data/business-truth.json';const truth=read(r,f);truth.phoneOrderHours='different';write(r,f,truth);assert.throws(()=>validateManual(r,{}),/catalogHash drift/);}));
test('renderer code drift invalidates the exact approval',()=>fixture(r=>{receipt(r);fs.appendFileSync(path.join(r,'src/layouts/ArticleLayout.astro'),'\n');assert.throws(()=>validateManual(r,{}),/codeHash drift/);}));
test('manual sources cannot smuggle frozen Factory identifiers',()=>fixture(r=>{const f=read(r,'src/data/manual-page-map.json').pages[0].file;const text=fs.readFileSync(path.join(r,f),'utf8');fs.writeFileSync(path.join(r,f),text.replace('---\n','---\nsnapshotId: "fake"\n'));refresh(r);assert.throws(()=>validateManual(r,preview),/fabricated/);}));
test('manual URLs cannot shadow existing frozen routes',()=>fixture(r=>{const f='src/data/manual-page-map.json',map=read(r,f);map.pages[0].url=read(r,'src/data/publish-manifest.json').pages[0].url;write(r,f,map);refresh(r);assert.throws(()=>validateManual(r,preview),/frozen manual URL/);}));
test('manual nonregional batch cannot bypass geographic scope gate',()=>fixture(r=>{const f='src/data/manual-page-map.json',map=read(r,f);map.pages[0].category='regions';write(r,f,map);refresh(r);assert.throws(()=>validateManual(r,preview),/Regional content/);}));
test('funeral page cannot silently select celebration products',()=>fixture(r=>{const f='src/data/manual-page-map.json',map=read(r,f);map.pages.find(p=>p.category==='funeral').productKeys=['congrats-basic'];write(r,f,map);refresh(r);assert.throws(()=>validateManual(r,preview),/Funeral product/);}));
test('receipt must review exactly the included page set',()=>fixture(r=>{receipt(r,{pageIds:[]});assert.throws(()=>validateManual(r,{}),/scope differs/);}));

test("actual public image bytes are bound to approval",()=>fixture(r=>{receipt(r);fs.appendFileSync(path.join(r,"public/images/products/funeral-basic.webp"),"changed");assert.throws(()=>validateManual(r,{}),/assetHash drift/);}));

test("unknown reviewer label cannot substitute for assigned independent reviewer",()=>fixture(r=>{receipt(r,{reviewerId:"unknown-reviewer"});assert.throws(()=>validateManual(r,{}),/Unrecognized/);}));
