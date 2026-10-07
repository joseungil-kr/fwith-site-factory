import {assertManualRelease} from './src/lib/manual-release-guard.mjs';
assertManualRelease();
import {defineConfig} from 'astro/config';
import sitemap from '@astrojs/sitemap';
import config from './src/data/site-config.json' with {type:'json'};
import architecture from './src/lib/all-architecture.mjs';
const site = process.env.SITE_URL || config.previewUrl;
const thinHubs=new Set(architecture.hubs.filter(h=>h.children<3).map(h=>h.url));
export default defineConfig({site, output:'static', trailingSlash:'always', integrations:[sitemap({filter: page => {
  const path=new URL(page).pathname;
  return !path.startsWith('/404') && !thinHubs.has(path);
}})]});

