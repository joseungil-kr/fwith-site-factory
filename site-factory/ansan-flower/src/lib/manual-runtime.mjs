import {validateManual} from './manual-contract.mjs';
const state=validateManual(process.cwd(),process.env);
export const manualPages=state.pages;
export const manualPreview=state.preview;
