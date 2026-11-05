import {onlyInt,safeText,dateCheck,calcTotals,calcInternalCost,calculatePayable} from './logic.js';
import {ensureReceivableOrderCanIssue} from './receivables.js';

const now=()=>new Date().toISOString();
const kstToday=()=>new Date(Date.now()+9*3600000).toISOString().slice(0,10);
const response=(obj,status=200)=>new Response(JSON.stringify(obj),{
  status,headers:{'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store','X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer'}
});
const fail=(message,status=400)=>response({error:message},status);
const one=(db,query,...args)=>db.getOne(query,...args);
const all=(db,query,...args)=>db.all(query,...args);
const hashHex=async input=>[...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(input)))].map(b=>b.toString(16).padStart(2,'0')).join('');
const generateToken=()=>[...crypto.getRandomValues(new Uint8Array(32))].map(b=>b.toString(16).padStart(2,'0')).join('');
const VALID_TOKEN=/^[a-f0-9]{64}$/;
const DISPLAY_TOKEN_PREFIX='ba5e';
const DISPLAY_KEY_NAME='buyer_link_display_signing_key_v1';
const toHex=bytes=>[...new Uint8Array(bytes)].map(b=>b.toString(16).padStart(2,'0')).join('');
// A private signing key allows safe reconstruction of administrator-visible
// per-client links. The original random bearer token remains hashed only.
function getDisplaySigningBytes(db){
  let value=db.ctx.storage.kv.get(DISPLAY_KEY_NAME);
  if(!VALID_TOKEN.test(value||'')){
    value=generateToken();
    db.ctx.storage.kv.put(DISPLAY_KEY_NAME,value);
  }
  return Uint8Array.from(value.match(/.{2}/g),b=>parseInt(b,16));
}
async function signedDisplayToken(db,link){
  const idHex=Number(link.client_id).toString(16).padStart(12,'0');
  if(idHex.length!==12)throw new Error('지원하지 않는 거래처 ID');
  const key=await crypto.subtle.importKey('raw',getDisplaySigningBytes(db),{name:'HMAC',hash:'SHA-256'},false,['sign']);
  const message='buyer-link-display-v1:'+link.client_id+':'+link.token_hash+':'+link.issued_at;
  const mac=toHex(await crypto.subtle.sign('HMAC',key,new TextEncoder().encode(message)));
  return DISPLAY_TOKEN_PREFIX+idHex+mac.slice(0,48);
}
function constantTimeEqual(a,b){
  if(typeof a!=='string'||typeof b!=='string'||a.length!==b.length)return false;
  let difference=0;
  for(let i=0;i<a.length;i++)difference|=a.charCodeAt(i)^b.charCodeAt(i);
  return difference===0;
}
const VALID_REQUEST_KEY=/^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$/i;

export function ensureBuyerSchema(db){
  db.sql.exec('CREATE TABLE IF NOT EXISTS buyer_links(client_id INTEGER PRIMARY KEY,token_hash TEXT NOT NULL UNIQUE,issued_at TEXT NOT NULL,revoked_at TEXT);');
  db.sql.exec("CREATE TABLE IF NOT EXISTS buyer_requests(id INTEGER PRIMARY KEY AUTOINCREMENT,client_id INTEGER NOT NULL,request_key TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'pending',requested_delivery TEXT NOT NULL,note TEXT NOT NULL DEFAULT '',created_at TEXT NOT NULL,processed_at TEXT,issued_order_id INTEGER,UNIQUE(client_id,request_key));");
  db.sql.exec('CREATE TABLE IF NOT EXISTS buyer_lines(id INTEGER PRIMARY KEY AUTOINCREMENT,request_id INTEGER NOT NULL,product_id INTEGER NOT NULL,name TEXT NOT NULL,unit_price INTEGER NOT NULL,qty INTEGER NOT NULL);');
  db.sql.exec('CREATE INDEX IF NOT EXISTS buyer_requests_status_idx ON buyer_requests(status,id)');
  db.sql.exec('CREATE INDEX IF NOT EXISTS buyer_lines_product_idx ON buyer_lines(product_id,request_id)');
}

export function buyerSupplySummary(db){
  const rows=all(db,"SELECT p.id AS product_id,p.name,p.active,COALESCE((SELECT SUM(delta) FROM movements WHERE product_id=p.id),0) AS stock,COALESCE((SELECT SUM(bl.qty) FROM buyer_lines bl JOIN buyer_requests br ON br.id=bl.request_id WHERE bl.product_id=p.id AND br.status='pending'),0) AS requested FROM products p ORDER BY p.sort_order,p.id");
  const shortages=rows.filter(row=>row.requested>row.stock).map(row=>({...row,shortage:row.requested-row.stock}));
  const pending=one(db,"SELECT COUNT(*) AS n FROM buyer_requests WHERE status='pending'").n;
  return {pending_count:pending,shortage_count:shortages.length,shortages,products:rows};
}

