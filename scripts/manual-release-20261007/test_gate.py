import copy,unittest
from gate import check
class GateTests(unittest.TestCase):
 def setUp(self):
  self.p={'enabled':True,'pixelReviewMode':'loopback','providerBaselineSha256':{'preview':'b'*64,'production':'b'*64},'assignedAuthorId':'author','assignedReviewerId':'reviewer','unresolvedBlockers':[],'siteKey':'s','branch':'site-prod','previewBranch':'manual-preview','root':'site/s','productionOrigin':'https://s.fwith.kr','worker':'s-existing','previewWorker':'s-existing-qa','previewOrigin':'https://s-existing-qa.joseungil.workers.dev'}
  keys=('sourceReview','immutableBaseline','nativeGates','routes','assets','cta','catalog','canonicalGraph','pixelQA','productionIndexableBuild','productionArtifactReview','unreleasedDeltaReconciled')
  proof={'pixelEvidenceMode':'loopback','status':'passed','reviewer':'reviewer','evidenceUrl':'https://github.com/joseungil-kr/fwith-site-factory/issues/1','artifactManifestSha256':'a'*64,'checks':dict.fromkeys(keys,True)}
  self.a={'providerBaselineSha256':{'preview':'b'*64,'production':'b'*64},'revision':'c'*40,'siteKey':'s','productionOrigin':self.p['productionOrigin'],'worker':self.p['worker'],'sourceFiles':{'site/s/a':'b'*64},'author':'author','preview':copy.deepcopy(proof),'production':copy.deepcopy(proof)}
 def run_gate(self,branch='site-prod',files=None):return check(self.p,self.a,'production','c'*40,branch,'site/s',files or self.a['sourceFiles'])
 def test_valid(self):self.run_gate()
 def test_wrong_branch(self):
  with self.assertRaisesRegex(ValueError,'Wrong branch'):self.run_gate('foreign')
 def test_wrong_host(self):
  self.a['productionOrigin']='https://evil.invalid'
  with self.assertRaisesRegex(ValueError,'hostname'):self.run_gate()
 def test_wrong_source(self):
  with self.assertRaisesRegex(ValueError,'bundle'):self.run_gate(files={'site/s/a':'changed'})
 def test_pending(self):
  self.a['production']['status']='pending'
  with self.assertRaisesRegex(ValueError,'Pending'):self.run_gate()
 def test_preview_proof_not_production(self):
  self.a['production']['checks']['productionIndexableBuild']=False
  with self.assertRaisesRegex(ValueError,'productionIndexableBuild'):self.run_gate()
 def test_wrong_revision(self):
  self.a['revision']='d'*40
  with self.assertRaisesRegex(ValueError,'revision'):self.run_gate()
 def test_self_review(self):
  self.a['production']['reviewer']='author'
  with self.assertRaisesRegex(ValueError,'Independent'):self.run_gate()
 def test_unassigned_reviewer(self):
  self.a['production']['reviewer']='unassigned'
  with self.assertRaisesRegex(ValueError,'Unassigned'):self.run_gate()
 def test_blank_author(self):
  self.a['author']='  '
  with self.assertRaisesRegex(ValueError,'Independent'):self.run_gate()
 def test_review_blocker(self):
  self.p['unresolvedBlockers']=['R4']
  with self.assertRaisesRegex(ValueError,'Unresolved'):self.run_gate()
 def test_inactive(self):
  self.p['enabled']=False
  with self.assertRaisesRegex(ValueError,'inactive'):self.run_gate()
 def test_no_preview_worker(self):
  self.p['previewWorker']=None
  with self.assertRaisesRegex(ValueError,'preview target'):check(self.p,self.a,'preview','c'*40,'manual-preview','site/s',self.a['sourceFiles'])
if __name__=='__main__':unittest.main()
