import fs from 'node:fs';
import {fileURLToPath} from 'node:url';
import {collectBindings,productionRequested,readReviewEvidence,validateManualContract} from './manual-contract.mjs';
export function assertManualBoundary(env=process.env) {
 const root=fileURLToPath(new URL('../../',import.meta.url));
 const read=f=>JSON.parse(fs.readFileSync(new URL('../data/'+f,import.meta.url)));
 const config=read('site-config.json');
 // Original production approval boundary is retained in every build entrypoint.
 if(env.SITE_INDEXABLE==='true'&&config.productionApproved!==true)throw new Error('Production-indexable build is disabled for this unapproved regional template');
 const pages=read('manual-pages.json'),proof=read('manual-provenance.json'),products=read('products.json');
 const production=productionRequested(env,config);
 const reviewEvidenceBytes=production&&proof.independentReview?.status==='approved'?readReviewEvidence(root,proof.independentReview.evidencePath):null;
 return validateManualContract(pages,proof,fs.readFileSync(new URL('../data/manual-pages.json',import.meta.url)),products,{production,bindings:collectBindings(root),reviewEvidenceBytes});
}
