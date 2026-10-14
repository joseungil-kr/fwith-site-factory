"""Offline regression coverage for the existing publication workflow extension."""
import json
from pathlib import Path
import re
import subprocess
import unittest

ROOT=Path(__file__).resolve().parents[2]
WORKFLOW=ROOT/'.github/workflows/seoul-seocho-production-publish.yml'


class WorkflowTests(unittest.TestCase):
    def setUp(self):self.text=WORKFLOW.read_text()

    def test_existing_permissions_and_secret_names_only(self):
        blocks=re.findall(r'^([ ]*)permissions:\n((?:\1  [a-z-]+: [a-z]+\n)+)',self.text,re.M)
        self.assertEqual(blocks,[('', '  contents: read\n'),('    ', '      contents: read\n      actions: read\n      issues: write\n')])
        self.assertEqual(set(re.findall(r'secrets\.([A-Z_]+)',self.text)),{'CLOUDFLARE_API_TOKEN','CLOUDFLARE_ACCOUNT_ID'})
        self.assertNotIn('id-token:',self.text);self.assertNotIn('write-all',self.text)
        self.assertIn('wrangler@4.148.0',self.text)
        self.assertEqual(len(re.findall(r'GH_TOKEN:',self.text)),1)

    def test_only_two_explicit_region_selectors(self):
        for field in ['REGION','CONTROL_DIR']:
            self.assertRegex(self.text,rf"{field}: \$\{{\{{ github.event.issue.title == '\[GANGNAM-PRODUCTION-PUBLISH\] 20261014' && '[^']+' \|\| '[^']+' \}}\}}")
        self.assertIn("github.event.issue.title == '[SEOCHO-PRODUCTION-PUBLISH] 20261014' || github.event.issue.title == '[GANGNAM-PRODUCTION-PUBLISH] 20261014'",self.text)
        self.assertIn("github.actor == 'joseungil-kr'",self.text)
        self.assertIn("github.event.issue.user.login == 'joseungil-kr'",self.text)

    def test_deploy_still_single_shot_and_receipt_is_gated(self):
        self.assertEqual(self.text.count('wrangler@4.148.0 deploy'),1)
        self.assertIn("if: steps.deploy.outcome == 'success'",self.text)
        self.assertIn("steps.deploy.outcome == 'success' && steps.attach.outcome == 'success' && steps.binding.outcome == 'success' && steps.http.outcome == 'success'",self.text)
        self.assertIn("if (process.env.GITHUB_RUN_ATTEMPT !== '1')",self.text)
        self.assertIn('Source branch moved',self.text)

    def test_artifact_staging_preserves_seocho_and_isolates_gangnam(self):
        self.assertIn("path: ${{ env.REGION == 'seoul-gangnam' && 'gangnam-retained' || 'release' }}",self.text)
        self.assertIn("root = Path('gangnam-retained/release')",self.text)
        self.assertIn("assert not any(p.is_symlink() for p in root.rglob('*'))",self.text)
        self.assertIn("shutil.copytree(root, 'release', symlinks=True)",self.text)

    def metadata_script(self):
        blocks=re.findall(r'^          script: \|\n((?:            .*\n|\n)+)',self.text,re.M)
        self.assertEqual(len(blocks),2)
        return ''.join(line[12:] if line.startswith('            ') else line for line in blocks[0].splitlines(keepends=True))

    def run_metadata(self,region,mutation=None):
        script=self.metadata_script()
        review=dict(buildRunId='100',artifactId='200',buildControlSha='a'*40,qaRunId='100',artifactDigest='sha256:'+'b'*64)
        run=dict(id=100,run_attempt=1,status='completed',conclusion='success',event='issues',head_branch='main',head_sha='a'*40,
            path='.github/workflows/'+region+'-production-build-only.yml',repository={'full_name':'joseungil-kr/fwith-site-factory'})
        artifact=dict(id=200,expired=False,name=region+'-production-build-100'+('-'+'a'*40 if region=='seoul-gangnam' else ''),
            digest=review['artifactDigest'],workflow_run={'id':100,'head_sha':'a'*40})
        journal=dict(number=300,state='open',user={'login':'joseungil-kr'},title='[GANGNAM-INDEXNOW-RECEIPTS] 20261014',repository_url='https://api.github.com/repos/joseungil-kr/fwith-site-factory')
        fixture=dict(review=review,run=run,artifact=artifact,journal=journal)
        if mutation:
            section,key,value=mutation;fixture[section][key]=value
        program='''const fixture=JSON.parse(process.argv[1]);
process.env.REGION=process.argv[2];process.env.CONTROL_DIR='control/scripts/direct-'+process.env.REGION;
process.env.BUILD_RUN_ID='100';process.env.BUILD_ARTIFACT_ID='200';
let issueReads=0;
const github={rest:{actions:{getWorkflowRun:async()=>({data:fixture.run}),getArtifact:async()=>({data:fixture.artifact})},issues:{get:async()=>{issueReads++;return {data:fixture.journal};}}}};
const fakeRequire=name=>{if(name!=='fs')throw Error('unexpected require');return {readFileSync:path=>JSON.stringify(path.endsWith('production-release-review-binding.json')?{path:'docs/review.json'}:path.endsWith('production-publication.json')?{receiptIssue:300}:fixture.review)}};
const AsyncFunction=Object.getPrototypeOf(async function(){}).constructor;
(async()=>{try{await new AsyncFunction('github','context','require',process.argv[3])(github,{repo:{owner:'joseungil-kr',repo:'fwith-site-factory'}},fakeRequire);console.log(JSON.stringify({passed:true,issueReads}));}catch(error){console.log(JSON.stringify({passed:false,message:error.message,issueReads}));}})();'''
        result=subprocess.run(['node','-e',program,json.dumps(fixture),region,script],capture_output=True,text=True,check=True,timeout=20)
        return json.loads(result.stdout)

    def test_metadata_accepts_actual_shape_for_both_regions(self):
        self.assertEqual(self.run_metadata('seoul-seocho'),{'passed':True,'issueReads':0})
        self.assertEqual(self.run_metadata('seoul-gangnam'),{'passed':True,'issueReads':1})

    def test_metadata_rejects_changed_run_artifact_or_journal(self):
        mutations=[('run','run_attempt',2),('run','conclusion','failure'),('run','head_sha','b'*40),('run','path','.github/workflows/seoul-seocho-production-build-only.yml'),
            ('artifact','expired',True),('artifact','name','seoul-seocho-production-build-100'),('artifact','digest','sha256:'+'c'*64),
            ('review','qaRunId','101'),('journal','number',266),('journal','title','[SEOCHO-INDEXNOW-RECEIPTS] 20261014'),
            ('journal','state','closed'),('journal','user',{'login':'other'}),('journal','pull_request',{'url':'https://example.invalid'})]
        for mutation in mutations:
            with self.subTest(mutation=mutation):self.assertFalse(self.run_metadata('seoul-gangnam',mutation)['passed'])


if __name__=='__main__':unittest.main()
