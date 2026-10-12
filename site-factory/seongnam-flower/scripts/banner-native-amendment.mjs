// Historical tests still evaluate their immutable original revision. Current bytes
// are verified separately, and this pending amendment is not a release approval.
import fs from 'node:fs';import crypto from 'node:crypto';import assert from 'node:assert/strict';
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const fixture=JSON.parse(fs.readFileSync('tests/fixtures/banner-native-amendment.json','utf8'));
export function packageAmendment(before){
 const value=JSON.parse(before);const suffix=' && python3 scripts/qa_shared_banners.py'+(fixture.region==='hwaseong'?' && mv shared-banner-qa.json dist/shared-banner-qa.json':'');
 assert(value.scripts.build&&!value.scripts.build.includes('qa_shared_banners.py'),'Unexpected baseline package');
 value.scripts.build+=suffix;value.scripts['qa:shared-banners']='python3 scripts/qa_shared_banners.py'+(fixture.region==='hwaseong'?' && mv shared-banner-qa.json dist/shared-banner-qa.json':'');
 return JSON.stringify(value,null,2)+'\n';
}
export function assertCurrentAmendment(){
 assert.equal(fixture.status,'pending');assert.equal(fixture.productionApprovalGranted,false);
 for(const [name,row] of Object.entries(fixture.changed)){
  assert.equal(hash(Buffer.from(row.beforeUtf8)),row.beforeSha256,'Archived baseline changed: '+name);
  assert.equal(hash(fs.readFileSync(name)),row.afterSha256,'Current banner amendment drift: '+name);
 }
 for(const [name,digest] of Object.entries(fixture.additions))assert.equal(hash(fs.readFileSync(name)),digest,'Current addition drift: '+name);
 assert.equal(packageAmendment(fixture.changed['package.json'].beforeUtf8),fs.readFileSync('package.json','utf8'),'Package change is not exact additive banner QA');
}
export function historicalBytes(name){assertCurrentAmendment();return fixture.changed[name]?Buffer.from(fixture.changed[name].beforeUtf8):fs.readFileSync(name);}
export function historicalInventory(files){assertCurrentAmendment();assert.deepEqual(files,fixture.currentInventory.filter(name=>!fixture.nativeOptionalGeneratedPaths.includes(name)||fs.existsSync(name)).sort(),'Current amendment inventory drift');return files.filter(name=>!fixture.newPaths.includes(name));}
