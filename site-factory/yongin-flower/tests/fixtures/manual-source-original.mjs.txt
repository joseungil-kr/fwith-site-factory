import frozen from '../data/publish-manifest.json' with {type:'json'};
import manual from '../data/manual-pages.json' with {type:'json'};
const replacements=new Set(manual.pages.map(p=>p.pageKey));
export const effectiveManifest={...frozen,pages:[...frozen.pages.filter(p=>!replacements.has(p.pageKey)),...manual.pages]};
export {manual};
