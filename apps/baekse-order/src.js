import { DurableObject } from 'cloudflare:workers';
import {DEFAULT_PRODUCTS,onlyInt,safeText,dateCheck,calcTotals,calculatePayable,sessionDurationSeconds} from './logic.js';
import {ensureBuyerSchema,buyerSupplySummary,buyerLinkSummaries,handleBuyerPublic,handleBuyerAdmin} from './requests.js';
const json=(obj,status=200,headers={})=>new Response(JSON.stringify(obj),{status,headers:{'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store','X-Content-Type-Options':'nosniff',...headers}});
const err=(msg,status=400)=>json({error:msg},status);
const encode = new TextEncoder();
const hex = bytes=>[...new Uint8Array(bytes)].map(b=>b.toString(16).padStart(2,'0')).join('');
const digest=async s=>hex(await crypto.subtle.digest('SHA-256',encode.encode(s)));
const cleanRows = c=>Array.from(c);
const now=()=>new Date().toISOString();
const cookie=(token,age)=>`bs_order_session=${token}; Path=/api; HttpOnly; Secure; SameSite=Strict; Max-Age=${age}`;
export class OrderDatabase extends DurableObject {
 constructor(ctx,env){
  super(ctx,env);
  this.ctx=ctx;this.env=env;this.sql=ctx.storage.sql;
  ctx.blockConcurrencyWhile(async()=>{
    this.sql.exec(`CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,cost INTEGER NOT NULL,price INTEGER NOT NULL,active INTEGER NOT NULL DEFAULT 1,sort_order INTEGER NOT NULL DEFAULT 0,created_at TEXT NOT NULL);`);
    this.sql.exec(`CREATE TABLE IF NOT EXISTS clients (id INTEGER PRIMARY KEY AUTOINCREMENT,business TEXT NOT NULL,person TEXT NOT NULL,phone TEXT NOT NULL,business_no TEXT NOT NULL DEFAULT '',address TEXT NOT NULL DEFAULT '',active INTEGER NOT NULL DEFAULT 1,created_at TEXT NOT NULL);`);
    this.sql.exec(`CREATE TABLE IF NOT EXISTS movements (id INTEGER PRIMARY KEY AUTOINCREMENT,product_id INTEGER NOT NULL,delta INTEGER NOT NULL,cost INTEGER NOT NULL DEFAULT 0,note TEXT NOT NULL DEFAULT '',source TEXT NOT NULL DEFAULT '',created_at TEXT NOT NULL);`);
    this.sql.exec(`CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY AUTOINCREMENT,client_id INTEGER NOT NULL,client_snapshot TEXT NOT NULL,order_date TEXT NOT NULL,vat TEXT NOT NULL,supply INTEGER NOT NULL,tax INTEGER NOT NULL,total INTEGER NOT NULL,previous_balance INTEGER NOT NULL DEFAULT 0,bank_snapshot TEXT NOT NULL DEFAULT '{}',status TEXT NOT NULL DEFAULT 'issued',memo TEXT NOT NULL DEFAULT '',created_at TEXT NOT NULL,cancelled_at TEXT);`);
    this.sql.exec(`CREATE TABLE IF NOT EXISTS lines (id INTEGER PRIMARY KEY AUTOINCREMENT,order_id INTEGER NOT NULL,product_id INTEGER,name TEXT NOT NULL,qty INTEGER NOT NULL,unit_price INTEGER NOT NULL,cost INTEGER NOT NULL DEFAULT 0,line_total INTEGER NOT NULL);`);
    this.sql.exec(`CREATE TABLE IF NOT EXISTS audit (id INTEGER PRIMARY KEY AUTOINCREMENT,action TEXT NOT NULL,info TEXT NOT NULL,created_at TEXT NOT NULL);`);
    this.sql.exec(`CREATE TABLE IF NOT EXISTS sessions (hash TEXT PRIMARY KEY,expires INTEGER NOT NULL);`);
    this.sql.exec(`CREATE TABLE IF NOT EXISTS receipt_settings (
      id INTEGER PRIMARY KEY CHECK(id=1),
      bank_name TEXT NOT NULL DEFAULT '',
      account_number TEXT NOT NULL DEFAULT '',
      account_holder TEXT NOT NULL DEFAULT '',
      company_name TEXT NOT NULL DEFAULT '백세푸드',
      company_business_no TEXT NOT NULL DEFAULT '',
      company_address TEXT NOT NULL DEFAULT '',
      company_phone TEXT NOT NULL DEFAULT '',
      company_email TEXT NOT NULL DEFAULT '',
      updated_at TEXT NOT NULL
    );`);
    this.sql.exec("INSERT OR IGNORE INTO receipt_settings(id,bank_name,account_number,account_holder,updated_at) VALUES (1,'','','',?)",now());
    // Non-destructive schema upgrade for existing Durable Object SQLite databases.
    const orderCols=this.sql.exec('PRAGMA table_info(orders)').toArray().map(x=>x.name);
    if(!orderCols.includes('previous_balance'))this.sql.exec('ALTER TABLE orders ADD COLUMN previous_balance INTEGER NOT NULL DEFAULT 0');
    if(!orderCols.includes('bank_snapshot'))this.sql.exec("ALTER TABLE orders ADD COLUMN bank_snapshot TEXT NOT NULL DEFAULT '{}'");
    const productCols=this.sql.exec('PRAGMA table_info(products)').toArray().map(x=>x.name);
    if(!productCols.includes('sort_order'))this.sql.exec('ALTER TABLE products ADD COLUMN sort_order INTEGER NOT NULL DEFAULT 0');
    const settingCols=this.sql.exec('PRAGMA table_info(receipt_settings)').toArray().map(x=>x.name);
    for(const [name,defaultSQL] of [['company_name',"'백세푸드'"],['company_business_no',"''"],['company_address',"''"],['company_phone',"''"],['company_email',"''"]]){
      if(!settingCols.includes(name))this.sql.exec('ALTER TABLE receipt_settings ADD COLUMN '+name+' TEXT NOT NULL DEFAULT '+defaultSQL);
    }

    if(!this.sql.exec('SELECT id FROM products LIMIT 1').toArray()[0]) {
      for (const [name,cost,price] of DEFAULT_PRODUCTS) this.sql.exec('INSERT INTO products (name,cost,price,created_at) VALUES (?,?,?,?)',name,cost,price,now());
    }
    this.sql.exec('UPDATE products SET sort_order=id WHERE sort_order=0');
    ensureBuyerSchema(this);
    if(!this.sql.exec('SELECT id FROM clients LIMIT 1').toArray()[0]) this.sql.exec('INSERT INTO clients (business,person,phone,created_at) VALUES (?,?,?,?)','안산 중앙점','미입력','미입력',now());
  });
 }
 getOne(q,...args){return this.sql.exec(q,...args).toArray()[0]||null}
 all(q,...args){return cleanRows(this.sql.exec(q,...args))}
 audit(action,info){this.sql.exec('INSERT INTO audit (action,info,created_at) VALUES (?,?,?)',action,JSON.stringify(info),now())}
 async fetch(req){
   try {return await this.handle(req)}catch(e){return err(e.message||'처리 실패',e.status||400)}
 }
 async handle(req){
   const url=new URL(req.url), path=url.pathname;
   if(path.startsWith('/api/buyer/'))return handleBuyerPublic(this,req,path);
   if(req.method==='POST' && path==='/api/login'){
      if(!this.env.ADMIN_PASSWORD||this.env.ADMIN_PASSWORD.length<12)return err('관리자 비밀번호 설정이 필요합니다',503);
      const info=await req.json(); const pass=String(info.password||'');
      // A persistent login stores an opaque cookie, never the administrator password.
      const sessionAge=sessionDurationSeconds(info.remember);
      const ip=req.headers.get('CF-Connecting-IP')||'unknown';
      const key='login:'+ip;const attempts=this.ctx.storage.kv.get(key)||{count:0,since:Date.now()};
      if(Date.now()-attempts.since>900000){attempts.count=0;attempts.since=Date.now()}
      if(attempts.count>=10)return err('로그인 시도 제한: 15분 후 다시 시도하세요',429);
      if((await digest(pass))!==(await digest(this.env.ADMIN_PASSWORD))){attempts.count++;this.ctx.storage.kv.put(key,attempts);this.audit('login_failed',{ip});return err('로그인 정보가 일치하지 않습니다',401)}
      this.ctx.storage.kv.delete(key);
      const token=crypto.randomUUID()+crypto.randomUUID(),hash=await digest(token), expires=Date.now()+sessionAge*1000;
      this.sql.exec('DELETE FROM sessions WHERE expires<?',Date.now());
      this.sql.exec('INSERT INTO sessions (hash,expires) VALUES (?,?)',hash,expires);this.audit('login',{});
      return json({ok:true,remembered:info.remember===true},200,{'Set-Cookie':cookie(token,sessionAge)});
   }
   const token=(req.headers.get('Cookie')||'').match(/(?:^|;\s*)bs_order_session=([^;]+)/)?.[1];
   if(!token)return err('로그인이 필요합니다',401);
   const hash=await digest(token), session=this.getOne('SELECT expires FROM sessions WHERE hash=?',hash);
   if(!session||session.expires<Date.now())return err('로그인이 필요합니다',401);
   if(req.method!=='GET'){
     const origin=req.headers.get('Origin');const referer=req.headers.get('Referer');const expected=new URL(req.url).origin;
     if(origin!==expected && !(origin===null&&referer?.startsWith(expected+'/')))return err('Origin 검증 실패',403);
     if(Number(req.headers.get('Content-Length')||0)>500000)return err('요청 크기 초과',413);
   }
   if(path==='/api/session'&&req.method==='GET')return json({authenticated:true});
   if(path==='/api/logout'&&req.method==='POST'){this.sql.exec('DELETE FROM sessions WHERE hash=?',hash);return json({ok:true},200,{'Set-Cookie':cookie('',0)})}
   if(path==='/api/state'&&req.method==='GET'){
      const products=this.all('SELECT p.*,COALESCE((SELECT SUM(delta) FROM movements WHERE product_id=p.id),0) AS stock FROM products p ORDER BY p.sort_order,p.id');
      const clients=this.all('SELECT * FROM clients ORDER BY id');
      const orders=this.all('SELECT o.id,o.order_date,o.status,o.supply,o.tax,o.total,o.previous_balance,(o.total+o.previous_balance) AS amount_due,o.memo,o.created_at, json_extract(o.client_snapshot,\'$.business\') AS client_name FROM orders o ORDER BY o.id DESC LIMIT 300');
      const kstDate=new Date(Date.now()+9*3600000).toISOString().slice(0,10);
      const kstMonth=kstDate.slice(0,7);
      const todayStat=this.getOne("SELECT COUNT(*) AS count,COALESCE(SUM(total),0) AS amount FROM orders WHERE status='issued' AND order_date=?",kstDate);
      const monthStat=this.getOne("SELECT COUNT(*) AS count,COALESCE(SUM(total),0) AS amount FROM orders WHERE status='issued' AND substr(order_date,1,7)=?",kstMonth);
      const allStat=this.getOne("SELECT COUNT(*) AS count,COALESCE(SUM(total),0) AS amount FROM orders WHERE status='issued'");
      const metrics={date:kstDate,month:kstMonth,today_count:todayStat.count,today_amount:todayStat.amount,month_count:monthStat.count,month_amount:monthStat.amount,cumulative_count:allStat.count,cumulative_amount:allStat.amount};
      const movements=this.all('SELECT m.*,p.name AS product_name FROM movements m JOIN products p ON p.id=m.product_id ORDER BY m.id DESC LIMIT 300');
      const receipt_settings=this.getOne('SELECT bank_name,account_number,account_holder,company_name,company_business_no,company_address,company_phone,company_email FROM receipt_settings WHERE id=1');
      const buyer_dashboard=buyerSupplySummary(this);
      const buyer_links=buyerLinkSummaries(this);
      return json({products,clients,orders,movements,receipt_settings,metrics,buyer_dashboard,buyer_links});
   }
   if(path==='/api/export'&&req.method==='GET'){
      const data={exported_at:now(),products:this.all('SELECT * FROM products'),clients:this.all('SELECT * FROM clients'),orders:this.all('SELECT * FROM orders'),lines:this.all('SELECT * FROM lines'),movements:this.all('SELECT * FROM movements'),buyer_requests:this.all('SELECT * FROM buyer_requests'),buyer_lines:this.all('SELECT * FROM buyer_lines'),buyer_links:buyerLinkSummaries(this),audit:this.all('SELECT * FROM audit')};
      return json(data,200,{'Content-Disposition':'attachment; filename="baekse-order-backup.json"'});
   }
   const data=req.method==='POST'?await req.json():{};
   if(path.startsWith('/api/requests/'))return handleBuyerAdmin(this,req,path,data);
   if(path==='/api/receipt-settings'&&req.method==='POST'){
     const current=this.getOne('SELECT * FROM receipt_settings WHERE id=1');
     if(!current)throw new Error('관리자 설정이 준비되지 않았습니다');
     const field=(name,label,required,max)=>
       data[name]===undefined?current[name]:safeText(data[name],label,required,max);
     const bank_name=field('bank_name','은행명',false,80),
       account_number=field('account_number','계좌번호',false,60),
       account_holder=field('account_holder','예금주',false,80),
       company_name=field('company_name','회사명',true,100),
       company_business_no=field('company_business_no','사업자 등록번호',false,50),
       company_address=field('company_address','회사 주소',false,300),
       company_phone=field('company_phone','회사 연락처',false,40),
       company_email=field('company_email','이메일주소',false,120);
     const bank=[bank_name,account_number,account_holder];
     if(bank.some(Boolean)&&!bank.every(Boolean))throw new Error('은행명·계좌번호·예금주를 모두 입력하거나 모두 비우세요');
     if(account_number&&!/^[0-9\-\s]{3,60}$/.test(account_number))throw new Error('계좌번호는 숫자·공백·하이픈만 입력하세요');
     if(company_email&&!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(company_email))throw new Error('올바른 이메일주소를 입력하세요');
     this.sql.exec('UPDATE receipt_settings SET bank_name=?,account_number=?,account_holder=?,company_name=?,company_business_no=?,company_address=?,company_phone=?,company_email=?,updated_at=? WHERE id=1',
       bank_name,account_number,account_holder,company_name,company_business_no,company_address,company_phone,company_email,now());
     this.audit('admin_settings_update',{companyNameChanged:company_name!==current.company_name,bankConfigured:Boolean(bank_name)});
     return json({ok:true});
   }
   if(path==='/api/products'&&req.method==='POST'){
      const name=safeText(data.name,'제품명',true,80),cost=onlyInt(data.cost,'매입가',0,100000000),price=onlyInt(data.price,'출고가',0,100000000);
      if(data.id){const old=this.getOne('SELECT * FROM products WHERE id=?',onlyInt(data.id,'제품ID',1));if(!old)throw new Error('제품이 없습니다');this.sql.exec('UPDATE products SET name=?,cost=?,price=? WHERE id=?',name,cost,price,old.id);this.audit('product_update',{id:old.id});}
      else {const next=(this.getOne('SELECT COALESCE(MAX(sort_order),0)+1 AS n FROM products')||{}).n||1;this.sql.exec('INSERT INTO products(name,cost,price,sort_order,created_at) VALUES (?,?,?,?,?)',name,cost,price,next,now());this.audit('product_create',{name})}
      return json({ok:true});
   }
   if(path==='/api/products/move'&&req.method==='POST'){
     const id=onlyInt(data.id,'제품ID',1),direction=String(data.direction);
     if(!['up','down'].includes(direction))throw new Error('이동 방향이 올바르지 않습니다');
     const rows=this.all('SELECT id,sort_order FROM products ORDER BY sort_order,id');
     const index=rows.findIndex(p=>p.id===id);
     if(index<0)throw new Error('제품이 없습니다');
     const targetIndex=index+(direction==='up'?-1:1);
     if(targetIndex<0||targetIndex>=rows.length)throw new Error('더 이상 이동할 수 없습니다');
     const other=rows[targetIndex];
     this.ctx.storage.transactionSync(()=>{
       this.sql.exec('UPDATE products SET sort_order=? WHERE id=?',other.sort_order,id);
       this.sql.exec('UPDATE products SET sort_order=? WHERE id=?',rows[index].sort_order,other.id);
       this.audit('product_move',{id,direction,adjacentId:other.id});
     });
     return json({ok:true});
   }
   if(path==='/api/products/toggle'&&req.method==='POST'){
      const id=onlyInt(data.id,'제품ID',1),p=this.getOne('SELECT * FROM products WHERE id=?',id);if(!p)throw new Error('제품이 없습니다');this.sql.exec('UPDATE products SET active=? WHERE id=?',p.active?0:1,id);this.audit('product_toggle',{id,active:!p.active});return json({ok:true});
   }
   if(path==='/api/clients'&&req.method==='POST'){
      const business=safeText(data.business,'상호',true,100),person=safeText(data.person,'이름',true,70),phone=safeText(data.phone,'전화번호',true,40),business_no=safeText(data.business_no,'사업자번호',false,50),address=safeText(data.address,'주소',false,300);
      if(data.id){const id=onlyInt(data.id,'거래처ID',1);if(!this.getOne('SELECT id FROM clients WHERE id=?',id))throw new Error('거래처가 없습니다');this.sql.exec('UPDATE clients SET business=?,person=?,phone=?,business_no=?,address=? WHERE id=?',business,person,phone,business_no,address,id);this.audit('client_update',{id})}
      else{this.sql.exec('INSERT INTO clients(business,person,phone,business_no,address,created_at) VALUES (?,?,?,?,?,?)',business,person,phone,business_no,address,now());this.audit('client_create',{business})}
      return json({ok:true});
   }
   if(path==='/api/clients/toggle'&&req.method==='POST'){
      const id=onlyInt(data.id,'거래처ID',1),c=this.getOne('SELECT * FROM clients WHERE id=?',id);if(!c)throw new Error('거래처가 없습니다');this.sql.exec('UPDATE clients SET active=? WHERE id=?',c.active?0:1,id);this.audit('client_toggle',{id,active:!c.active});return json({ok:true})
   }
   if(path==='/api/stock'&&req.method==='POST'){
      const product_id=onlyInt(data.product_id,'제품ID',1),quantity=onlyInt(data.quantity,'입출고 수량',0,1000000),p=this.getOne('SELECT * FROM products WHERE id=?',product_id);if(!p||!p.active)throw new Error('유효하지 않은 제품');
      const type=String(data.type);if(type!=='adjust'&&quantity<1)throw new Error('입고 수량은 1개 이상');const current=this.getOne('SELECT COALESCE(SUM(delta),0) AS qty FROM movements WHERE product_id=?',product_id).qty;
      if(!['in','adjust','return'].includes(type))throw new Error('재고 처리 방식 오류');
      const delta=type==='adjust'?onlyInt(data.adjustment,'조정 수량',-1000000,1000000)-current:quantity;
      if(current+delta<0)throw new Error('재고가 마이너스가 될 수 없습니다');
      const cost=onlyInt(data.cost??p.cost,'매입가',0,100000000),note=safeText(data.note,'메모',false,500);
      this.sql.exec('INSERT INTO movements(product_id,delta,cost,note,source,created_at) VALUES (?,?,?,?,?,?)',product_id,delta,cost,note,type,now());this.audit('stock_change',{product_id,delta,type});return json({ok:true,stock:current+delta});
   }
   if(path==='/api/orders'&&req.method==='POST'){
      const client=this.getOne('SELECT * FROM clients WHERE id=? AND active=1',onlyInt(data.client_id,'거래처',1));if(!client)throw new Error('거래처를 선택하세요');
      if(client.person==='미입력'||client.phone==='미입력')throw new Error('거래처 필수 정보(이름·전화번호)를 먼저 입력하세요');
      const order_date=dateCheck(data.order_date),vat=data.vat==='tax'?'tax':data.vat==='none'?'none':null;if(!vat)throw new Error('부가세를 선택하세요');
      const memo=safeText(data.memo,'비고',false,500),list=Array.isArray(data.items)?data.items:[];
      if(list.length===0||list.length>50)throw new Error('출고 품목은 1~50개 입력하세요');
      const items=list.map(item=>{
        const qty=onlyInt(item.qty,'수량',1,1000000);
        if(item.product_id){const p=this.getOne('SELECT * FROM products WHERE id=? AND active=1',onlyInt(item.product_id,'제품ID',1));if(!p)throw new Error('등록되지 않은 상품');return{product_id:p.id,name:p.name,qty,unit_price:p.price,cost:p.cost}}
        const name=safeText(item.name,'기타 품명',true,120),unit_price=onlyInt(item.unit_price,'기타 출고단가',0,100000000);
        return {product_id:null,name,qty,unit_price,cost:0}
      });
      const totals=calcTotals(items,vat);
      const previous_balance=onlyInt(data.previous_balance??0,'전 잔고',0,2_000_000_000);
      const amount_due=calculatePayable(totals.total,previous_balance);
      const bank_setting=this.getOne('SELECT bank_name,account_number,account_holder,company_name,company_business_no,company_address,company_phone,company_email FROM receipt_settings WHERE id=1');
      const bank_snapshot=JSON.stringify(bank_setting||{bank_name:'',account_number:'',account_holder:''});
      const grouped=new Map();for(const i of items)if(i.product_id)grouped.set(i.product_id,(grouped.get(i.product_id)||0)+i.qty);
      for(const [id,q] of grouped){const remaining=this.getOne('SELECT COALESCE(SUM(delta),0) AS qty FROM movements WHERE product_id=?',id).qty;if(q>remaining)throw new Error(`${items.find(i=>i.product_id===id).name}: 재고 부족 (현재 ${remaining}개)`)}
      let id;
      this.ctx.storage.transactionSync(()=>{
        this.sql.exec('INSERT INTO orders(client_id,client_snapshot,order_date,vat,supply,tax,total,previous_balance,bank_snapshot,memo,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)',client.id,JSON.stringify({business:client.business,person:client.person,phone:client.phone,business_no:client.business_no,address:client.address}),order_date,vat,totals.supply,totals.tax,totals.total,previous_balance,bank_snapshot,memo,now());
        id=this.getOne('SELECT last_insert_rowid() AS id').id;
        for(const i of items){this.sql.exec('INSERT INTO lines(order_id,product_id,name,qty,unit_price,cost,line_total) VALUES(?,?,?,?,?,?,?)',id,i.product_id,i.name,i.qty,i.unit_price,i.cost,i.qty*i.unit_price);
          if(i.product_id)this.sql.exec('INSERT INTO movements(product_id,delta,cost,note,source,created_at) VALUES(?,?,?,?,?,?)',i.product_id,-i.qty,i.cost,'출고 #'+id,'order:'+id,now());}
        this.audit('order_create',{id,total:totals.total,previous_balance,amount_due});
      });
      return json({ok:true,id,...totals,previous_balance,amount_due});
   }
   if(path==='/api/orders/cancel'&&req.method==='POST'){
      const id=onlyInt(data.id,'명세표 ID',1),order=this.getOne('SELECT * FROM orders WHERE id=?',id);if(!order||order.status!=='issued')throw new Error('취소할 수 없는 출고건');
      this.ctx.storage.transactionSync(()=>{
        const lines=this.all('SELECT * FROM lines WHERE order_id=?',id);for(const l of lines)if(l.product_id)this.sql.exec('INSERT INTO movements(product_id,delta,cost,note,source,created_at) VALUES(?,?,?,?,?,?)',l.product_id,l.qty,l.cost,'출고취소 #'+id,'cancel:'+id,now());
        this.sql.exec('UPDATE orders SET status=?,cancelled_at=? WHERE id=?','cancelled',now(),id);this.audit('order_cancel',{id});
      });return json({ok:true});
   }
   if(path==='/api/orders/reissue'&&req.method==='POST'){
     const id=onlyInt(data.id,'명세표 ID',1);
     const order=this.getOne('SELECT * FROM orders WHERE id=?',id);
     if(!order||order.status!=='cancelled')throw new Error('출고처리할 취소 명세표가 없습니다');
     const lines=this.all('SELECT * FROM lines WHERE order_id=?',id);
     const grouped=new Map();
     for(const line of lines)if(line.product_id)grouped.set(line.product_id,(grouped.get(line.product_id)||0)+line.qty);
     for(const [productId,qty] of grouped){
       const product=this.getOne('SELECT id,name FROM products WHERE id=?',productId);
       if(!product)throw new Error('출고처리할 제품을 찾을 수 없습니다');
       const stock=this.getOne('SELECT COALESCE(SUM(delta),0) AS qty FROM movements WHERE product_id=?',productId).qty;
       if(stock<qty)throw new Error(product.name+': 재고 부족 (현재 '+stock+'개, 필요 '+qty+'개)');
     }
     this.ctx.storage.transactionSync(()=>{
       for(const line of lines)if(line.product_id)this.sql.exec(
         'INSERT INTO movements(product_id,delta,cost,note,source,created_at) VALUES(?,?,?,?,?,?)',
         line.product_id,-line.qty,line.cost,'출고복원 #'+id,'reissue:'+id,now()
       );
       this.sql.exec("UPDATE orders SET status='issued',cancelled_at=NULL WHERE id=?",id);
       this.audit('order_reissue',{id,total:order.total});
     });
     return json({ok:true,id,status:'issued'});
   }
   if(path==='/api/orders/delete'&&req.method==='POST'){
     if(data.confirm!=='DELETE')throw new Error('영구 삭제를 다시 확인하세요');
     const id=onlyInt(data.id,'명세표 ID',1);
     const order=this.getOne('SELECT * FROM orders WHERE id=?',id);
     if(!order)throw new Error('삭제할 명세표가 없습니다');
     const lineCount=this.getOne('SELECT COUNT(*) AS n FROM lines WHERE order_id=?',id).n;
     this.ctx.storage.transactionSync(()=>{
       this.sql.exec('DELETE FROM movements WHERE source IN (?,?,?)','order:'+id,'cancel:'+id,'reissue:'+id);
       this.sql.exec('DELETE FROM lines WHERE order_id=?',id);
       this.sql.exec('DELETE FROM orders WHERE id=?',id);
       this.audit('order_delete',{id,previousStatus:order.status,supply:order.supply,lineCount});
     });
     return json({ok:true,id,deleted:true,previousStatus:order.status});
   }
   if(path==='/api/orders/detail'&&req.method==='GET'){
     const id=onlyInt(Number(url.searchParams.get('id')),'명세표 ID',1),order=this.getOne('SELECT * FROM orders WHERE id=?',id);if(!order)return err('명세표를 찾을 수 없습니다',404);
     const bank_saved=JSON.parse(order.bank_snapshot||'{}');
     const current_settings=this.getOne('SELECT bank_name,account_number,account_holder,company_name,company_business_no,company_address,company_phone,company_email FROM receipt_settings WHERE id=1')||{};
     const bank={...current_settings,...bank_saved};
     return json({order:{...order,client:JSON.parse(order.client_snapshot),bank,
       amount_due:calculatePayable(order.total,order.previous_balance??0)},items:this.all('SELECT * FROM lines WHERE order_id=? ORDER BY id',id)});
   }
   return err('없는 API 주소',404);
 }
}
export default {
 async fetch(request,env){
   const url=new URL(request.url);
   if(url.pathname.startsWith('/api/')){
     if(!env.ORDER_DB)return err('DB 연결 없음',503);
     const obj=env.ORDER_DB.get(env.ORDER_DB.idFromName('baekse-order-single-db'));
     return obj.fetch(request);
   }
   if(!env.ASSETS)return err('정적 파일 미설정',503);
   const res=await env.ASSETS.fetch(request);
   const h=new Headers(res.headers);h.set('X-Robots-Tag','noindex, nofollow, noarchive');h.set('X-Content-Type-Options','nosniff');h.set('Referrer-Policy','no-referrer');h.set('Cache-Control','no-store');h.set('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; connect-src 'self'; img-src 'self' data:; frame-ancestors 'none'; base-uri 'none'; form-action 'self'");
   return new Response(res.body,{status:res.status,headers:h});
 }
};
