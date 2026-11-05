import test from 'node:test';
import assert from 'node:assert/strict';
import {webcrypto,createHash} from 'node:crypto';
import {readFileSync} from 'node:fs';
import {buyerLinkDisplaySummaries,handleBuyerAdmin,handleBuyerPublic} from '../requests.js';

if(!globalThis.crypto)globalThis.crypto=webcrypto;
const origin='https://order.baeksefood.com';
function fixture(){
  const clients=new Map([[1,{id:1,business:'안산 중앙점',active:1}],[2,{id:2,business:'두번째 거래처',active:1}]]);
  const links=new Map(),storage=new Map();
  const db={
    ctx:{storage:{kv:{get:key=>storage.get(key),put:(key,value)=>storage.set(key,value)}}},
    audit(){},
    sql:{exec(query,...args){
      if(query.startsWith('INSERT INTO buyer_links')){
        const [client_id,token_hash,issued_at]=args;
        links.set(client_id,{client_id,token_hash,issued_at,revoked_at:null});return;
      }
      if(query.startsWith('UPDATE buyer_links SET revoked_at=')){
        const link=links.get(args[1]);if(link)link.revoked_at=args[0];return;
      }
      throw new Error('Unexpected SQL mutation '+query);
    }},
    getOne(query,...args){
      if(query.startsWith('SELECT id,active FROM clients'))return clients.get(args[0])||null;
      if(query.startsWith('SELECT client_id FROM buyer_links')){
        const link=links.get(args[0]);return link&&!link.revoked_at?{client_id:link.client_id}:null;
      }
      if(query.includes('WHERE l.token_hash=?')){
        const found=[...links.values()].find(l=>l.token_hash===args[0]&&!l.revoked_at);
        const client=found&&clients.get(found.client_id);
        return client?.active?{id:client.id,business:client.business,active:client.active}:null;
      }
      if(query.includes('WHERE l.client_id=?')){
        const link=links.get(args[0]),client=clients.get(args[0]);
        return link&&!link.revoked_at&&client?.active?{...link,id:client.id,business:client.business,active:client.active}:null;
      }
      if(query.startsWith('SELECT company_name FROM receipt_settings'))return {company_name:'백세푸드'};
      throw new Error('Unexpected query '+query);
    },
    all(query,...args){
      if(query.startsWith('SELECT client_id,token_hash,issued_at,revoked_at FROM buyer_links'))return [...links.values()].sort((a,b)=>a.client_id-b.client_id);
      if(query.startsWith('SELECT id,name,price FROM products'))return [];
      if(query.startsWith('SELECT id,status,requested_delivery,created_at,processed_at FROM buyer_requests'))return [];
      throw new Error('Unexpected list query '+query);
    }
  };
  return {db,clients,links,storage};
}
const request=(path,token)=>new Request(origin+path,{method:'POST',headers:{Origin:origin,'Content-Type':'application/json'},body:JSON.stringify({token})});
async function issue(db,id){
  const result=await handleBuyerAdmin(db,new Request(origin+'/api/requests/link/issue',{method:'POST'}),'/api/requests/link/issue',{client_id:id});
  assert.equal(result.status,200);
  return (await result.json()).url;
}
async function overview(db,url){
  const result=await handleBuyerPublic(db,request('/api/buyer/overview',url.split('#')[1]),'/api/buyer/overview');
  return {status:result.status,data:await result.json()};
}

test('per-client display URLs are unique, stable after refresh, and authenticate only their owner',async()=>{
  const {db,storage}=fixture();
  const url1=await issue(db,1),url2=await issue(db,2);
  assert.notEqual(url1,url2);
  assert.match(url1,/^https:\/\/order\.baeksefood\.com\/request\/#(?:[0-9a-f]{64})$/);
  assert.match(url2,/^https:\/\/order\.baeksefood\.com\/request\/#(?:[0-9a-f]{64})$/);
  const rows=await buyerLinkDisplaySummaries(db,origin);
  assert.equal(rows.find(r=>r.client_id===1).url,url1);
  assert.equal(rows.find(r=>r.client_id===2).url,url2);
  assert.deepEqual(await buyerLinkDisplaySummaries(db,origin),rows);
  assert.equal(storage.size,1,'only one private signing key is persisted');
  assert.equal((await overview(db,url1)).data.client.business,'안산 중앙점');
  assert.equal((await overview(db,url2)).data.client.business,'두번째 거래처');
  const tampered=url1.slice(0,-1)+(url1.endsWith('0')?'1':'0');
  assert.equal((await overview(db,tampered)).status,403);
});

test('old sent links continue working, but revocation and reissue invalidate affected link only',async()=>{
  const {db,links}=fixture();
  const legacy='f'.repeat(64);
  links.set(1,{client_id:1,token_hash:createHash('sha256').update(legacy).digest('hex'),issued_at:'2026-11-04T08:00:00.000Z',revoked_at:null});
  assert.equal((await overview(db,origin+'/request/#'+legacy)).status,200);
  const display=(await buyerLinkDisplaySummaries(db,origin)).find(l=>l.client_id===1).url;
  assert.equal((await overview(db,display)).status,200);
  const url2=await issue(db,2);
  const revoke=await handleBuyerAdmin(db,new Request(origin+'/api/requests/link/revoke',{method:'POST'}),'/api/requests/link/revoke',{client_id:1});
  assert.equal(revoke.status,200);
  assert.equal((await overview(db,display)).status,403);
  assert.equal((await overview(db,origin+'/request/#'+legacy)).status,403);
  assert.equal((await overview(db,url2)).status,200);
  const fresh=await issue(db,1);
  assert.notEqual(fresh,display);
  assert.equal((await overview(db,fresh)).status,200);
  assert.equal((await overview(db,display)).status,403);
});

test('inline client link and copy UI replaces the separate panel',()=>{
  const app=readFileSync(new URL('../public/app.js',import.meta.url),'utf8');
  const html=readFileSync(new URL('../public/index.html',import.meta.url),'utf8');
  assert.match(app,/class="buyer-link-row"/);
  assert.match(app,/data-client-link-copy/);
  assert.match(app,/const url=entry\?\.url;/);
  assert.doesNotMatch(app,/issuedBuyerUrls|get\(id\)|generated-link-value|copy-generated-link/);
  assert.doesNotMatch(html,/id="link-result"|id="generated-link-value"|copy-generated-link/);
});
