import {defineConfig} from 'astro/config';
import {validateRuntime} from './src/lib/suncheon-runtime.mjs';
validateRuntime();
export default defineConfig({output:'static',trailingSlash:'always'});
