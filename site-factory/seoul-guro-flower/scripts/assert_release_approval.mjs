import fs from 'node:fs';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
const sha = b => crypto.createHash('sha256').update(b).digest('hex');
export function validateReleaseApproval(config, approval, manifest, read) {
  assert.equal(config.productionApproved, true, 'Production-indexable build is disabled');
  assert.deepEqual(Object.keys(approval).sort(), ["allowedConfigChange", "approvedConfigSha256", "baselineManifestSha256", "baselineSourceRevision", "baselineVisualReview", "candidateManifestSha256", "candidateVisualAssessment", "fixedPlanSha256", "independentReleaseReview", "origin", "originalPlanN", "priorConfigSha256", "publicReleaseVerified", "publicationAuthorized", "publishedCoverage", "schemaVersion", "siteKey", "sourceBranch", "sourceRoot", "unchangedCustomerContent", "userInstruction", "userInstructionMeaning", "worker", "writer"]);
  assert.equal(approval.priorConfigSha256, '837e42ad28825a165c57cef9883dd193bf158ec74b52863f7d57062b745f5bf2');
  assert.equal(approval.baselineManifestSha256, '4078a8c3d67710650500b1a97cd8343d1157432c2a45930367fae47a271488fb');
  assert.equal(approval.publicReleaseVerified, false);
  assert.deepEqual(approval.publishedCoverage, {numerator:0, denominator:3, percent:0});
  assert.deepEqual(approval.allowedConfigChange, {productionApproved:{from:false,to:true}});
  assert.deepEqual(Object.keys(approval.unchangedCustomerContent).sort(), ["public/39c4ed924bc6084c670a963c26d9f018.txt", "public/_headers", "public/favicon.svg", "public/images/editorial/opening-wreath-illustration-v1.webp", "public/images/products/congrats-basic.jpg", "public/images/products/congrats-large.jpg", "public/images/products/congrats-premium.jpg", "public/images/products/congrats-xl.jpg", "public/images/products/funeral-basic.jpg", "public/images/products/funeral-large.jpg", "public/images/products/funeral-premium.jpg", "public/images/products/funeral-xl.jpg", "public/images/shared-banners/flower-budget.webp", "public/images/shared-banners/flower-consultation.webp", "public/images/shared-banners/flower-message.webp", "src/components/FaqSection.astro", "src/components/InlineOrderBanner.astro", "src/components/InlineText.astro", "src/components/MarkdownContent.astro", "src/components/ProductCards.astro", "src/components/RegionDirectory.astro", "src/components/SharedFlowerBanner.astro", "src/components/faq.mjs", "src/config/site.ts", "src/data/architecture.json", "src/data/business-truth.json", "src/data/copy-review-bindings.json", "src/data/direct-checkpoint.json", "src/data/editorial-assets.json", "src/data/guro-plan-binding.json", "src/data/page-map.json", "src/data/pages.json", "src/data/products.json", "src/data/region-coverage.json", "src/data/region-policy.json", "src/data/shared-banner-manifest.json", "src/data/social-image-provenance.json", "src/layouts/BaseLayout.astro", "src/lib/catalog.mjs", "src/lib/content.mjs", "src/lib/directory-banner-split.mjs", "src/lib/directory-links.mjs", "src/lib/guro-regions.mjs", "src/lib/heading-anchors.mjs", "src/lib/hubs.mjs", "src/lib/journey.mjs", "src/lib/regional-runtime.mjs", "src/lib/regions-legacy.mjs", "src/lib/regions.mjs", "src/lib/social-image.mjs", "src/lib/sources.mjs", "src/lib/visual.mjs", "src/pages/404.astro", "src/pages/[category]/[slug].astro", "src/pages/[category]/index.astro", "src/pages/index.astro", "src/pages/robots.txt.ts", "src/styles/global.css"]);

  assert.equal(approval.schemaVersion, 1); assert.equal(approval.publicationAuthorized, true);
  assert.equal(approval.siteKey, 'seoul-guro-flower-direct');
  assert.equal(approval.sourceBranch, 'site-factory-seoul-guro-direct');
  assert.equal(approval.sourceRoot, 'site-factory/seoul-guro-flower');
  assert.equal(approval.origin, 'https://seoul-guro.fwith.kr');
  assert.equal(approval.worker, 'seoul-guro-flower-guide');
  assert.equal(approval.baselineSourceRevision, '500d82d01c1cdaed3ebde047bb3ce056705daac1');
  assert.equal(approval.originalPlanN, 3);
  assert.equal(approval.fixedPlanSha256, manifest.directRelease.fixedPlanSha256);
  assert.equal(manifest.directRelease.plannedOriginalCount, 3);
  assert.equal(manifest.directRelease.publicationAuthorized, true);
  assert.deepEqual(manifest.directRelease.publishedCoverage, {numerator:0, denominator:3, percent:0});
  assert.equal(sha(read('src/data/site-config.json')), approval.approvedConfigSha256);
  const baseline = JSON.parse(read('tests/reference/release-baseline/site-config.json'));
  assert.equal(sha(read('tests/reference/release-baseline/site-config.json')), approval.priorConfigSha256);
  assert.deepEqual({...config, productionApproved:false}, baseline);
  assert.equal(sha(read('src/data/publish-manifest.json')), approval.candidateManifestSha256);
  assert.equal(sha(read('tests/reference/release-baseline/publish-manifest.json')), approval.baselineManifestSha256);
  const previousManifest = JSON.parse(read('tests/reference/release-baseline/publish-manifest.json'));
  const expectedManifest = structuredClone(previousManifest);
  Object.assign(expectedManifest.directRelease, {publicationAuthorized:true, publicationState:'authorized-release-candidate-public-verification-pending', releaseApprovalFile:'src/data/release-approval.json', sitemapUrlCount:5});
  assert.deepEqual(manifest, expectedManifest);
  // Keep the original release evidence immutable. Only this exact five-file requested amendment changes its byte comparison.
  const originalApproval = read('src/data/release-approval.json');
  assert.equal(sha(originalApproval), '0f9f3d4dff2c63014cfcb46f81303edea876b12efb0d8e81168ee53196bf985a', 'Historical release approval drift');
  assert.deepEqual(approval, JSON.parse(originalApproval), 'Historical release authority cannot be rewritten');
  const amendmentRaw = read('src/data/shared-banner-phone-amendment.json');
  assert.equal(sha(amendmentRaw), 'aeb0161f6beb2b23281efc436125ced4c4e975cccc5494fc39b96cfa735c0ae9', 'Shared banner amendment drift');
  const amendment = JSON.parse(amendmentRaw);
  for (const [path, digest] of Object.entries(approval.unchangedCustomerContent)) {
    const replacement = amendment.replacements[path];
    if (replacement) assert.equal(replacement.fromSha256, digest, 'Banner amendment baseline mismatch');
    assert.equal(sha(read(path)), replacement ? replacement.toSha256 : digest, path);
  }
  return true;
}
export function validateCurrentRelease() {
  if (process.env.SITE_URL) assert.equal(process.env.SITE_URL, 'https://seoul-guro.fwith.kr', 'production origin override');
  const read = path => fs.readFileSync(new URL('../' + path, import.meta.url));
  return validateReleaseApproval(JSON.parse(read('src/data/site-config.json')), JSON.parse(read('src/data/release-approval.json')), JSON.parse(read('src/data/publish-manifest.json')), read);
}
