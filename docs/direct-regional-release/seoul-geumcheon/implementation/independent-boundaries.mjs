import fs from 'node:fs';
import crypto from 'node:crypto';
import {pathToFileURL} from 'node:url';
const R='/workspace/shared/geumcheon-factory/site-factory/seoul-geumcheon-flower';
const O='/workspace/shared/geumcheon-runtime-reference/site-factory/seoul-guro-flower';
const E='/workspace/shared/geumcheon-evidence/technical-review';
const read=(root,n)=>JSON.parse(fs.readFileSync(root+'/src/data/'+n+'.json','utf8'));
const current=await import(pathToFileURL(R+'/src/lib/regions.mjs'));
const baseline=await import(pathToFileURL(O+'/src/lib/regions.mjs'));
const directory=await import(pathToFileURL(R+'/src/lib/directory-links.mjs'));
const split=await import(pathToFileURL(R+'/src/lib/directory-banner-split.mjs'));
const c=read(R,'region-coverage'),p=read(R,'region-policy'),rows=read(R,'pages'),a=read(R,'architecture'),products=read(R,'products');
const gc=read(O,'region-coverage'),gp=read(O,'region-policy'),gr=read(O,'pages'),ga=read(O,'architecture'),gproducts=read(O,'products');
const checks=[];const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const check=(name,fn)=>{try{const value=fn();checks.push({name,pass:value!==false,value});}catch(e){checks.push({name,pass:false,error:String(e)});}};
const reject=(name,fn)=>{try{fn();checks.push({name,pass:false,error:'Mutation unexpectedly accepted'});}catch(e){checks.push({name,pass:true,error:String(e)});}};
check('Valid Geumcheon exact definition',()=>current.validateDefinition(c,p)===c);
check('Valid Geumcheon rows exactly N1',()=>current.regionalRows(rows,a,c,p).length===1);
check('Current dispatcher original Guro N3',()=>same(current.regionalRows(gr,ga,gc,gp),baseline.regionalRows(gr,ga,gc,gp)));
check('Current dispatcher original Guro metadata identical',()=>gr.every(r=>same(current.regionalMetadata(gc,gp,gproducts,r.pageKey),baseline.regionalMetadata(gc,gp,gproducts,r.pageKey))));
check('Current dispatcher original Guro directory identical',()=>same(current.directoryGroups(gr,ga,gc,gp),baseline.directoryGroups(gr,ga,gc,gp)));
check('Current dispatcher Guro validation preserved',()=>gr.every(r=>{current.assertRegionalMetadata(r,gc,gp,gproducts);current.validateRegionalPurchase(r,gproducts,r.contentMarkdown);return true}));
const mutations=[
 ['zero representatives',x=>x.representatives=[]],
 ['N2 duplicate representatives',x=>x.representatives.push(structuredClone(x.representatives[0]))],
 ['unknown candidate',x=>x.representatives[0].candidateIds.push('unknown')],
 ['held candidate replacing one active',x=>x.representatives[0].candidateIds[0]='gasan-digital-opening'],
 ['candidate order drift',x=>x.representatives[0].candidateIds.reverse()],
 ['duplicate candidate',x=>x.representatives[0].candidateIds.push(x.representatives[0].candidateIds[0])],
 ['missing candidate',x=>x.representatives[0].candidateIds.pop()],
 ['unit union reversed',x=>x.representatives[0].unitKeys.reverse()],
 ['unit union expanded to Siheung',x=>x.representatives[0].unitKeys.push(x.units[2].unitKey)],
 ['unit union duplicate',x=>x.representatives[0].unitKeys.push(x.representatives[0].unitKeys[0])],
 ['legacy singular unit',x=>x.representatives[0].unitKey=x.units[0].unitKey],
 ['legacy singular facility',x=>x.representatives[0].facilityKey='shillakwon-seoul'],
 ['wrong purchase intent',x=>x.representatives[0].purchaseIntentKey='opening-congrats-wreath'],
 ['wrong context',x=>x.representatives[0].contextKey='guro|funeral-condolence-wreath'],
 ['wrong intent key',x=>x.representatives[0].intentKey='seoul-guro|funeral-condolence-wreath'],
 ['route fragment in canonical',x=>x.representatives[0].url+='#fragment'],
 ['renamed slug',x=>x.representatives[0].slug='gasan-digital-opening'],
 ['renamed heading',x=>x.representatives[0].facilityAnchors[0].heading='Unknown'],
 ['wrong anchor destination',x=>x.representatives[0].facilityAnchors[0].href=x.representatives[0].url+'#wrong'],
 ['duplicate anchors',x=>x.representatives[0].facilityAnchors[1]=structuredClone(x.representatives[0].facilityAnchors[0])],
 ['removed anchor',x=>x.representatives[0].facilityAnchors.pop()],
 ['moved facility legal unit',x=>x.facilities[0].unitKey=x.units[2].unitKey],
 ['wrong facility address',x=>x.facilities[0].address='different'],
 ['HTTP facility source',x=>x.facilities[0].sourceUrl=x.facilities[0].sourceUrl.replace('https:','http:')],
 ['credential URL facility source',x=>x.facilities[0].sourceUrl='https://u:p@example.com/'],
 ['untrusted facility source',x=>x.facilities[0].sourceUrl='https://example.com/'],
 ['extra facility',x=>x.facilities.push({...x.facilities[0],facilityKey:'different'})],
 ['missing facility',x=>x.facilities.pop()],
 ['area context activated',x=>x.areaContexts.push({contextKey:'gasan-digital-opening',unitKey:x.units[0].unitKey,contextType:'area-context',sourceUrl:'https://www.geumcheon.go.kr/',name:'Gasan'})],
 ['legal membership removed',x=>x.units.pop()],
 ['legal name changed',x=>x.units[0].name='가짜동'],
 ['legal code changed',x=>x.units[0].legalCode='1154510300'],
 ['admin membership removed',x=>x.administrativeCrosswalk.pop()],
 ['admin relation removed',x=>x.administrativeCrosswalk[0].relations=[]],
 ['admin relation moved',x=>x.administrativeCrosswalk[0].relations[0].unitKey=x.units[2].unitKey],
 ['membership hash changed',x=>x.membershipSourceSha256='0'.repeat(64)],
 ['wrong site key',x=>x.siteKey='other'],
 ['wrong scope key',x=>x.scopeKey='other'],
 ['legacy assignment',x=>x.representativeAssignment='facility-purchase-context-v1'],
 ['Guro assignment',x=>x.representativeAssignment='guro-grouped-purchase-context-v1'],
 ['assignment removed',x=>delete x.representativeAssignment]
];
for(const [name,mutation] of mutations){reject('Geumcheon rejects '+name,()=>{const x=structuredClone(c);mutation(x);current.validateDefinition(x,p)});}
for(const field of ['siteKey','scopeKey','representativeAssignment'])reject('Policy rejects altered '+field,()=>{const x=structuredClone(p);x[field]='other';current.validateDefinition(c,x)});
for(const [label,mut] of [ ['disabled policy',x=>x.enabled=false], ['missing visual binding',x=>x.visualBindings=[]]])reject('Geumcheon '+label,()=>{const x=structuredClone(p);mut(x);if(label==='disabled policy')current.regionalRows(rows,a,c,x);else current.assertRegionalMetadata(rows[0],c,x,products)});
for(const [name,mut] of [ ['missing all routes',x=>x.length=0],['extra duplicate route',x=>x.push(structuredClone(x[0]))],['unapproved row',x=>x[0].approvalVerified=false],['wrong candidate row',x=>x[0].candidateIds=['wrong']],['wrong anchor row',x=>x[0].facilityAnchors[0].anchor='wrong'],['wrong unit row',x=>x[0].regionUnitKeys=[]],['wrong snapshot',x=>x[0].snapshotHash=''] ])reject('Row rejects '+name,()=>{const x=structuredClone(rows);mut(x);current.regionalRows(x,a,c,p)});
for(const [name,mut] of [['duplicate architecture node',x=>x.pages.push(structuredClone(x.pages[0]))],['wrong architecture context',x=>x.pages[0].candidateIds=['wrong']],['wrong architecture parent',x=>x.pages[0].parentHub='/funeral/']])reject('Architecture rejects '+name,()=>{const x=structuredClone(a);mut(x);current.regionalRows(rows,x,c,p)});
for(const field of ['candidateIds','facilityAnchors','regionUnitKeys','regionalProductKeys','ogImageSha256'])reject('Metadata rejects '+field,()=>{const x=structuredClone(rows[0]);x[field]=Array.isArray(x[field])?[]:'wrong';current.assertRegionalMetadata(x,c,p,products)});
reject('Purchase family mismatch',()=>{const x=structuredClone(rows[0]);x.regionalProductFamilies=['congrats'];current.validateRegionalPurchase(x,products,x.contentMarkdown)});
reject('Guro zero representatives remains forbidden',()=>{const x=structuredClone(gc);x.representatives=[];current.validateDefinition(x,gp)});
reject('Guro N1 remains forbidden',()=>{const x=structuredClone(gc);x.representatives=x.representatives.slice(0,1);current.validateDefinition(x,gp)});
reject('Guro/Geumcheon mixed opt-in is forbidden',()=>current.validateDefinition(gc,p));
reject('Geumcheon/Guro mixed opt-in is forbidden',()=>current.validateDefinition(c,gp));
const groups=current.directoryGroups(rows,a,c,p),dest=directory.publishedDestinationsByUnit(groups);
check('One directory article, two inverse destinations',()=>groups.flatMap(d=>d.items).length===1&&[...dest.values()].flat().length===2);
for(const u of c.units){const expected=c.facilities.filter(f=>f.unitKey===u.unitKey).map(f=>rows[0].url+'#'+f.facilityKey);check('Legal alias exact '+u.name,()=>same(current.aliasTargets(u.name,rows,a,c,p),expected));}
for(const admin of c.administrativeCrosswalk){const expected=c.facilities.filter(f=>admin.relations.some(r=>r.unitKey===f.unitKey)).map(f=>rows[0].url+'#'+f.facilityKey);check('Administrative alias exact '+admin.name,()=>same(current.aliasTargets(admin.name,rows,a,c,p),expected));}
check('N1 directory split explicitly disabled',()=>same(split.planDirectoryBannerSplit([1],false),{enabled:false,totalCards:1,splitAfter:null,districtIndex:-1,itemIndex:-1}));
reject('N1 cannot request split by counting two anchors',()=>split.planDirectoryBannerSplit([1],true));
for(const n of [2,3,4,5,10])check('Preserved real-card midpoint '+n,()=>split.planDirectoryBannerSplit([n],true).splitAfter===Math.ceil(n/2));
const result={reviewedAt:new Date().toISOString(),pass:checks.every(x=>x.pass),counts:{total:checks.length,pass:checks.filter(x=>x.pass).length,fail:checks.filter(x=>!x.pass).length},checks};
fs.writeFileSync(E+'/independent-boundaries.json',JSON.stringify(result,null,2));
console.log(JSON.stringify({pass:result.pass,counts:result.counts}));for(const x of checks.filter(x=>!x.pass))console.log('FAIL '+x.name+' '+(x.error||''));
process.exitCode=result.pass?0:1;
