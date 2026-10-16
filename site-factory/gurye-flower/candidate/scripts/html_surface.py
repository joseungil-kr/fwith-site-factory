"""Dependency-free HTML tree inspection adapted from Gwanak qa_gwanak.Surface.
Supports only the small selector subset used by the local QA, not a browser DOM.
"""
from html.parser import HTMLParser
import re
VOID={'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}
class Node:
 def __init__(self,name='document',attrs=None,parent=None):self.name=name;self.attrs=attrs or {};self.parent=parent;self.children=[]
 def __getitem__(self,key):return self.attrs[key]
 def get(self,key,default=None):return self.attrs.get(key,default)
 def has_attr(self,key):return key in self.attrs
 @property
 def parents(self):
  p=self.parent
  while p:yield p;p=p.parent
 @property
 def title(self):return self.find('title')
 def get_text(self,separator='',strip=False):
  def segments(n):
   for c in n.children:
    if isinstance(c,str):yield c
    else:yield from segments(c)
  values=list(segments(self));return separator.join(x.strip() if strip else x for x in values if not strip or x.strip())
 def descendants(self):
  for child in self.children:
   if isinstance(child,Node):yield child;yield from child.descendants()
 def find_all(self,name=None,recursive=True,**attrs):
  pool=self.descendants() if recursive else (c for c in self.children if isinstance(c,Node))
  return [n for n in pool if (name is None or (n.name in name if isinstance(name,list) else n.name==name)) and all(n.get(k)==v for k,v in attrs.items())]
 def find(self,name=None,recursive=True,**attrs):return next(iter(self.find_all(name,recursive,**attrs)),None)
 def find_next_sibling(self):
  siblings=[c for c in self.parent.children if isinstance(c,Node)] if self.parent else [];i=siblings.index(self);return siblings[i+1] if i+1<len(siblings) else None
 def find_previous_sibling(self):
  siblings=[c for c in self.parent.children if isinstance(c,Node)] if self.parent else [];i=siblings.index(self);return siblings[i-1] if i else None
 def matches(self,part):
  # Exact r2 positions; reject unsupported pseudos rather than silently broaden matching.
  for kind,number in re.findall(r':(nth-child|nth-of-type)\((\d+)\)',part):
   siblings=[n for n in self.parent.children if isinstance(n,Node) and (kind=='nth-child' or n.name==self.name)] if self.parent else []
   if self not in siblings or siblings.index(self)+1!=int(number):return False
  part=re.sub(r':(?:nth-child|nth-of-type)\(\d+\)','',part)
  if ':' in re.sub(r'\[[^\]]*\]','',part):raise ValueError('Unsupported selector pseudo: '+part)
  attrs=re.findall(r'\[([^\]=]+)(?:=["\']?([^\]"\']*)["\']?)?\]',part)
  simple=re.sub(r'\[[^\]]*\]','',part)
  tag=re.match(r'^[a-zA-Z][\w-]*',simple)
  if tag and self.name!=tag.group():return False
  for cls in re.findall(r'\.([\w-]+)',simple):
   if cls not in self.get('class','').split():return False
  for id in re.findall(r'#([\w-]+)',simple):
   if self.get('id')!=id:return False
  for k,v in attrs:
   if k not in self.attrs or (v and self.attrs[k]!=v):return False
  return True
 def select(self,selector):
  result=[]
  for branch in selector.split(','):
   terms=branch.strip().replace('>',' > ').split();current=[self];child=False
   if terms and terms[0]==':scope':terms=terms[1:]
   for term in terms:
    if term=='>':child=True;continue
    candidates=[]
    for n in current:
     pool=(c for c in n.children if isinstance(c,Node)) if child else n.descendants()
     for c in pool:
      if c.matches(term) and c not in candidates:candidates.append(c)
    current=candidates;child=False
   result.extend(c for c in current if c not in result)
  order={id(n):i for i,n in enumerate(self.descendants())};return sorted(result,key=lambda n:order.get(id(n),-1))
 def select_one(self,selector):return next(iter(self.select(selector)),None)
class Surface(HTMLParser):
 def __init__(self,html):super().__init__(convert_charrefs=True);self.root=Node();self.stack=[self.root];self.feed(html)
 def handle_starttag(self,tag,attrs):
  if len(attrs)!=len(dict(attrs)):raise ValueError('Duplicate HTML attribute')
  n=Node(tag,dict(attrs),self.stack[-1]);self.stack[-1].children.append(n)
  if tag not in VOID:self.stack.append(n)
 def handle_startendtag(self,tag,attrs):self.handle_starttag(tag,attrs);self.handle_endtag(tag)
 def handle_endtag(self,tag):
  for i in range(len(self.stack)-1,0,-1):
   if self.stack[i].name==tag:del self.stack[i:];break
 def handle_data(self,text):self.stack[-1].children.append(text)
def BeautifulSoup(text,parser=None):return Surface(text).root
