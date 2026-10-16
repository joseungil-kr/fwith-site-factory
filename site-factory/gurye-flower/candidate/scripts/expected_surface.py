"""Independent structural projection of sealed authored JSON. Never invents customer sentences."""
from pathlib import Path
import json,re
C=Path(__file__).resolve().parents[1];A=C.parent/'inputs/author'
copy=json.loads((A/'customer-copy.json').read_text());D=copy['display'];U=D['siteUI']
norm=lambda s:re.sub(r'\s+',' ',s).strip()
def blocks(text):
 out=[]
 # Separate paragraph/list runs without combining an introductory paragraph with its following list.
 for chunk in re.split(r'\n\s*\n',text.strip()):
  lines=chunk.splitlines();i=0
  while i<len(lines):
   list_mode=lines[i].startswith('- ');run=[]
   while i<len(lines) and lines[i].startswith('- ')==list_mode:run.append(lines[i][2:] if list_mode else lines[i]);i+=1
   out.append(('ul',run) if list_mode else ('p','\n'.join(run)))
 return out

def expected(route='/'):
 out=[]
 def add(key,text,tag,href=None):
  v={'key':key,'text':text,'tag':tag}
  if href is not None:v['href']=href
  out.append(v)
 def anchor(href):return '/'+href if route!='/ ' and route!='/' and href.startswith('#') else href
 add('ui.skipLabel',U['skipLabel'],'a',U['skipHref']);add('ui.brandLabel',U['brandLabel'],'b');add('ui.regionLabel',U['regionLabel'],'small')
 for i,a in enumerate(U['navigation']):add(f'ui.navigation.{i}',a['label'],'a',anchor(a['href']))
 if route=='/':
  add('page.h1',D['page']['h1'],'h1')
  for i,p in enumerate(copy['intro'].split('\n\n')):add(f'intro.{i}',p,'p')
  for i,a in enumerate(U['heroActions']):add(f'ui.heroActions.{i}',a['label'],'a',a['href'])
  for s in copy['sections']:
   add(f"section.{s['id']}.heading",s['heading'],'h2')
   if s['id']=='questions':
    for f in copy['faq']:add(f["id"]+'.question',f['question'],'h3');add(f['id']+'.answer',f['answer'],'p')
    continue
   for i,(tag,value) in enumerate(blocks(s['markdown'])):
    if tag=='p':add(f"section.{s['id']}.body.{i}",value,'p')
    else:
     for j,t in enumerate(value):add(f"section.{s['id']}.body.{i}.{j}",t,'li')
    if s['id']=='products-and-cost' and i==0:
     add('ui.productGroupHeading',U['productGroupHeading'],'p')
     for p in D['products']:
      for field,tag in [('heading','h3'),('priceLabel','p'),('shippingLabel','p'),('sumLabel','p'),('description','p'),('ctaLabel','a')]:add(f"product.{p['sku']}.{field}",p[field],tag,p['ctaHref'] if field=='ctaLabel' else None)
     for f in ['productNotice','amountNotice']:add('ui.'+f,U[f],'p')
  add('ui.closingAction',U['closingAction']['label'],'a',U['closingAction']['href']);add('sources.heading',D['sourceArea']['heading'],'h2');add('sources.checkedLabel',D['sourceArea']['checkedLabel'],'p')
  for i,s in enumerate(D['sourceArea']['items']):add(f'sources.{i}',s['label'],'a',s['href'])
 else:
  n=D['notFoundCopyPlan'];add('404.h1',n['h1'],'h1');add('404.body',n['body'],'p');add('404.ctaLabel',n['ctaLabel'],'a',n['ctaHref'])
 add('ui.footerBrand',U['footerBrand'],'strong');add('ui.phoneLinkLabel',U['phoneLinkLabel'],'a','tel:18440644')
 for i,a in enumerate(U['footerLinks']):add(f'ui.footerLinks.{i}',a['label'],'a',anchor(a['href']))
 add('ui.copyright',U['copyright'],'small')
 return out
