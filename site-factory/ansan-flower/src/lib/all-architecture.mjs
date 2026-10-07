import frozen from '../data/architecture.json' with {type:'json'};
import {manualPages} from './manual-runtime.mjs';
export default {...frozen,pages:[...frozen.pages,...manualPages]};
