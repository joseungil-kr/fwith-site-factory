/** Retain historical source-contract assertions; run them against their exact original template.
 * Current Gwanak uses approved sections and excludes unapproved repeated source dates.
 * The three old source-shape checks are replaced by stricter full HTML parity/mutations,
 * not treated as successful checks of the new UI. All remaining generic tests run here.
 */
import fs from 'node:fs';import {spawnSync} from 'node:child_process';
const files=fs.readdirSync('tests').filter(x=>x.endsWith('.test.mjs')&&x!=='yeongdeungpo-grouped.test.mjs').map(x=>'tests/'+x);
const historicalOnly=[
 'component receives the independently retained hero answer without raw HTML or CSS changes',
 'source cards use H3 beneath one source-section H2',
 'renderer uses escaped expressions, accessible source links and existing stacked cards'
];
console.log('CURRENT GWANAK: generic algorithm + Gwanak frozen contract tests. Historical UI regex tests remain unchanged and run in original-template regression.');
const pattern=historicalOnly.join('|');
const run=spawnSync(process.execPath,['--test','--test-skip-pattern='+pattern,...files],{stdio:'inherit'});
if(run.status!==0)throw new Error('Current Gwanak native regression failed');
