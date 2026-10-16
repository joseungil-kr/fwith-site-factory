from pathlib import Path
import json,hashlib,re,datetime
from html_surface import BeautifulSoup
from expected_surface import C,A,copy,D,U,expected,norm

def check(html,route='/'):
 s=BeautifulSoup(html);want=expected(route);nodes=s.select('[data-copy-key]')
 assert len(nodes)==len(want),(len(nodes),len(want))
 for n,e in zip(nodes,want):
  assert n['data-copy-key']==e['key'],(n['data-copy-key'],e['key'])
  assert norm(n.get_text(' ',strip=True))==norm(e['text']),e['key']
  assert n.name==e['tag'],e['key']
  if 'href' in e:assert n.get('href')==e['href'],e['key']
  for p in [n,*n.parents]:assert not p.has_attr('hidden') and p.get('aria-hidden')!='true' and not p.has_attr('inert') and p.name!='details' and 'display:none' not in p.get('style','').replace(' ',''),'Hidden reviewed text'
 assert norm(s.find('body').get_text(' ',strip=True))==norm(' '.join(e['text'] for e in want)),'Extra, duplicate or missing customer text'
 assert len(s.find_all('h1'))==1
 assert not s.find_all(['script','form','iframe','button'])
 assert s.find('html')['lang']=='ko'
 assert s.select_one('meta[name="robots"]')['content']=='noindex,nofollow'
 assert not s.select('link[rel="canonical"]')
 assert s.find('title').get_text()==(D['page']['title'] if route=='/' else D['notFoundCopyPlan']['title'])
 assert s.select_one('meta[name="description"]')['content']==(D['page']['description'] if route=='/' else D['notFoundCopyPlan']['body'])
 assert s.find('nav')['aria-label']==U['navAriaLabel']
 ids=[n['id'] for n in s.select('[id]')];assert len(ids)==len(set(ids))
 for a in s.find_all('a'):
  h=a['href']
  if h.startswith('#'):assert h[1:] in ids,h
  elif h.startswith('/#'):assert h[2:] in ['products-and-cost','receiving-place','ribbon-and-order','order-timing','sources']
  else:assert h=='/' or h=='tel:18440644' or h.startswith('https://fwith.co.kr/') or h=='https://www.data.go.kr/data/15143467/fileData.do',h
 if route=='/':
  assert len(s.find_all('h2'))==7 and len(s.find_all('h3'))==7
  assert [n.get_text() for n in s.select('#questions h3')]==[f['question'] for f in copy['faq']]
  assert [n.get_text() for n in s.select('#questions p')]==[f['answer'] for f in copy['faq']]
  assert [n['data-product-sku'] for n in s.select('[data-product-sku]')]==['B201','B203','B205','B060']
  assert [n['data-shared-flower-banner'] for n in s.select('[data-shared-flower-banner]')]==['message','budget','consultation']
  # Placement, not only counts: one message above costs, budget after costs, consultation after ribbon.
  seq=[n.get('id') or n.get('data-shared-flower-banner') for n in s.select('article[data-page-id] > section,article[data-page-id] > figure')]
  assert seq==['opening','message','products-and-cost','budget','receiving-place','ribbon-and-order','consultation','order-timing','changes-and-cancellation','questions','sources'],seq
  assets=json.loads((C/'asset-render-binding.json').read_text())['assets'];images=s.find_all('img');assert len(images)==7
  for a in assets:
   matches=[n for n in images if n['src']==a['renderSrc']];assert len(matches)==1;n=matches[0]
   assert n['alt']==a['alt'] and [int(n['width']),int(n['height'])]==a['dimensions']
   assert n['loading']=='lazy' and n['decoding']=='async'
   assert hashlib.sha256((C/'dist'/a['renderSrc'][1:]).read_bytes()).hexdigest()==a['sha256']
 else:assert not s.find_all('img') and not s.find_all('h2')
 return {'route':route,'exactVisibleOccurrences':len(want),'h1':1,'h2':len(s.find_all('h2')),'h3':len(s.find_all('h3')),'images':len(s.find_all('img')),'allCopyKeysInExactOrder':True,'wholeBodyTextExact':True,'robots':'noindex,nofollow','canonical':None}

def validate_output_paths(dist):
 files=sorted(p.relative_to(dist).as_posix() for p in dist.rglob('*') if p.is_file())
 styles=[p for p in files if p.startswith('_astro/') and p.endswith('.css')]
 assets=json.loads((C/'asset-render-binding.json').read_text())['assets']
 expected_paths=sorted(['index.html','404.html','robots.txt']+styles+[a['renderSrc'][1:] for a in assets])
 assert len(styles)==1 and files==expected_paths and len(files)==11,'Unexpected output paths or production/key artifact'
 assert not any(p.is_symlink() for p in dist.rglob('*')),'Symlink output'
 return files

def main():
 (C/'evidence').mkdir(parents=True,exist_ok=True)
 dist=C/'dist';validate_output_paths(dist);html=sorted(p.relative_to(dist).as_posix() for p in dist.rglob('*.html'));assert html==['404.html','index.html'],html
 assert (dist/'robots.txt').read_text()=='User-agent: *\nDisallow: /\n'
 assert not list(dist.glob('*sitemap*')) and not any('indexnow' in p.name.lower() for p in dist.rglob('*'))
 rows=[check((dist/'index.html').read_text()),check((dist/'404.html').read_text(),'/404.html')]
 report={'timeUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS_AUTHOR_HTML_CHECKS','pages':rows,'facilityPages':0,'productionArtifacts':False,'newBinaryUpload':False,'actualPublicHTTPVerified':False,'searchOutcomeVerified':False}
 (C/'evidence/html-qa.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');(C/'evidence/expected-occurrences.json').write_text(json.dumps({'home':expected('/'),'404':expected('/404.html')},ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
