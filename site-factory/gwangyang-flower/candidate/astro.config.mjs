import {defineConfig} from 'astro/config';
import {validateRuntime} from './src/lib/gwangyang-runtime.mjs';
validateRuntime();
export default defineConfig({output:'static',trailingSlash:'always'});
