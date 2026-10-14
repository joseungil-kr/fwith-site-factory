import config from '../src/data/site-config.json' with {type:'json'};
if(config.productionApproved!==false||config.hostnameOwnershipVerified!==false)throw new Error('Seocho local preparation cannot carry publication or hostname approval');
if(process.env.SITE_INDEXABLE==='true')throw new Error('Production-indexable build is disabled for this unapproved regional template');
if(config.previewUrl!=='https://seoul-seocho.local.invalid'||(process.env.SITE_URL&&process.env.SITE_URL!==config.previewUrl))throw new Error('Unverified Seocho host override is forbidden in local preparation');
