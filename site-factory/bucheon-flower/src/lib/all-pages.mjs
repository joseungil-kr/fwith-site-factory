import original from '../data/pages.json' with {type:'json'};
import manual from '../data/manual-pages.json' with {type:'json'};
export default [...original,...manual];
