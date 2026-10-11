import test from 'node:test';
import assert from 'node:assert/strict';
import {spawnSync} from 'node:child_process';

test('static QA resolves encoded paths safely and preserves frozen/regional hub counts',()=>{
 const result=spawnSync('python3',['-c',String.raw`
import ast, tempfile, pathlib, urllib.parse, re
source=pathlib.Path('scripts/qa_static.py').read_text()
tree=ast.parse(source)
functions=ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('target_exists','count_hubs')],type_ignores=[])
with tempfile.TemporaryDirectory() as temp:
 root=pathlib.Path(temp); dist=root/'dist';dist.mkdir()
 ns={'Path':pathlib.Path,'DIST':dist,'urlparse':urllib.parse.urlparse,'unquote':urllib.parse.unquote,'re':re}
 exec(compile(functions,'qa_static.py','exec'),ns)
 for name in ['안산꽃배달','funeral']:
  (dist/name).mkdir();(dist/name/'index.html').write_text('ok')
 (dist/'index.html').write_text('home');(root/'outside.html').write_text('private')
 (dist/'escape').symlink_to(root,target_is_directory=True)
 check=ns['target_exists']
 assert check('/%EC%95%88%EC%82%B0%EA%BD%83%EB%B0%B0%EB%8B%AC/?q=1#top')
 assert check('/안산꽃배달/') and check('/funeral/') and check('/')
 for bad in ['/missing/','/%FF/','/%ZZ/','/../outside.html','/%2e%2e/outside.html','/%2E%2E%2Foutside.html','/escape/outside.html','/%00/','/foo%5c..%5coutside.html']:
  assert not check(bad),bad
 frozen=[{'status':'published','routeType':'category','category':'funeral'},{'status':'approved','routeType':'category','category':'regions'},{'status':'draft','routeType':'category','category':'regions'}]
 manual=[{'publicationMode':'manual-user-request','routeType':'category','category':'funeral'}]*13
 before=[dict(x) for x in frozen]
 assert ns['count_hubs'](frozen,manual,['funeral','regions'])=={'funeral':14,'regions':1}
 assert ns['count_hubs'](frozen,[],['funeral','regions'])=={'funeral':1,'regions':1}
 assert frozen==before
 print('encoded paths, traversal/symlink rejection, merged counts and frozen/regional preservation passed')
`],{encoding:'utf8'});
 assert.equal(result.status,0,result.stdout+result.stderr);
});

test('production rejects loopback while only exact explicit local noindex preview is allowed',()=>{
 const result=spawnSync('python3',['-c',String.raw`
import ast,pathlib,re,urllib.parse
source=pathlib.Path('scripts/qa_static.py').read_text();tree=ast.parse(source)
functions=ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('explicit_manual_preview_origin','has_disallowed_loopback')],type_ignores=[])
ns={'re':re,'urlparse':urllib.parse.urlparse};exec(compile(functions,'qa_static.py','exec'),ns)
check=ns['has_disallowed_loopback'];origin=ns['explicit_manual_preview_origin']
valid={'MANUAL_PREVIEW':'1','SITE_INDEXABLE':'false','SITE_URL':'http://127.0.0.1:8934'}
assert not check('<link href="http://127.0.0.1:8934/regions/">',valid)
assert not check('{"url":"http://127.0.0.1:8934"}',valid)
assert not check('<p>https://ansan.fwith.kr/</p>',{})
for raw in ['localhost','LOCALHOST','127.0.0.1','http://127.0.0.1:9999/x','http://localhost:8934/x','http://127.0.0.1:8934.evil/x','http://127.0.0.1:8934@evil.example/x']:
 assert check(raw,valid),raw
for env in [{},{'SITE_INDEXABLE':'false'},{'MANUAL_PREVIEW':'1'},{'MANUAL_PREVIEW':'1','SITE_INDEXABLE':'true','SITE_URL':'http://127.0.0.1:8934'},{**valid,'SITE_URL':'https://ansan.fwith.kr'}, {**valid,'SITE_URL':'https://127.0.0.1:8934'}, {**valid,'SITE_URL':'http://localhost.evil:8934'}, {**valid,'SITE_URL':'http://u:p@localhost:8934'}, {**valid,'SITE_URL':'http://localhost:bad'}, {**valid,'SITE_URL':'http://localhost:8934/path'}, {**valid,'SITE_URL':'http://localhost:8934/?x=1'}, {**valid,'SITE_URL':'http://localhost:8934/#x'}]:
 assert origin(env) is None,env
 for raw in ['http://localhost:8934/','http://127.0.0.1:8934/','http://[::1]:8934/']:
  assert check(raw,env),(env,raw)
for host in ['localhost','127.0.0.1','[::1]']:
 env={**valid,'SITE_URL':'http://'+host+':8934'}
 assert not check('<link href="'+env['SITE_URL']+'/">',env)
 assert check('<link href="'+env['SITE_URL']+'/">',{**env,'SITE_INDEXABLE':'true'})
print('strict production/explicit loopback preview positive and negative cases pass')
`],{encoding:'utf8'});assert.equal(result.status,0,result.stdout+result.stderr);
});


test('sitemap absence is permitted only for strict preview and preview sitemap output is rejected',()=>{
 const result=spawnSync('python3',['-c',String.raw`
import ast,pathlib,tempfile,urllib.parse,types
source=pathlib.Path('scripts/qa_static.py').read_text();tree=ast.parse(source)
fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='explicit_manual_preview_origin')
block=source.split('sitemap = DIST / "sitemap-index.xml"',1)[1].split('if PRIMARY_LANDING_SLUG:',1)[0]
with tempfile.TemporaryDirectory() as temp:
 dist=pathlib.Path(temp);sitemap=dist/'sitemap-index.xml'
 valid={'MANUAL_PREVIEW':'1','SITE_INDEXABLE':'false','SITE_URL':'http://127.0.0.1:8934'}
 def run(env):
  ns={'urlparse':urllib.parse.urlparse,'os':types.SimpleNamespace(environ=env),'DIST':dist,'sitemap':sitemap,'errors':[],'EXPECTED_ORIGIN':'https://ansan.fwith.kr'}
  exec(compile(ast.Module(body=[fn],type_ignores=[]),'qa_static.py','exec'),ns);exec(block,ns);return ns['errors']
 assert run(valid)==[]
 for env in [{},{**valid,'SITE_INDEXABLE':'true'},{**valid,'MANUAL_PREVIEW':'0'},{**valid,'SITE_URL':'https://ansan.fwith.kr'}]:
  assert run(env)==['Missing sitemap-index.xml']
 sitemap.write_text('https://ansan.fwith.kr/sitemap-0.xml')
 assert run({})==[]
 assert run(valid)==['Explicit manual preview must not generate sitemap XML']
 sitemap.write_text('https://wrong.example/sitemap-0.xml')
 assert run({})==['Sitemap does not use expected production origin']
 sitemap.unlink();(dist/'sitemap-0.xml').write_text('leftover')
 assert run(valid)==['Explicit manual preview must not generate sitemap XML']
print('strict preview and production sitemap requirements passed')
`],{encoding:'utf8'});assert.equal(result.status,0,result.stdout+result.stderr);
});
