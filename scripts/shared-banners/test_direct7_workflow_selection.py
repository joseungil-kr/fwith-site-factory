#!/usr/bin/env python3
"""Exercise the fixed expressions against owner, scope and exact-revision cases."""
from pathlib import Path
import json,re,subprocess,unittest
ROOT=Path(__file__).resolve().parents[2]
REGIONS=('anyang','gwangmyeong','pyeongtaek','yeoju','seoul-eunpyeong','seoul-seodaemun','seoul-mapo')
SHA='a'*40
class Selection(unittest.TestCase):
 def expressions(self,region):
  t=(ROOT/f'.github/workflows/{region}-direct-publish.yml').read_text()
  build=t.split('  build:\n',1)[1].split('  publish:',1)[0]
  gate=next(x.strip()[4:] for x in build.splitlines() if x.startswith('    if: '))
  rev=re.search(r'REVISION: \$\{\{ (.*?) \}\}',build).group(1)
  return gate,rev
 def evaluate(self,region,github,inputs):
  gate,rev=self.expressions(region)
  js="""const x=JSON.parse(process.argv[1]);const contains=(a,b)=>String(a).includes(b);const fromJSON=JSON.parse;let result;try{const choose=new Function('github','inputs','contains','fromJSON','return ('+x.gate+')');const select=new Function('github','inputs','contains','fromJSON','return ('+x.revision+')');const allowed=choose(x.github,x.inputs,contains,fromJSON);const revision=allowed?select(x.github,x.inputs,contains,fromJSON):null;result={allowed,revision:revision??null,validRevision:/^[a-f0-9]{40}$/.test(revision??'')};}catch(e){result={allowed:false,revision:null,validRevision:false}};process.stdout.write(JSON.stringify(result))"""
  p=subprocess.run(['node','-e',js,json.dumps({'gate':gate,'revision':rev,'github':github,'inputs':inputs})],check=True,capture_output=True,text=True);return json.loads(p.stdout)
 def ctx(self,r,**kw):
  g={'repository':'joseungil-kr/fwith-site-factory','ref':'refs/heads/main','event_name':'issues','actor':'joseungil-kr','event':{'issue':{'title':'[REGIONAL-COPY-DEPLOY] batch','user':{'login':'joseungil-kr'},'body':json.dumps({'revisions':{r:SHA},'existing_update':True})}}};g.update(kw);return g
 def test_selected_owner_batch_exact_revision(self):
  for r in REGIONS:self.assertEqual(self.evaluate(r,self.ctx(r),{}),{'allowed':True,'revision':SHA,'validRevision':True})
 def test_foreign_actor_author_repo_branch_title_rejected(self):
  for r in REGIONS:
   for key,value in [('actor','other-user'),('repository','other/repository'),('ref','refs/heads/other')]:self.assertFalse(self.evaluate(r,self.ctx(r,**{key:value}),{})['allowed'])
   for slot,value in [('title','unrelated'),('user',{'login':'other-user'})]:
    g=self.ctx(r);g['event']['issue'][slot]=value;self.assertFalse(self.evaluate(r,g,{})['allowed'])
 def test_missing_map_cannot_fall_back_to_single_site_payload(self):
  for r in REGIONS:
   g=self.ctx(r);g['event']['issue']['body']=json.dumps({'revisions':{},'purpose':r,'expected_revision':SHA});self.assertFalse(self.evaluate(r,g,{})['validRevision'])
 def test_existing_dispatch_is_preserved(self):
  for r in REGIONS:self.assertEqual(self.evaluate(r,self.ctx(r,event_name='workflow_dispatch'),{'expected_revision':SHA})['revision'],SHA)
 def test_existing_gwangmyeong_single_issue_is_preserved(self):
  g=self.ctx('gwangmyeong');g['event']['issue'].update(title='[REGIONAL-COPY-DEPLOY] gwangmyeong',body=json.dumps({'expected_revision':SHA}));self.assertEqual(self.evaluate('gwangmyeong',g,{})['revision'],SHA)
if __name__=='__main__':unittest.main()
