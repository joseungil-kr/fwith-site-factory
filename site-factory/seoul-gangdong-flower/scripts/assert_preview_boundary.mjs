import {verifyReuse} from './verify_reuse_provenance.mjs';
import {assertBoundary,verifyInputs} from '../src/lib/gangdong-runtime.mjs';
assertBoundary();verifyInputs();verifyReuse();console.log('Local-only boundary and selected frozen input seal and reuse provenance verified');
