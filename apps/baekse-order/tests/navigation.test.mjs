import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';

const html=readFileSync(new URL('../public/index.html',import.meta.url),'utf8');

test('administrator navigation has exactly eight requested items, labels and order',()=>{
  const nav=html.match(/<nav class="nav" id="nav">([\s\S]*?)<\/nav>/)?.[1];
  assert.ok(nav,'administrator nav must exist');
  const items=[...nav.matchAll(/<button data-tab="([^"]+)"(?: class="[^"]*")?>([\s\S]*?)<\/button>/g)].map(([,id,raw])=>({id,label:raw.replace(/<[^>]+>/g,'').trim()}));
  assert.deepEqual(items,[
    {id:'home',label:'대시보드'},
    {id:'order',label:'출고등록'},
    {id:'requests',label:'발주요청(0)'},
    {id:'bills',label:'거래명세표'},
    {id:'products',label:'제품관리'},
    {id:'clients',label:'거래처관리'},
    {id:'receivables',label:'미수금관리(입금관리)'},
    {id:'settings',label:'설정'}
  ]);
  for(const item of items)assert.ok(html.includes('data-page="'+item.id+'"'),'No screen for '+item.id);
  assert.ok(!nav.includes('data-tab="stock"'),'Stock must not be in top menu');
});

test('stock and inventory management remains accessible from product management',()=>{
  const productPage=html.match(/<section class="page hidden" data-page="products">([\s\S]*?)<\/section>/)?.[1];
  assert.ok(productPage?.includes('data-go="stock"'),'Product management must link to inventory');
  assert.ok(html.includes('data-page="stock"'),'Inventory screen must remain available');
});

test('mobile toggle, buyer pending counter and tab click handlers remain wired',()=>{
  assert.ok(html.includes('id="mobile-menu-toggle"'));
  assert.ok(html.includes('id="nav-requests-pending"'));
  assert.ok(html.includes('id="mobile-requests-pending"'));
  const app=readFileSync(new URL('../public/app.js',import.meta.url),'utf8');
  assert.ok(app.includes("$('#nav').onclick="));
  assert.ok(app.includes("e.target.closest('[data-go]')"));
});
