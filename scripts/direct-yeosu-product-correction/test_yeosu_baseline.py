"""Yeosu-only binding, request, workflow and historical evidence regressions."""
import ast,copy,hashlib,json,unittest
from pathlib import Path
from unittest.mock import patch
import provider_baseline as b
import previous_public as public
import test_provider_baseline as reused

class YeosuBinding(unittest.TestCase):
 def test_actual_fixed_identity_and_no_historical_version_invention(self):
  p=b.load_policy()
  self.assertEqual((b.HOST,b.WORKER,b.PREVIOUS,b.CURRENT),('yeosu.fwith.kr','yeosu-flower-guide','472c54a40cf873c925ed2d314748351381ee8682','7260f8d0c77b05cde16ed5b7de1b775313bfc1dd'))
  self.assertEqual((p['previousPublicationRunId'],p['previousBuildRunId']),(38745536071,38742707182))
  self.assertIsNone(p['historicalProviderVersionId']);self.assertIsNone(p['historicalProviderDeploymentId']);self.assertIs(p['historicalVersionKnown'],False)
  self.assertEqual(b.TITLE,'[YEOSU-PRODUCT-CORRECTION-BASELINE-INSPECT] 20261017')
 def test_all_nine_historical_files_are_pinned_and_identity_consistent(self):
  p=b.load_policy();self.assertEqual(len(p['evidence']),9)
  files={Path(row['path']).name:json.loads(b.read(b.ROOT/row['path'])) for row in p['evidence']}
  self.assertEqual(files['binding-after.json']['accountSha256'],b.ACCOUNT_SHA)
  self.assertEqual(files['binding-after.json']['hostname'],b.HOST);self.assertEqual(files['binding-after.json']['worker'],b.WORKER)
  self.assertEqual(files['release-manifest.json']['files'],files['http-contract.json']['files']);self.assertEqual(len(files['http-contract.json']['files']),18)
  self.assertEqual(files['selected-release.json']['revision'],b.PREVIOUS)
  self.assertEqual(files['publication-artifact-identity.json']['runId'],38745536071)
  self.assertEqual(files['publication-artifact-identity.json']['digest'],'sha256:4d2254a29052ea8762b23ce8aa486aedfb9c9cbf7b1953af5d891f97c08093e1')
 def test_policy_or_prior_evidence_change_blocks_before_transport(self):
  original=b.read
  for target in [b.D/'provider-baseline-policy.json',b.ROOT/b.load_policy()['previousPublicContractPath'],b.D/'managed_robots.py',b.D/'existing_provider.py']:
   with self.subTest(target=target.name),patch.object(b,'read',side_effect=lambda p:original(p)+(b' ' if Path(p)==target else b'')),self.assertRaises(ValueError):b.load_policy()
 def test_open_non_pr_duplicate_and_nonfinite_request_rejected(self):
  env,event=reused.Authorization().case()
  for state in [None,'closed']:
   x=copy.deepcopy(event);x['issue']['state']=state
   with self.subTest(state=state),self.assertRaisesRegex(ValueError,'open_non_pr_issue_required'):b.authorize(env,x)
  x=copy.deepcopy(event);x['issue']['pull_request']={}
  with self.assertRaisesRegex(ValueError,'open_non_pr_issue_required'):b.authorize(env,x)
  x=copy.deepcopy(event);x['issue']['body']='{"mode":"wrong",'+x['issue']['body'][1:]
  with self.assertRaisesRegex(ValueError,'duplicate_request_key'):b.authorize(env,x)
  x=copy.deepcopy(event);x['issue']['body']=x['issue']['body'].replace('"schemaVersion": 1','"schemaVersion": NaN')
  with self.assertRaisesRegex(ValueError,'nonfinite_request_value'):b.authorize(env,x)
 def test_missing_control_revision_template_cannot_authorize(self):
  env,event=reused.Authorization().case();body=json.loads(event['issue']['body']);body['expected_control_revision']=None;event['issue']['body']=json.dumps(body)
  with self.assertRaisesRegex(ValueError,'exact_baseline_request_required'):b.authorize(env,event)
 def test_trusted_control_exact_scopes_and_wrong_head_fail(self):
  expected='b'*40;seen=[]
  def git(command):
   seen.append(command)
   if command[-2:]==['rev-parse','HEAD']:return (expected+'\n').encode()
   if 'status' in command:return b''
   scope=command[-1];files=sorted(p for p in (b.ROOT/scope).rglob('*') if p.is_file()) if (b.ROOT/scope).is_dir() else [b.ROOT/scope]
   return b''.join(('100644 blob '+hashlib.sha1(b'blob '+str(len(p.read_bytes())).encode()+b'\0'+p.read_bytes()).hexdigest()+'\t'+p.relative_to(b.ROOT).as_posix()).encode()+b'\0' for p in files)
  with patch.object(b.subprocess,'check_output',side_effect=git):self.assertEqual(b.trusted_control({'GITHUB_SHA':expected}),expected)
  scopes=[c[-1] for c in seen if 'ls-tree' in c]
  self.assertEqual(scopes,['scripts/direct-yeosu-product-correction','docs/direct-yeosu-product-correction','.github/workflows/yeosu-product-correction-baseline-inspect.yml'])
  with patch.object(b.subprocess,'check_output',return_value=b'bad\n'),self.assertRaisesRegex(ValueError,'actual_control_revision_mismatch'):b.trusted_control({'GITHUB_SHA':expected})
 def test_trusted_control_dirty_untracked_and_missing_scope_fail(self):
  expected='b'*40
  for values,error in [([(expected+'\n').encode(),b'?? scripts/direct-yeosu-product-correction/leak'], 'baseline_control_checkout_changed'), ([(expected+'\n').encode(),b'',b''],'tracked_baseline_scope_missing')]:
   with self.subTest(error=error),patch.object(b.subprocess,'check_output',side_effect=values),self.assertRaisesRegex(ValueError,error):b.trusted_control({'GITHUB_SHA':expected})
 def test_public_identity_and_explicit_get_only(self):
  self.assertEqual(public.ORIGIN,'https://yeosu.fwith.kr');self.assertEqual(public.PROOF_PATH,'39c4ed924bc6084c670a963c26d9f018.txt')
  self.assertEqual(public.ROUTES,{'/','/regions/','/regions/yeosu-jeonnam-hospital-funeral-wreath/'})
  tree=ast.parse((b.D/'previous_public.py').read_text());calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='Request']
  self.assertEqual(len(calls),1);self.assertEqual(next(x.value.value for x in calls[0].keywords if x.arg=='method'),'GET')
 def test_workflow_scopes_credentials_to_one_observation_step(self):
  text=(b.ROOT/'.github/workflows/yeosu-product-correction-baseline-inspect.yml').read_text()
  self.assertEqual(text.count('secrets.CLOUDFLARE_API_TOKEN'),1);self.assertEqual(text.count('secrets.CLOUDFLARE_ACCOUNT_ID'),1)
  before,after=text.split('      - name: Observe fixed historical account and exact existing host through allowlisted GET only\n')
  step,retention=after.split('      - name: Retain sanitized observation')
  self.assertNotIn('secrets.',before+retention);self.assertIn(' observe --report baseline-observation.json',step)
  self.assertNotIn('issues: write',text);self.assertNotIn('contents: write',text);self.assertNotIn('actions: write',text)
  self.assertIn('persist-credentials: false',text);self.assertIn('ref: ${{ github.sha }}',text)
  self.assertEqual(text.count('      - uses: actions/checkout@v4'),1)
 def test_workflow_requested_concurrency_matches_job_predicate(self):
  text=(b.ROOT/'.github/workflows/yeosu-product-correction-baseline-inspect.yml').read_text()
  condition=next(line.strip()[4:] for line in text.splitlines() if line.startswith('    if:'))
  group=next(line.strip() for line in text.splitlines() if line.startswith('  group:'))
  self.assertEqual(group,"group: yeosu-product-correction-baseline-${{ "+condition+" && 'requested' || github.run_id }}")
  self.assertIn('cancel-in-progress: false',text);self.assertIn("github.run_attempt == 1",condition);self.assertIn(b.TITLE,condition)
 def test_no_publishing_or_indexnow_transport_imported(self):
  workflow=(b.ROOT/'.github/workflows/yeosu-product-correction-baseline-inspect.yml').read_text()
  for word in ['wrangler','npm ','npx ','indexnow_finalize','publish.py','existing_update','phone_update','createComment','createIssue','PUT','POST','PATCH','DELETE']:self.assertNotIn(word,workflow)
  tree=ast.parse((b.D/'provider_baseline.py').read_text());requests=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='Request']
  self.assertEqual(len(requests),1);self.assertEqual(next(x.value.value for x in requests[0].keywords if x.arg=='method'),'GET')
 def test_success_observation_never_accepts_or_publishes(self):
  env,event=reused.Authorization().case();get=lambda p:None;get.envelope_compatibility={'domainsListNullPairObserved':False}
  state={'synthetic':'not_real_provider'}
  with patch.object(b,'trusted_control'),patch.object(b,'provider_get',return_value=('fixture',get)),patch.object(b,'state_with_diagnostics',return_value=state),patch.object(b,'old_public',return_value={'synthetic':True}),patch.object(b,'save'):
   out=b.observe(env,event)
  self.assertEqual(out['state'],'OBSERVED_NOT_ACCEPTED_FOR_MUTATION');self.assertEqual(out['providerMethods'],['GET'])
  for key in ['providerMutationsPerformed','IndexNowSubmitted','baselineAccepted','publicationEligible']:self.assertIs(out[key],False)
  self.assertEqual(out['previousPublicationRunId'],38745536071);self.assertEqual(out['correctionSourceRevision'],b.CURRENT)

if __name__=='__main__':unittest.main(verbosity=2)
