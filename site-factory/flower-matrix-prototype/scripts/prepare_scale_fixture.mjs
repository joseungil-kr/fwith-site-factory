import fs from 'node:fs';
const count=Number(process.argv[2]||0);
if(!Number.isInteger(count)||count<1||count>1000)throw new Error('region count must be 1..1000');
const regions=JSON.parse(fs.readFileSync('src/data/regions-matrix.json','utf8'));
const base=regions[0];
const scaled=Array.from({length:count},(_,i)=>{
  const n=String(i+1).padStart(3,'0');
  return {
    ...base,
    key:'scale-'+n,
    name:'부하검증지역 '+n,
    slug:'scale-'+n,
    sourceUrl:'https://example.invalid/scale/'+n,
    sourceType:'test-only-synthetic-region',
    deliveryNote:'빌드 성능 검증 전용 가상 지역입니다. 공개 금지.',
    decisionNote:'빌드 성능 검증 전용 가상 지역입니다. 공개 콘텐츠가 아닙니다.'
  };
});
fs.writeFileSync('src/data/regions-matrix.json',JSON.stringify(scaled,null,2)+'\n');
const instances=JSON.parse(fs.readFileSync('src/data/site-instances.json','utf8'));
for(const x of instances)x.enabledRegions=scaled.map(r=>r.key);
fs.writeFileSync('src/data/site-instances.json',JSON.stringify(instances,null,2)+'\n');
console.log(JSON.stringify({testOnly:true,syntheticRegions:count,productGroups:instances[0].enabledProductGroups.length,detailPages:count*instances[0].enabledProductGroups.length}));
