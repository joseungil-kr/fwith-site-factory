import {defineConfig} from 'astro/config';
import sitemap from '@astrojs/sitemap';
import config from './src/data/site-config.json' with {type:'json'};
import instances from './src/data/site-instances.json' with {type:'json'};
const key=process.env.SITE_INSTANCE||config.defaultInstance;
const instance=instances.find(x=>x.key===key);
if(!instance) throw new Error('Unknown SITE_INSTANCE: '+key);
const site = process.env.SITE_URL || instance.domain;
export default defineConfig({site, output:'static', trailingSlash:'always', integrations:[sitemap({filter: page => !new URL(page).pathname.startsWith('/404')})]});
