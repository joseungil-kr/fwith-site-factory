import original from '../data/architecture.json' with {type:'json'};
import pages from './all-pages.mjs';
export default {...original,hubs:original.hubs.map(h=>{const n=pages.filter(p=>p.category===h.category).length;return {...h,children:n,indexable:n>=3,menuVisible:n>=5};})};
