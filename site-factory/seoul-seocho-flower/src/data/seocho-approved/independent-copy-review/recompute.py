import json,hashlib,re,difflib,sys
from pathlib import Path
from datetime import datetime,timezone
from PIL import Image
P=Path('/workspace/shared/seocho-plan-copy-20261013');R=Path('/workspace/shared/seocho-research-20261013');O=P/'independent-copy-review'
rev=int(sys.argv[1]) if len(sys.argv)>1 else 2
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
load=lambda p:json.loads(Path(p).read_text())
commonrev=rev if (P/f'copy/common-visible-copy.rev{rev}.json').exists() else 2
a=load(P/f'copy/article-copy.rev{rev}.json');c=load(P/f'copy/common-visible-copy.rev{commonrev}.json');plan=load(P/'plan/fixed-plan.json');registry=load(P/'plan/evidence-registry.json');assets=load(P/'handoff/approved-assets.json')
checks=[]
def check(label,got,want):checks.append({'check':label,'pass':got==want,'observed':got,'expected':want})
check('frozen plan exact SHA',sha(P/'plan/fixed-plan.json'),'5675a7cc1cf5b142458133cb2fc55ce7224ca5e819b2e11f6684bc2d59728318')
check('research manifest exact SHA',sha(R/'file-manifest.json'),'be5698e17a23190532eb0559e00ac86a78eaa82335c3ca0ecbf3a5f322e493e3')
manifest=load(R/'file-manifest.json');check('all 265 research file bytes match manifest',[x['file'] for x in manifest['files'] if sha(R/x['file'])!=x['sha256']],[])
check('article denominator',len(a['articles']),2)
check('directory no banners',c['common']['directory']['bannerCount'],0)
check('directory real cards',c['common']['directory']['actualRichCardCount'],2)
check('article order and slugs',[(x['id'],x['url']) for x in a['articles']],[(x['id'],x['url']) for x in plan['pages']])
for f in [a,c]:
 for n in ['fixedPlan','planReview','fixedPlanVerdict']:
  check(f'rev{rev} binding {n} '+('article' if f is a else 'common'),sha(f['bindings'][n+'Path']),f['bindings'][n+'Sha256'])
for key,source in registry.items():
 if 'file' in source:check('original source SHA '+key,sha(source['file']),source['sha256'])
for asset in assets['assets']:
 path=P/asset['file'];check('asset bytes '+asset.get('sku',asset.get('variant')),sha(path),asset['sha256']);check('asset original equal '+asset.get('sku',asset.get('variant')),sha(path),sha(asset['sourceFile']))
 check('asset dimensions '+asset.get('sku',asset.get('variant')),list(Image.open(path).size),asset['dimensions'])
 if asset['kind']=='actual-sale-product':
  card=next(x for x in c['common']['productCards'] if x['sku']==asset['sku']);check('approved card exact reuse '+asset['sku'],card,asset['copy'])
  check('card current name and price '+asset['sku'],[card['name'],card['basicPriceKRW']],[registry[asset['sku']]['name'],registry[asset['sku']]['priceKRW']]);check('specific product CTA '+asset['sku'],card['cta']['href'],registry[asset['sku']]['url'])
