from pathlib import Path
from html.parser import HTMLParser
import json
class Links(HTMLParser):
 def __init__(self,html):
  super().__init__();self.current=None;self.kind=None;self.admin={};self.legal={};self.anchors={};self.heading=None;self.feed(html)
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag=='li' and (a.get('data-administrative-unit') or a.get('data-legal-unit')):
   self.kind='admin' if a.get('data-administrative-unit') else 'legal';self.current=a.get('data-administrative-unit') or a['data-legal-unit'];getattr(self,self.kind)[self.current]=[]
  elif tag=='a' and self.current:getattr(self,self.kind)[self.current].append(a.get('href'))
  if tag in ['h2','h3'] and a.get('id'):self.heading=a['id'];self.anchors.setdefault(self.heading,[]).append('')
 def handle_data(self,data):
  if self.heading:self.anchors[self.heading][-1]+=data
 def handle_endtag(self,tag):
  if tag=='li':self.current=None
  if tag in ['h2','h3']:self.heading=None
r=Path('.');c=json.loads((r/'src/data/region-coverage.json').read_text());pages=json.loads((r/'src/data/pages.json').read_text());doc=Links((r/'dist/regions/index.html').read_text());assignment=c.get('representativeAssignment');grouped=assignment in ['guro-grouped-purchase-context-v1','geumcheon-grouped-funeral-context-v1','yeongdeungpo-grouped-occasion-context-v1']
def expected(unit):
 if grouped:return [a['href'] for p in pages for a in p['facilityAnchors'] if a['unitKey']==unit]
 return [p['url'] for p in pages if unit in p['regionUnitKeys']]
count=0
for admin in c['administrativeCrosswalk']:
 # N2 administrative rows are geography only: never imply a facility's precise administrative assignment.
 links=[] if assignment=='yeongdeungpo-grouped-occasion-context-v1' else [link for relation in admin['relations'] for link in expected(relation['unitKey'])]
 assert doc.admin[admin['aliasKey']]==links,f'Incomplete/wrong administrative links: {admin["aliasKey"]}'
 count+=len(links)
if grouped:
 assert set(doc.legal)=={u['unitKey'] for u in c['units']}
 for u in c['units']:assert doc.legal[u['unitKey']]==expected(u['unitKey']),f'Wrong legal links: {u["unitKey"]}'
 for p in pages:
  actual=Links((r/'dist'/p['url'].strip('/')/'index.html').read_text())
  for a in p['facilityAnchors']:assert actual.anchors.get(a['anchor'])==[a['heading']],f'Anchor missing/duplicated/wrong heading: {a["href"]}'
 expected_count={'geumcheon-grouped-funeral-context-v1':2,'guro-grouped-purchase-context-v1':7,'yeongdeungpo-grouped-occasion-context-v1':8}[assignment]
 assert sum(len(p['facilityAnchors']) for p in pages)==expected_count
print(f'DIRECTORY QA: {len(doc.admin)} administrative entries; {count} exact destination links; grouped={grouped}; all named destination anchors checked')
