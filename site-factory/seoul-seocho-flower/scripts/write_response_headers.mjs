import {readFileSync,writeFileSync} from 'node:fs';
import {getReleaseMode} from './release_mode.mjs';
const baseline=readFileSync('public/_headers','utf8').replace(/^\s*X-Robots-Tag:.*\n?/gmi,'');
const indexing=getReleaseMode().indexable?'':'  X-Robots-Tag: noindex, nofollow, noarchive\n';
writeFileSync('dist/_headers',baseline.trimEnd()+'\n'+indexing);
