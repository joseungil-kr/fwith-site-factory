"""Unchanged HTML inspection primitives extracted from the pinned historical parser.
No regional release or approval modules are imported.
"""
from html.parser import HTMLParser
import re

VOID={'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}

def norm(value): return ' '.join(value.split())

def descendants(node):
 for child in node['children']:
  yield child
  yield from descendants(child)

def matches(node,tag=None,key=None,value=None):
 return (tag is None or node['tag']==tag) and (key is None or key in node['attrs'] and (value is None or node['attrs'][key]==value))

def within(node,tag=None,key=None,value=None): return [n for n in descendants(node) if matches(n,tag,key,value)]

def hidden(node):
 while node:
  a=node['attrs'];classes=a.get('class','').split()
  if node['tag'] in ('details','template','script','style') or 'hidden' in a or 'inert' in a or a.get('aria-hidden')=='true' or any(c in classes for c in ('hidden','sr-only','visually-hidden')) or re.search(r'(display\s*:\s*none|visibility\s*:\s*hidden|content-visibility\s*:\s*hidden)',a.get('style','')): return True
  node=node['parent']
 return False

class Surface(HTMLParser):
 def __init__(self,html):
  super().__init__(convert_charrefs=True);self.nodes=[];self.stack=[];self.text_events=[];self.feed(html)
 def handle_starttag(self,tag,attrs):
  assert len(attrs)==len(dict(attrs)),f'Duplicate HTML attribute: {tag}'
  node={'tag':tag,'attrs':dict(attrs),'text':'','children':[],'parent':self.stack[-1] if self.stack else None,'i':len(self.nodes)};self.nodes.append(node)
  if self.stack:self.stack[-1]['children'].append(node)
  if tag not in VOID:self.stack.append(node)
 def handle_startendtag(self,tag,attrs): self.handle_starttag(tag,attrs);self.handle_endtag(tag)
 def handle_endtag(self,tag):
  for i in range(len(self.stack)-1,-1,-1):
   if self.stack[i]['tag']==tag:del self.stack[i:];break
 def handle_data(self,text):
  for node in self.stack: node['text']+=text
  if self.stack and norm(text):self.text_events.append((self.stack[-1],norm(text)))
 def where(self,tag=None,key=None,value=None):return [n for n in self.nodes if matches(n,tag,key,value)]
 def cls(self,cls):return [n for n in self.nodes if cls in n['attrs'].get('class','').split()]
 def text(self,tag):return [norm(n['text']) for n in self.where(tag)]

def exactly(doc,tag,text,count=1):
 nodes=[n for n in doc.where(tag) if norm(n['text'])==norm(text)]
 assert len(nodes)==count,f'Exact {tag} missing/duplicated: {text[:90]}'
 assert not any(hidden(n) for n in nodes),f'Approved {tag} is hidden: {text[:90]}'
 return nodes

def link_exact(doc,label,href,count=None,scope=None):
 nodes=within(scope,'a') if scope else doc.where('a')
 found=[n for n in nodes if norm(n['text'])==norm(label) and n['attrs'].get('href')==href]
 assert len(found)==count if count is not None else bool(found),f'Approved CTA/source missing/duplicated: {label} -> {href}'
 assert not any(hidden(n) for n in found),f'Approved link hidden: {label}'
 return found

