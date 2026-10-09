# Decap CMS authentication activated — 2026-10-09

- Site: https://astro-chat-lab-qa.joseungil.workers.dev
- CMS: https://astro-chat-lab-qa.joseungil.workers.dev/admin/
- GitHub backend: `joseungil-kr/fwith-site-factory`, `astro-chat-lab` branch.
- Files: `site-factory/astro-chat-lab/src/content/posts`.
- Uploads: repository `site-factory/astro-chat-lab/public/uploads`, public URL `/uploads/`.
- Official Decap version: 3.16.3, MIT, pinned CDN distribution.
- OAuth Worker: https://astro-chat-lab-oauth-qa.joseungil.workers.dev
- OAuth endpoint: `/auth`; GitHub callback: `/callback`.
- Login scope: `public_repo`. It reaches **all public repos** accessible to the consenting GitHub account and cannot be restricted to this folder or branch.
- OAuth Worker accepts only the account `joseungil-kr` with write/maintain/admin permission in the target repo.
- GitHub OAuth Client Secret exists only in Cloudflare's encrypted Worker Secret, never in repo / CMS YAML.
- Original blog's static deployment continues via the existing branch-restricted GitHub Actions push workflow.
- Trial site's `noindex` and `robots.txt Disallow: /` stay enabled.
- CMS `draft: true` excludes a post from the public site but **does not** hide its source in this PUBLIC GitHub repository.
- OAuth HTTP preflight checks configured state, correct callback, broad scope rejection, and strict cookie/state handshake before static deployment. These are not a substitute for actual human login.
- Browser login, native Decap Markdown editing, image upload and the actual CMS-produced GitHub commit remain to be verified by the authenticated site owner; none were simulated through GitHub file writes.
- The old bootstrap only runs when `UPSTREAM_PIN.json` is absent, so it will not erase CMS posts on subsequent pushes.
