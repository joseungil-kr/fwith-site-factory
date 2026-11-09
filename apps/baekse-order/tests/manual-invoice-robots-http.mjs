import assert from 'node:assert/strict';
const base='http://127.0.0.1:8788';
let booted=false;
for(let i=0;i<70;i++){
 try{
  const r=await fetch(base+'/manual-invoice/');
  if(r.status===200){booted=true;break;}
 }catch{}
 await new Promise(resolve=>setTimeout(resolve,700));
}
assert.equal(booted,true,'Local Cloudflare Worker did not start');
for(const [path,expected] of [
 ['/manual-invoice/','index'],
 ['/manual-invoice/?blank=1&print=1','noindex'],
 ['/','noindex'],
 ['/simple-receipt/','noindex'],
 ['/print-form/','noindex'],
 ['/request/','noindex'],
 ['/manual-invoice/og-image.png','index']
]){
 const response=await fetch(base+path);
 assert.equal(response.status,200,path);
 const robots=response.headers.get('x-robots-tag')||'';
 assert.equal(robots.includes('noindex'),expected==='noindex',path+' x-robots-tag='+robots);
 if(expected==='index')assert.ok(robots.includes('index')&&robots.includes('follow'),path+' '+robots);
 if(path==='/manual-invoice/'){
  const html=await response.text();
  assert.ok(html.includes('name="robots" content="index,follow'));
  assert.ok(html.includes('property="og:image"'));
  assert.ok(html.includes('class="seo-guide"'));
  assert.ok(html.includes('rel="canonical"'));
 }
 if(path.includes('og-image.png')){
  assert.equal(response.headers.get('content-type')?.split(';')[0],'image/png');
  assert.ok((await response.arrayBuffer()).byteLength>5000);
 }
}
for(const path of ['/robots.txt','/sitemap.xml']){
 const r=await fetch(base+path);
 assert.equal(r.status,200,path);
 const body=await r.text();
 assert.ok(body.includes(path==='/robots.txt'?'Sitemap: https://order.baeksefood.com/sitemap.xml':'<loc>https://order.baeksefood.com/manual-invoice/</loc>'),path);
}
const api=await fetch(base+'/api/state');
assert.equal(api.status,401,'Anonymous ERP access must remain blocked');
console.log('INVOICE_SEO_WORKER_PASS indexable one public invoice URL only, blank variants and ERP still noindex');
