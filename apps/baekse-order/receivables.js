/**
 * Per-client accounts receivable ledger.
 * Balances = explicitly set opening balance + issued orders created AFTER enrollment - nonvoid payments.
 * Older invoices are intentionally excluded to avoid double-counting an opening balance.
 * The order's previous_balance is a printed snapshot only and is NEVER summed into the ledger.
 */
import {onlyInt,safeText,dateCheck,calculatePayable} from './logic.js';

const now=()=>new Date().toISOString();
const one=(db,sql,...args)=>db.getOne(sql,...args);
const rows=(db,sql,...args)=>db.all(sql,...args);
const val=(number,label)=>onlyInt(number,label,0,2_000_000_000);
const json=(body,status=200)=>new Response(JSON.stringify(body),{status,headers:{'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store','X-Content-Type-Options':'nosniff'}});
const bad=(message,status=400)=>json({error:message},status);
const uuid=/^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$/i;

export function ensureReceivableSchema(db){
  db.sql.exec("CREATE TABLE IF NOT EXISTS receivable_accounts(client_id INTEGER PRIMARY KEY,opening_balance INTEGER NOT NULL,cutoff_order_id INTEGER NOT NULL,activated_at TEXT NOT NULL,updated_at TEXT NOT NULL)");
  db.sql.exec("CREATE TABLE IF NOT EXISTS receivable_payments(id INTEGER PRIMARY KEY AUTOINCREMENT,client_id INTEGER NOT NULL,request_key TEXT NOT NULL,amount INTEGER NOT NULL,paid_date TEXT NOT NULL,memo TEXT NOT NULL DEFAULT '',kind TEXT NOT NULL DEFAULT 'cash',created_at TEXT NOT NULL,voided_at TEXT,UNIQUE(client_id,request_key))");
  const paymentCols=db.sql.exec('PRAGMA table_info(receivable_payments)').toArray().map(x=>x.name);
  if(!paymentCols.includes('kind'))db.sql.exec("ALTER TABLE receivable_payments ADD COLUMN kind TEXT NOT NULL DEFAULT 'cash'");
  db.sql.exec("CREATE INDEX IF NOT EXISTS receivable_payments_client_id ON receivable_payments(client_id,id)");
}
export function getAccount(db,clientId){
  return one(db,'SELECT * FROM receivable_accounts WHERE client_id=?',clientId);
}
export function getReceivable(db,clientId){
  const account=getAccount(db,clientId);
  if(!account)return null;
  const sale=one(db,"SELECT COALESCE(SUM(total),0) AS amount,COUNT(*) AS count FROM orders WHERE client_id=? AND id>? AND status='issued' AND order_type='sale'",clientId,account.cutoff_order_id);
  const paid=one(db,"SELECT COALESCE(SUM(amount),0) AS amount FROM receivable_payments WHERE client_id=? AND kind='cash' AND voided_at IS NULL",clientId);
  const balance=account.opening_balance+sale.amount-paid.amount;
  if(!Number.isSafeInteger(balance))throw new Error('미수금 누계의 허용 범위를 초과했습니다.');
  return {client_id:clientId,opening_balance:account.opening_balance,cutoff_order_id:account.cutoff_order_id,
    activated_at:account.activated_at,updated_at:account.updated_at,issued_amount:sale.amount,
    issued_count:sale.count,paid_amount:paid.amount,balance};
}
export function getReceivables(db){
  const accounts=rows(db,'SELECT client_id FROM receivable_accounts ORDER BY client_id');
  const result=accounts.map(a=>getReceivable(db,a.client_id));
  return {accounts:result,total:result.reduce((n,a)=>n+a.balance,0),tracked_clients:result.length};
}
export function previousBalanceForOrder(db,clientId,manualAmount=0){
  const tracked=getReceivable(db,clientId);
  const previous_balance=tracked?val(tracked.balance,'미수금 잔액'):val(manualAmount,'전 잔고');
  return {tracked:Boolean(tracked),previous_balance};
}
/** Block removal that would leave a tracked client with an unsupported negative balance.
 * Older orders (at/before cutoff) are already represented in the entered opening balance.
 */
export function assertReceivableOrderRemoval(db,order){
  if(!order||order.status!=='issued'||order.order_type==='internal')return;
  const account=getReceivable(db,order.client_id);
  if(!account||order.id<=account.cutoff_order_id)return;
  if(account.balance-order.total<0){
    throw new Error('해당 거래처의 입금액이 남은 출고금액을 초과합니다. 입금 기록을 먼저 확인하거나 취소 처리한 뒤 다시 시도하세요.');
  }
}
export function ensureReceivableOrderCanIssue(db,clientId,saleTotal,manualAmount=0){
  const result=previousBalanceForOrder(db,clientId,manualAmount);
  calculatePayable(saleTotal,result.previous_balance);
  return result;
}
export function receivablePaymentHistory(db,clientId){
  return rows(db,'SELECT id,amount,paid_date,memo,kind,created_at,voided_at FROM receivable_payments WHERE client_id=? ORDER BY id DESC LIMIT 100',clientId);
}

