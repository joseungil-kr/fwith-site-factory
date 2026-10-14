import {createHash} from 'node:crypto';
import {readFileSync, lstatSync} from 'node:fs';
import {resolve, isAbsolute} from 'node:path';
import {fileURLToPath} from 'node:url';

const ROOT = process.cwd();
export const PREVIEW_ORIGIN = 'https://seoul-seocho.local.invalid';
export const TARGET = Object.freeze({
  repository: 'joseungil-kr/fwith-site-factory',
  sourceRoot: 'site-factory/seoul-seocho-flower',
  siteKey: 'seoul-seocho-flower-direct',
  hostname: 'seoul-seocho.fwith.kr',
  origin: 'https://seoul-seocho.fwith.kr',
  worker: 'seoul-seocho-flower-guide',
  frozenSourceRevision: '2a4de872c85da0b66815c5e5668e0c7de9ce4341',
  customerCopySha256: 'c466be6fd967a690cb008ca74ae35d7dec8e93f522cb0b19c8ae86a375b8b53c',
});
export const SITEMAP_ROUTES = Object.freeze(['/', '/regions/seocho-celebration-wreath/', '/regions/seocho-funeral-wreath/']);
const hash = bytes => createHash('sha256').update(bytes).digest('hex');
const require = (ok, code) => { if (!ok) throw new Error(code); };
const sha256 = value => typeof value === 'string' && /^[0-9a-f]{64}$/.test(value);

function regularBytes(path) {
  require(lstatSync(path).isFile() && !lstatSync(path).isSymbolicLink(), 'release_file_not_regular');
  return readFileSync(path);
}

// A pinned control-side record is required. This source module does not grant
// provider permissions or replace the publisher's source/ancestry/collision checks.
export function validateBinding(binding, env) {
  require(binding.schemaVersion === 1 && binding.state === 'approved', 'release_binding_not_approved');
  for (const [key, value] of Object.entries(TARGET)) require(binding[key] === value, `release_${key}_mismatch`);
  require(typeof binding.sourceRevision === 'string' && /^[0-9a-f]{40}$/.test(binding.sourceRevision), 'release_revision_invalid');
  require(env.SITE_FACTORY_REVISION === binding.sourceRevision, 'release_revision_mismatch');
  require(sha256(binding.sourceContractSha256), 'release_source_contract_missing');
  require(binding.approvals && Object.keys(binding.approvals).sort().join(',') === 'hostBinding,indexNowProof,publication'
    && Object.values(binding.approvals).every(value => value === true), 'release_approval_missing');
  require(binding.evidenceReferences && Object.keys(binding.evidenceReferences).sort().join(',') === 'hostBinding,indexNowProof,publication', 'release_evidence_missing');
  for (const value of Object.values(binding.evidenceReferences)) {
    require(typeof value === 'string' && /^https:\/\/github\.com\/joseungil-kr\/fwith-site-factory\/(?:blob\/[0-9a-f]{40}\/[^\s]+|issues\/[1-9][0-9]*(?:#issuecomment-[0-9]+)?)$/.test(value), 'release_evidence_not_pinned_or_auditable');
  }
  require(binding.proof && /^\/[A-Za-z0-9-]{8,128}\.txt$/.test(binding.proof.path) && sha256(binding.proof.sha256), 'release_proof_descriptor_invalid');
  require(binding.proof.origin === TARGET.origin, 'release_proof_origin_mismatch');
  require(JSON.stringify(binding.sitemapRoutes) === JSON.stringify(SITEMAP_ROUTES), 'release_sitemap_contract_mismatch');
  require(binding.notFoundStatus === 404 && binding.thinDirectoryRobots === 'noindex,follow', 'release_route_contract_mismatch');
  return binding;
}

export function getReleaseMode(root = ROOT, env = process.env) {
  const config = JSON.parse(regularBytes(resolve(root, 'src/data/site-config.json')));
  require(config.productionApproved === false && config.hostnameOwnershipVerified === false
    && config.previewUrl === PREVIEW_ORIGIN && config.worker === null && config.siteKey === TARGET.siteKey,
  'frozen_preview_config_changed');
  const proposal = JSON.parse(regularBytes(resolve(root, 'src/data/production-target.json')));
  for (const [key, value] of Object.entries(TARGET)) require(proposal[key] === value, `proposed_${key}_mismatch`);
  require(proposal.schemaVersion === 1 && proposal.state === 'proposed-unverified'
    && ['providerOwnershipVerified', 'publicationApproved', 'hostBindingApproved', 'indexNowProofApproved'].every(key => proposal[key] === false),
  'proposal_must_not_claim_approval');
  const mode = env.SITE_RELEASE_MODE || 'preview';
  require(['preview', 'production'].includes(mode), 'unknown_release_mode');
  if (mode === 'preview') {
    require(!env.SITE_INDEXABLE || env.SITE_INDEXABLE === 'false', 'preview_indexing_forbidden');
    require(!env.SITE_URL || env.SITE_URL === PREVIEW_ORIGIN, 'preview_origin_override_forbidden');
    require(!env.SITE_RELEASE_BINDING_PATH && !env.SITE_RELEASE_BINDING_SHA256, 'preview_binding_ambiguous');
    return {mode, origin: PREVIEW_ORIGIN, indexable: false, revision: env.SITE_FACTORY_REVISION || 'local', sitemapRoutes: []};
  }
  require(env.SITE_INDEXABLE === 'true', 'production_indexing_flag_required');
  require(env.SITE_URL === TARGET.origin, 'production_origin_mismatch');
  require(isAbsolute(env.SITE_RELEASE_BINDING_PATH || '') && sha256(env.SITE_RELEASE_BINDING_SHA256), 'pinned_control_binding_required');
  const bytes = regularBytes(env.SITE_RELEASE_BINDING_PATH);
  require(hash(bytes) === env.SITE_RELEASE_BINDING_SHA256, 'release_binding_digest_mismatch');
  const binding = validateBinding(JSON.parse(bytes), env);
  require(hash(regularBytes(resolve(root, 'src/data/seocho-copy.json'))) === TARGET.customerCopySha256, 'release_customer_copy_changed');
  const proof = regularBytes(resolve(root, 'public', binding.proof.path.slice(1)));
  require(hash(proof) === binding.proof.sha256, 'release_proof_digest_mismatch');
  require(proof.toString('utf8') === binding.proof.path.slice(1, -4) + '\n', 'release_proof_body_mismatch');
  return {mode, origin: TARGET.origin, indexable: true, revision: binding.sourceRevision,
    sitemapRoutes: SITEMAP_ROUTES, thinDirectoryRobots: 'noindex,follow', notFoundStatus: 404,
    bindingSha256: env.SITE_RELEASE_BINDING_SHA256};
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const root = process.argv[2] ? resolve(process.argv[2]) : ROOT;
  process.stdout.write(JSON.stringify(getReleaseMode(root)) + '\n');
}