check('banners exact approved text',c['common']['banners'],assets['bannersCopy'])
computed=[]
for art,p in zip(a['articles'],plan['pages']):
 check('products set '+art['id'],art['productSkus'],p['products'])
 check('section-to-markdown '+art['id'],art['contentMarkdown'],'\n\n'.join('## '+s['heading']+'\n\n'+'\n\n'.join(s['paragraphs']) for s in art['sections']))
 check('title begins primary '+art['id'],art['title'].startswith(art['primaryKeyword']),True)
 check('H1 contains primary '+art['id'],art['primaryKeyword'] in art['h1'],True)
 check('card not primary-prefixed '+art['id'],art['cardSummary'].startswith(art['primaryKeyword']),False)
 check('article card exact summary '+art['id'],next(x['summary'] for x in c['common']['articleCards'] if x['id']==art['id']),art['cardSummary'])
 check('sources registry-resolved '+art['id'],[key for s in art['sections']+art['faq'] for key in s.get('evidence',[]) if key not in registry],[])
 bodylen=len(art['firstAnswer'])+sum(len(s['heading'])+sum(len(v) for v in s['paragraphs']) for s in art['sections']);faqlen=sum(len(x['question'])+len(x['answer']) for x in art['faq'])
 check('unique body count '+art['id'],bodylen,art['uniqueBodyCharsIncludingFirstAnswer']);check('FAQ count '+art['id'],faqlen,art['faqChars'])
 check('FAQ/body distinct exact answers '+art['id'],[q['answer'] for q in art['faq'] if q['answer'] in art['contentMarkdown']],[])
 check('plain transcript contains every customer text leaf '+art['id'],all(t in (P/f'copy/article-copy.rev{rev}.txt').read_text() for t in [art[k] for k in ['title','h1','metaDescription','cardSummary','firstAnswer']]+[p for s in art['sections'] for p in [s['heading']]+s['paragraphs']]+[z for q in art['faq'] for z in [q['question'],q['answer']]]),True)
 commonprefix=len(__import__('os').path.commonprefix([art['title'],art['cardSummary']]))
 check('title-card common prefix <=8 '+art['id'],commonprefix<=8,True)
 similarity=difflib.SequenceMatcher(None,art['cardSummary'],art['firstAnswer'],autojunk=False).ratio()
 check('card-first answer similarity <70% '+art['id'],similarity<.7,True)
 computed.append({'id':art['id'],'firstAnswerChars':len(art['firstAnswer']),'bodyIncludingHeadingsAndFirstAnswer':bodylen,'bodyOnlyParagraphsAndFirstAnswer':len(art['firstAnswer'])+sum(sum(map(len,s['paragraphs'])) for s in art['sections']),'faqCount':len(art['faq']),'faqChars':faqlen,'titleCardCommonPrefixChars':commonprefix,'cardFirstAnswerCharacterSequenceRatio':similarity})
manifest_path=P/f'copy/review-input-manifest.rev{rev}.json'
if manifest_path.exists():
 for v in load(manifest_path)['files']:check('review-input manifest '+v['file'],[len((P/v['file']).read_bytes()),sha(P/v['file'])],[v['bytes'],v['sha256']])
g=load('/workspace/shared/gwanak-plan-copy-20261013/copy/article-copy.rev4.json')
cross=[]
for art,prior in zip(a['articles'],g['articles']):
 seq=difflib.SequenceMatcher(None,art['contentMarkdown'],prior['contentMarkdown'],autojunk=False).ratio()
 pars=[x for s in art['sections'] for x in s['paragraphs']];old=[x for s in prior['sections'] for x in s['paragraphs']]
 cross.append({'id':art['id'],'comparison':'Gwanak same-purchase-type rev4 exact paragraphs + contentMarkdown','sequenceRatio':seq,'exactFullParagraphMatches':[x for x in pars if x in old],'limit':'Ratio is descriptive; independently read both full texts. Shared seller SKUs/policies are legitimate, but local content must add purchase value.'})
output={'reviewedAtUTC':datetime.now(timezone.utc).isoformat(),'classification':'직접 확인: independent local bytes and calculations','revision':rev,'files':{str(p.relative_to(P)):sha(p) for p in [P/f'copy/article-copy.rev{rev}.json',P/f'copy/article-copy.rev{rev}.txt',P/f'copy/common-visible-copy.rev{commonrev}.json',P/'plan/fixed-plan.json',P/'plan/evidence-registry.json',P/'handoff/approved-assets.json']},'checks':checks,'checkCount':len(checks),'failureCount':sum(not x['pass'] for x in checks),'counts':computed,'crossRegion':cross,'scope':'Copy/asset data only. No runtime, browser, deployment, order, payment, or fulfillment checks.'}
(O/f'recomputed-checks.rev{rev}.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'revision':rev,'checks':len(checks),'failed':[x for x in checks if not x['pass']],'counts':computed,'crossRegion':cross},ensure_ascii=False,indent=2))
