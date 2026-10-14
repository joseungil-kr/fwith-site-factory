import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {publishedEntriesByUnit} from '../src/lib/directory-links.mjs';
import {groupsFor,coverage} from '../src/lib/regional-runtime.mjs';
const pages=JSON.parse(fs.readFileSync(new URL('../src/data/pages.json',import.meta.url)));
test('same legal dong retains every distinct facility and intent in source order',()=>{
 const entries=publishedEntriesByUnit(groupsFor(pages));
 const magok=entries.get('강서구/법정동/마곡동');
 assert.equal(magok.length,2);
 assert.deepEqual(magok.map(e=>e.page.slug),['magok-dong-ewha-seoul-funeral-wreath','magok-dong-mplus-office-congrats-wreath']);
 for(const admin of coverage.administrativeCrosswalk.filter(a=>a.relations.some(r=>r.unitKey==='강서구/법정동/마곡동'))){
  const targets=admin.relations.flatMap(r=>(entries.get(r.unitKey)||[]).map(e=>e.page.url));
  assert.ok(magok.every(entry=>targets.includes(entry.page.url)));
 }
});
test('repeated group views do not duplicate one URL, and unrepresented units stay empty',()=>{
 const groups=groupsFor(pages),entries=publishedEntriesByUnit([...groups,...groups]);
 assert.equal(entries.get('강서구/법정동/마곡동').length,2);
 assert.equal(entries.get('강서구/법정동/염창동'),undefined);
});
test('directory displays explicit purchase titles for every entry without last-write-wins map',()=>{
 const source=fs.readFileSync(new URL('../src/components/RegionDirectory.astro',import.meta.url),'utf8');
 assert.match(source,/entries\.map/);assert.match(source,/entry\.page\.primaryKeyword/);
 assert.doesNotMatch(source,/new Map<string,RegionEntry>/);
});
