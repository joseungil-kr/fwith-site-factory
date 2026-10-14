from pathlib import Path
import json,hashlib,datetime
O=Path(__file__).parent;read=lambda p:json.loads(p.read_text());h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
a=read(O/'copy/article-copy.final.json');arts={x['id']:x for x in a['articles']};reg=read(O/'plan/evidence-registry.json')
coverage=read(O/'copy/intent-completion-matrix.json')
for q in coverage:
 art=arts[q['article']];ids=[u.split('#')[-1] for u in q['answerLocations']];secs=[s for s in art['sections'] if s['id'] in ids];q['answer']=[z for sec in secs for z in sec['paragraphs']];q['evidenceIds']=list(dict.fromkeys(e for sec in secs for e in sec['evidence']))
facts=[];faq=[];lines=[]
for art in a['articles']:
 for sec in art['sections']:facts.append({'article':art['id'],'sectionId':sec['id'],'exactParagraphs':sec['paragraphs'],'evidence':[{'id':e,**reg[e]} for e in sec['evidence']],'scope':'Source-backed facts plus explicitly tagged original editorial guidance; actual delivery/admission/total not asserted.'})
 for f in art['faq']:faq.append({'article':art['id'],'question':f['question'],'answer':f['answer'],'evidence':[{'id':e,**reg[e]} for e in f['evidence']]})
 lines.extend([f"PAGE {art['url']}",f"TITLE {art['title']}",f"H1 {art['h1']}",f"META {art['metaDescription']}",f"CARD {art['cardSummary']}",art['firstAnswer']])
 for sec in art['sections']:lines.extend([f"H2 {sec['heading']} [{sec['id']}]",*sec['paragraphs']])
 for q in art['faq']:lines.extend(['FAQ '+q['question'],q['answer']])
 lines.extend([art['sourceNote']]+[f"{s['name']} | {s['url']}" for s in art['sourceLinks']]+['CTA '+str(art['primaryCta']),'RELATED '+str(art['relatedLink']),''])
(O/'copy/article-copy.final.txt').write_text('\n\n'.join(lines)+'\n');(O/f"copy/article-copy.rev{a['revision']}.txt").write_text('\n\n'.join(lines)+'\n')
put(O/'copy/intent-completion-matrix.json',coverage);put(O/'copy/claim-evidence-map.json',facts);put(O/'copy/faq-evidence-map.json',faq)
files=['plan/fixed-plan.json','plan/evidence-registry.json','plan/fact-clarifications.json','copy/article-copy.final.json','copy/common-visible-copy.final.json','copy/article-copy.final.txt','copy/intent-completion-matrix.json','copy/claim-evidence-map.json','copy/faq-evidence-map.json','validation/copy-validation.json','validation/counts.json','validation/duplicate-comparison.json','handoff/approved-assets.json','handoff/directory-input.json']
m={'createdAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'revision':a['revision'],'files':[{'path':p,'bytes':(O/p).stat().st_size,'sha256':h(O/p)} for p in files]};put(O/'copy/review-input-manifest.json',m);put(O/f"copy/review-input-manifest.rev{a['revision']}.json",m)
print('article SHA',h(O/'copy/article-copy.final.json'));print('common SHA',h(O/'copy/common-visible-copy.final.json'));print('manifest SHA',h(O/'copy/review-input-manifest.json'))
