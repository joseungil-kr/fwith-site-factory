import frozen from '../data/pages.json' with {type:'json'};
import manual from '../data/manual-pages.json' with {type:'json'};
import originalArchitecture from '../data/architecture.json' with {type:'json'};
export const pages=[...frozen,...manual];
export const architecture={...originalArchitecture,hubs:originalArchitecture.hubs.map(h=>({...h,children:pages.filter(p=>p.category===h.category).length})),pages:[...originalArchitecture.pages,...manual.map(p=>({pageKey:p.pageKey,url:p.url,intentKey:p.intentKey,publicationMode:p.publicationMode,manualReleaseId:p.manualReleaseId}))]};
export default pages;
