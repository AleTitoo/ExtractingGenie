const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { migrateLibrary } = require('../desktop/migration');

test('library rename preserves exact report bytes and is repeatable', t => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'platinum-migration-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const old = path.join(root, 'old'), next = path.join(root, 'new');
  fs.mkdirSync(path.join(old, 'library'), { recursive: true });
  const pdf = Buffer.from([0, 255, 42, 17]);
  fs.writeFileSync(path.join(old, 'library', 'report.pdf'), pdf);
  fs.writeFileSync(path.join(old, 'library', 'report.json'), '{"activity":"2.0022751E+03"}');
  migrateLibrary(old, next);
  migrateLibrary(old, next);
  assert.deepEqual(fs.readFileSync(path.join(next, 'library', 'report.pdf')), pdf);
  assert.equal(fs.readFileSync(path.join(next, 'library', 'report.json'), 'utf8'), '{"activity":"2.0022751E+03"}');
  assert.ok(fs.existsSync(path.join(old, 'library', 'report.pdf')));
});

test('conflicting saved reports are retained instead of silently overwritten', t => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'platinum-conflict-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const old = path.join(root, 'old'), next = path.join(root, 'new');
  for (const folder of [old, next]) fs.mkdirSync(path.join(folder, 'library'), { recursive: true });
  fs.writeFileSync(path.join(old, 'library', 'report.json'), 'original');
  fs.writeFileSync(path.join(next, 'library', 'report.json'), 'other');
  assert.throws(() => migrateLibrary(old, next), /conflicting files/);
  assert.equal(fs.readFileSync(path.join(old, 'library', 'report.json'), 'utf8'), 'original');
  assert.equal(fs.readFileSync(path.join(next, 'library', 'report.json'), 'utf8'), 'other');
});
