import json,subprocess,tempfile,unittest
from pathlib import Path
from gate import tracked_files,worktree,digest,evidence,compact
class RevisionFlow(unittest.TestCase):
 def test_immutable_blobs_and_generated_revision(self):
  with tempfile.TemporaryDirectory() as tmp:
   r=Path(tmp);p=r/'site/s/src/data/build-revision.json';p.parent.mkdir(parents=True);p.write_text('{"revision":"old"}')
   def run(*args):return subprocess.check_output(['git','-C',tmp,*args])
   run('init','-q');run('config','user.email','test@example.invalid');run('config','user.name','Fixture');run('add','.');run('commit','-qm','fixture')
   rev=run('rev-parse','HEAD').decode().strip();files=tracked_files(r,'site/s',rev)
   worktree(r,files,'site/s',rev,False);p.write_text(json.dumps({'revision':rev}))
   self.assertEqual(files,tracked_files(r,'site/s',rev));worktree(r,files,'site/s',rev,True)
   p.write_text(json.dumps({'revision':'wrong'}))
   with self.assertRaisesRegex(ValueError,'generated'):worktree(r,files,'site/s',rev,True)
 def test_sha_schema(self):
  with tempfile.TemporaryDirectory() as tmp:
   r=Path(tmp);p=r/'site/s/src/data/build-revision.json';p.parent.mkdir(parents=True);p.write_text(json.dumps({'sha':'c'*40}))
   worktree(r,{},'site/s','c'*40,True,'sha')
   with self.assertRaisesRegex(ValueError,'generated'):worktree(r,{},'site/s','c'*40,True,'revision')
 def test_missing_or_wrong_evidence_fails(self):
  with tempfile.TemporaryDirectory() as tmp:
   r=Path(tmp);path=r/'.github/manual-release-20261007/evidence/test.json';path.parent.mkdir(parents=True)
   proof={'evidenceFile':str(path.relative_to(r)),'evidenceSha256':'a'*64}
   with self.assertRaises(FileNotFoundError):evidence(r,{}, {},'production',proof)
   path.write_text('{}')
   with self.assertRaisesRegex(ValueError,'bytes mismatch'):evidence(r,{}, {},'production',proof)
if __name__=='__main__':unittest.main()
