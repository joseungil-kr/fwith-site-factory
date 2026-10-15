import {defineConfig} from 'astro/config';
import {validateRuntime} from './src/lib/yeosu-runtime.mjs';
validateRuntime();
// Local files only: no public site origin, deploy adapter, integration or production switch.
export default defineConfig({output:'static',trailingSlash:'always'});
