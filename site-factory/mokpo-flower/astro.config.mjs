import {defineConfig} from 'astro/config';
import {validateRuntime} from './src/lib/mokpo-runtime.mjs';
validateRuntime();
// No `site`, no public origin, no deploy adapter, no sitemap URL generation.
export default defineConfig({output:'static',trailingSlash:'always',server:{host:'127.0.0.1'}});
