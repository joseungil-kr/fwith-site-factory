import {defineConfig} from 'astro/config';
import {assertBoundary} from './src/lib/hwasun-runtime.mjs';
assertBoundary();
export default defineConfig({output:'static',trailingSlash:'always'});
