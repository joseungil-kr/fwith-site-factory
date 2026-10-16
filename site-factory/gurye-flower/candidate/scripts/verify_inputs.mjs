import {validateAuthor,validateReview,validateAssets,assertBoundary} from '../src/lib/gurye-runtime.mjs';
assertBoundary();const count=validateAuthor();validateReview();validateAssets();
console.log(JSON.stringify({packagedAuthorFilesVerified:count,historicalManifestEntries:132,packagedHistoricalEntries:8,archivedReferenceOnlyEntries:124,rootIndependentCopyReviewBound:true,historicalIndependentStaticReviewBound:true,assetsExactExistingBlobs:7,publicationEnabled:false,original132BytesReverifiedByRunner:false}));
