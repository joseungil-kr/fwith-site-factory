import {validateManual} from '../src/lib/manual-contract.mjs';
const state=validateManual(process.cwd(),process.env);
console.log('MANUAL CONTRACT PASS',JSON.stringify({pages:state.pages.length,mode:state.preview?'local-noindex-preview':'reviewed-production',contentHash:state.hashes.contentHash,bundleHash:state.hashes.bundleHash}));
