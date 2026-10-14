import json,hashlib,datetime
from pathlib import Path
p=Path('/workspace/shared/seocho-plan-copy-20261013');r=Path('/workspace/shared/seocho-research-20261013');o=p/'independent-plan-review'
def sha(f):return hashlib.sha256(Path(f).read_bytes()).hexdigest()
readfiles=['repo/SALES_COPY_ACCEPTANCE.md','repo/SEARCH_CONTENT_STRATEGY.md','repo/SHARED_BANNER_STANDARD.md','repo/PRECEDENCE_AND_COVERAGE.md','facilities/raw/funeral-route.txt','facilities/raw/eltower-route.txt','facilities/raw/eltower-wedding.txt','facilities/raw/eltower-faq.txt','facilities/raw/at-convenience.txt','facilities/raw/at-2017-wreath.txt','facilities/raw/at-hall1.txt','facilities/raw/at-hall2.txt','facilities/raw/at-operating-guideline-2026.txt','facilities/raw/at-safety-guideline-2025.txt','facilities/raw/sac-museum-rules.txt','raw/order-policy.jpg','raw/change-policy.jpg','raw/fwith-cs.png','raw/KIKcd_B.20261012.seocho.txt','raw/KIKcd_H.20261012.seocho.txt','raw/KIKmix.20261012.seocho.txt']
readfiles += ['facilities/raw/'+x for x in ['funeral-floor1.jpg','funeral-floor2.png','funeral-floor3.jpg']]
readfiles += [f'raw/{sku}-photo.jpg' for sku in ['B201','B203','B205','B060','C200','C203','C204','C205']]
readfiles += [f'raw/fwith-{sku}.html' for sku in ['B201','B203','B205','B060','C200','C203','C204','C205']]
readfiles += [f'purchase/raw/{f}.txt' for f in ['js-funeral','js-wedding','js-opening','thewreath-wedding','thewreath-opening','yedo-opening','yedo-relocation','binso-facility']]
v={
 'schemaVersion':1,'reviewedAtUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'reviewer':'independent reviewer /root/draft_seocho_customer_pages/review_seocho_page_plan',
 'verdict':'ACCEPTED_FOR_LOCAL_ORIGINAL_PLAN_N_FREEZE_ONLY','permitLocalArticleCountFreeze':True,'approvedOriginalPlanN':2,
 'reviewIs': 'Independent judgment of candidate page count, separation, preservation, factual boundaries, and planned customer decisions on the exact locally saved inputs. Not customer-copy, implementation, publication, or live-fulfillment approval.',
 'exactInputs':{
  'candidatePlan':{'path':str(p/'plan/candidate-plan.json'),'sha256':sha(p/'plan/candidate-plan.json')},
  'candidateInventory':{'path':str(p/'plan/candidate-inventory.json'),'sha256':sha(p/'plan/candidate-inventory.json')},
  'inputBindings':{'path':str(p/'plan/input-bindings.json'),'sha256':sha(p/'plan/input-bindings.json')},
  'researchManifest':{'path':str(r/'file-manifest.json'),'sha256':sha(r/'file-manifest.json'),'entriesRehashed':265,'mismatches':0},
  'recomputedChecks':{'path':str(o/'recomputed-checks.json'),'sha256':sha(o/'recomputed-checks.json')}
 },
 'blockingDefects':[],
 'directlyConfirmed':[
  'Recomputed every one of the 265 research manifest entries and all 16 input-binding hashes with no mismatch. Candidate SHA is 42e80f9b020cdba3eb451d939c30cace578925ff1a402344edbc464b2a4f1559.',
  'Candidate inventory preserves all eight ledger groups, including held aT wedding, SAC museums, other competitor-listed venues and dong page combinations. Seven held-page decisions match the plan exactly. Candidate originalPlanN remains null and frozen remains false.',
  'Read the saved commercial body text of eight competitor originals, and independently extracted purchase-link sets from original HTML for wedding/opening pairs. js shares two SKU URLs; thewreath shares all five product URLs; Yedo repeats its catalog. Their service promises were not accepted as fwith facts.',
  'All eighteen exact query strings match their saved raw search reports and have nonempty result payloads. These are six geographic terms across three purchase situations, not eighteen independent pages or measured demand.',
  'Original MOIS extracted rows exactly match the candidate geography: ten legal dongs, eighteen administrative dongs, twenty-three relationships. 반포3동 maps to legal 잠원동; 서초3동 spans 서초동 and 방배동. All three facility administrative assignments remain null.',
  'Seller HTML independently confirms all eight SKU names and basic prices, including B205 109000 KRW and C204 99000 KRW, and the separate order-time delivery-fee field. Viewed all eight current saved product images; no flower-count, size, longevity or quality inference was drawn.',
  'Visually read both original seller policy images. They disclose mixed fresh/artificial materials, no separate wreath collection, possible material variation, and change/refund clauses whose general application is not resolved by the plan.',
  'Official saved directions distinguish 서울성모장례식장 at 반포대로 222/반포동 505, 엘타워 at 강남대로 213/양재동 24, and aT센터 at 강남대로 27/양재동 232. Viewed all three Seoul St. Mary floor-map images; no current occupancy or obituary was used.',
  'Official 엘타워 wedding text gives Grand 7F, Grace 6F, Orce 5F and Elhouse 8F. Its prior-goods FAQ requires coordination; it does not establish wreath intake permission.',
  'aT official sources distinguish exhibition halls on 1F and 3F. The 2017 release describes a planned artificial-flower three-tier restriction for weddings. The exhibition-goods filing and contractor safety rules are not generalized to every wreath delivery.',
  'Read SAC 2026 Articles 1, 2 and 11(1): the three named museum/exhibition facilities define exhibition space to include exhibit rooms and ancillary interior areas, and prohibit wreaths there. This does not establish a ban on every performance or outdoor space.',
  'Read the supplied latest sales-copy, search-content and shared-banner rules. Candidate planning retains friendly seller voice, four real SKU cards per article, source/price limits, three unchanged banners, and independent exact-copy checks before later acceptance.'
 ],
 'editorialJudgments':[
  {'decision':'Keep two articles','reason':'Condolence and celebration have different recipients, tone, ribbon purpose and actual product sets. Merging them would blur the first buying decision. Two is a result of this evidence, not a quota inherited from purchase groups.'},
  {'decision':'Do not split wedding and opening/relocation now','reason':'Their order information and ribbon purposes differ, so each needs a clear section. In this packet they share four verified celebration SKUs, price policy and seller CTA; opening/relocation lacks additional verified Seocho-specific service facts sufficient to justify another rich URL.'},
  {'decision':'Use Seoul St. Mary and Eltower as factual anchors','reason':'Their verified room or hall details can resolve receipt information within the relevant article. A separate URL would currently repeat products, policy and CTA with limited additional buying value.'},
  {'decision':'Keep aT exhibition contextual and aT wedding held','reason':'Exhibition logistics explain why event and booth details matter, but neither layout nor paperwork proves product admission. Current wedding material suitability remains unknown.'},
  {'decision':'Keep SAC museums and unverified competitor venue aliases held','reason':'SAC has a specific actual restriction, while the other venues lack current official confirmation in this packet. No substitute bouquets/plants or inferred same-building alias can activate a sales destination.'}
 ],
 'nonBlockingCopyReviewRisks':[
  'The celebration guide spans several occasions. Keep distinct reader paths and a compact relevant restriction section; do not let aT/SAC warnings or long address comparisons dominate friendly product help.',
  'Actual product photos contain sample wedding or condolence ribbons. Treat them as the real catalog photos, not evidence of a specific delivery, final ribbon wording or material proportions.',
  'Use the exact three museum names and the exhibition/interior scope when drafting the SAC restriction. Do not write an entire-complex prohibition or suggest a lobby workaround.',
  'No live venue admission, installation, storage, collection, arrival guarantee, stock, final price, partnership or completed delivery is established. Keep those boundaries intact in every CTA and banner-adjacent string.',
  'The plan title/H1 choices can be reviewed now, but first-answer quality, 2500–3000-character drafting target, information completeness, duplicate text, friendliness and rendered visibility cannot pass before the actual copy exists.'
 ],
 'toolReportedOnly':[
  'HTTP statuses, capture timestamps and operator-site 502 are saved acquisition reports; no fresh network request was made in this review.',
  'Search result contents and source capture tooling do not prove search ranking, demand, market share or a completed order.'
 ],
 'unverified':[
  'The final frozen-plan bytes and their review binding, pending the next reviewer readback.',
  'Customer copy and all visible UI strings; actual source, build HTML, accessibility, viewport behavior, public URL responses and indexing.',
  'Current wreath intake or materials at aT wedding; actual operational receipt at any named venue; all order-specific fulfillment and final costs.'
 ],
 'freezeInstructions':{
  'preserveCandidateBytes':True,
  'permittedStatusOnlyChanges':['Set originalPlanN to 2','Set frozen to true and a clearly local plan-approved status','Add freeze timestamp, candidate SHA and this verdict path/SHA','Move historical research notDone claims to a clearly historicalResearchNotDone field without deleting their content','Remove approved/frozen article N from current unverified only after freeze, retaining copy, implementation, order, release and operational unknowns'],
  'mustPreserve':['Both article IDs, URLs, planned buyer decisions and SKU sets','All eight candidate groups and seven held-page decisions','Ten/eighteen/twenty-three geography, legal-address distinctions and null administrative assignments','All actual restrictions, unsupported-claim prohibitions and scope boundaries','Five planned routes; home/list/404 and anchors are not article units'],
  'predictedNotBuilt':'actualArticleChildren, articleCount, route denominator and index/banner settings in this plan are intended future outputs, not evidence that implementation exists.',
  'nextGate':'Provide exact frozen-plan path and digest for independent preservation and review-binding readback. Content changes beyond the listed status-only changes require re-review.',
  'notAuthorizedOrClaimed':['Remote writes','Source ownership','Implementation','Publication','IndexNow or indexing','Actual order','Venue contact']
 },
 'inspectionScope':{'mode':'Offline saved originals, their extracted texts, exact-input rehashing and direct image inspection. No competitor original text or image copied into a customer artifact.','readArtifacts':[{'path':str(r/f),'sha256':sha(r/f)} for f in readfiles]},
 'verificationRecovery':'An optional BeautifulSoup parser was unavailable (ModuleNotFoundError). Retried using the Python standard-library HTMLParser; all eight seller original HTML checks then succeeded. No source artifacts were changed.'
}
(o/'plan-review-verdict.json').write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
print('VERDICT',str(o/'plan-review-verdict.json'));print('SHA256',sha(o/'plan-review-verdict.json'))
print('readback',json.load(open(o/'plan-review-verdict.json'))['verdict'])
