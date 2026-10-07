import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import pages,{frozenPages,manualPages,manualRevisions,assemble,digest} from '../src/lib/all-pages.mjs';
const copy=x=>structuredClone(x);
test('manual pages remain distinct from frozen ledger and preserve every original URL',()=>{assert.equal(pages.length,47);assert.equal(frozenPages.length,30);for(const p of frozenPages)assert(pages.some(x=>x.pageKey===p.pageKey&&x.url===p.url));for(const p of manualPages)assert(!('snapshotId' in p));});
test('an addendum cannot silently target changed original content',()=>{const b=copy(frozenPages);b.find(p=>p.pageKey===manualRevisions[0].pageKey).h1+=' changed';assert.throws(()=>assemble(b,manualPages,manualRevisions),/hash mismatch/);});
test('addendum tampering and unknown targets fail closed',()=>{let r=copy(manualRevisions);r[0].sectionsToAppend[0][1]+=' changed';assert.throws(()=>assemble(frozenPages,manualPages,r),/digest mismatch/);r=copy(manualRevisions);r[0].pageKey='unknown';assert.throws(()=>assemble(frozenPages,manualPages,r),/Unknown/);});
test('manual content cannot claim a frozen snapshot or reuse a primary URL',()=>{let m=copy(manualPages);m[0].snapshotId='fake';assert.throws(()=>assemble(frozenPages,m,manualRevisions),/frozen approval/);m=copy(manualPages);m[0].url=frozenPages[0].url;assert.throws(()=>assemble(frozenPages,m,manualRevisions),/Duplicate/);});
test('rendered additions carry their own digest while original sections remain unchanged',()=>{for(const r of manualRevisions){const base=frozenPages.find(p=>p.pageKey===r.pageKey);const effective=pages.find(p=>p.pageKey===r.pageKey);assert.deepEqual(effective.sections,base.sections);assert.equal(digest(base),r.baseContentSha256);const html=fs.readFileSync('dist'+r.url+'index.html','utf8');assert(html.includes('data-manual-revision="'+r.revisionId+'"'));assert(html.includes('data-original-snapshot="'+base.snapshotId+'"'));assert.equal((html.match(/<h1\b/g)||[]).length,1);}});

test('SKKU Seobu-ro2066 campus is Cheoncheon-dong, never inferred from Yulcheon administrative name',()=>{
 const p=manualPages.find(p=>p.slug==='jangan-flower-delivery');
 assert(p.description.includes('천천동 캠퍼스'));assert(p.cardSummary.includes('천천동 캠퍼스'));
 assert(p.sections[0][0].includes('천천동 캠퍼스'));assert(p.sections[0][1].includes('서부로 2066(천천동)'));
 assert(!JSON.stringify(p.sections).includes('율전동 캠퍼스'));
 assert(p.coveredLegalDongs.includes('천천동')&&!p.coveredLegalDongs.includes('율전동'));
 assert(p.sources.some(s=>s.url==='https://ciot.skku.edu/contact'));
 const ledger=JSON.parse(fs.readFileSync('src/data/manual-coverage.json','utf8')).ledger;
 assert.equal(ledger.find(r=>r.legalDong==='천천동').status,'specific_destination_context');
 assert.equal(ledger.find(r=>r.legalDong==='율전동').status,'address_mapping_only_residual');
});
