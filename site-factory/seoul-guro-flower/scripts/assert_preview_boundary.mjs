import config from '../src/data/site-config.json' with {type:'json'};
import {validateCurrentRelease} from './assert_release_approval.mjs';
if (process.env.SITE_INDEXABLE === 'true') {
  if (config.productionApproved !== true) throw new Error('Production-indexable build is disabled for this unapproved regional template');
  validateCurrentRelease();
}
