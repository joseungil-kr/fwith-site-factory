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
