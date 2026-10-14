import pathlib,json,hashlib,datetime,collections
O=pathlib.Path('/workspace/shared/gangnam-plan-copy-20261013');B=pathlib.Path('/workspace/shared/gangnam-research-20261013');R=O/'independent-plan-review'
def load(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
p=O/'plan/fixed-plan.json';f=load(p);v=load(R/'final-verdict.json');source=load(B/'proposed-page-intents.json');ledger=load(O/'plan/candidate-ledger.json');inventory=load(O/'plan/candidate-inventory.json');holds=load(O/'plan/candidate-hold-rationale.json');membership=load(O/'plan/membership.json');checks=[]
def check(id,value,detail):checks.append({'id':id,'pass':bool(value),'detail':detail})
check('P01_expected_fixed_plan_digest',sha(p)=='82bf53fb58d01c65d7fe87e730fcaf39ec60620603f671696074ba41510e68c3','Exact supplied fixed-plan bytes independently rehashed.')
check('P02_three_urls',f['originalPlanN']==3 and len(f['pages'])==3 and [x['url'] for x in f['pages']]==v['exactUrls'],'Three exact URLs equal independent recommendation; no extra purchase article.')
check('P03_unique_urls',len({x['url'] for x in f['pages']})==3 and all(x['url']==f"/regions/{x['slug']}/" for x in f['pages']),'Unique /regions/ paths and matching slugs.')
check('P04_final_verdict_bound',any(x['path']==str(R/'final-verdict.json') and x['sha256']==sha(R/'final-verdict.json') for x in f['independentReview']),'Frozen plan binds real final-verdict, not only received worker message.')
for ref in f['independentReview']:check('P05_review_file_'+pathlib.Path(ref['path']).name,pathlib.Path(ref['path']).is_file() and sha(pathlib.Path(ref['path']))==ref['sha256'],'Read actual referenced file and recomputed digest.')
check('P06_research_input',f['inputManifest']['sha256']==sha(B/'delivery-manifest.json')==v['researchDeliveryManifestSha256'],'Research snapshot consistent across frozen plan and independent review.')
check('P07_proposal_bound',f['candidatePlanSha256']==sha(B/'proposed-page-intents.json'),'Exact earlier candidate plan is bound.')
check('P08_inventory_unchanged',inventory==load(B/'facilities/facility-evidence.json'),'All original facility inventory values including facts, unknowns, legal fields and exclusions retained exactly.')
check('P09_holds_unchanged',holds==load(B/'facilities/candidate-hold-rationale.json'),'All original candidate/hold/exclusion rationale values retained exactly.')
check('P10_ledger_digest',f['candidateLedgerSha256']==sha(O/f['candidateLedgerFile']),'Frozen plan binds actual candidate ledger.')
check('P11_twelve_groups',ledger['count']==12==len(ledger['groups']) and len({x['id'] for x in ledger['groups']})==12 and ledger['isPageQuota'] is False,'Seven local facilities, three nonlocal exclusions and two unresolved discovery groups retained as twelve groups.')
counts=collections.Counter(x['status'] for x in ledger['groups']);expected={'active_factual_anchor':5,'hold_office_address_only':2,'excluded_nonlocal':3,'hold_original_access_or_address':2}
check('P12_status_accounting',dict(counts)==expected,dict(counts))
byid={x['id']:x for x in ledger['groups']}
for x in inventory['facilities']:
 y=byid.get(x['id'],{});check('P13_local_'+x['id'],y.get('name')==x['displayName'] and y.get('sourceDecision')==x['decision'] and y.get('roadAddress')==x['roadAddress'] and y.get('legalDong')==x['legalDong'] and y.get('administrativeDong') is None and y.get('newStandaloneFacilityUrl') is None,'Name, original decision, road/legal address and non-assignment preserved; no separate facility URL.')
for status,key in [('excluded_nonlocal','exclusions'),('hold_original_access_or_address','heldDiscoveries')]:
 check('P14_'+status,[x['original'] for x in ledger['groups'] if x['status']==status]==holds[key],'Every original group record preserved in same order.')
anchors=f['facilityAnchors'];active={x['id'] for x in ledger['groups'] if x['status']=='active_factual_anchor'}
check('P15_five_anchors',len(anchors)==5 and {x['id'] for x in anchors}==active,'Only five active verified factual anchors projected; address-only offices omitted from customer anchors.')
check('P16_alias_merge',ledger['aliasesMerged']=={'gangnam-severance-funeral':'yonsei-gangnam-funeral'} and sum(x['id']=='yonsei-gangnam-funeral' for x in anchors)==1,'One Yonsei Gangnam/Gangnam Severance anchor, no duplicate facility.')
legalMap={x['name']:x['code'] for x in membership['legalUnits']};imap={x['id']:x for x in inventory['facilities']};pages={x['id']:x for x in f['pages']}
for x in anchors:
 s=imap[x['id']];check('P17_anchor_'+x['id'],x['roadAddress']==s['roadAddress'] and x['legalDong']==s['legalDong'] and x['administrativeDong'] is None and x['legalDongCode']==(legalMap[s['legalDong']] if s['legalDong'] else None) and x['href']==pages[x['articleId']]['url']+'#'+x['id'] and x['id'] in pages[x['articleId']]['candidateIds'],'Road/legal facts match input; legal code only maps explicit source dong; admin remains null; article/anchor projection correct.')
check('P18_explicit_nulls',all(next(x for x in anchors if x['id']==id)['legalDong'] is None and next(x for x in anchors if x['id']==id)['legalDongCode'] is None for id in ['samsung-seoul-funeral','setec']),'Samsung and SETEC legalDong/legalDongCode remain null, no road-name inference.')
check('P19_membership_preserved',membership==load(B/'membership.json'),'All 14 legal units, 22 administrative units and 31 relations preserved as full original JSON, not merely counts.')
check('P20_directory_counts',f['directory']['legalDongCount']==14 and f['directory']['administrativeDongCount']==22 and f['directory']['relationships']==31 and f['directory']['actualRichCards']==3 and f['directory']['allFacilityAdministrativeDongs'] is None,'Directory counts separate from three article denominator; all facility administrative assignments absent.')
check('P21_holds_merges',f['holdsAndMerges']==source['holdsAndMerges'],'All six proposal hold/merge records retained unchanged including opening/relocation, standalone Samsung, synonym/dong quotas, St Mary, nonlocal offices and unresolved offices.')
check('P22_early_purchase_history',pathlib.Path(f['purchaseCandidateHistoryFile']).resolve()==(B/'purchase/content-candidates-and-holds.json').resolve() and len(load(pathlib.Path(f['purchaseCandidateHistoryFile']))['candidates'])==8,'Eight earlier purchase candidates remain in the hash-verified research snapshot; no replacement or dropped history.')
sg={x['id']:x for x in source['groups']}
for page in f['pages']:
 s=sg[page['sourceProposedId']]
 check('P23_page_'+page['id'],page['candidateIds']==s['facilityIds'] and page['products']==s['productSkus'] and page['uniqueFactsToUse']==s['uniqueFacts'] and page['unknowns']==s['unknowns'] and page['buyerDecision']==s['intent'],'Exact facility/product/factual-scoping/unknown/buyer-decision projection from proposal.')
check('P24_route_denominator',f['routeDenominator']==['/','/regions/']+v['exactUrls']+['/404.html'],'Six technical routes properly distinct from N=3 purchase articles. No assumed live routes.')
check('P25_local_only',f['status']=='LOCAL_PLAN_FROZEN_AFTER_INDEPENDENT_REVIEW' and f['frozen'] is True and f['directory']['prepublicationRobots']=='noindex,nofollow,noarchive' and f['directory']['prepublicationSitemap']==[],'Local frozen-plan status and proposed prepublication settings retained; actual rendered settings not checked here.')
failed=[x for x in checks if not x['pass']]
out={'schemaVersion':1,'reviewedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'verdict':'FROZEN_PROJECTION_ACCEPTED' if not failed else 'FROZEN_PROJECTION_FAILED','classification':'직접 확인','scope':'Small local readback of frozen plan and its inventory/provenance projection. No renewed remote research; no customer-copy, render or publication quality approval.','fixedPlanFile':str(p),'fixedPlanSha256':sha(p),'independentPlanVerdictSha256':sha(R/'final-verdict.json'),'originalPlanN':f['originalPlanN'],'exactUrls':[x['url'] for x in f['pages']],'inputDigests':[{'file':str(O/'plan'/n),'sha256':sha(O/'plan'/n)} for n in ['candidate-ledger.json','candidate-inventory.json','candidate-hold-rationale.json','membership.json']],'checks':checks,'checkCount':len(checks),'failedChecks':failed,'noFixedPlanChanges':True,'unverified':['Chronological authorship is reported by author; this projection check does not prove creation timing from mutable filesystem metadata. FrozenAt and prior review time are recorded evidence only.','New article rev1 content, layout, actual anchor presence and customer-copy suitability were not inspected in this narrow check.','No public HTTP, provider, Git source or IndexNow verification.'],'note':'A pass here means the immutable research/decision projection is faithful. It is not a final copy or site completion verdict.'}
(R/'frozen-projection-verdict.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
# Actual saved artifact readback.
a=load(R/'frozen-projection-verdict.json');assert a['fixedPlanSha256']==sha(p) and a['exactUrls']==v['exactUrls'] and not failed
print(json.dumps({'file':str(R/'frozen-projection-verdict.json'),'sha256':sha(R/'frozen-projection-verdict.json'),'fixedPlanSha256':sha(p),'checks':len(checks),'failed':len(failed)},ensure_ascii=False,indent=2))
