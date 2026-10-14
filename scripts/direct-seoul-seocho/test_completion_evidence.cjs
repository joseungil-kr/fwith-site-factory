'use strict';
const assert = require('node:assert/strict');
const {actualOutcomes} = require('./completion_evidence.cjs');
const valid = '2026-10-14T08:02:00Z   DEPLOY: success\n' +
  '2026-10-14T08:02:00Z   ATTACH: failure\n' +
  '2026-10-14T08:02:00Z   BINDING: failure\n' +
  '2026-10-14T08:02:00Z   HTTP: skipped\n' +
  '2026-10-14T08:02:00Z   INDEXNOW: skipped\n' +
  '2026-10-14T08:02:00Z {"code":"unexpected_release_files"}\n';
assert.equal(actualOutcomes(valid).DEPLOY, 'success');
for (const [before, after] of [['DEPLOY: success', 'DEPLOY: failure'], ['ATTACH: failure', 'ATTACH: success'],
  ['BINDING: failure', 'BINDING: success'], ['HTTP: skipped', 'HTTP: success'],
  ['INDEXNOW: skipped', 'INDEXNOW: success'], ['unexpected_release_files', 'other_error']]) {
  assert.throws(() => actualOutcomes(valid.replace(before, after)));
}
assert.throws(() => actualOutcomes(valid + '2026-10-14T08:02:00Z   DEPLOY: success\n'));
assert.throws(() => actualOutcomes('summary: success'));
console.log('PASS: exact actual outcomes plus 8 negative log cases; summary success is insufficient');
