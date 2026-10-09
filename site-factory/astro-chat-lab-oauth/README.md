# Astro Chat Lab — GitHub OAuth setup

This separate Worker is the Decap 3.16.3 OAuth broker ONLY for
https://astro-chat-lab-qa.joseungil.workers.dev/admin/.

## Fixed URLs

- Worker: astro-chat-lab-oauth-qa
- Public authorization endpoint: https://astro-chat-lab-oauth-qa.joseungil.workers.dev/auth
- GitHub OAuth callback: https://astro-chat-lab-oauth-qa.joseungil.workers.dev/callback
- Health: https://astro-chat-lab-oauth-qa.joseungil.workers.dev/health
- Admin origin: https://astro-chat-lab-qa.joseungil.workers.dev

OAuth requests only scope public_repo. GitHub OAuth public_repo authorizes
access to OTHER PUBLIC repositories writable by the same consenting user;
the CMS folder and branch are NOT authorization isolation.

## Secure GitHub OAuth App registration

1. In https://github.com/settings/developers, open OAuth Apps -> New OAuth App.
2. Name: Astro Chat Lab Decap CMS
3. Homepage URL: https://astro-chat-lab-qa.joseungil.workers.dev/
4. Authorization callback URL (EXACTLY):
   https://astro-chat-lab-oauth-qa.joseungil.workers.dev/callback
5. Do NOT enable wildcard callback URLs or device flow.
6. Generate a client secret via GitHub's own UI. Do not disclose it in chat,
   commit it to the repository, or expose it in admin/config.yml.
7. In Cloudflare dashboard -> Workers & Pages -> astro-chat-lab-oauth-qa ->
   Settings -> Variables/Secrets, add:
   - GITHUB_OAUTH_CLIENT_ID = GitHub OAuth App Client ID (public identifier;
     safe to use as plaintext variable, but can also be encrypted)
   - GITHUB_OAUTH_CLIENT_SECRET = GitHub OAuth App Client Secret
     (MUST use encrypted Secret type)
8. Once both exist, /health returns configured:true (HTTP 200). No secret
   values are returned.
9. Only then change the static CMS config to:
     backend:
       base_url: https://astro-chat-lab-oauth-qa.joseungil.workers.dev
       auth_endpoint: auth
   and remove the CMS_MANUAL_INIT guard from /admin/index.html.
10. Login via GitHub and test actual Decap editing, draft and image saving.

## Security and compliance

State is 256-bit random, bound to a distinct 256-bit HttpOnly SameSite=Lax
secure cookie, stored for 10 minutes in a private SQLite-backed Durable Object
and atomically consumed once before code exchange. Cookie is deleted on
callback. Callback only responds from the fixed auth Worker hostname,
uses strict opener postMessage target, checks event.origin and event.source,
and uses a strict CSP with a one-time nonce. No wildcard postMessage, no
CORS blanket allowance, no token logging. OAuth tokens are returned only
to the Decap popup opener after verified origin/source handshake.
Only GitHub login joseungil-kr with admin/maintain/write repo permission
can get a success response.

No authentication credentials have been provisioned by the deployed
source. OAuth setup and actual browser operations must be independently
verified. On a public GitHub repository, draft files remain publicly readable
in GitHub even though they are excluded from the Astro site.

Source reference: official Decap v3.16.3 NetlifyAuthenticator, MIT.
Only the handshake protocol is reused from reviewed examples; the
insecure original Cloudflare community proxy is NOT installed.

The auth Durable Object is used only for short-lived OAuth state and
does not serve as a blog content database. Cloudflare plan usage limits apply.

## Non-sensitive OAuth failure diagnosis

The browser popup may show `GitHub authentication service unavailable [STAGE]`.
These stage names contain no tokens, authorization codes, state values, or secret
material; a previous generic 502 did not reveal which remote request failed.
`TOKEN_FETCH` and `TOKEN_FORMAT` refer to GitHub OAuth exchange transport
and JSON, `USER_FETCH/FORMAT` refer to GitHub's user endpoint, and
`PERMISSION_FETCH/FORMAT` refer to the repository collaborator permission
endpoint. `CALLBACK_RENDER` is an unclassified response-generation exception.

If login fails, capture only the bracketed STAGE shown in the popup. Never
paste callback query parameters, tokens, OAuth code, or cookies into chat.
Retry with a fresh `/admin/` login since an OAuth state is one-use only.

Wrangler `keep_vars: true` preserves the public Client ID entered in the
Cloudflare dashboard. Cloudflare preserves encrypted secrets through code deploy.
The workflow now fails closed unless live /health is HTTP 200 configured:true.
