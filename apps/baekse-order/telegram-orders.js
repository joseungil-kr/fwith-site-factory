// Candidate only. Never put tokens, chat IDs, API bodies or buyer data in diagnostics.
const TEXT='백세푸드 새 발주요청이 접수됐습니다.\nhttps://order.baeksefood.com/';
// Use server-side names and quantities captured with the buyer request.
function label(value,limit){
 const clean=String(value??'').replace(/[\p{Cc}\p{Cf}\p{Zl}\p{Zp}]/gu,' ').replace(/\s+/gu,' ').trim();
 let out='';for(const char of clean){if(out.length+char.length>limit-1)return out+'…';out+=char;}return out;
}
export function orderNoticeText(snapshot){
 if(snapshot==null)return TEXT;
 if(!Array.isArray(snapshot.items)||snapshot.items.length<1||snapshot.items.length>50)throw new Error('Invalid notice items');
 const branch=label(snapshot.business,180);if(!branch)throw new Error('Invalid notice branch');
 const lines=snapshot.items.map(item=>{
  if(!Number.isInteger(item.qty)||item.qty<1||item.qty>10000)throw new Error('Invalid notice quantity');
  const name=label(item.name,60);if(!name)throw new Error('Invalid notice name');
  return `${name} : ${item.qty}개`;
 });
 return `백세푸드 새 발주요청이 접수됐습니다.\n발주처 : ${branch}\n${lines.join('\n')}\nhttps://order.baeksefood.com/`;
}
const rows=(db,q,...p)=>Array.from(db.sql.exec(q,...p));
const note=(db,code)=>{try{db.audit('telegram_order_notice',{code});}catch{}};
function config(env){
 if(env.TELEGRAM_ORDER_ENABLED!=='true')return null;
 const token=env.TELEGRAM_ORDER_BOT_TOKEN,chat=env.TELEGRAM_ORDER_CHAT_ID;
 if(typeof token!=='string'||!/^\d+:[A-Za-z0-9_-]{20,}$/.test(token)||typeof chat!=='string'||! /^[1-9]\d{0,15}$/.test(chat))return null;
 return {token,chat};
}
async function destination(c){return Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(c.token+'\n'+c.chat)))).map(x=>x.toString(16).padStart(2,'0')).join('');}
export function ensureTelegramSchema(db){
 db.sql.exec(`CREATE TABLE IF NOT EXISTS telegram_order_outbox(request_id INTEGER PRIMARY KEY,destination TEXT NOT NULL,state TEXT NOT NULL DEFAULT 'pending',attempts INTEGER NOT NULL DEFAULT 0,due INTEGER NOT NULL,updated INTEGER NOT NULL,result TEXT,message_id INTEGER)`);
 db.sql.exec('CREATE INDEX IF NOT EXISTS telegram_order_due ON telegram_order_outbox(state,due)');
 if(!rows(db,'PRAGMA table_info(telegram_order_outbox)').some(c=>c.name==='message_text'))db.sql.exec('ALTER TABLE telegram_order_outbox ADD COLUMN message_text TEXT');
}
export async function prepareTelegram(db){
 try{const c=config(db.env);if(!c)return null;ensureTelegramSchema(db);return await destination(c);}catch{note(db,'prepare_failed');return null;}
}
// Called inside the existing request+lines transaction. A failed optional INSERT is
// caught, without changing the parent transaction or its buyer response.
export function enqueueTelegram(db,id,target,snapshot){
 if(!target)return;
 try{const text=snapshot==null?null:orderNoticeText(snapshot);const t=Date.now();db.sql.exec('INSERT OR IGNORE INTO telegram_order_outbox(request_id,destination,due,updated,message_text) VALUES(?,?,?,?,?)',id,target,t,t,text);}catch{note(db,'enqueue_failed');}
}
export async function scheduleTelegram(db,strict=false){
 try{
  // Serialize the read/set sequence across interleaved order requests.
  const prior=db.telegramSchedule||Promise.resolve();
  const task=prior.catch(()=>{}).then(async()=>{
   const next=rows(db,"SELECT MIN(due) AS due FROM telegram_order_outbox WHERE state='pending'")[0]?.due;
   if(next==null)return;
   const alarm=await db.ctx.storage.getAlarm();
   const due=Math.max(Date.now()+100,next);
   if(alarm===null||alarm>due)await db.ctx.storage.setAlarm(due);
  });
  db.telegramSchedule=task;await task;
 }catch{note(db,'schedule_failed');if(strict)throw new Error('Telegram alarm scheduling unavailable');}
}
export function kickTelegram(db){try{db.ctx.waitUntil(scheduleTelegram(db));}catch{note(db,'schedule_failed');}}
export async function recoverTelegram(db){try{ensureTelegramSchema(db);await scheduleTelegram(db);}catch{note(db,'recovery_failed');}}
export async function telegramAlarm(db,fetcher=fetch){
 let remoteStarted=false;
 try{
  ensureTelegramSchema(db);
  // A prior sending attempt may have succeeded before interruption. Never resend.
  db.sql.exec("UPDATE telegram_order_outbox SET state='ambiguous',result='interrupted',updated=? WHERE state='sending'",Date.now());
  const row=rows(db,"SELECT * FROM telegram_order_outbox WHERE state='pending' AND due<=? ORDER BY due,request_id LIMIT 1",Date.now())[0];
  if(!row)return;
  const c=config(db.env);
  if(!c||await destination(c)!==row.destination){
   db.sql.exec("UPDATE telegram_order_outbox SET state='disabled',result='config_changed',updated=? WHERE request_id=? AND state='pending'",Date.now(),row.request_id);return;
  }
  // Durable watchdog first. If scheduling fails, do not attempt external delivery.
  await db.ctx.storage.setAlarm(Date.now()+60000);
  const claimed=rows(db,"UPDATE telegram_order_outbox SET state='sending',attempts=attempts+1,updated=? WHERE request_id=? AND state='pending' RETURNING request_id",Date.now(),row.request_id);
  if(!claimed.length)return;
  await db.ctx.storage.sync();
  let state='ambiguous',result='transport_unknown',due=Date.now(),messageId=null;
  try{
   remoteStarted=true;
   const res=await fetcher(`https://api.telegram.org/bot${c.token}/sendMessage`,{method:'POST',redirect:'manual',headers:{'Content-Type':'application/json'},body:JSON.stringify({chat_id:c.chat,text:row.message_text??TEXT,link_preview_options:{is_disabled:true}}),signal:AbortSignal.timeout(8000)});
   const body=await res.json();
   if(res.status===200&&body?.ok===true&&Number.isInteger(body?.result?.message_id)){state='sent';result='accepted';messageId=body.result.message_id;}
   else if(res.status===429&&body?.ok===false&&body?.error_code===429&&Number.isInteger(body?.parameters?.retry_after)&&body.parameters.retry_after>0&&body.parameters.retry_after<=86400){
    state=row.attempts+1<3?'pending':'failed';result='rate_limited';due=Date.now()+body.parameters.retry_after*1000;
   }else if(res.status>=400&&res.status<500&&body?.ok===false&&body.error_code===res.status){state='failed';result='rejected';}
   else result='response_unknown';
  }catch{ /* Timeout, invalid JSON or transport failure is not safe to resend. */ }
  db.sql.exec('UPDATE telegram_order_outbox SET state=?,result=?,due=?,updated=?,message_id=? WHERE request_id=?',state,result,due,Date.now(),messageId,row.request_id);
 }catch{
  note(db,'alarm_failed');
  // Before the remote call there was no send: let Cloudflare retry this alarm.
  // Persisted sending still becomes ambiguous conservatively on that retry.
  if(!remoteStarted)throw new Error('Telegram alarm preparation unavailable');
  // After a possible send, leave sending for the durable watchdog to mark unknown.
 }
 finally{await scheduleTelegram(db,true);}
}
