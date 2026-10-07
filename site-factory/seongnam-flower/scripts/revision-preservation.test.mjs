import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import crypto from 'node:crypto';
const fixture=JSON.parse(fs.readFileSync('src/data/revision-preservation-fixture.json','utf8'));
const baseCommit="06f4049c2c8e818ef7474e628031c5f901b4ecab";
const sha256=b=>crypto.createHash('sha256').update(b).digest('hex');
const gitBlob=b=>crypto.createHash('sha1').update(Buffer.concat([Buffer.from('blob '+b.length+'\0'),b])).digest('hex');
const inventory=()=>{const out=[];function walk(d){for(const e of fs.readdirSync(d||'.',{withFileTypes:true})){if(['node_modules','dist','.astro','.git','__pycache__'].includes(e.name))continue;const f=d?d+'/'+e.name:e.name;if(e.isDirectory())walk(f);else if(e.isFile())out.push(f);}}walk('');return out.sort();};
function verify(overrides={}){
 assert.equal(fixture.baseCommit,baseCommit,'wrong fixture source pin');
 for(const [file,blob] of Object.entries(fixture.baselineGitBlobs)){
  if(fixture.separatelyValidatedBindings.includes(file)||fixture.revisedVerificationFiles.includes(file))continue;
  const bytes=overrides[file]??fs.readFileSync(file);
  if(fixture.approvedRevisionSha256[file])assert.equal(sha256(bytes),fixture.approvedRevisionSha256[file],'approved revision drift: '+file);
  else assert.equal(gitBlob(bytes),blob,'frozen or unrelated source drift: '+file);
 }
 for(const [file,hash] of Object.entries(fixture.approvedRevisionSha256))assert.equal(sha256(overrides[file]??fs.readFileSync(file)),hash,'approved revision drift: '+file);
 const expected=new Set([...Object.keys(fixture.baselineGitBlobs),...fixture.addedFiles,...fixture.separatelyValidatedBindings.filter(f=>fs.existsSync(f))]);
 assert.deepEqual(inventory(),[...expected].sort(),'unreviewed added or deleted source');
}
test('exact pinned baseline preserved outside explicit reviewed revision and separately gated bindings',()=>verify());
test('injected frozen original drift is rejected',()=>{const f=Object.keys(fixture.baselineGitBlobs).find(f=>f.startsWith('src/content/articles/')&&f.endsWith('.md'))||'src/data/pages.json';assert.throws(()=>verify({[f]:Buffer.from('injected original drift')}),/source drift/);});
test('injected unrelated runtime drift is rejected',()=>{const f=Object.keys(fixture.baselineGitBlobs).find(f=>f.startsWith('src/lib/')&&f.endsWith('.mjs'));assert.throws(()=>verify({[f]:Buffer.from('injected runtime drift')}),/source drift/);});
test('approved content revision is exact, not a broad path waiver',()=>{const f=Object.keys(fixture.approvedRevisionSha256).find(f=>f.endsWith('.md'))||'src/data/manual-pages.json';assert.throws(()=>verify({[f]:Buffer.from('injected allowed-path drift')}),/revision drift/);});
