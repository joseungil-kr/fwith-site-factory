import {spawnSync} from 'node:child_process';
// The checked-in release record is unbound. No environment-only publication bypass.
const result=spawnSync('python3',['scripts/release_mode.py'],{cwd:new URL('..',import.meta.url),stdio:'inherit'});
if(result.error)throw result.error;
if(result.status!==0)throw new Error('Gwanak source release boundary rejected');
