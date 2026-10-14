from pathlib import Path
import tempfile,shutil,json,re,subprocess
from qa_songpa import inspect,ROOT
mode=json.loads(subprocess.check_output(["node",str(ROOT/"scripts/songpa_release.mjs"),"--json"],text=True));production=mode["mode"]=="production"
cases=[]
def mutate(name,path,old,new):cases.append((name,path,old,new))
r=json.loads((ROOT/'src/data/songpa-runtime.json').read_text());home='index.html';detail='regions/songpa-condolence-wreath/index.html'
mutate('wrong canonical',home,mode['origin']+'/','https://example.com/')
mutate('wrong indexing metadata',home,'index,follow' if production else 'noindex,nofollow,noarchive','noindex,nofollow,noarchive' if production else 'index,follow')
mutate('first answer replaced',home,r['pages'][0]['firstAnswer'],'내용 변경')
mutate('first answer hidden',home,'data-first-answer','hidden data-first-answer')
mutate('missing FAQ answer',detail,r['pages'][1]['faqs'][0]['answer'],'')
mutate('FAQ collapsed',detail,'<p data-faq-answer','<p hidden data-faq-answer')
mutate('FAQ hidden class',detail,'<p data-faq-answer','<p class="hidden" data-faq-answer')
mutate('FAQ inline hidden',detail,'<p data-faq-answer','<p style="display:none" data-faq-answer')
mutate('wrong product CTA',detail,'https://fwith.co.kr/shop/item.php?it_id=B201','https://fwith.co.kr/shop/item.php?it_id=C200')
mutate('wrong product price',detail,'기본가격 59,000원','기본가격 49,000원')
mutate('wrong product photo',detail,'/images/products/B201.jpg','/images/products/C200.jpg')
mutate('wrong product alt',detail,r['products'][0]['alt'],'상품')
mutate('source replaced',detail,'https://funeral.amc.seoul.kr/asan/depts/funeral/K/bbsDetail.do?contentId=247950&amp;menuId=3878','https://example.com/')
mutate('missing source heading',detail,'출처 및 확인 정보','확인 정보')
mutate('missing order alias',detail,'id="order"','id="order-gone"')
mutate('wrong region prose',detail,'서울아산병원','관악구 병원')
mutate('wrong banner asset',home,'/images/shared-banners/flower-message.webp','/images/shared-banners/flower-budget.webp')
mutate('noindex directory padded banner','regions/index.html','</article>','<figure data-shared-flower-banner="message"></figure></article>')
mutate('broken local navigation',home,'href="/#catalog"','href="/missing/"')
mutate('heading level skipped',detail,'<h2>59,000원','<h4>59,000원')
mutate('unapproved prose added',home,'</article>','<p>검증하지 않은 추가 문구입니다.</p></article>')
mutate('script added',home,'</body>','<script>alert(1)</script></body>')
mutate('wrong robots','robots.txt','Allow: /' if production else 'Disallow: /','Disallow: /' if production else 'Allow: /')
mutate('sitemap public URL','sitemap-0.xml' if production else 'sitemap.xml','</urlset>','<url><loc>https://example.com/</loc></url></urlset>')
rows=[]
for name,path,old,new in cases:
 with tempfile.TemporaryDirectory(prefix='songpa-html-') as temp:
  d=Path(temp)/'dist';shutil.copytree(ROOT/'dist',d);p=d/path;s=p.read_text();assert old in s,(name,old);p.write_text(s.replace(old,new,1))
  try:result=inspect(d);rejected=bool(result['failures']);reason=result['failures'][:3]
  except Exception as e:rejected=True;reason=[type(e).__name__+': '+str(e)]
  assert rejected,'Mutation was not rejected: '+name
  rows.append({'mutation':name,'rejected':True,'reason':reason})
for name,action in [
 ('extra geographic route',lambda d: (d/'regions/extra').mkdir(parents=True)),
 ('banner byte tamper',lambda d:(d/'images/shared-banners/flower-message.webp').write_bytes(b'bad')),
 ('ownership file added',lambda d:(d/'google-verification.html.txt').write_text('ownership')),
 ('CSS hides FAQ',lambda d:next((d/'_astro').glob('*.css')).write_text(next((d/'_astro').glob('*.css')).read_text()+'.faq{display:none}'))]:
 with tempfile.TemporaryDirectory(prefix='songpa-html-') as temp:
  d=Path(temp)/'dist';shutil.copytree(ROOT/'dist',d);action(d)
  if name=='extra geographic route':(d/'regions/extra/index.html').write_text('<h1>Extra</h1>')
  try:
   result=inspect(d);rejected=bool(result['failures']);reason=result['failures'][:3]
  except Exception as e:rejected=True;reason=[type(e).__name__+': '+str(e)]
  assert rejected,name;rows.append({'mutation':name,'rejected':True,'reason':reason})
(ROOT/'songpa-negative-fixtures.json').write_text(json.dumps({'count':len(rows),'allRejected':True,'fixtures':rows},ensure_ascii=False,indent=2)+'\n')
print(f'{len(rows)} compiled HTML/asset negative fixtures rejected')
