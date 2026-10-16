"""Verbatim existing strict one-beacon normalizer; no general rewriting."""
import hashlib
from html.parser import HTMLParser
import re
from urllib.parse import urlsplit

def strip_one_cf_beacon(body,expected_sha):
    # Latin-1 is lossless here: parser offsets remain exact byte offsets.
    text=body.decode('latin-1'); starts=[0]+[m.end() for m in re.finditer('\n',text)]
    class Beacon(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=False); self.pending=None; self.spans=[]; self.markers=0
        def source_offset(self):
            line,column=self.getpos(); return starts[line-1]+column
        def handle_starttag(self,tag,attrs):
            if tag!='script': return
            values=dict(attrs); src=values.get('src') or ''; u=urlsplit(src)
            marker='data-cf-beacon' in values or u.hostname=='static.cloudflareinsights.com'
            if not marker: return
            self.markers+=1
            assert self.markers==1 and self.pending is None, 'multiple_404_beacon_markers'
            assert len(values)==len(attrs), 'duplicate_404_beacon_attributes'
            assert set(values)<={'src','defer','async','integrity','crossorigin','data-cf-beacon','type'}, 'unexpected_404_beacon_attribute'
            assert values.get('type') in (None,'','module'), 'wrong_404_beacon_type'
            assert 'data-cf-beacon' in values and u.scheme=='https' and u.netloc=='static.cloudflareinsights.com', 'wrong_404_beacon_identity'
            assert re.fullmatch(r'/beacon[.]min[.]js(?:/[A-Za-z0-9]+)?',u.path) and not u.query and not u.fragment, 'wrong_404_beacon_path'
            start=self.source_offset(); self.pending=(start,start+len(self.get_starttag_text()))
        def handle_startendtag(self,tag,attrs):
            self.handle_starttag(tag,attrs)
            assert self.pending is None, 'self_closing_404_beacon'
        def handle_endtag(self,tag):
            if tag!='script' or self.pending is None: return
            start,content_start=self.pending; end_start=self.source_offset()
            closing=re.match(r'</script\s*>',text[end_start:],re.I)
            assert closing and not text[content_start:end_start].strip(), 'nonempty_or_malformed_404_beacon'
            self.spans.append((start,end_start+closing.end())); self.pending=None
    parser=Beacon(); parser.feed(text); parser.close()
    assert parser.markers==1 and len(parser.spans)==1 and parser.pending is None, 'unverified_404_beacon'
    start,end=parser.spans[0]
    candidate=body[:start]+body[end:]
    if hashlib.sha256(candidate).hexdigest()==expected_sha: return candidate
    if body[end:end+1]==b'\n': candidate=body[:start]+body[end+1:]
    assert hashlib.sha256(candidate).hexdigest()==expected_sha, 'wrong_404_body'
    return candidate
