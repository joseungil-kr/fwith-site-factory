import test from "node:test";
import assert from "node:assert/strict";
import { webcrypto } from "node:crypto";
import oauth, {OAuthStateVault,ADMIN_ORIGIN,AUTH_ORIGIN,CALLBACK} from "../src/index.mjs";

if(!globalThis.crypto)globalThis.crypto=webcrypto;
const path="/auth?provider=github&site_id=astro-chat-lab-qa.joseungil.workers.dev&scope=public_repo";
const fakeID="Ov23li123456789012345";
const fakeSecret="this-is-not-a-real-client-secret";
function env(){
  const states=new Map();
  const stateAPI={
    idFromName:s=>s,
    get:s=>{
      if(!states.has(s)){
        const map=new Map();
        const storage={
          async get(k){return map.get(k);},
          async put(k,v){map.set(k,v);},
          async delete(k){map.delete(k);},
          async setAlarm(){},
          async transaction(f){return f(this);}
        };
        states.set(s,new OAuthStateVault({storage}));
      }
      const doInstance=states.get(s);
      return {fetch:(url,options)=>doInstance.fetch(new Request(url,options))};
    }
  };
  return {GITHUB_OAUTH_CLIENT_ID:fakeID,GITHUB_OAUTH_CLIENT_SECRET:fakeSecret,
    OAUTH_STATE:stateAPI,debugStates:states};
}
function get(p,h={}){return new Request(AUTH_ORIGIN+p,{headers:h});}
async function start(e){
  const r=await oauth.fetch(get(path,{"Referer":ADMIN_ORIGIN+"/admin/"}),e);
  assert.equal(r.status,302);
  assert.equal(r.headers.get("Access-Control-Allow-Origin"),null);
  assert.match(r.headers.get("Set-Cookie"),/Secure; HttpOnly; SameSite=Lax/);
  const u=new URL(r.headers.get("Location"));
  assert.equal(u.origin,"https://github.com");
  assert.equal(u.searchParams.get("scope"),"public_repo");
  assert.equal(u.searchParams.get("redirect_uri"),CALLBACK);
  assert.equal(u.searchParams.get("client_id"),fakeID);
  const state=u.searchParams.get("state");
  assert.match(state,/^[A-Za-z0-9_-]{43}$/);
  return {state,cookie:r.headers.get("Set-Cookie").split(";")[0]};
}
test("unconfigured OAuth fails closed",async()=>{
  const e=env();delete e.GITHUB_OAUTH_CLIENT_SECRET;
  assert.equal((await oauth.fetch(get("/health"),e)).status,503);
  const r=await oauth.fetch(get(path),e);
  assert.equal(r.status,503);
  assert.equal(r.headers.get("Location"),null);
});
test("unknown hosts, paths, methods, foreign referrers and broad scopes denied",async()=>{
  const e=env();
  assert.equal((await oauth.fetch(new Request("https://evil.example/auth"),e)).status,403);
  assert.equal((await oauth.fetch(new Request(AUTH_ORIGIN+"/auth",{method:"POST"}),e)).status,405);
  assert.equal((await oauth.fetch(get("/nothere"),e)).status,404);
  assert.equal((await oauth.fetch(get(path.replace("public_repo","repo")),e)).status,400);
  assert.equal((await oauth.fetch(get(path.replace("astro-chat-lab-qa","another")),e)).status,400);
  assert.equal((await oauth.fetch(get(path,{"Referer":"https://evil.example/"}),e)).status,403);
  assert.equal((await oauth.fetch(get("/callback?code=validcode&state=not-real"),e)).status,400);
});
test("valid state, one-time exchange, popup source/origin and explicit postMessage target",async()=>{
  const e=env();
  const login=await start(e);
  const original=globalThis.fetch;let called=0;
  globalThis.fetch=async url=>{
    called++;
    if(String(url).endsWith("/login/oauth/access_token"))
      return new Response(JSON.stringify({access_token:"fake-github-token",scope:"public_repo"}),{status:200});
    if(String(url).endsWith("/user"))
      return new Response(JSON.stringify({login:"joseungil-kr"}),{status:200});
    if(String(url).includes("/collaborators/"))
      return new Response(JSON.stringify({permission:"admin"}),{status:200});
    throw new Error("unexpected call");
  };
  try{
    const callback="/callback?code=sample-code&state="+login.state;
    assert.equal((await oauth.fetch(get(callback),e)).status,400);
    assert.equal(called,0);
    assert.equal((await oauth.fetch(get(callback.replace(login.state,"A".repeat(43)),
      {"Cookie":login.cookie}),e)).status,400);
    assert.equal(called,0);
    const good=await oauth.fetch(get(callback,{"Cookie":login.cookie}),e);
    assert.equal(good.status,200);
    const html=await good.text();
    assert.match(html,/event\.source!==window\.opener/);
    assert.match(html,/event\.origin!==allowed/);
    assert.match(html,/authorization:github:success:/);
    assert.ok(html.includes(ADMIN_ORIGIN));
    assert.ok(!html.includes('postMessage("authorizing:github","*"'));
    assert.match(good.headers.get("Content-Security-Policy"),/nonce-/);
    assert.match(good.headers.get("Cache-Control"),/no-store/);
    assert.equal(called,3);
    const repeated=await oauth.fetch(get(callback,{"Cookie":login.cookie}),e);
    assert.equal(repeated.status,400);
    assert.equal(called,3);
    assert.ok(!(await repeated.text()).includes("fake-github-token"));
  }finally{globalThis.fetch=original;}
});
test("expired state rejected before GitHub token exchange",async()=>{
  const e=env(),login=await start(e);
  await e.debugStates.get(login.state).ctx.storage.put("challenge",
    {verifier:"0".repeat(64),expires:Date.now()-1});
  const bad=await oauth.fetch(get("/callback?code=sample-code&state="+login.state,
    {"Cookie":login.cookie}),e);
  assert.equal(bad.status,400);
});
test("wrong Github account, no write permission and broad OAuth token scope rejected",async()=>{
  const cases=[
    {login:"joseungil-kr",permission:"admin",scope:"repo"},
    {login:"other-user",permission:"admin",scope:"public_repo"},
    {login:"joseungil-kr",permission:"read",scope:"public_repo"},
  ];
  const original=globalThis.fetch;
  try{
    for(const cs of cases){
      const e=env(),l=await start(e);
      globalThis.fetch=async url=>{
        if(String(url).endsWith("/login/oauth/access_token"))
          return new Response(JSON.stringify({access_token:"unsafe-test-token",scope:cs.scope}),{status:200});
        if(String(url).endsWith("/user"))
          return new Response(JSON.stringify({login:cs.login}),{status:200});
        if(String(url).includes("/collaborators/"))
          return new Response(JSON.stringify({permission:cs.permission}),{status:200});
        throw Error("unexpected URL");
      };
      const out=await oauth.fetch(get("/callback?state="+l.state+"&code=sample-code",
        {"Cookie":l.cookie}),e);
      assert.equal(out.status,403);
      assert.ok(!(await out.text()).includes("unsafe-test-token"));
    }
  }finally{globalThis.fetch=original;}
});

