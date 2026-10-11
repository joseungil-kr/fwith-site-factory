import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import crypto from 'node:crypto';
const read=n=>JSON.parse(fs.readFileSync(new URL('../src/data/'+n+'.json',import.meta.url),'utf8'));
const canonical=v=>JSON.stringify(v,(_,x)=>x&&typeof x==='object'&&!Array.isArray(x)?Object.fromEntries(Object.entries(x).sort(([a],[b])=>a<b?-1:a>b?1:0)):x);
const sha=x=>crypto.createHash('sha256').update(x).digest('hex');
const original={"gwangmyeong-flower-direct-region-gwangmyeong-dong": "4e516157c68345cb2d76eabba1fd1b6e822a622a17723a34774ad3a1a4473b3e", "gwangmyeong-flower-direct-region-cheolsan-dong": "23f93f0191d8c8172e8baeb77136e74573a0dc94b9afdaea272ba123c55cffac", "gwangmyeong-flower-direct-region-haan-dong": "b8a6c6fd0991bc9a39bac0cde41522e6b450fdd8563d66a92588e3b13557da8e", "gwangmyeong-flower-direct-region-soha-dong": "09d03d3391be886e8a2f41f9a5733f31ec3fe7ac7d6a96757f98d77b8b581009", "gwangmyeong-flower-direct-region-iljik-dong": "54e2f111d1eec7d2e076ec2cee457ac9590f80e01ba9c87274bd856da3d85073", "gwangmyeong-flower-direct-region-noonsa-dong": "9e431a6847e036867b13b4246d40c7a6dbbbb792b40727004536ab8c53d3c021", "gwangmyeong-flower-direct-region-gahak-dong": "71222446fa160b9afd0ec9075187f7a99a0d31f06155b1ac011454c0302a6940", "gwangmyeong-flower-direct-region-okgil-dong": "9b1c532e2773eeedc142c2b364fb5549d3a3d93fe610574d8a86f8e7f3059a3d"};
test('copy revision preserves eight original articles and all original and additive denominators',()=>{
 const p=read('pages'),m=read('publish-manifest');assert.equal(p.length,9);
 for(const [key,digest] of Object.entries(original))assert.equal(sha(canonical(p.find(x=>x.pageKey===key))),digest);
 assert.equal(m.directRelease.plannedOriginalCount,8);assert.equal(m.directRelease.reviewedArticleCount,8);
 assert.equal(m.additiveBatches[0].plannedOriginalCount,1);assert.equal(m.additiveBatches[0].resultingArticleCount,9);
});
test('revised customer copy binds the independent review without internal investigation notes',()=>{
 const p=read('pages').find(x=>x.pageKey==="gwangmyeong-flower-direct-event-gwangmyeong-lapoete-wedding-wreath");assert.equal(p.snapshotHash,'c54ac59b1b2e5b99687171973c601af6ad364e48543e999fbbda0217f4a4d040');
 assert.equal(sha(p.contentMarkdown),'d76e809b549711bb56098cca8ef93b7dbb9df25f4d7c3787d9ec85cdec23e05e');assert.doesNotMatch(p.contentMarkdown,/접속.*제한|검색 공개문|추정하지|가정하지|보장하지|검수|검증 도구/);
 assert.equal(read('publish-manifest').copyRevisions.at(-1).independentCopyReviewSha256,'9e0737893f6849f0c281908b5b446bcdad14e512f131354aaeab673dd837f5fa');
});
