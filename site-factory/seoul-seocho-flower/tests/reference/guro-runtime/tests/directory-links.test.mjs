import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';
import {publishedEntriesByUnit,publishedDestinationsByUnit} from '../src/lib/directory-links.mjs';
import {groupsFor,coverage} from '../src/lib/regional-runtime.mjs';
const pages=JSON.parse(fs.readFileSync(new URL('../src/data/pages.json',import.meta.url)));
test('legacy helper retains every distinct intent per unit and deduplicates repeated group views',()=>{
 const a={representative:{unitKeys:['legacy/unit']},page:{url:'/regions/a/'}},b={representative:{unitKeys:['legacy/unit']},page:{url:'/regions/b/'}};
 const group={items:[a,b]};const result=publishedEntriesByUnit([group,group]);assert.deepEqual(result.get('legacy/unit'),[a,b]);assert.equal(result.get('legacy/unrepresented'),undefined);
});
test('Guro same-dong links retain four named destinations across three articles',()=>{
 const groups=groupsFor(pages),dest=publishedDestinationsByUnit([...groups,...groups]);
 const guro=dest.get('구로구/법정동/구로동');assert.equal(guro.length,4);assert.deepEqual(guro.map(x=>x.candidateId),['korea-guro-funeral','weddingcity-sindorim','g-tower-convention','guro-digital-valley-offices']);
 assert.equal(dest.get('구로구/법정동/신도림동').length,2);assert.equal(dest.get('구로구/법정동/항동'),undefined);
 for(const admin of coverage.administrativeCrosswalk.filter(a=>a.relations.some(r=>r.unitKey==='구로구/법정동/구로동'))){const targets=admin.relations.flatMap(r=>(dest.get(r.unitKey)||[]).map(e=>e.href));assert.ok(guro.every(entry=>targets.includes(entry.href)));}
});
test('directory renders named destination anchors without a last-write-wins map',()=>{
 const source=fs.readFileSync(new URL('../src/components/RegionDirectory.astro',import.meta.url),'utf8');assert.match(source,/entries\.map/);assert.match(source,/href=\{entry.href\}/);assert.match(source,/\{entry.name\}/);assert.match(source,/data-legal-unit/);assert.doesNotMatch(source,/new Map<string,RegionEntry>/);
});