test("non-secret stage identifiers classify provider transport and parse failures",async()=>{
  const original=globalThis.fetch;
  const failures=[
    {at:"TOKEN_FETCH",mode:"throw",failOn:1},
    {at:"TOKEN_FORMAT",mode:"html",failOn:1},
    {at:"USER_FETCH",mode:"throw",failOn:2},
    {at:"USER_FORMAT",mode:"html",failOn:2},
    {at:"PERMISSION_FETCH",mode:"throw",failOn:3},
    {at:"PERMISSION_FORMAT",mode:"html",failOn:3},
  ];
  try{
    for(const choice of failures){
      const e=env(),login=await start(e);
      let calls=0;
      globalThis.fetch=async(url)=>{
        calls++;
        if(calls===choice.failOn){
          if(choice.mode==="throw")throw new Error("sensitive_internal_error");
          return new Response("not-json-or-secrets",{status:200,headers:{"Content-Type":"text/html"}});
        }
        if(String(url).includes("/login/oauth/access_token"))
          return new Response(JSON.stringify({access_token:"sensitive-fake-token",scope:"public_repo"}),{status:200});
        if(String(url).endsWith("/user"))
          return new Response(JSON.stringify({login:"joseungil-kr"}),{status:200});
        if(String(url).includes("/collaborators/"))
          return new Response(JSON.stringify({permission:"admin"}),{status:200});
        throw new Error("invalid upstream request");
      };
      const url="/callback?code=sample-code&state="+login.state;
      const first=await oauth.fetch(get(url,{"Cookie":login.cookie}),e);
      assert.equal(first.status,502,choice.at);
      const body=await first.text();
      assert.equal(body,"GitHub authentication service unavailable ["+choice.at+"]");
      assert.ok(!body.includes("sensitive"));
      assert.ok(!body.includes("sample-code"));
      assert.ok(!body.includes(login.state));
      const replay=await oauth.fetch(get(url,{"Cookie":login.cookie}),e);
      assert.equal(replay.status,400);
      assert.equal(replay.headers.get("Location"),null);
    }
  }finally{globalThis.fetch=original;}
});

