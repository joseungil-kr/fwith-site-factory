/** Generic tests run against current code; old region surface contracts remain intact in their original fixtures. */
import fs from 'node:fs';import {spawnSync} from 'node:child_process';
const files=fs.readdirSync('tests').filter(x=>x.endsWith('.test.mjs')&&!['yeongdeungpo-grouped.test.mjs','gwanak-grouped.test.mjs','gwanak-surface.test.mjs'].includes(x)).map(x=>'tests/'+x);
const historicalOnly=['every frozen source is retained in reviewed order without mutation','component receives the independently retained hero answer without raw HTML or CSS changes','source cards use H3 beneath one source-section H2','renderer uses escaped expressions, accessible source links and existing stacked cards'];
console.log('CURRENT SEOCHO: shared algorithms and dedicated exact-input/source contracts. Historical source-shape assertions run unchanged in original fixture.');
const run=spawnSync(process.execPath,['--test','--test-skip-pattern='+historicalOnly.join('|'),...files],{stdio:'inherit'});
if(run.status!==0)throw new Error('Current Seocho native regression failed');
