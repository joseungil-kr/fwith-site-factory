from pathlib import Path
import json,copy,hashlib,datetime,difflib
O=Path(__file__).parent;B=Path('/workspace/shared/gangnam-plan-copy-20261013');R=Path('/workspace/shared/gangnam-research-20261013');rules=Path('/workspace/shared/gangnam-evidence/rules-at-pinned-main')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def bind(p,ptr=None):
 d={'file':str(p),'sha256':sha(p)}
 if ptr is not None:d['jsonPointer']=ptr
 return d
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
x=json.loads((O/'mapping/keyword-mapping.draft.json').read_text());x['metadataRefinedAt']=datetime.datetime.now(datetime.timezone.utc).isoformat();x['status']='METADATA_PROVENANCE_REFINED_UNSCORED';x['refinesMapping']=bind(O/'mapping/keyword-mapping.draft.json')
targets=json.loads((O/'assessment/targets.frozen.json').read_text())['records']
for i,rec in enumerate(x['records']):
 id=rec['id'];idx=i-1;target=targets[i]['evaluationTarget']
 rec['keyword_cluster_definition']={k:target[k] for k in ['region','service','essentialModifiers','intentKey','pageRole','expectedCustomerQuestion']}
 rec['keyword_cluster_definition']['source']=bind(O/'assessment/targets.frozen.json',f'/records/{i}/evaluationTarget')
 rec['query_class_origin']={'classification':'추정·판단: existing home role classified using core-commercial definition','roleSource':bind(B/'copy/common-visible-copy.final.json','/common/home'),'ruleSource':{**bind(rules/'site_factory_query_first_v1_1_test.md'),'lines':[15,17]}} if id=='home' else {'classification':'직접 확인: unchanged frozen queryClass mapped to snake_case','source':bind(B/'plan/fixed-plan.json',f'/pages/{idx}/queryClass'),'value':rec['query_class']}
 rec['query_priority_semantics']['ruleSource']={**bind(rules/'COMBINED_RULES.md'),'lines':[237,237]}
 rec['query_priority_semantics']['selectionSource']=bind(B/'copy/common-visible-copy.final.json','/common/home') if id=='home' else bind(B/'plan/fixed-plan.json',f'/pages/{idx}/buyerDecision')
 for ev in rec['query_evidence']:
  if ev['type']=='accepted-intent-decision' and id=='home':
   ev.update(bind(B/'copy/common-visible-copy.final.json','/common/home'));ev['explanation']='Existing accepted home intro, purposes and product choices support the regional flower-wreath overview. The separately frozen article denominator remains N3.'
  if ev['type']=='official-facility-evidence':
   ev['factsOrigin']=bind(R/'proposed-page-intents.json',f'/groups/{idx}/uniqueFacts');ev['caution']='Facility claims remain bounded to their original context. No live receipt, stock, final total or delivery guarantee established.'
   if id=='event':
    ev['facts'][0]['fact']='코엑스는 삼성동 영동대로513이며 코엑스마곡과 구분한다. 공식 회의실 행사준비가이드는 행사 후 화환 등 폐기물 처리비용을 안내한다.'
    ev['dateClarification']={**bind(B/'plan/fact-clarifications.json','/coexGuideDate'),'explanation':'2026.03.18 is the official download-list posting date, not an asserted PDF edition. The earlier proposal wording is not adopted as a current guide-edition claim.'}
  if ev['type']=='accepted-copy-and-full-intent-review':ev['scope']='Existing independent exact revision3 full-copy/intent finding only; not a numeric A04 score and not automatically a revision4 acceptance.'
write(O/'mapping/keyword-mapping.metadata-refined.json',x)
old=O/'mapping/keyword-mapping.draft.json';new=O/'mapping/keyword-mapping.metadata-refined.json'
(O/'mapping/metadata-provenance.diff').write_text(''.join(difflib.unified_diff(old.read_text().splitlines(True),new.read_text().splitlines(True),fromfile=str(old),tofile=str(new))))
print(sha(new))
