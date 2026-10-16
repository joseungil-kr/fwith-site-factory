"""Offline fixtures only; synthetic commits and approvals are not release evidence."""
import copy,json,tempfile,unittest,shutil,contextlib
from pathlib import Path
from unittest.mock import patch
import production_build as b
@contextlib.contextmanager
def temporary_control_directory():
 with tempfile.TemporaryDirectory() as temp:
  path=Path(temp)/'scripts/direct-damyang';path.mkdir(parents=True);yield path
class ProductionTests(unittest.TestCase):
 def fixture(self,d):
  assert d.name=='direct-damyang' and d.parent.name=='scripts', "Fixture control path must be rooted inside its temporary repository"
  c={**b.contract_template(),'sourceRevision':'a'*40,'sourceTree':'b'*40}
  v={**b.binding_template(c),'authorizationEvidence':'https://github.com/'+b.REPOSITORY+'/blob/'+('c'*40)+'/docs/direct-damyang/production-authorization-20261016.json'}
  original=Path(__file__).resolve().parent
  for name in ['bounded-contract.json','source-manifest.json','adapter-manifest.json','private-source-manifest.json','preview-equivalence.json']:
   (d/name).write_bytes((original/name).read_bytes())
  authpath=d.parents[1]/'docs/direct-damyang/production-authorization-20261016.json';authpath.parent.mkdir(parents=True,exist_ok=True)
  a={**b.authorization_template(c),'authorizationEvidence':[b.public_issue_approval_evidence()]}
  authpath.write_text(json.dumps(a));b.save(d/'authorization-binding.json',dict(schemaVersion=1,path='docs/direct-damyang/production-authorization-20261016.json',sha256=b.sha(authpath.read_bytes()),revision='c'*40,publicIssuesApproved=True))
  original=Path(__file__).resolve().parent
  (d/'content-review-binding.json').write_bytes((original/'content-review-binding.json').read_bytes())
  for row in json.loads((d/'content-review-binding.json').read_text())['files']:
   target=d.parents[1]/row['path'];target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(original.parents[1]/row['path'],target)
  def save():
   raw=json.dumps(c).encode();(d/'production-source-contract.json').write_bytes(raw);v['sourceContractSha256']=b.sha(raw);(d/'production-binding.json').write_text(json.dumps(v))
  save();return c,v,save
 def test_exact_pinned_contract(self):
  with temporary_control_directory() as d,patch.object(b,'DIRECTORY',Path(d)):
   self.fixture(Path(d));self.assertEqual(b.load()[1]['worker'],'damyang-flower-guide')
 def test_public_safe_authorization_evidence_exact_and_private_fields_rejected(self):
  with temporary_control_directory() as d,patch.object(b,'DIRECTORY',Path(d)):
   self.fixture(Path(d));path=d.parents[1]/'docs/direct-damyang/production-authorization-20261016.json';original=json.loads(path.read_text());descriptor=json.loads((d/'authorization-binding.json').read_text())
   accepted=b.public_issue_approval_evidence();mutations=[[],None,[accepted,accepted]]
   for key,value in [('approved',False),('approved',1),('approvedAtUTC','2026-10-15T18:24:16Z'),('scope','all-actions'),('publicData',['site-url','commit','qa-and-receipt-results','private-message']),('secretsExcluded',False),('messageId','PRIVATE_FIELD_FORBIDDEN'),('verbatimUserAnswer','PRIVATE_FIELD_FORBIDDEN')]:
    mutations.append([{**accepted,key:value}])
   for evidence in mutations:
    with self.subTest(evidence=evidence):
     changed={**original,'authorizationEvidence':evidence};b.save(path,changed);b.save(d/'authorization-binding.json',{**descriptor,'sha256':b.sha(path.read_bytes())})
     with self.assertRaisesRegex(ValueError,'exact_public_safe_approval_evidence_required'):b.load()
   b.save(path,original);b.save(d/'authorization-binding.json',{**descriptor,'sha256':b.sha(path.read_bytes())});self.assertEqual(b.load()[1]['worker'],'damyang-flower-guide')
 def test_binding_mutations(self):
  with temporary_control_directory() as d,patch.object(b,'DIRECTORY',Path(d)):
   c,v,save=self.fixture(Path(d))
   for k,val in [('worker','seoul-gangdong-flower-guide'),('origin','https://wrong.invalid'),('schemaVersion',True),('htmlFiles',5),('sitemapRoutes',['/','/regions/']),('notFoundRobots','index,follow'),('coreHubLaunchStatus','PASS'),('fullLaunchStatus','PASS'),('publicHttpVerified',True),('approvals',dict(publication=True,hostBinding=True,indexNowProof=False)),('authorizationEvidence','unverified'),('extra',True)]:
    with self.subTest(key=k):
     old=copy.deepcopy(v);v[k]=val;save()
     with self.assertRaises(ValueError):b.load()
     v.clear();v.update(old);save()
 def test_contract_mutations(self):
  with temporary_control_directory() as d,patch.object(b,'DIRECTORY',Path(d)):
   c,v,save=self.fixture(Path(d))
   for k,val in [('sourceRevision',None),('sourceTree',None),('sourceBranch','source/wrong'),('sourceFiles',1),('sourceRoot','wrong'),('privateFiles',55),('frozenAdapterTreeSha256','a'*64),('schemaVersion',True)]:
    with self.subTest(key=k):
     old=copy.deepcopy(c);c[k]=val;save()
     with self.assertRaises(ValueError):b.load()
     c.clear();c.update(old);save()
 def request(self):
  c={'sourceRevision':'a'*40};digest='b'*64;env=dict(GITHUB_REPOSITORY=b.REPOSITORY,GITHUB_REF='refs/heads/main',GITHUB_ACTOR=b.OWNER,GITHUB_TRIGGERING_ACTOR=b.OWNER,GITHUB_RUN_ATTEMPT='1',GITHUB_EVENT_NAME='issues',GITHUB_SHA='c'*40)
  body=dict(schemaVersion=1,mode='production-build-only',source_branch=b.BRANCH,source_revision=c['sourceRevision'],expected_control_revision=env['GITHUB_SHA'],binding_sha256=digest)
  event=dict(action='opened',repository=dict(full_name=b.REPOSITORY,owner=dict(login=b.OWNER,type='User')),issue=dict(title=b.TITLE,user=dict(login=b.OWNER),body=json.dumps(body)));return c,digest,env,event
 def test_exact_request(self):self.assertFalse(b.select(*self.request())['publicationExecuted'])
 def test_request_environment_mutations(self):
  for k,val in [('GITHUB_ACTOR','other'),('GITHUB_TRIGGERING_ACTOR','other'),('GITHUB_RUN_ATTEMPT','2'),('GITHUB_EVENT_NAME','push'),('GITHUB_REF','refs/heads/source'),('GITHUB_SHA','short')]:
   c,d,e,v=self.request();e[k]=val
   with self.subTest(key=k),self.assertRaises(ValueError):b.select(c,d,e,v)
 def test_body_mutations(self):
  for k,val in [('schemaVersion',True),('mode','publish'),('source_revision','d'*40),('expected_control_revision','d'*40),('binding_sha256','d'*64),('extra',True)]:
   c,d,e,v=self.request();body=json.loads(v['issue']['body']);body[k]=val;v['issue']['body']=json.dumps(body)
   with self.subTest(key=k),self.assertRaises(ValueError):b.select(c,d,e,v)
 def test_provider_credentials_forbidden(self):
  env=dict(SITE_RELEASE_MODE='production',SITE_INDEXABLE='true',SITE_URL=b.ORIGIN,SITE_FACTORY_REVISION='a'*40,SITE_RELEASE_BINDING_PATH=str(b.DIRECTORY/'production-binding.json'),SITE_RELEASE_BINDING_SHA256='b'*64)
  b.environment({'sourceRevision':'a'*40},'b'*64,env)
  for k,val in [('CLOUDFLARE_API_TOKEN','TEST_ONLY'),('CLOUDFLARE_ACCOUNT_ID','TEST_ONLY'),('SITE_URL','https://wrong.invalid')]:
   with self.subTest(key=k),self.assertRaises(ValueError):b.environment({'sourceRevision':'a'*40},'b'*64,{**env,k:val})
 def test_exact_existing_body_requires_focus_without_normalization(self):
  body=b'<body><main id="main-content" tabindex="-1"><p>Text &amp; one</p></main></body>'
  self.assertEqual(b.exact_body(body),body)
  for bad in [body.replace(b' tabindex="-1"',b''),body.replace(b'tabindex="-1"',b'tabindex="0"'),body+body]:
   with self.assertRaises(ValueError):b.exact_body(bad)
  self.assertNotEqual(b.sha(b.exact_body(body.replace(b'Text',b'Changed'))),b.sha(body))
 def test_frozen_manifest_digest(self):self.assertEqual(b.sha(b.read(b.DIRECTORY/'private-source-manifest.json')),b.PRIVATE_MANIFEST_SHA)
 def test_equivalence_digest(self):self.assertEqual(b.sha(b.read(b.DIRECTORY/'preview-equivalence.json')),b.PREVIEW_EQUIVALENCE_SHA)
 def test_bounded_contract_digest(self):self.assertEqual(b.sha(b.read(b.DIRECTORY/'bounded-contract.json')),b.BOUNDED_CONTRACT_SHA)
 def test_build_workflow_has_no_provider_or_publish(self):
  text=(Path(__file__).resolve().parents[2]/'.github/workflows/damyang-production-build-only.yml').read_text()
  for word in ['secrets.','issues: write','publish.py','wrangler','--no-sandbox']:self.assertNotIn(word,text)
  for word in ['node-version: 24','fetch-depth: 0','npm ci','npm test','test_damyang_runner_output.py','production_capture.py']:self.assertIn(word,text)
if __name__=='__main__':unittest.main()
