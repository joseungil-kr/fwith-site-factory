import {chromium} from 'playwright';
import assert from 'node:assert/strict';
import {mkdirSync} from 'node:fs';
import {resolve} from 'node:path';

const origin='http://127.0.0.1:8787';
const forms=[
 ['manual-invoice/','거래명세표 A4 가로'],
 ['manual-invoice-vertical/','거래명세표 A4 세로'],
 ['simple-receipt/','간이영수증']
];
const navPaths=[
 'https://baeksefood.com/',
 '/manual-invoice/',
 '/manual-invoice-vertical/',
 '/simple-receipt/'
];
const labels=[
 '백세푸드 홈','거래명세표 A4 가로','거래명세표 A4 세로','간이영수증',
 '빈 양식 PDF 다운로드','전체 초기화','출력하기 / PDF 저장'
];
for(let i=0;i<50;i++){
 try{const r=await fetch(origin+'/manual-invoice/');if(r.ok)break;}
 catch{}
 if(i===49)throw new Error('Test web server is not listening');
 await new Promise(resolve=>setTimeout(resolve,200));
}
mkdirSync('qa-manual-forms',{recursive:true});
const browser=await chromium.launch({headless:true});
try{
 const context=await browser.newContext({locale:'ko-KR',timezoneId:'Asia/Seoul',viewport:{width:1440,height:900}});
 const page=await context.newPage();
 const errors=[];
 page.on('pageerror',e=>errors.push(e.message));
 for(const width of [1440,800,390]){
  await page.setViewportSize({width,height:940});
  const layouts=[];
  for(const [route,title] of forms){
   const response=await page.goto(origin+'/'+route,{waitUntil:'networkidle'});
   assert.equal(response.status(),200,route);
   const nav=page.locator('.toolbar-nav');
   const items=nav.locator(':scope > a, :scope > button');
   assert.equal(await items.count(),7,'All pages must have 4 nav links and 3 actions: '+route);
   const names=await items.allTextContents();
   assert.deepEqual(names.map(s=>s.trim()),labels,'Menu labels/order must match on '+route);
   for(let i=0;i<4;i++)assert.equal(await items.nth(i).getAttribute('href'),navPaths[i]);
   assert.equal(await nav.locator('[aria-current="page"]').count(),1);
   assert.equal(await nav.locator('#clear-form').count(),1);
   assert.equal(await nav.locator('#print-form').count(),1);
   const pdf=nav.locator('#blank-pdf');
   assert.equal(await pdf.count(),1,'Every layout should offer the same PDF action');
   assert.ok((await pdf.getAttribute('href')).includes('.pdf')||(await pdf.getAttribute('href')).includes('blank=1'));
   if(route==='simple-receipt/')
    assert.equal(await pdf.getAttribute('href'),'https://baeksefood.com/downloads/print-forms/receipt.pdf');
   const geometry=await page.locator('.toolbar').evaluate(header=>{
    const q=x=>header.querySelector(x);
    const r=node=>{
     const b=node.getBoundingClientRect();
     return {x:b.x,y:b.y,w:b.width,h:b.height,right:b.right,bottom:b.bottom};
    };
    const n=q('.toolbar-nav'),nr=r(n);
    return {
     header:r(header),info:r(q('.toolbar-info')),nav:nr,
     title:r(q('.toolbar-info h1')),lead:r(q('.toolbar-info p')),
     controls:[...n.children].map(r),
     screenWidth:document.documentElement.clientWidth,
     navOverflow:n.scrollWidth>n.clientWidth+1,
     headerOverflow:header.scrollWidth>header.clientWidth+1
    };
   });
   assert.equal(geometry.navOverflow,false,'Navigation must not overflow at '+width+' '+route);
   assert.equal(geometry.headerOverflow,false,'Header must not overflow at '+width+' '+route);
   assert.ok(geometry.header.w<=width+1,'Toolbar must fit viewport');
   assert.ok(geometry.lead.h>=39&&geometry.lead.h<=41,'Description area must be 2-line fixed height');
   // First 4 links are the navigation row(s); the other three are reserved action slots.
   const c=geometry.controls;
   const near=(a,b)=>Math.abs(a-b)<2;
   if(width>650){
    assert.ok(c.slice(0,4).every(x=>near(x.y,c[0].y)),'Desktop links must stay on row one');
    assert.ok(c.slice(4).every(x=>near(x.y,c[4].y)),'Desktop actions must stay on row two');
    assert.ok(c[4].y>c[0].y+25);
   }else{
    assert.ok(near(c[0].y,c[1].y)&&near(c[2].y,c[3].y),'Mobile first 4 links occupy two consistent rows');
    assert.ok(near(c[4].y,c[5].y)&&c[6].y>c[5].y+25,'Mobile actions occupy identical third and fourth rows');
   }
   if(width===390||width===1440)
    await page.locator('.toolbar').screenshot({path:resolve('qa-manual-forms/header-'+width+'-'+route.replaceAll('/','')+'.png')});
   layouts.push({route,geometry});
  }
  const baseline=layouts[0].geometry;
  for(const entry of layouts.slice(1)){
   const g=entry.geometry;
   for(const key of ['h','y'])
    assert.ok(Math.abs(g.header[key]-baseline.header[key])<2,'Header position/height must not jump at '+width+' '+entry.route+' '+key);
   for(const key of ['h','y'])
    assert.ok(Math.abs(g.nav[key]-baseline.nav[key])<2,'Navigation row position/height must not jump at '+width+' '+entry.route+' '+key);
   for(let i=0;i<7;i++){
    const v=g.controls[i],b=baseline.controls[i];
    for(const key of ['x','y','w','h'])
     assert.ok(Math.abs(v[key]-b[key])<2,'Menu control '+i+' '+key+' moved between pages at '+width+' '+entry.route+': '+JSON.stringify({baseline:b,actual:v}));
   }
  }
  console.log('UNIFORM_3_FORM_HEADER_LAYOUT_PASS',width,Math.round(baseline.header.h),Math.round(baseline.nav.h));
 }
 assert.deepEqual(errors,[],'There must be no JS page errors while switching templates');
}finally{await browser.close();}