export function buyerLinkSummaries(db){
  return all(db,'SELECT client_id,issued_at,revoked_at FROM buyer_links ORDER BY client_id');
}
// Only the authenticated administrator state API calls this. No plaintext token
// is written to SQL or included in the full-data export.
export async function buyerLinkDisplaySummaries(db,origin){
  const rows=all(db,'SELECT client_id,token_hash,issued_at,revoked_at FROM buyer_links ORDER BY client_id');
  const display=[];
  for(const link of rows){
    display.push({client_id:link.client_id,issued_at:link.issued_at,revoked_at:link.revoked_at,
      url:link.revoked_at?null:origin+'/request/#'+await signedDisplayToken(db,link)});
  }
  return display;
}

async function getClientByToken(db,token){
  if(typeof token!=='string'||!VALID_TOKEN.test(token))return null;
  const token_hash=await hashHex(token);
  const row=one(db,"SELECT c.id,c.business,c.active FROM buyer_links l JOIN clients c ON c.id=l.client_id WHERE l.token_hash=? AND l.revoked_at IS NULL AND c.active=1",token_hash);
  if(row)return row;
  // Previously issued raw URLs remain valid. New display URLs are an additional
  // per-client signed credential, invalidated on reissue and revocation.
  if(!token.startsWith(DISPLAY_TOKEN_PREFIX))return null;
  const clientId=Number.parseInt(token.slice(4,16),16);
  if(!Number.isSafeInteger(clientId)||clientId<1)return null;
  const link=one(db,'SELECT l.client_id,l.token_hash,l.issued_at,c.id,c.business,c.active FROM buyer_links l JOIN clients c ON c.id=l.client_id WHERE l.client_id=? AND l.revoked_at IS NULL AND c.active=1',clientId);
  if(!link)return null;
  const expected=await signedDisplayToken(db,link);
  return constantTimeEqual(token,expected)?{id:link.id,business:link.business,active:link.active}:null;
}

async function getBody(request,maxLength=16000){
  const body=await request.text();
  if(body.length>maxLength)throw new Error('요청 데이터가 너무 큽니다.');
  const obj=JSON.parse(body);
  if(!obj||typeof obj!=='object'||Array.isArray(obj))throw new Error('발주 내용이 올바르지 않습니다.');
  return obj;
}

export async function handleBuyerPublic(db,request,path){
  if(request.method!=='POST')return fail('허용하지 않는 요청 방식입니다.',405);
  if(request.headers.get('Origin')!==new URL(request.url).origin)return fail('사이트에서 요청해 주세요.',403);
  let data;
  try{data=await getBody(request);}catch(e){return fail(e.message||'발주 내용을 확인해 주세요.');}
  const client=await getClientByToken(db,data.token);
  if(!client)return fail('발주 링크가 유효하지 않습니다. 업체 관리자에게 새로운 링크를 요청하세요.',403);
  if(path==='/api/buyer/overview'){
    const products=all(db,'SELECT id,name,price FROM products WHERE active=1 ORDER BY sort_order,id');
    const history=all(db,'SELECT id,status,requested_delivery,created_at,processed_at FROM buyer_requests WHERE client_id=? ORDER BY id DESC LIMIT 15',client.id);
    const settings=one(db,'SELECT company_name FROM receipt_settings WHERE id=1');
    return response({client:{business:client.business},supplier_name:settings?.company_name||'백세푸드',products,history});
  }
  if(path!=='/api/buyer/submit')return fail('없는 발주 API 주소입니다.',404);
  let delivery,items,note,request_key;
  try{
    delivery=dateCheck(data.requested_delivery);
    const current=kstToday(),upper=new Date(Date.now()+90*86400000+9*3600000).toISOString().slice(0,10);
    if(delivery<current||delivery>upper)throw new Error('희망 납품일은 오늘부터 90일 이내로 선택하세요.');
    request_key=String(data.request_key||'').trim().toLowerCase();
    if(!VALID_REQUEST_KEY.test(request_key))throw new Error('발주 요청을 새로고침한 후 다시 진행하세요.');
    note=safeText(data.note,'메모',false,300);
    const supplied=Array.isArray(data.items)?data.items:[];
    if(supplied.length<1||supplied.length>50)throw new Error('발주 상품을 1~50종 선택하세요.');
    const seen=new Set();
    items=supplied.map(raw=>{
      const id=onlyInt(raw.product_id,'제품ID',1),qty=onlyInt(raw.qty,'발주수량',1,10000);
      if(seen.has(id))throw new Error('같은 제품을 중복 발주할 수 없습니다.');
      seen.add(id);
      const product=one(db,'SELECT id,name,price FROM products WHERE id=? AND active=1',id);
      if(!product)throw new Error('판매가 중지된 제품이 포함돼 있습니다. 화면을 새로고침하세요.');
      return {product_id:id,qty,name:product.name,unit_price:product.price};
    });
    calcTotals(items,'none'); // No inventory validation at request stage.
  }catch(e){return fail(e.message||'발주 내용을 다시 확인해 주세요.');}
  const existing=one(db,'SELECT id,status FROM buyer_requests WHERE client_id=? AND request_key=?',client.id,request_key);
  if(existing)return response({ok:true,id:existing.id,status:existing.status,duplicate:true});
  const pendingCount=one(db,"SELECT COUNT(*) AS n FROM buyer_requests WHERE client_id=? AND status='pending'",client.id).n;
  if(pendingCount>=50)return fail('미처리 발주가 너무 많습니다. 관리자에게 먼저 확인을 요청하세요.',429);
  let id;
  db.ctx.storage.transactionSync(()=>{
    db.sql.exec("INSERT INTO buyer_requests(client_id,request_key,status,requested_delivery,note,created_at) VALUES(?,?,'pending',?,?,?)",client.id,request_key,delivery,note,now());
    id=one(db,'SELECT last_insert_rowid() AS id').id;
    for(const item of items)db.sql.exec('INSERT INTO buyer_lines(request_id,product_id,name,unit_price,qty) VALUES(?,?,?,?,?)',id,item.product_id,item.name,item.unit_price,item.qty);
    db.audit('buyer_request_created',{id,client_id:client.id,lines:items.length});
  });
  return response({ok:true,id,status:'pending'});
}

