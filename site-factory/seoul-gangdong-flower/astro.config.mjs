import {defineConfig} from 'astro/config';
import {resolveGangdongRelease} from './scripts/gangdong_release.mjs';
const release=resolveGangdongRelease();
export default defineConfig({site:release.origin,output:'static',trailingSlash:'always'});
