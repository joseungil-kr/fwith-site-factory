// Synthetic SQLite handler tests; not a Cloudflare runtime simulation.
import {test} from 'node:test';
import assert from 'node:assert/strict';
import {DatabaseSync} from 'node:sqlite';
import {createHash} from 'node:crypto';
import {handleBuyerPublic,ensureBuyerSchema} from '../requests.js';
import {telegramAlarm} from '../telegram-orders.js';
const token='a'.repeat(64), hash=createHash('sha256').update(token).digest('hex');
const base='https://order.baeksefood.com', path='/api/buyer/submit';
const date=new Date(Date.now()+86400000+9*3600000).toISOString().slice(0,10);
function make(enabled='true') {
 const sql=new DatabaseSync(':memory:'); let alarm=null;
 const db={env:{TELEGRAM_ORDER_ENABLED:enabled,TELEGRAM_ORDER_BOT_TOKEN:'111111:mock_not_real_secret_11111111',TELEGRAM_ORDER_CHAT_ID:'23456'}};
 const audit=[];
 db.sql={exec(q,...p){const s=sql.prepare(q); if(s.columns().length)return s.all(...p); s.run(...p);return [];}};
 db.getOne=(q,...p)=>db.sql.exec(q,...p)[0]??null;
 db.audit=(act,body)=>audit.push([act,body]);
 db.ctx={waitUntil(){},storage:{async getAlarm(){return alarm;},async setAlarm(a){alarm=a;},async sync(){},transactionSync(f){sql.exec('BEGIN');try{f();sql.exec('COMMIT')}catch(e){sql.exec('ROLLBACK');throw e}}}};
 sql.exec("CREATE TABLE clients(id INTEGER PRIMARY KEY,business TEXT,active INTEGER); INSERT INTO clients VALUES(1,'synthetic branch',1); CREATE TABLE products(id INTEGER PRIMARY KEY,name TEXT,price INTEGER,active INTEGER); INSERT INTO products VALUES(2,'synthetic product',300,1);");
 ensureBuyerSchema(db);db.sql.exec("INSERT INTO buyer_links VALUES(1,?,'2026-10-01',NULL)",hash);
 return db;
}
function request(overrides={}, origin=base){return new Request(base+path,{method:'POST',headers:{Origin:origin,'Content-Type':'application/json'},body:JSON.stringify({token,requested_delivery:date,request_key:'00000000-0000-4000-8000-000000000001',items:[{product_id:2,qty:2}],note:'never forward this synthetic note',...overrides})})}
test('accepted buyer HTTP, repeated identical request, and invalid origin: one accepted Telegram payload only',async()=>{
 const d=make();
 assert.equal((await handleBuyerPublic(d,request({},'https://invalid.example'),path)).status,403);
 const original=await handleBuyerPublic(d,request(),path);
 assert.equal(original.status,200);const body=await original.json();
 const duplicate=await (await handleBuyerPublic(d,request(),path)).json();
 assert.equal(duplicate.duplicate,true);assert.equal(duplicate.id,body.id);
 assert.equal(d.getOne('SELECT COUNT(*) AS n FROM buyer_requests').n,1);
 assert.equal(d.getOne('SELECT COUNT(*) AS n FROM buyer_lines').n,1);
 assert.equal(d.getOne('SELECT COUNT(*) AS n FROM telegram_order_outbox').n,1);
 let sends=0;
 await telegramAlarm(d,async(_url,options)=>{
  sends++;
  const body=JSON.parse(options.body);
  assert.equal(body.text,'백세푸드 새 발주요청이 접수됐습니다.\nhttps://order.baeksefood.com/');
  assert.equal(body.chat_id,'23456');
  return Response.json({ok:true,result:{message_id:123,chat:{type:'private',id:23456}}});
 });
 assert.equal(sends,1);
 assert.equal(d.getOne('SELECT state FROM telegram_order_outbox').state,'sent');
});
test('disabled or malformed recipient still accepts orders without creating notifications', async()=>{
 for(const mode of ['disabled','group']) {
  const d=make(mode==='disabled'?'false':'true');if(mode==='group')d.env.TELEGRAM_ORDER_CHAT_ID='-100123';
  assert.equal((await handleBuyerPublic(d,request(),path)).status,200);
  assert.equal(d.getOne('SELECT COUNT(*) AS n FROM buyer_requests').n,1);
  const table=d.getOne("SELECT name FROM sqlite_master WHERE name='telegram_order_outbox'");
  if(table)assert.equal(d.getOne('SELECT COUNT(*) AS n FROM telegram_order_outbox').n,0);
 }
});
test('buyer line insert failure rolls back accepted order and cannot notify',async()=>{
 const d=make();
 d.sql.exec("CREATE TRIGGER fixture_lines_failure BEFORE INSERT ON buyer_lines BEGIN SELECT RAISE(ABORT,'synthetic failure'); END");
 await assert.rejects(handleBuyerPublic(d,request(),path),/synthetic failure/);
 assert.equal(d.getOne('SELECT COUNT(*) AS n FROM buyer_requests').n,0);
 assert.equal(d.getOne('SELECT COUNT(*) AS n FROM telegram_order_outbox').n,0);
});
test('noncanonical host accepts the existing buyer request but never enqueues Telegram',async()=>{
 const d=make();const original=request();const body=await original.text();const host='https://funeralflower-home-preview.example.workers.dev';
 const alternate=new Request(host+path,{method:'POST',headers:{Origin:host,'Content-Type':'application/json'},body});
 const response=await handleBuyerPublic(d,alternate,path);assert.equal(response.status,200);
 assert.equal(d.getOne('SELECT COUNT(*) AS n FROM buyer_requests').n,1);
 assert.equal(d.getOne("SELECT COUNT(*) AS n FROM sqlite_master WHERE type='table' AND name='telegram_order_outbox'").n,0);
});
