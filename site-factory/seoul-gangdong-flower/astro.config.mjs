import {defineConfig} from 'astro/config';
import {assertBoundary,ORIGIN,validateRuntime} from './src/lib/gangdong-runtime.mjs';
import runtime from './src/data/gangdong-runtime.json' with {type:'json'};
assertBoundary();validateRuntime(runtime);
export default defineConfig({site:ORIGIN,output:'static',trailingSlash:'always'});
