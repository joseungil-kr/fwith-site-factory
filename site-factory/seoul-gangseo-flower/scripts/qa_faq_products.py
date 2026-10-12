#!/usr/bin/env python3
"""Verify visible rendered FAQ answers and exact per-product order destinations."""
from html.parser import HTMLParser
from pathlib import Path
import json,re

VOID={'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}
def text_content(value):
    return ' '.join(re.sub(r'\*\*([^*]+)\*\*', r'\1', re.sub(r'\[([^\]]+)\]\([^)]+\)',r'\1',value)).split())
def normalize_faq(items):
    result=[]
    for item in items or []:
        q,a=(item[0],item[1]) if isinstance(item,list) else (item['question'],item['answer'])
        assert isinstance(q,str) and q.strip() and isinstance(a,str) and a.strip(),'Invalid FAQ record'
        result.append({'question':text_content(q),'answer':text_content(a)})
    return result
class Output(HTMLParser):
    def __init__(self,html):
        super().__init__(convert_charrefs=True);self.stack=[];self.faq=[];self.products=[];self.order_ctas=[];self.hidden_faq=[];self.feed(html)
    def handle_starttag(self,tag,attrs):
        a=dict(attrs);classes=a.get('class','').split()
        hidden=('hidden' in a or 'inert' in a or a.get('aria-hidden')=='true' or
                re.search(r'(?:display\s*:\s*none|visibility\s*:\s*hidden|content-visibility\s*:\s*hidden)',a.get('style','')) or
                any(c in classes for c in ['hidden','sr-only','visually-hidden']) or tag=='details')
        faq={'question':[],'answer':[]} if 'data-faq-entry' in a else None
        if faq is not None:self.faq.append(faq)
        product={'key':a['data-product-key'],'links':[],'classes':classes} if a.get('data-product-key') else None
        if product is not None:self.products.append(product)
        entry={'tag':tag,'hidden':hidden,'faq':faq,'product':product,'question':'data-faq-question' in a,'answer':'data-faq-answer' in a}
        if tag not in VOID:self.stack.append(entry)
        if 'data-visible-faq' in a or 'data-faq-entry' in a or 'data-faq-question' in a or 'data-faq-answer' in a:
            if any(e['hidden'] for e in self.stack):self.hidden_faq.append(a)
        if tag=='a':
            for e in self.stack:
                if e['product'] is not None:e['product']['links'].append(a.get('href'))
            if a.get('data-order-product-key'):self.order_ctas.append((a['data-order-product-key'],a.get('href')))
    def handle_endtag(self,tag):
        for i in range(len(self.stack)-1,-1,-1):
            if self.stack[i]['tag']==tag:del self.stack[i:];break
    def handle_data(self,value):
        if any(e['hidden'] or e['tag'] in ['script','style'] for e in self.stack):return
        record=next((e['faq'] for e in reversed(self.stack) if e['faq'] is not None),None)
        if record is not None:
            for key in ['question','answer']:
                if any(e[key] for e in self.stack):record[key].append(value)
    def visible_faq(self):
        return [{key:' '.join(''.join(value).split()) for key,value in entry.items()} for entry in self.faq]
def inspect(root=Path('.'),write_report=True):
    data=root/'src/data';dist=root/'dist'
    pages=json.loads((data/'pages.json').read_text());products=json.loads((data/'products.json').read_text());catalog={p['key']:p for p in products}
    for p in products:
        assert p['orderUrl']==p['sourceUrl'],f'Product order URL must equal verified detail source: {p["key"]}'
        assert '/shop/item.php?' in p['sourceUrl'],f'Product URL is not an individual detail page: {p["key"]}'
    rows=[];total_links=0
    for path in sorted(dist.rglob('*.html')):
        doc=Output(path.read_text());rel=path.relative_to(dist).as_posix();url='/' if rel=='index.html' else '/'+rel.removesuffix('index.html')
        for product in doc.products:
            target=catalog[product['key']]['sourceUrl']
            if 'product-card' in product['classes'] or product['links']:
                assert product['links']==[target],f'Wrong rendered product CTA: {url} {product["key"]} {product["links"]}'
                total_links+=1
        for key,href in doc.order_ctas:
            assert href==catalog[key]['sourceUrl'],f'Wrong product-specific order CTA: {url} {key}'
        page=next((p for p in pages if p['url']==url),None)
        if page is not None:
            expected=normalize_faq(page.get('faq'))
            assert not doc.hidden_faq,f'FAQ is hidden/collapsed: {url}'
            assert doc.visible_faq()==expected,f'FAQ output differs from reviewed questions/answers: {url}'
            assert len(doc.faq)==len(expected),f'FAQ count mismatch: {url}'
            rows.append({'path':url,'contentMarkdown':bool(page.get('contentMarkdown')),'visibleFaq':len(expected),'productCards':sum('product-card' in p['classes'] for p in doc.products),'productOrderCtas':len(doc.order_ctas)})
    assert len(rows)==len(pages),'Not all detail pages were inspected'
    report={'details':rows,'visibleFaq':sum(r['visibleFaq'] for r in rows),'verifiedProductLinks':total_links,'checks':['FAQ content exact match','FAQ outside details/hidden markup','SKU links equal sourceUrl','orderUrl equals sourceUrl']}
    if write_report:(root/'faq-product-qa.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(f'FAQ / PRODUCT QA: {len(rows)} details, {report["visibleFaq"]} visible FAQs, {total_links} exact product links')
    return report
if __name__=='__main__':inspect()