export async function handleReceivablesAdmin(db,request,path,data){
  if(path==='/api/receivables/detail' && request.method==='GET'){
    const id=onlyInt(Number(new URL(request.url).searchParams.get('client_id')),'거래처',1);
    const client=one(db,'SELECT id,business FROM clients WHERE id=?',id);
    if(!client)return bad('거래처가 없습니다.',404);
    return json({client:{id:client.id,business:client.business},
      account:getReceivable(db,id),payments:receivablePaymentHistory(db,id)});
  }
  if(request.method!=='POST')return bad('허용되지 않은 요청 방식입니다.',405);
  if(path==='/api/receivables/opening'){
    const id=onlyInt(data.client_id,'거래처',1),amount=val(data.opening_balance,'기초 미수금');
    const client=one(db,'SELECT id FROM clients WHERE id=?',id);
    if(!client)return bad('거래처를 찾을 수 없습니다.',404);
    if(one(db,'SELECT default_order_type FROM clients WHERE id=?',id)?.default_order_type==='internal')return bad('내부출고 거래처에는 미수금 관리가 필요하지 않습니다.');
    if(getAccount(db,id))return bad('이미 미수금 관리가 시작된 거래처입니다. 기초잔액 수정 기능을 사용하세요.');
    const cutoff=(one(db,'SELECT COALESCE(MAX(id),0) AS max_id FROM orders')||{}).max_id||0;
    const timestamp=now();
    db.ctx.storage.transactionSync(()=>{
      db.sql.exec('INSERT INTO receivable_accounts(client_id,opening_balance,cutoff_order_id,activated_at,updated_at) VALUES(?,?,?,?,?)',id,amount,cutoff,timestamp,timestamp);
      db.audit('receivable_opening',{client_id:id,amount,cutoff_order_id:cutoff});
    });
    return json({ok:true,account:getReceivable(db,id)});
  }
  if(path==='/api/receivables/opening/revise'){
    const id=onlyInt(data.client_id,'거래처',1),amount=val(data.opening_balance,'수정 기초 미수금'),
      reason=safeText(data.reason,'수정 사유',true,200);
    const account=getAccount(db,id);
    if(!account)return bad('먼저 기초 미수금을 등록하세요.');
    const current=getReceivable(db,id);
    const projected=amount+current.issued_amount-current.paid_amount;
    if(projected<0 || projected>2_000_000_000)return bad('변경하면 미수금이 음수가 되거나 한도를 초과합니다. 입금 내역부터 확인하세요.');
    if(account.opening_balance===amount)return bad('기존 기초 미수금과 동일합니다.');
    db.ctx.storage.transactionSync(()=>{
      db.sql.exec('UPDATE receivable_accounts SET opening_balance=?,updated_at=? WHERE client_id=?',amount,now(),id);
      db.audit('receivable_opening_revised',{client_id:id,previous:account.opening_balance,next:amount,reason});
    });
    return json({ok:true,account:getReceivable(db,id)});
  }
  if(path==='/api/receivables/payments'){
    const id=onlyInt(data.client_id,'거래처',1),amount=onlyInt(data.amount,'입금액',1,2_000_000_000),
      paid_date=dateCheck(data.paid_date),memo=safeText(data.memo,'입금 메모',false,200);
    const key=String(data.request_key||'');
    if(!uuid.test(key))return bad('입금 등록 요청 키가 올바르지 않습니다.');
    const existing=one(db,'SELECT id,amount,paid_date,voided_at FROM receivable_payments WHERE client_id=? AND request_key=?',id,key);
    if(existing)return json({ok:true,duplicate:true,id:existing.id,voided:Boolean(existing.voided_at)});
    if(one(db,'SELECT default_order_type FROM clients WHERE id=?',id)?.default_order_type==='internal')return bad('내부출고 거래처에는 실제 입금을 등록할 수 없습니다.');
    const current=getReceivable(db,id);
    if(!current)return bad('이 거래처의 기초 미수금부터 등록하세요.');
    if(current.balance<amount)return bad('입금액이 현재 미수금보다 큽니다. 초과입금·선수금은 현재 지원하지 않습니다.');
    let paymentId;
    db.ctx.storage.transactionSync(()=>{
      db.sql.exec('INSERT INTO receivable_payments(client_id,request_key,amount,paid_date,memo,created_at) VALUES(?,?,?,?,?,?)',id,key,amount,paid_date,memo,now());
      paymentId=one(db,'SELECT last_insert_rowid() AS id').id;
      db.audit('receivable_payment_created',{id:paymentId,client_id:id,amount,paid_date});
    });
    return json({ok:true,id:paymentId,account:getReceivable(db,id)});
  }
  if(path==='/api/receivables/payments/void'){
    const id=onlyInt(data.id,'입금번호',1),
      reason=safeText(data.reason,'입금 취소 사유',true,200);
    const item=one(db,'SELECT id,client_id,amount,kind,voided_at FROM receivable_payments WHERE id=?',id);
    if(!item)return bad('입금 내역이 없습니다.',404);
    if(item.voided_at)return bad('이미 취소된 입금 내역입니다.');
    if(item.kind!=='cash')return bad('비현금 내부정리 기록은 입금 취소 대상이 아닙니다.');
    const current=getReceivable(db,item.client_id);
    if(!current||current.balance+item.amount>2_000_000_000)return bad('입금 취소 후 미수금이 계산 한도를 초과합니다.');
    db.ctx.storage.transactionSync(()=>{
      db.sql.exec('UPDATE receivable_payments SET voided_at=? WHERE id=? AND voided_at IS NULL',now(),id);
      db.audit('receivable_payment_voided',{id,client_id:item.client_id,amount:item.amount,reason});
    });
    return json({ok:true,account:getReceivable(db,item.client_id)});
  }
  return bad('없는 미수금 관리 API 주소입니다.',404);
}
