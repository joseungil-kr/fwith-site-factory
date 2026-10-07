import fs from 'node:fs';import path from 'node:path';import {validateManualContract,digest,discoverReleaseFiles} from '../src/lib/manual-contract.mjs';
const manifest=JSON.parse(fs.readFileSync('src/data/manual-manifest.json','utf8'));
const proof=JSON.parse(fs.readFileSync('src/data/manual-provenance.json','utf8'));
const preview=process.env.MANUAL_PREVIEW==='true';
// Preview is always non-indexable; a production request with a preview flag is invalid.
if(preview&&process.env.SITE_INDEXABLE==='true')throw new Error('Manual preview cannot be indexable');
const inventory=discoverReleaseFiles();const observed={};for(const file of inventory)observed[file]=fs.existsSync(file)?digest(fs.readFileSync(file)):null;
let evidence=null;
const ref=proof.independentReview?.evidencePath;
if(ref){if(path.isAbsolute(ref)||ref.split('/').includes('..'))throw new Error('Unsafe review evidence path');if(fs.existsSync(ref))evidence=JSON.parse(fs.readFileSync(ref,'utf8'));}
validateManualContract(manifest,proof,observed,{inventory,preview,indexable:process.env.SITE_INDEXABLE==='true',evidence});
if(!preview){for(const asset of JSON.parse(fs.readFileSync('src/data/manual-required-assets.json','utf8'))){if(!fs.existsSync(asset.path))throw new Error('Missing existing release asset: '+asset.path);const b=fs.readFileSync(asset.path);const actual=(await import('node:crypto')).default.createHash('sha1').update(Buffer.concat([Buffer.from('blob '+b.length+'\0'),b])).digest('hex');if(actual!==asset.gitBlobSha)throw new Error('Existing asset changed: '+asset.path);}}
console.log('Manual contract valid for '+(preview?'non-indexable preview':'exact reviewed release'));
