import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';

const html=readFileSync(new URL('../public/index.html',import.meta.url),'utf8');

test('administrator navigation has exactly nine requested items, labels and order',()=>{
  const nav=html.match(/<nav class="nav" id="nav">([\s\S]*?)<\/nav>/)?.[1];
  assert.ok(nav,'administrator nav must exist');
  const items=[...nav.matchAll(/<button data-tab="([^"]+)"(?: class="[^"]*")?>([\s\S]*?)<\/button>/g)].map(([,id,raw])=>({id,label:raw.replace(/<[^>]+>/g,'').trim()}));
  assert.deepEqual(items,[
    {id:'home',label:'대시보드'},
    {id:'order',label:'출고등록'},
    {id:'requests',label:'발주요청(0)'},
    {id:'bills',label:'거래명세표'},
    {id:'products',label:'제품관리'},
    {id:'stock',label:'재고관리'},
    {id:'clients',label:'거래처관리'},
    {id:'receivables',label:'매출관리'},
    {id:'settings',label:'설정'}
  ]);
  for(const item of items)assert.ok(html.includes('data-page="'+item.id+'"'),'No screen for '+item.id);
  assert.ok(nav.includes('data-tab="stock"'),'Stock must be in top menu');
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

test('text-only company brand links to dashboard and stays configurable',()=>{
  assert.ok(html.includes('<button class="brand" type="button" data-go="home" aria-label="대시보드로 이동"><b>백세푸드</b></button>'));
  assert.ok(!html.includes('brand-emblem')&&!html.includes('Operations Management'));
  const app=readFileSync(new URL('../public/app.js',import.meta.url),'utf8');
  assert.ok(app.includes("$('.brand b').textContent=s.company_name||'백세푸드'"));
  assert.ok(app.includes("e.target.closest('[data-go]')"));
});

test('pending request count refreshes on navigation, focus and 60s poll without clearing other pages',()=>{
  const app=readFileSync(new URL('../public/app.js',import.meta.url),'utf8');
  assert.ok(app.includes("else safeRefreshRequestBadge()"));
  assert.ok(app.includes("function refreshRequestBadge()"));
  assert.ok(app.includes("document.hidden||$('#app').classList.contains('hidden')"));
  assert.ok(app.includes("if(requestId!==pendingBadgeFetchSeq||!result.summary)return"));
  assert.ok(app.includes("state.buyer_dashboard=result.summary"));
  assert.ok(app.includes("document.addEventListener('visibilitychange'"));
  assert.ok(app.includes("window.addEventListener('focus',safeRefreshRequestBadge)"));
  assert.ok(app.includes("setInterval(safeRefreshRequestBadge,60_000)"));
  assert.ok(app.includes("if(requestId!==buyerListFetchSeq)return"));
  assert.ok(app.includes("renderRequestNavCount()"));
});
