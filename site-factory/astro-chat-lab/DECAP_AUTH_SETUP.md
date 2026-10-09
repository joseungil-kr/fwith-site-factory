# Decap CMS integration status (isolated Astro chat lab)

- Astro site: https://astro-chat-lab-qa.joseungil.workers.dev/
- Admin: /admin/
- Backend: GitHub repo `joseungil-kr/fwith-site-factory`, branch `astro-chat-lab`.
- Media: repo `site-factory/astro-chat-lab/public/uploads`, site `/uploads/`.
- Decap: fixed official release `3.16.3` (2026-09-22), MIT.
- Current state: AUTH NOT CONFIGURED. `window.CMS_MANUAL_INIT = true` disables login until explicit approval, verified OAuth deployment, and correct `base_url/auth_endpoint` are installed.
- This is NOT a successful CMS login, editor save or image upload.

## Why approval is required

Decap GitHub backend 3.16.3 defaults to the broad `repo` OAuth scope unless `backend.auth_scope` is set. The test config explicitly requests `public_repo` instead. GitHub's OAuth `public_repo` scope applies to public repos available to the consenting user, NOT only this one and NOT only this folder. The `astro-chat-lab` branch and folder in CMS configuration are convenience targets, not authorization boundaries. This repository also holds operating sites. Draft files committed to this public repository are publicly readable on GitHub, even with `draft: true`.

Before activating:
1. Get permission to register a **new GitHub OAuth App** with homepage of this test site and an exact callback on a **new dedicated OAuth Worker** (proposed `astro-chat-lab-oauth-qa`). Do not modify the existing static Worker.
2. Explicitly approve the broader `public_repo` scope and repository access risk. If unacceptable, use a separate repository with only this test blog before authorizing.
3. Enter GitHub OAuth Client ID (public identifier) and Client Secret (confidential) only through official secure GitHub/Cloudflare settings. Do not send secrets through chat, commits or CMS YAML. Existing Cloudflare *deployment* token is not a CMS login token.
4. Review the OAuth Worker implementation for one-time session-bound cryptographic state, expiry, callback origin binding, strict parent `postMessage` origin/source, zero wildcard targets, callback error containment, server-side secrets, verified GitHub user access, and token leakage prevention. Do not reuse the insecure community proxy unchanged.
5. GET-verify Worker name availability; deploy only after consent; verify the actual workers.dev callback origin; set exact `base_url`, `auth_endpoint`, and enable Decap initialization. The callback URL must match the GitHub OAuth App.
6. Manually test browser login/edit/publish (the GitHub connector alone cannot establish CMS-origin browser interactions), read back the actual CMS commit and Actions run, then verify real public HTML, assets, draft exclusion and noindex/404.

## Upstream security review

- Official Decap: `decaporg/decap-cms`, `decap-cms@3.16.3`, MIT, actively maintained; use static CDN script pinned to version.
- `FilecoinFoundationWeb/decap-proxy`: Cloudflare Worker example, 2024; its `state` is only 4 random bytes and is **not checked** on callback; `window.opener.postMessage(..., "*")` sends access tokens to an unrestricted origin. Do NOT deploy unchanged.
- `sterlingwes/decap-proxy`: useful protocol layout, but callback origin/state handling must be independently audited and hardened. Reuse protocol knowledge, not unreviewed auth code.
- Decap's pinned browser authenticator checks the origin against `base_url`, but its own event handler does not explicitly check `event.source`. The dedicated callback must check `event.source === window.opener` and the expected admin origin before returning any sensitive response.
