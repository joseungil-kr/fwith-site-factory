import test from 'node:test';
import assert from 'node:assert/strict';
import {spawnSync} from 'node:child_process';
test('Gwanak release boundary and sitemap contracts pass offline synthetic negative tests',()=>{
 const result=spawnSync('python3',['scripts/test_release_mode.py'],{cwd:new URL('..',import.meta.url),encoding:'utf8'});
 assert.equal(result.status,0,result.stdout+result.stderr);
});