test("GitHub token exchange uses manual redirects and blocks cross-origin secret forwarding",async()=>{
  const original=globalThis.fetch;
  const e=env(),login=await start(e);
  let requests=0;
  globalThis.fetch=async(url,options)=>{
    requests++;
    assert.equal(url,"https://github.com/login/oauth/access_token");
    assert.equal(options.method,"POST");
    assert.equal(options.redirect,"manual");
    return new Response(null,{status:302,headers:{Location:"https://evil.example/collect"}});
  };
  try {
    const out=await oauth.fetch(get("/callback?state="+login.state+"&code=sample-code",
      {"Cookie":login.cookie}),e);
    assert.equal(out.status,502);
    assert.equal(await out.text(),"GitHub authentication service unavailable [TOKEN_REDIRECT]");
    assert.equal(requests,1);
    assert.equal((await oauth.fetch(get("/callback?state="+login.state+"&code=sample-code",
      {"Cookie":login.cookie}),e)).status,400);
  }finally{globalThis.fetch=original;}
});
test("non-2xx GitHub token endpoint response is classified without exposing body",async()=>{
  const original=globalThis.fetch;
  const e=env(),login=await start(e);
  globalThis.fetch=async(url,options)=>{
    assert.equal(options.redirect,"manual");
    return new Response('contains-token-or-secret-but-must-never-be-read',{status:404});
  };
  try {
    const out=await oauth.fetch(get("/callback?state="+login.state+"&code=sample-code",
      {"Cookie":login.cookie}),e);
    assert.equal(out.status,502);
    assert.equal(await out.text(),"GitHub authentication service unavailable [TOKEN_HTTP_404]");
  }finally{globalThis.fetch=original;}
});
test("GitHub 200 OAuth credential errors are safely classified without raw details",async()=>{
  const original=globalThis.fetch;
  const e=env(),login=await start(e);
  globalThis.fetch=async()=>new Response(JSON.stringify({
    error:"incorrect_client_credentials",
    error_description:"DO-NOT-LEAK-SECRET"
  }),{status:200});
  try {
    const out=await oauth.fetch(get("/callback?state="+login.state+"&code=sample-code",
      {"Cookie":login.cookie}),e);
    assert.equal(out.status,502);
    assert.equal(await out.text(),
      "GitHub authentication service unavailable [TOKEN_INCORRECT_CLIENT_CREDENTIALS]");
  }finally{globalThis.fetch=original;}
});
