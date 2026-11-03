// Actual local Worker integration test; no real account password is used.
import assert from 'node:assert/strict';
const base='http://127.0.0.1:8787', password='ci-only-strong-example-password-2026';
let ready=false;
for(let i=0;i<80;i++){
  try {const r=await fetch(base+'/');ready=r.ok&&((await r.text()).includes('백세푸드'));if(ready)break;}catch{}
  await new Promise(resolve=>setTimeout(resolve,1000));
}
assert.ok(ready,'Local Worker not reachable');
let anonymous=await fetch(base+'/api/state');assert.equal(anonymous.status,401);
async function login(remember){
 const response=await fetch(base+'/api/login',{method:'POST',headers:{'Content-Type':'application/json','Origin':base},body:JSON.stringify({password,remember})});
 assert.equal(response.status,200,'Login failed: '+await response.text());
 const header=response.headers.get('set-cookie')||'';
 assert.ok(header.includes('HttpOnly')&&header.includes('Secure')&&header.includes('SameSite=Strict'),'Session cookie security flags missing');
 assert.ok(header.includes('Path=/api'),'Session cookie scope incorrect');
 return {header,cookie:header.split(';')[0]};
}
let short=await login(false);
assert.ok(short.header.includes('Max-Age=28800'),'Default session must expire in 8 hours');
assert.equal((await fetch(base+'/api/session',{headers:{Cookie:short.cookie}})).status,200);
let logout=await fetch(base+'/api/logout',{method:'POST',headers:{Cookie:short.cookie,Origin:base}});
assert.equal(logout.status,200);
assert.equal((await fetch(base+'/api/session',{headers:{Cookie:short.cookie}})).status,401,'Logout must revoke existing session');
let long=await login(true);
assert.ok(long.header.includes('Max-Age=2592000'),'Remember-me session must expire after 30 days');
const auth=await fetch(base+'/api/state',{headers:{Cookie:long.cookie}});
assert.equal(auth.status,200);const state=await auth.json();assert.equal(state.products.length,6);
logout=await fetch(base+'/api/logout',{method:'POST',headers:{Cookie:long.cookie,Origin:base}});
assert.equal(logout.status,200);
assert.equal((await fetch(base+'/api/state',{headers:{Cookie:long.cookie}})).status,401);
let hidden=await fetch(base+'/');
let html=await hidden.text();
assert.ok(html.includes('id="login-remember"')&&html.includes('name="remember"'),'Remember-me checkbox missing');
console.log('REMEMBER_HTTP_PASS: cookie default 8h/remember 30d, secure flags, login, stock authorization, logout token revocation');
