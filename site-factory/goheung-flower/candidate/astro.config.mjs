import {defineConfig} from 'astro/config';
import {assertBoundary} from './src/lib/goheung-runtime.mjs';
assertBoundary();
export default defineConfig({output:'static',trailingSlash:'always'});
