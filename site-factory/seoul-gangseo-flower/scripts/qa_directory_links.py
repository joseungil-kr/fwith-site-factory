from pathlib import Path
from html.parser import HTMLParser
import json
class AdminLinks(HTMLParser):
 def __init__(self,html):
  super().__init__();self.current=None;self.links={};self.feed(html)
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag=='li' and a.get('data-administrative-unit'):
   self.current=a['data-administrative-unit'];self.links[self.current]=[]
  elif tag=='a' and self.current:self.links[self.current].append(a.get('href'))
 def handle_endtag(self,tag):
  if tag=='li':self.current=None
r=Path('.');c=json.loads((r/'src/data/region-coverage.json').read_text());p=json.loads((r/'src/data/pages.json').read_text());doc=AdminLinks((r/'dist/regions/index.html').read_text());count=0
for admin in c['administrativeCrosswalk']:
 expected=[]
 for relation in admin['relations']:
  expected.extend(page['url'] for page in p if relation['unitKey'] in page['regionUnitKeys'])
 assert doc.links[admin['aliasKey']]==expected, f'Incomplete or wrong administrative purchase links: {admin["aliasKey"]}'
 count+=len(expected)
print(f'DIRECTORY QA: {len(doc.links)} administrative entries; {count} exact purchase links; all same-dong intents retained')