export async function handleBuyerAdmin(db,request,path,data){
  if(path==='/api/requests/list'&&request.method==='GET'){
    const requests=all(db,"SELECT br.id,br.client_id,br.status,br.requested_delivery,br.note,br.created_at,br.processed_at,br.issued_order_id,c.business AS client_name,c.person AS client_contact FROM buyer_requests br JOIN clients c ON c.id=br.client_id ORDER BY CASE WHEN br.status='pending' THEN 0 ELSE 1 END,br.id DESC LIMIT 150");
    const lines=all(db,'SELECT request_id,product_id,name,unit_price,qty FROM buyer_lines ORDER BY request_id,id');
    const map=new Map();
    for(const row of lines){const list=map.get(row.request_id)||[];list.push(row);map.set(row.request_id,list);}
    return response({requests:requests.map(row=>({...row,items:map.get(row.id)||[]})),summary:buyerSupplySummary(db)});
  }
  if(request.method!=='POST')return fail('허용하지 않는 요청 방식입니다.',405);
  if(path==='/api/requests/link/issue'){
    const client_id=onlyInt(data.client_id,'거래처',1);
    const client=one(db,'SELECT id,active FROM clients WHERE id=?',client_id);
    if(!client||!client.active)return fail('사용 중인 거래처만 발주 링크를 만들 수 있습니다.');
    const token=generateToken(),token_hash=await hashHex(token);
    const issuedAt=now();
    db.sql.exec("INSERT INTO buyer_links(client_id,token_hash,issued_at,revoked_at) VALUES(?,?,?,NULL) ON CONFLICT(client_id) DO UPDATE SET token_hash=excluded.token_hash,issued_at=excluded.issued_at,revoked_at=NULL",client_id,token_hash,issuedAt);
    db.audit('buyer_link_issued',{client_id});
    const origin=new URL(request.url).origin;
    return response({ok:true,url:origin+'/request/#'+await signedDisplayToken(db,{client_id,token_hash,issued_at:issuedAt}),client_id});
  }
  if(path==='/api/requests/link/revoke'){
    const client_id=onlyInt(data.client_id,'거래처',1);
    const link=one(db,'SELECT client_id FROM buyer_links WHERE client_id=? AND revoked_at IS NULL',client_id);
    if(!link)return fail('중지할 발주 링크가 없습니다.');
    db.sql.exec('UPDATE buyer_links SET revoked_at=? WHERE client_id=?',now(),client_id);
    db.audit('buyer_link_revoked',{client_id});
    return response({ok:true,client_id});
  }
  if(path==='/api/requests/cancel'){
    const id=onlyInt(data.id,'발주번호',1);
    const row=one(db,'SELECT id,status FROM buyer_requests WHERE id=?',id);
    if(!row||row.status!=='pending')return fail('대기 중인 발주만 취소할 수 있습니다.');
    db.sql.exec("UPDATE buyer_requests SET status='cancelled',processed_at=? WHERE id=?",now(),id);
    db.audit('buyer_request_cancelled',{id});
    return response({ok:true,id,status:'cancelled'});
  }
  if(path==='/api/requests/fulfill'){
    const id=onlyInt(data.id,'발주번호',1);
    const order=one(db,'SELECT * FROM buyer_requests WHERE id=?',id);
    if(!order||order.status!=='pending')return fail('이미 처리되었거나 없는 발주입니다.');
    const client=one(db,'SELECT * FROM clients WHERE id=? AND active=1',order.client_id);
    if(!client)return fail('비활성화된 거래처는 출고할 수 없습니다.');
    if(client.person==='미입력'||client.phone==='미입력')return fail('거래처 담당자·전화번호를 먼저 등록하세요.');
    const lines=all(db,'SELECT * FROM buyer_lines WHERE request_id=? ORDER BY id',id);
    if(lines.length===0)return fail('발주 품목이 없습니다.');
    const order_type=client.default_order_type==='internal'?'internal':'sale';
    let vat,date,previous_balance,memo,totals,amount_due,internal_cost;
    try{
      vat=order_type==='internal'?'none':String(data.vat||'none');
      if(vat!=='none'&&vat!=='tax')throw new Error('부가세 선택이 올바르지 않습니다.');
      date=dateCheck(String(data.order_date||kstToday()));
      memo=safeText('발주요청 #'+id+(order.note?' · '+order.note:''),'비고',false,500);
      totals=order_type==='internal'?{supply:0,tax:0,total:0}:calcTotals(lines,vat);
      internal_cost=order_type==='internal'?calcInternalCost(lines.map(i=>({...i,cost:one(db,'SELECT cost FROM products WHERE id=?',i.product_id)?.cost||0}))):0;
      previous_balance=order_type==='internal'?0:ensureReceivableOrderCanIssue(db,client.id,totals.total,data.previous_balance??0).previous_balance;
      amount_due=order_type==='internal'?0:calculatePayable(totals.total,previous_balance);
    }catch(e){return fail(e.message);}
    const grouped=new Map();
    for(const line of lines)if(line.product_id)grouped.set(line.product_id,(grouped.get(line.product_id)||0)+line.qty);
    for(const [product_id,needed] of grouped){
      const product=one(db,'SELECT id,name,cost FROM products WHERE id=?',product_id);
      if(!product)return fail('발주 제품이 삭제되어 출고할 수 없습니다.');
      const remaining=one(db,'SELECT COALESCE(SUM(delta),0) AS qty FROM movements WHERE product_id=?',product_id).qty;
      if(remaining<needed)return fail(product.name+': 재고 부족 '+(needed-remaining)+'개 (입고 후 다시 출고처리하세요.)');
    }
    const seller=one(db,'SELECT bank_name,account_number,account_holder,company_name,company_business_no,company_address,company_phone,company_email FROM receipt_settings WHERE id=1');
    const client_snapshot=JSON.stringify({business:client.business,person:client.person,phone:client.phone,business_no:client.business_no,address:client.address});
    let issued_order_id;
    db.ctx.storage.transactionSync(()=>{
      db.sql.exec("INSERT INTO orders(client_id,client_snapshot,order_date,order_type,vat,supply,tax,total,previous_balance,bank_snapshot,delivery_status,memo,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,'pending',?,?)",
        client.id,client_snapshot,date,order_type,vat,totals.supply,totals.tax,totals.total,previous_balance,JSON.stringify(seller||{}),memo,now());
      issued_order_id=one(db,'SELECT last_insert_rowid() AS id').id;
      for(const line of lines){
        const product=one(db,'SELECT cost FROM products WHERE id=?',line.product_id);
        const cost=product?.cost||0;
        db.sql.exec('INSERT INTO lines(order_id,product_id,name,qty,unit_price,cost,line_total) VALUES(?,?,?,?,?,?,?)',
          issued_order_id,line.product_id,line.name,line.qty,order_type==='internal'?0:line.unit_price,cost,order_type==='internal'?0:line.qty*line.unit_price);
        db.sql.exec('INSERT INTO movements(product_id,delta,cost,note,source,created_at) VALUES(?,?,?,?,?,?)',
          line.product_id,-line.qty,cost,'발주출고 #'+id,'order:'+issued_order_id,now());
      }
      db.sql.exec("UPDATE buyer_requests SET status='fulfilled',processed_at=?,issued_order_id=? WHERE id=? AND status='pending'",
        now(),issued_order_id,id);
      db.audit('buyer_request_fulfilled',{id,issued_order_id,client_id:client.id,order_type,supply:totals.supply,internal_cost});
    });
    return response({ok:true,id,issued_order_id,status:'fulfilled',order_type,internal_cost,...totals,previous_balance,amount_due});
  }
  return fail('없는 발주 관리 API 주소입니다.',404);
}
