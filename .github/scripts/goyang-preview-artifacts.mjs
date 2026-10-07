import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';
export const MAX_SCREENS_PER_PART=20, PART_COUNT=8, MAX_RAW_BYTES=30*1024*1024;
const sha=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');
export function planParts(files){
 assert(files.length<=146,'Unexpected screenshot scope');
 const parts=Array.from({length:PART_COUNT},(_,i)=>({name:`screens-${String(i+1).padStart(2,'0')}`,files:[],bytes:0}));
 for(const [index,file] of files.entries()){
  assert(Number.isSafeInteger(file.bytes)&&file.bytes>0,'Invalid image length');
  const part=parts[Math.floor(index/MAX_SCREENS_PER_PART)];part.files.push(file);part.bytes+=file.bytes;
 }
 for(const p of parts){assert(p.files.length<=MAX_SCREENS_PER_PART);assert(p.bytes<MAX_RAW_BYTES,'Part exceeds 30 MiB safety cap; split proposal before upload, never reduce image quality');}
 return parts;
}
export function partitionEvidence(output){
 const screens=path.join(output,'screenshots'),destination=path.join(output,'parts'),logs=path.join(destination,'logs');fs.mkdirSync(logs,{recursive:true});
 let logBytes=0;const logsManifest=[];
 for(const name of fs.readdirSync(output).sort()){
  if(!/\.(?:json|log|txt)$/.test(name))continue;
  const source=path.join(output,name);assert(fs.lstatSync(source).isFile()&&!fs.lstatSync(source).isSymbolicLink(),'Unsafe evidence log');
  const bytes=fs.readFileSync(source);logBytes+=bytes.length;logsManifest.push({name,bytes:bytes.length,sha256:sha(bytes)});
 }
 if(logBytes>=MAX_RAW_BYTES-1024*1024){fs.writeFileSync(path.join(logs,'partition-error.txt'),'Logs exceed 29 MiB safety cap; large logs were not copied for upload.');throw new Error('Logs exceed 29 MiB safety cap');}
 for(const f of logsManifest)fs.copyFileSync(path.join(output,f.name),path.join(logs,f.name));
 try {
  const names=fs.existsSync(screens)?fs.readdirSync(screens).sort():[];
  const files=names.map(name=>{assert(/^[a-z0-9-]+\.jpg$/.test(name),'Unexpected screenshot filename');const p=path.join(screens,name);assert(fs.lstatSync(p).isFile()&&!fs.lstatSync(p).isSymbolicLink());const b=fs.readFileSync(p);return{name,bytes:b.length,sha256:sha(b)};});
  const parts=planParts(files);
  for(const p of parts)if(p.files.length){const dir=path.join(destination,p.name,'screenshots');fs.mkdirSync(dir,{recursive:true});for(const f of p.files){const target=path.join(dir,f.name);fs.copyFileSync(path.join(screens,f.name),target);assert.equal(sha(fs.readFileSync(target)),f.sha256,'Screenshot bytes changed');}}
  const manifest={maxScreensPerPart:MAX_SCREENS_PER_PART,fixedPartCount:PART_COUNT,maxRawBytesPerPart:MAX_RAW_BYTES,downloadLimitBytes:32*1024*1024,archiveCompressionLevel:0,quality:'original full-page JPEG 85, unchanged from pinned successful capture; no recompression/resizing',parts,logs:logsManifest,logBytes,completeScreenshotScope:files.length===146};
  const bytes=JSON.stringify(manifest,null,2)+'\n';assert(logBytes+Buffer.byteLength(bytes)<MAX_RAW_BYTES);fs.writeFileSync(path.join(logs,'artifact-partition-manifest.json'),bytes);console.log(JSON.stringify({screenshots:files.length,parts:parts.map(p=>({name:p.name,count:p.files.length,bytes:p.bytes})),logBytes}));
  return manifest;
 }catch(e){fs.writeFileSync(path.join(logs,'partition-error.txt'),String(e.stack||e));throw e;}
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 assert.equal(process.env.GITHUB_REF,'refs/heads/manual-goyang-three-facility-preview-20261007');
 partitionEvidence(path.join(process.cwd(),'goyang-preview-evidence'));
}

