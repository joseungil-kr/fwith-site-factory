import {readFileSync,writeFileSync} from 'node:fs';
const baseline=readFileSync('public/_headers','utf8').replace(/^\s*X-Robots-Tag:.*\n?/gmi,'');
const indexing=process.env.SITE_INDEXABLE==='true'?'':'  X-Robots-Tag: noindex, nofollow, noarchive\n';
const {effectiveArchitecture}=await import('../src/lib/all-pages.mjs');
const hubs=effectiveArchitecture.hubs;
const thin=indexing?'':hubs.filter(h=>h.children<3).map(h=>`${h.url}\n  X-Robots-Tag: ${h.category==='regions'?'noindex, follow':'noindex, nofollow, noarchive'}\n`).join('');
writeFileSync('dist/_headers',baseline.trimEnd()+'\n'+indexing+thin);
