import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';import crypto from 'node:crypto';import {assertCurrentAmendment,packageAmendment} from '../scripts/banner-native-amendment.mjs';
const raw=fs.readFileSync('tests/fixtures/banner-native-amendment.json');
test('new pending banner amendment fixture is independently pinned',()=>assert.equal(crypto.createHash('sha256').update(raw).digest('hex'),'0a68087ffc0c391e07d832526a76b789d15c97d673f37be5f9c137b3f140065e'));
test('current banner bytes, additions and exact additive QA package transform are bound',()=>assertCurrentAmendment());
test('original package scripts cannot be silently replaced',()=>{let j=JSON.parse(JSON.parse(raw).changed['package.json'].beforeUtf8);j.scripts.build+=' && echo unapproved';assert.notEqual(packageAmendment(JSON.stringify(j)),fs.readFileSync('package.json','utf8'));});
