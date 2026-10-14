from pathlib import Path
import json,hashlib,re,datetime
P=Path('/workspace/shared/gangnam-plan-copy-20261013');O=P/'independent-copy-review/facts/rev3';R=Path('/workspace/shared/gangnam-research-20261013')
def j(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def w(n,d):(O/n).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
checks=[]
def ck(n,p,d=None):checks.append({'check':n,'pass':bool(p),'details':d})
a=j(P/'copy/article-copy.final.json');old=j(P/'independent-copy-review/facts/snapshot/article-copy.final.json');c=j(P/'copy/common-visible-copy.final.json');reg=j(P/'plan/evidence-registry.json');rt=j(P/'handoff/runtime-input.json');inv=j(P/'handoff/visible-copy-inventory.json');faq=j(P/'copy/faq-evidence-map.json')
ck('article_hash_requested',sha(P/'copy/article-copy.final.json')=='6aa8e1f7acefaed276486ebefbb93bddb1e9b5eb1b15023ed9d7fda3ec3daeb3')
ck('common_hash_unchanged',sha(P/'copy/common-visible-copy.final.json')=='da15580bb4f05ae39a60a51d6bdc3fe9fcc65d9e2d738dcd573ebc483aa70cdd')
ck('review_manifest_rev3_hash',sha(P/'copy/review-input-manifest.rev3.json')=='16b79965417ef15fe774692802cc890e656f2ee9a9c053d0d3e61cb62d0e987b')
ck('runtime_articles_exact',rt['articles']==a['articles'])
ck('runtime_common_exact',rt['common']==c['common'])
ck('runtime_directory_exact',rt['directory']==j(P/'handoff/directory-input.json'))
ck('runtime_assets_exact',rt['assets']==j(P/'handoff/approved-assets.json'))
ck('runtime_n_and_paths',rt['originalPlanN']==3 and rt['expectedPaths']==['/','/regions/']+[x['url'] for x in a['articles']]+['/404.html'])
ck('no_publication_claim',all(x is False or x is None for x in rt['publication'].values()))
ck('runtime_binding_exact',all(sha(P/f)==v['sha256'] and (P/f).stat().st_size==v['bytes'] for f,v in rt['inputBindings'].items()))
ck('handoff_binding_exact',j(P/'handoff/input-bindings.json')['files']==rt['inputBindings'])
ck('visible_inventory_bound_to_exact_copy',inv['articleHash']==sha(P/'copy/article-copy.final.json') and inv['commonHash']==sha(P/'copy/common-visible-copy.final.json'))
def resolve(path):
 n=rt
 for token in re.findall(r'([^\.\[\]]+)',path):n=n[int(token)] if isinstance(n,list) else n[token]
 return n
ck('all_246_visible_inventory_values_exact',len(inv['visibleTextFields'])==246 and all(resolve(x['path'])==x['text'] for x in inv['visibleTextFields']))
ck('all_44_target_inventory_values_exact',len(inv['functionalTargets'])==44 and all(resolve(x['path'])==x['value'] for x in inv['functionalTargets']))
ck('twelve_product_data_references_exact',len(inv['dataReferences'])==3 and sum(len(x['values']) for x in inv['dataReferences'])==12 and all(resolve(x['path'])==x['values'] for x in inv['dataReferences']))
ck('visible_inventory_excludes_functional_and_data_refs',all(not x['path'].endswith('Href') and 'productCardSkus' not in x['path'] for x in inv['visibleTextFields']))
ck('faq_map_exact',faq==[{'article':ar['id'],'question':f['question'],'answer':f['answer'],'evidence':[{'id':e,**reg[e]} for e in f['evidence']]} for ar in a['articles'] for f in ar['faq']])
ck('one_day_policy_attributed_in_all_three',all('배송 완료 후 하루 이상' in ' '.join(next(s for s in ar['sections'] if s['id']=='changes')['paragraphs']) and '공식몰' in next(s for s in ar['sections'] if s['id']=='changes')['paragraphs'][0] for ar in a['articles']))
ev=next(ar for ar in a['articles'] if ar['id']=='event');coex=next(s for s in ev['sections'] if s['id']=='coex')
ck('coex_date_ambiguity_removed','2026년 3월' not in ' '.join(coex['paragraphs']) and '2026년 3월' not in ev['sourceNote'])
ck('coex_meeting_scope_retained','회의실' in ' '.join(coex['paragraphs']) and '처리비용이 발생' in ' '.join(coex['paragraphs']) and '해당 행사의 운영 조건' in ' '.join(coex['paragraphs']))
ck('new_faq_conditional_source_attribution',all(t in ev['faq'][0]['answer'] for t in ['취소 가능 여부','제작·출고','카드사 처리기간','일주일 정도','공식몰']))
changed=[]
for ar,pr in zip(a['articles'],old['articles']):
 for s,ps in zip(ar['sections'],pr['sections']):
  if s!=ps:changed.append({'article':ar['id'],'section':s['id'],'entireFinalSection':s,'previousSection':ps})
 for k in ['faq','sourceNote']:
  if ar[k]!=pr[k]:changed.append({'article':ar['id'],'field':k,'entireFinalValue':ar[k],'previousValue':pr[k]})
w('all-changed-customer-content.json',changed)
w('delta-projection-checks.json',{'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checks':checks,'checkCount':len(checks),'passCount':sum(x['pass'] for x in checks),'failures':[x for x in checks if not x['pass']],'changedContentGroups':len(changed),'runtimeSha256':sha(P/'handoff/runtime-input.json')})
print(json.dumps({'checkCount':len(checks),'passes':sum(x['pass'] for x in checks),'failures':[x for x in checks if not x['pass']],'changedContentGroups':len(changed),'changedSections':[(x['article'],x.get('section',x.get('field'))) for x in changed]},ensure_ascii=False,indent=2))
