// Offline reproduction of exact upstream temp-directory function bodies.
// No Wrangler CLI, provider SDK, credentials, npm installation or network is used.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import vm from 'node:vm';
import {stripTypeScriptTypes} from 'node:module';
import {fileURLToPath} from 'node:url';
const out=path.dirname(fileURLToPath(import.meta.url));
const task=path.resolve(out,'../..');
const evidence=JSON.parse(fs.readFileSync(path.join(out,'pinned-source.json'),'utf8'));
const source=p=>evidence.sources.find(x=>x.path===p).content;
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
for(const s of evidence.sources){
  const bytes=Buffer.from(s.content);
  const gitsha=crypto.createHash('sha1').update(Buffer.from(`blob ${bytes.length}\0`)).update(bytes).digest('hex');
  if(gitsha!==s.gitBlobSha)throw Error('Git blob content mismatch: '+s.path);
}
const upstream=source('packages/workers-utils/src/wrangler-tmp-dir.ts');
const imports=['import fs from "node:fs";','import path from "node:path";','import { onExit } from "signal-exit";','import { removeDirSync } from "./fs-helpers";'];
let executable=upstream;
for(const line of imports){if(!executable.includes(line))throw Error('Import drift');executable=executable.replace(line,'');}
executable=stripTypeScriptTypes(executable).replace(/^export /gm,'');
// Keep this execution within a newly created, verified child of our evidence directory.
const scratch=fs.mkdtempSync(path.join(out,'tmp-repro-'));
const inside=p=>{const r=path.resolve(p);if(!r.startsWith(scratch+path.sep))throw Error('Out-of-scope filesystem access');return r;};
const listeners=new Set();
const onExit=fn=>{listeners.add(fn);return()=>listeners.delete(fn);};
const removeDirSync=p=>fs.rmSync(inside(p),{recursive:true,force:true,maxRetries:5,retryDelay:100});
const sandbox={fs,path,process:{cwd:()=>scratch},onExit,removeDirSync};
vm.createContext(sandbox);
vm.runInContext(executable+'\nthis.callTmp=getWranglerTmpDir;',sandbox);
function inventory(root){return Object.fromEntries(fs.readdirSync(root,{recursive:true,withFileTypes:true}).filter(x=>x.isFile()).map(x=>{const p=path.join(x.parentPath,x.name);return[path.relative(root,p).replaceAll(path.sep,'/'),sha(fs.readFileSync(p))];}).sort((a,b)=>a[0].localeCompare(b[0])));}
const actual=path.join(task,'seocho-production-runtime-20261014/build');
const config=path.join(task,'seocho-production-public-runtime-20261014/result/release/wrangler.publish.json');
const oldRelease=path.join(scratch,'old/release');
const cleanRelease=path.join(scratch,'fixed/release');
for(const root of [oldRelease,cleanRelease]){fs.cpSync(actual,root,{recursive:true});fs.copyFileSync(config,path.join(root,'wrangler.publish.json'));}
const before=inventory(cleanRelease);
const beforeRoot=fs.readdirSync(oldRelease).sort();
const oldDeploy=sandbox.callTmp(oldRelease,'deploy');
const oldBundle=sandbox.callTmp(oldRelease,'bundle');
const during=[oldDeploy.path,oldBundle.path].map(p=>path.relative(scratch,p));
oldBundle.remove();oldDeploy.remove();
const oldAfter=fs.readdirSync(oldRelease).sort();
if(!oldAfter.includes('.wrangler')||!fs.existsSync(path.join(oldRelease,'.wrangler/tmp')))throw Error('No reproduced extra root');
if(fs.readdirSync(path.join(oldRelease,'.wrangler/tmp')).length!==0)throw Error('Child cleanup failed');
// --outdir only suppresses the deploy destination call: bundle still calls this helper.
const outdirOnly=path.join(scratch,'outdir-only/release');fs.mkdirSync(outdirOnly,{recursive:true});
const remainingBundle=sandbox.callTmp(outdirOnly,'bundle');remainingBundle.remove();
if(!fs.existsSync(path.join(outdirOnly,'.wrangler/tmp')))throw Error('Outdir-only gap missing');
const isolated=path.join(scratch,'fixed/wrangler-work');fs.mkdirSync(isolated);
const fixedDeploy=sandbox.callTmp(isolated,'deploy');const fixedBundle=sandbox.callTmp(isolated,'bundle');
fixedBundle.remove();fixedDeploy.remove();
const after=inventory(cleanRelease);
if(JSON.stringify(before)!==JSON.stringify(after))throw Error('Fixed artifact changed');
const cfg=JSON.parse(fs.readFileSync(path.join(cleanRelease,'wrangler.publish.json')));
const resolvedAssets=path.resolve(path.dirname(path.join(cleanRelease,'wrangler.publish.json')),cfg.assets.directory);
if(resolvedAssets!==path.join(cleanRelease,'dist'))throw Error('Absolute config asset path changed');
const result={schemaVersion:1,state:'PASS_PINNED_TMP_FUNCTION_REPRODUCTION',sourceCommit:evidence.sourceCommit,nodeVersion:process.version,
  upstreamTmpSha256:sha(upstream),upstreamGitBlobHashesVerified:true,
  executionScope:'Exact upstream temp function bodies with TypeScript types stripped; signal-exit registration shim; scoped fs.rmSync uses upstream options. Not a full Wrangler CLI dry-run.',
  sourceMapping:{assetsOnlyEntry:'resolveEntryWithAssets returns no projectRoot; entry.ts falls back to cwd',configAssetResolution:'assets.ts resolves configured assets relative to config.configPath',outdirOnlyInsufficient:'bundle.ts unconditionally requests projectRoot bundle temp directory'},
  old:{rootBefore:beforeRoot,rootAfter:oldAfter,tempPathsDuring: during,parentStillPresent:'.wrangler/tmp',childrenAfterCleanup:[],originalAllowlistWouldReject:true},
  outdirOnly:{bundleStillCreates:'.wrangler/tmp'},fixed:{cwdOutsideArtifact:true,configPathAbsolute:true,assetsPathResolvesToOriginalDist:true,artifactBefore:before,artifactAfter:after,allFileBytesUnchanged:true,distFileCount:Object.keys(after).filter(x=>x.startsWith('dist/')).length,rootAfter:fs.readdirSync(cleanRelease).sort()},
  limitations:['Original run 38532307939 did not retain its directory inventory; .wrangler is reproduced/source-proven, not directly observed on that runner.','No full CLI process or live deployment executed.'],liveDeployment:false,credentialsRead:false,networkCalls:0,scratchDirectory:scratch};
fs.writeFileSync(path.join(out,'tmp-reproduction.json'),JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify({state:result.state,oldRootAfter:oldAfter,fixedUnchanged:true,distFiles:result.fixed.distFileCount}));
