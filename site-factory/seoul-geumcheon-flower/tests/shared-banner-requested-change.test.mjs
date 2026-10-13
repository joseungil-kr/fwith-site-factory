import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import crypto from 'node:crypto';
const read=p=>fs.readFileSync(new URL('../'+p,import.meta.url));
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const overlay=JSON.parse(read('src/data/shared-banner-requested-change.json'));
const manifest=JSON.parse(read('src/data/shared-banner-manifest.json'));
const common=JSON.parse(read('src/data/geumcheon-copy.json'));
const historical=JSON.parse(read('tests/reference/release-baseline/release-approval.before-banner-phone.json'));
const phonePins={
 'flower-message':'a5ecdeb1914566a32d45b084351e2782fc8b234e9a4fbb8635a60a9921cac5f5',
 'flower-budget':'081198095eb005603721be7c778f4d477f4dd93dcf96f0c261f18bf06bb91421',
 'flower-consultation':'d6654aa44c365f64e330d0be2042972d3320fad54231425aaffca1dfdcd25ebc'
};
test('shared component differs from historical renderer only by the requested caption removal and exact visible phone in alt',()=>{
 const original=read('tests/reference/guro-runtime/src/components/SharedFlowerBanner.astro').toString();
 const removed='  <figcaption>꽃이랑 공통 안내 이미지 · 실제 판매상품 사진이 아닌 AI 생성 이미지입니다.</figcaption>\n';
 assert.equal(original.split(removed).length,2);
 assert.equal(read('src/components/SharedFlowerBanner.astro').toString(),original.replace(removed,'').replaceAll("안내 이미지.'","안내 이미지. 전화 1844-0644.'"));
 assert.doesNotMatch(read('src/components/SharedFlowerBanner.astro').toString(),/<figcaption>/);
 assert.equal((read('src/components/SharedFlowerBanner.astro').toString().match(/전화 1844-0644\./g)||[]).length,3);
});
test('phone image bytes match exact approved pins while dimensions, format and old copy seals stay intact',()=>{
 assert.deepEqual(Object.fromEntries(manifest.map(r=>[r.name,r.sha256])),phonePins);
 for(const row of manifest){
  const path='public/images/shared-banners/'+row.name+'.webp',bytes=read(path);
  assert.equal(sha(bytes),row.sha256);assert.equal(bytes.length,row.bytes);
  assert.equal(bytes.toString('ascii',0,4),'RIFF');assert.equal(bytes.toString('ascii',8,12),'WEBP');
  assert.deepEqual([row.width,row.height],[1774,887]);
  assert.equal(overlay.replacements[path].afterSha256,row.sha256);
  assert.equal(overlay.replacements[path].beforeSha256,historical.unchangedCustomerContent[path]);
 }
 assert.equal(sha(read('src/data/geumcheon-copy.json')),'01f9e71d13ad3a11122b832d649f60b6da976c85513ee90b6ccb531737fb7455');
});
