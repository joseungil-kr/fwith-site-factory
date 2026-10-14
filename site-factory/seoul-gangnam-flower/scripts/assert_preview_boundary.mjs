import fs from 'node:fs';
const c=JSON.parse(fs.readFileSync('src/data/site-config.json','utf8'));
if(process.env.SITE_INDEXABLE==='true'||c.productionApproved!==false||c.hostnameOwnershipVerified!==false||c.sourceCommit!==null||c.worker!==null||c.canonicalHostname!==null||c.publicHttpVerified!==false||c.indexNowSubmitted!==false)throw new Error('Gangnam successor is LOCAL-only; publication and ownership remain unverified');
if(process.env.SITE_URL&&process.env.SITE_URL!==c.previewUrl)throw new Error('Only the reserved .local.invalid preview origin is allowed');
console.log('LOCAL Gangnam boundary verified');
