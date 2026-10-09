/**
 * Isolated Decap GitHub OAuth for the Astro chat lab (not a generic proxy).
 * Session: 256-bit nonce + independent proof cookie, 10-minute SQLite-backed
 * Durable Object, atomic one-time consumption. No token persistence/logging.
 */
export const ADMIN_ORIGIN = "https://astro-chat-lab-qa.joseungil.workers.dev";
export const AUTH_ORIGIN = "https://astro-chat-lab-oauth-qa.joseungil.workers.dev";
export const CALLBACK = AUTH_ORIGIN + "/callback";
const USER = "joseungil-kr";
const REPO = "fwith-site-factory";
const LIFETIME = 600000;
const COOKIE = "__Host-astro_lab_oauth";
const COOKIE_FLAGS = "Path=/; Secure; HttpOnly; SameSite=Lax";

function headers(extra = {}) {
  return Object.assign({
    "Cache-Control": "no-store, max-age=0",
    "Pragma": "no-cache",
    "Referrer-Policy": "no-referrer",
    "X-Content-Type-Options": "nosniff",
    "X-Robots-Tag": "noindex, nofollow",
    "X-Frame-Options": "DENY",
  }, extra);
}
function fail(message, status = 400, extra = {}) {
  return new Response(message, {
    status, headers: headers(Object.assign({ "Content-Type": "text/plain; charset=utf-8" },extra)),
  });
}
function fresh(bytes) {
  const data=crypto.getRandomValues(new Uint8Array(bytes));
  return btoa(String.fromCharCode(...data)).replace(/\+/g,"-").replace(/\//g,"_").replace(/=+$/,"");
}
async function digest(value) {
  const hash=await crypto.subtle.digest("SHA-256",new TextEncoder().encode(value));
  return Array.from(new Uint8Array(hash),c=>c.toString(16).padStart(2,"0")).join("");
}
function constantTime(a,b) {
  if(typeof a!=="string"||typeof b!=="string"||a.length!==b.length)return false;
  let diff=0;
  for(let i=0;i<a.length;i++)diff|=a.charCodeAt(i)^b.charCodeAt(i);
  return diff===0;
}
function extractCookie(value) {
  for(const part of (value||"").split(";")){
    const idx=part.indexOf("=");
    if(idx>=0 && part.slice(0,idx).trim()===COOKIE)return part.slice(idx+1).trim();
  }
  return "";
}
function stateFormat(s){return typeof s==="string"&&/^[A-Za-z0-9_-]{43}$/.test(s);}
function verifierFormat(s){return typeof s==="string"&&/^[a-f0-9]{64}$/.test(s);}
function clearCookie(){return COOKIE+"=; Max-Age=0; "+COOKIE_FLAGS;}
function vault(env,nonce){return env.OAUTH_STATE.get(env.OAUTH_STATE.idFromName(nonce));}

/** Security-sensitive state API only accessible through the Worker binding. */
export class OAuthStateVault {
  constructor(ctx){this.ctx=ctx;}
  async fetch(request){
    const action=new URL(request.url).pathname;
    if(request.method!=="POST")return fail("Method not allowed",405);
    let input;
    try{input=await request.json();}catch{return fail("Invalid input",400);}
    if(action==="/network-probe-once") {
      return this.ctx.storage.transaction(async tx=>{
        if(await tx.get("transportProbeConsumed"))return fail("Probe already consumed",409);
        await tx.put("transportProbeConsumed",true);
        return fail("Probe authorized",201);
      });
    }
    if(!verifierFormat(input.verifier))return fail("Invalid verifier",400);
    if(action==="/create"){
      if(typeof input.expires!=="number"||input.expires<=Date.now()||
        input.expires>Date.now()+LIFETIME+1000)return fail("Invalid expiry",400);
      return this.ctx.storage.transaction(async tx=>{
        if(await tx.get("challenge"))return fail("Already exists",409);
        await tx.put("challenge",{verifier:input.verifier,expires:input.expires});
        await tx.setAlarm(input.expires);
        return fail("Created",201);
      });
    }
    if(action==="/consume"){
      return this.ctx.storage.transaction(async tx=>{
        const current=await tx.get("challenge");
        if(!current)return fail("Already consumed",409);
        // Deliberately consume EVEN on mismatch or expiry (fail closed).
        await tx.delete("challenge");
        if(current.expires<=Date.now()||!constantTime(current.verifier,input.verifier))
          return fail("Invalid state",403);
        return fail("Consumed",200);
      });
    }
    return fail("Not found",404);
  }
  async alarm(){await this.ctx.storage.delete("challenge");}
}
async function requestState(env,nonce,proof,action,expires){
  const target=vault(env,nonce);
  const payload={verifier:await digest(proof)};
  if(action==="create")payload.expires=expires;
  const result=await target.fetch("https://internal.invalid/"+action,{
    method:"POST",headers:{"Content-Type":"application/json"},
    body:JSON.stringify(payload)
  });
  return result.status===(action==="create"?201:200);
}
function ready(env){
  return typeof env.GITHUB_OAUTH_CLIENT_ID==="string" &&
    /^[A-Za-z0-9_]{10,100}$/.test(env.GITHUB_OAUTH_CLIENT_ID) &&
    typeof env.GITHUB_OAUTH_CLIENT_SECRET==="string" &&
    env.GITHUB_OAUTH_CLIENT_SECRET.length>=16 && Boolean(env.OAUTH_STATE);
}
async function auth(request,url,env){
  if(url.searchParams.get("provider")!=="github"||
     url.searchParams.get("scope")!=="public_repo"||
     url.searchParams.get("site_id")!==new URL(ADMIN_ORIGIN).hostname)
    return fail("Invalid provider, CMS site or GitHub scope",400);
  // Referer may be omitted due to browser privacy policy, but cannot be a foreign origin.
  const ref=request.headers.get("Referer");
  if(ref){
    try{if(new URL(ref).origin!==ADMIN_ORIGIN)return fail("Invalid opener origin",403);}
    catch{return fail("Invalid opener origin",403);}
  }
  if(!ready(env))return fail("GitHub OAuth setup is not finished",503);
  const state=fresh(32),proof=fresh(32);
  if(!await requestState(env,state,proof,"create",Date.now()+LIFETIME))
    return fail("Failed to initialize OAuth state",503);
  const redirect=new URL("https://github.com/login/oauth/authorize");
  redirect.searchParams.set("client_id",env.GITHUB_OAUTH_CLIENT_ID);
  redirect.searchParams.set("redirect_uri",CALLBACK);
  redirect.searchParams.set("scope","public_repo");
  redirect.searchParams.set("state",state);
  redirect.searchParams.set("allow_signup","false");
  return new Response(null,{
    status:302,headers:headers({
      Location:redirect.toString(),
      "Set-Cookie":COOKIE+"="+state+"."+proof+"; Max-Age=600; "+COOKIE_FLAGS
    })
  });
}
// Only fixed, non-sensitive stage codes may reach the popup. Never copy raw
// GitHub responses, exception messages, URL parameters or tokens into errors.
class OAuthStageFailure extends Error {
  constructor(stage) {
    super("OAuth upstream stage failed");
    this.stage=stage;
  }
}
async function github(url,token,stage){
  let r;
  try {
    r=await fetch(url,{
      headers:{
        Authorization:"Bearer "+token,
        "User-Agent":"astro-chat-lab-oauth/1",
        Accept:"application/vnd.github+json",
        "X-GitHub-Api-Version":"2022-11-28"
      },redirect:"error"
    });
  } catch {
    throw new OAuthStageFailure(stage+"_FETCH");
  }
  if(!r.ok)return null;
  try {
    return await r.json();
  } catch {
    throw new OAuthStageFailure(stage+"_FORMAT");
  }
}
async function exchange(env,code){
  let r;
  try {
    r=await fetch("https://github.com/login/oauth/access_token",{
      method:"POST",redirect:"error",
      headers:{"Accept":"application/json","Content-Type":"application/json",
        "User-Agent":"astro-chat-lab-oauth/1"},
      body:JSON.stringify({client_id:env.GITHUB_OAUTH_CLIENT_ID,
        client_secret:env.GITHUB_OAUTH_CLIENT_SECRET,code,redirect_uri:CALLBACK})
    });
  } catch {
    throw new OAuthStageFailure("TOKEN_FETCH");
  }
  if(!r.ok)return null;
  let info;
  try {
    info=await r.json();
  } catch {
    throw new OAuthStageFailure("TOKEN_FORMAT");
  }
  const scope=typeof info.scope==="string"?info.scope.split(",").map(x=>x.trim()):[];
  if(typeof info.access_token!=="string"||!scope.includes("public_repo")||
    scope.includes("repo")||scope.includes("delete_repo"))return null;
  const user=await github("https://api.github.com/user",info.access_token,"USER");
  if(!user||user.login!==USER)return null;
  const permission=await github("https://api.github.com/repos/"+USER+"/"+REPO+
    "/collaborators/"+encodeURIComponent(user.login)+"/permission",
    info.access_token,"PERMISSION");
  if(!permission||!["admin","maintain","write"].includes(permission.permission))return null;
  return info.access_token;
}
function callbackPage(token){
  // Decap 3.16.3 NetlifyAuthenticator handshake with STRICT target/source/origin.
  // Token exists in one no-store callback HTML response ONLY, never a URL or log.
  const nonce=fresh(16);
  const target=JSON.stringify(ADMIN_ORIGIN);
  const message=JSON.stringify("authorization:github:success:"+
    JSON.stringify({token,provider:"github"})).replace(/</g,"\\u003c");
  const html=[
    '<!doctype html><html lang="ko"><head><meta charset="utf-8">',
    '<meta name="robots" content="noindex,nofollow">',
    '<title>Decap GitHub 로그인</title></head>',
    '<body><p>GitHub 인증을 마무리하고 편집기로 돌아갑니다.</p>',
    '<script nonce="'+nonce+'">',
    '(() => { "use strict";',
    ' const allowed='+target+';',
    ' if(!window.opener){document.body.textContent="편집기 창을 찾을 수 없습니다.";return;}',
    ' const receive = (event) => {',
    '  if(event.origin!==allowed || event.source!==window.opener ||',
    '     event.data!=="authorizing:github") return;',
    '  window.removeEventListener("message",receive);',
    '  window.opener.postMessage('+message+',allowed);',
    ' };',
    ' window.addEventListener("message",receive);',
    ' window.opener.postMessage("authorizing:github",allowed);',
    '})();',
    '</script></body></html>'
  ].join("\n");
  return new Response(html,{status:200,headers:headers({
    "Content-Type":"text/html; charset=utf-8",
    "Set-Cookie":clearCookie(),
    "Content-Security-Policy":"default-src 'none'; script-src 'nonce-"+nonce+
      "'; base-uri 'none'; frame-ancestors 'none'; form-action 'none'",
  })});
}
async function callback(request,url,env){
  if(!ready(env))return fail("GitHub OAuth setup is not finished",503);
  const state=url.searchParams.get("state");
  const code=url.searchParams.get("code");
  const cookie=extractCookie(request.headers.get("Cookie"));
  const dot=cookie.indexOf(".");
  const boundState=dot>=0?cookie.slice(0,dot):null;
  const proof=dot>=0?cookie.slice(dot+1):null;
  const clear={"Set-Cookie":clearCookie()};
  if(!stateFormat(state)||!stateFormat(boundState)||!stateFormat(proof)||
    !constantTime(state,boundState)||typeof code!=="string"||
    code.length<5||code.length>1024)
    return fail("Invalid or expired authentication session",400,clear);
  if(!await requestState(env,state,proof,"consume"))
    return fail("Invalid or expired authentication session",400,clear);
  try{
    const token=await exchange(env,code);
    if(!token)return fail("GitHub account or repository write access denied",403,clear);
    return callbackPage(token);
  }catch(error){
    const stage=error instanceof OAuthStageFailure ? error.stage : "CALLBACK_RENDER";
    return fail("GitHub authentication service unavailable ["+stage+"]",502,clear);
  }
}

/**
 * One-time, self-expiring transport diagnosis. No real OAuth credentials or
 * authorization codes are used. Called once by the deployment runner, then
 * removed from the source immediately after the diagnostic completes.
 */
async function tokenTransportProbe(env) {
  if(Date.now()>Date.parse("2026-10-09T08:00:00Z"))return fail("Not found",404);
  const once=await env.OAUTH_STATE.get(
    env.OAUTH_STATE.idFromName("token-transport-diagnostic-v1")
  ).fetch("https://internal.invalid/network-probe-once",{
    method:"POST",
    headers:{"Content-Type":"application/json"},
    body:"{}",
  });
  if(once.status!==201)return fail("Already tested",410);
  const results={};
  for(const mode of ["manual","error"]) {
    try {
      const result=await fetch("https://github.com/login/oauth/access_token",{
        method:"POST",
        redirect:mode,
        headers:{
          Accept:"application/json",
          "Content-Type":"application/json",
          "User-Agent":"astro-chat-lab-transport-check/1",
        },
        body:JSON.stringify({
          client_id:"invalid-diagnostic-client",
          client_secret:"not-a-secret",
          code:"not-an-oauth-code",
          redirect_uri:CALLBACK,
        })
      });
      results[mode]={status:result.status,redirected:result.status>=300&&result.status<400};
    }catch(err) {
      const name=err instanceof TypeError ? "TypeError" : err instanceof Error ? "Error" : "Unknown";
      const safe=typeof err?.message==="string"?err.message:"";
      const className=/redirect/i.test(safe)?"redirect":
        /network|fetch failed|connection|socket/i.test(safe)?"network":
        /invalid|unsupported/i.test(safe)?"request":
        /policy|disallow|forbid|security/i.test(safe)?"policy":"unknown";
      results[mode]={errorName:name,errorKind:className};
    }
  }
  return new Response(JSON.stringify({diagnostic:"noncredential-token-transport",results}),{
    status:200,
    headers:headers({"Content-Type":"application/json; charset=utf-8"}),
  });
}

export default {
  async fetch(request,env){
    const url=new URL(request.url);
    if(url.origin!==AUTH_ORIGIN)return fail("Unrecognized OAuth hostname",403);
    if(request.method!=="GET")return fail("Method not allowed",405);
    if(url.pathname==="/__diagnostics__/token-transport-20261009")
      return tokenTransportProbe(env);
    if(url.pathname==="/health"){
      const configured=ready(env);
      return new Response(JSON.stringify({
        service:"astro-chat-lab-oauth-qa",
        configured,callback:CALLBACK
      }),{status:configured?200:503,headers:headers({
        "Content-Type":"application/json; charset=utf-8"
      })});
    }
    if(url.pathname==="/auth")return auth(request,url,env);
    if(url.pathname==="/callback")return callback(request,url,env);
    return fail("Not found",404);
  }
};
