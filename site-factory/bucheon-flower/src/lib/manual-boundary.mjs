// Only an explicitly nonindexable, clean loopback URL is a pending local preview.
export function isLocalPreview(env={}) {
 if(env.SITE_INDEXABLE!=='false'||typeof env.SITE_URL!=='string')return false;
 if(!/^https?:\/\/(?:localhost|127\.0\.0\.1|\[::1\])(?::[0-9]{1,5})?\/?$/.test(env.SITE_URL))return false;
 try {
  const u=new URL(env.SITE_URL);
  return ['http:','https:'].includes(u.protocol)&&['localhost','127.0.0.1','[::1]'].includes(u.hostname)
    &&!u.username&&!u.password&&u.pathname==='/'&&!u.search&&!u.hash;
 } catch {return false;}
}
