from PIL import Image,ImageDraw
from pathlib import Path
import hashlib,json
R=Path('/workspace/scratch/e695498f2eb8/gwanak-qa-run-38400663920');O=Path('/workspace/scratch/e695498f2eb8/gwanak-pixel-independent-38400663920');out=[]
for w in [320,390]:
 for p in sorted((R/'fullpages'/str(w)).glob('*.jpg')):
  img=Image.open(p);pieces=[]
  for y in range(0,img.height,1500):pieces.append((y,min(y+1540,img.height)))
  for group in range(0,len(pieces),4):
   part=pieces[group:group+4];sheet=Image.new('RGB',(w*len(part),1580),'#ddd');draw=ImageDraw.Draw(sheet)
   for i,(y,z)in enumerate(part):
    sheet.paste(img.crop((0,y,w,z)),(w*i,40));draw.text((w*i+5,4),f'{w}/{p.stem}\ny={y}..{z}',fill='#000')
   name=f'full-{w}-{p.stem}-{group//4}.png';sheet.save(O/name)
   out.append({'sheet':name,'kind':'fullpage-lossless-tiles','originals':[{'path':str(p.relative_to(R)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'ranges':part}],'opened':False})
 for start in range(0,len(files:=sorted((R/'supplemental'/str(w)).rglob('*.jpg'))),3):
  ps=files[start:start+3];h=Image.open(ps[0]).height;sheet=Image.new('RGB',(w*len(ps),h+65),'#ddd');draw=ImageDraw.Draw(sheet)
  for i,p in enumerate(ps):
   im=Image.open(p);sheet.paste(im,(w*i,65));label=str(p.relative_to(R/'supplemental'/str(w)));draw.text((w*i+5,4),label.replace('/','\n'),fill='#000')
  name=f'supp-{w}-{start//3:02d}.png';sheet.save(O/name)
  out.append({'sheet':name,'kind':'supplemental-lossless-contact-sheet','originals':[{'path':str(p.relative_to(R)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'ranges':[[0,h]]}for p in ps],'opened':False})
(O/'inspection-sheets.json').write_text(json.dumps(out,indent=2)+'\n')
for x in out:print(x['sheet'])
