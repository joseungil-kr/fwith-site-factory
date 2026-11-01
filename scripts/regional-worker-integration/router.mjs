// Local pilot only. Deploy only after live-version backup and independent review.
const hosts = new Map([
  ['seoul-dongjak.fwith.kr', '/__regional/dongjak'],
  ['seoul-geumcheon.fwith.kr', '/__regional/geumcheon'],
]);

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const prefix = hosts.get(url.hostname);
    if (!prefix) return new Response('Not Found', {status: 404});
    // Reject encoded separators rather than let different URL parsers cross namespaces.
    if (/%(?:2f|5c|25)/i.test(url.pathname)) return new Response('Bad Request', {status: 400});
    const assetUrl = new URL(url);
    assetUrl.pathname = prefix + url.pathname;
    const response = await env.ASSETS.fetch(new Request(assetUrl, request));
    const location = response.headers.get('Location');
    if (!location || response.status < 300 || response.status >= 400) return response;
    const redirect = new URL(location, assetUrl);
    if (redirect.origin !== assetUrl.origin || !redirect.pathname.startsWith(prefix + '/')) {
      return new Response('Invalid asset redirect', {status: 502});
    }
    redirect.pathname = redirect.pathname.slice(prefix.length);
    const headers = new Headers(response.headers);
    headers.set('Location', location.startsWith('/') && !location.startsWith('//')
      ? redirect.pathname + redirect.search + redirect.hash : redirect.href);
    return new Response(response.body, {status: response.status, statusText: response.statusText, headers});
  },
};
