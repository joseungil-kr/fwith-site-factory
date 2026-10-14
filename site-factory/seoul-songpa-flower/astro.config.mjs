import {defineConfig} from 'astro/config';
import {resolveSongpaRelease} from './scripts/songpa_release.mjs';
const release=resolveSongpaRelease();
export default defineConfig({site:release.origin,output:'static',trailingSlash:'always'});
