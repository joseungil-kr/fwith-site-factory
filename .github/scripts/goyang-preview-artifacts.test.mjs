import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';import os from 'node:os';import path from 'node:path';
import {planParts,partitionEvidence,MAX_RAW_BYTES} from './goyang-preview-artifacts.mjs';
test('146 original captures use fixed eight <=20-image parts',()=>assert.deepEqual(planParts(Array.from({length:146},(_,i)=>({name:`page-${i}.jpg`,bytes:1024}))).map(p=>p.files.length),[20,20,20,20,20,20,20,6]));
test('oversized scope is rejected',()=>assert.throws(()=>planParts(Array.from({length:147},()=>({bytes:1}))),/scope/));
test('oversized part fails without lowering image quality',()=>assert.throws(()=>planParts([{bytes:MAX_RAW_BYTES}]),/cap/));
test('copied artifact image bytes and log separation are exact',()=>{const root=fs.mkdtempSync(path.join(os.tmpdir(),'goyang-part-test-'));try{fs.mkdirSync(path.join(root,'screenshots'));const b=Buffer.from([255,216,4,5,255,217]);fs.writeFileSync(path.join(root,'screenshots/test-desktop.jpg'),b);fs.writeFileSync(path.join(root,'capture-results.json'),'{}');const m=partitionEvidence(root);assert.equal(m.parts[0].files.length,1);assert.deepEqual(fs.readFileSync(path.join(root,'parts/screens-01/screenshots/test-desktop.jpg')),b);assert(!fs.existsSync(path.join(root,'parts/logs/screenshots')));}finally{fs.rmSync(root,{recursive:true,force:true});}});

