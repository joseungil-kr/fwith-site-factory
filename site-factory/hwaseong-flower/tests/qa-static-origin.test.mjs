import test from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';

// Load the real pure helpers without executing the CLI's dist inspection.
const python = `
import ast, json, re, sys
from pathlib import Path
from urllib.parse import urlparse
source = ast.parse(Path('scripts/qa_static.py').read_text())
names = {'valid_loopback_preview_origin', 'uses_expected_origin', 'unexpected_loopback_reference'}
helpers = ast.Module(body=[n for n in source.body if isinstance(n, ast.FunctionDef) and n.name in names], type_ignores=[])
exec(compile(helpers, 'scripts/qa_static.py', 'exec'))
data = json.loads(sys.argv[1])
EXPECTED_ORIGIN = data.pop('expected', 'http://127.0.0.1:8935')
print(json.dumps(globals()[data['function']](*data['args'])))
`;
function invoke(name, args, expected) {
  const result = spawnSync('python3', ['-c', python, JSON.stringify({function: name, args, expected})], {encoding: 'utf8'});
  assert.equal(result.status, 0, result.stderr);
  return JSON.parse(result.stdout);
}

for (const origin of ['http://127.0.0.1:8935', 'http://localhost:8935/']) {
  test(`static QA accepts exact noindex loopback preview ${origin}`, () => {
    assert.equal(invoke('valid_loopback_preview_origin', [origin, true, 'false']), true);
  });
}
const invalid = [
  ['public production origin', 'https://hwaseong.fwith.kr', true, 'false'],
  ['public origin containing loopback text', 'http://localhost.example.com:8935', true, 'false'],
  ['wrong port', 'http://127.0.0.1:8936', true, 'false'],
  ['missing port', 'http://127.0.0.1', true, 'false'],
  ['unexpected scheme', 'https://127.0.0.1:8935', true, 'false'],
  ['credentials', 'http://user@127.0.0.1:8935', true, 'false'],
  ['path suffix', 'http://127.0.0.1:8935/preview', true, 'false'],
  ['query suffix', 'http://127.0.0.1:8935?preview=1', true, 'false'],
  ['fragment suffix', 'http://127.0.0.1:8935#preview', true, 'false'],
  ['indexable preview', 'http://127.0.0.1:8935', true, 'true'],
  ['missing explicit noindex', 'http://127.0.0.1:8935', true, null],
  ['missing manual flag', 'http://127.0.0.1:8935', false, 'false'],
];
for (const [label, ...args] of invalid) {
  test(`static QA rejects ${label}`, () => assert.equal(invoke('valid_loopback_preview_origin', args), false));
}
test('static QA preview exception removes only exact allowed origin', () => {
  assert.equal(invoke('unexpected_loopback_reference', ['<link href="http://127.0.0.1:8935/funeral/">', true]), false);
  for (const text of ['http://127.0.0.1:89350/', 'http://127.0.0.1:8935.evil/', 'http://localhost:8935/', 'http://127.0.0.1:8935@evil/']) {
    assert.equal(invoke('unexpected_loopback_reference', [text, true]), true, text);
  }
  assert.equal(invoke('unexpected_loopback_reference', ['http://127.0.0.1:8935/', false]), true);
});
test('static QA compares public canonical origins exactly', () => {
  const expected = 'https://hwaseong.fwith.kr';
  assert.equal(invoke('uses_expected_origin', [expected + '/funeral/'], expected), true);
  for (const value of [expected + '.evil/', 'http://hwaseong.fwith.kr/', expected + ':444/', 'https://user@hwaseong.fwith.kr/']) {
    assert.equal(invoke('uses_expected_origin', [value], expected), false, value);
  }
});
