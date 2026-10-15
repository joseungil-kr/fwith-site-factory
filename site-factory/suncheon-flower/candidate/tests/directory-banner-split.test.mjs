import test from 'node:test';
import assert from 'node:assert/strict';
import {planDirectoryBannerSplit as plan} from '../src/lib/directory-banner-split.mjs';
for (const counts of [[], [0], [1], [2], [1,1], [0,1,0]]) {
  test(`noindex zero, one or two actual cards omit all banners: ${JSON.stringify(counts)}`, () => {
    const p=plan(counts,false); assert.equal(p.enabled,false); assert.equal(p.districtIndex,-1); assert.equal(p.itemIndex,-1); assert.equal(p.splitAfter,null);
  });
}
for (const [counts,index,item,split] of [[[2],0,1,1],[[1,1],0,1,1],[[3],0,2,2],[[44],0,22,22],[[4,3],0,4,4],[[2,5],1,2,4],[[1,1,1],1,1,2],[[0,1,0,2,0],3,1,2],[[1,0,2],2,1,2]]) {
  test(`split actual cards in original multi-district order: ${counts}`,()=>{
    const p=plan(counts);assert.equal(p.enabled,true);assert.equal(p.districtIndex,index);assert.equal(p.itemIndex,item);assert.equal(p.splitAfter,split);
    assert(p.splitAfter>=1 && p.totalCards-p.splitAfter>=1);
  });
}
test('existing noindex/showBanners=false eligibility always wins',()=>{
  for(const counts of [[3],[44],[4,3],[1,1,1]])assert.equal(plan(counts,false).enabled,false);
});
test('bad counts fail closed without inventing cards',()=>{
  for(const counts of [null,[NaN],[-1],[1.5],[Infinity],['3']])assert.throws(()=>plan(counts));
  assert.throws(()=>plan([Number.MAX_SAFE_INTEGER,1]));
});
test('plan neither mutates nor reorders district counts',()=>{
  const counts=Object.freeze([4,3]);assert.deepEqual(plan(counts),{enabled:true,totalCards:7,splitAfter:4,districtIndex:0,itemIndex:4});assert.deepEqual(counts,[4,3]);
});
test('exhaustive small groups leave a real card on each side and one insertion only',()=>{
  for(let a=0;a<6;a++)for(let b=0;b<6;b++)for(let c=0;c<6;c++) {
    const counts=[a,b,c],total=a+b+c;
    if(total<2){assert.throws(()=>plan(counts,true),/at least two actual cards/);continue;}
    const p=plan(counts);
    assert.equal(counts.slice(0,p.districtIndex).reduce((s,n)=>s+n,0)+p.itemIndex,p.splitAfter);
    assert(p.itemIndex>0&&p.itemIndex<=counts[p.districtIndex]);assert(p.splitAfter>=1&&total-p.splitAfter>=1);
    assert.equal(p.splitAfter,Math.ceil(total/2));
  }
});

test('indexable eligibility is never silently downgraded when spacing is impossible',()=>{for(const counts of [[],[0],[1]])assert.throws(()=>plan(counts,true),/at least two actual cards/);});
