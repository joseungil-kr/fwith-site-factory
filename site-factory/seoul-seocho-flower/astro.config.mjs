import {defineConfig} from 'astro/config';
import sitemap from '@astrojs/sitemap';
import {getReleaseMode} from './scripts/release_mode.mjs';
import architecture from './src/data/architecture.json' with {type:'json'};
const release = getReleaseMode();
const site = release.origin;
const thinHubs=new Set(architecture.hubs.filter(h=>h.children<3).map(h=>h.url));
export default defineConfig({site, output:'static', trailingSlash:'always', integrations:[sitemap({filter: page => {
  const path=new URL(page).pathname;
  return release.indexable && release.sitemapRoutes.includes(path) && !path.startsWith('/404') && !thinHubs.has(path);
}})]});
