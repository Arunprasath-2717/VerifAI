const assert = require('node:assert/strict');
const { test } = require('node:test');
const fs = require('node:fs');
const path = require('node:path');
const root = path.join(__dirname, '..', '..', 'extension');
test('extension capture is user initiated and credentials stay outside page scripts', () => {
  const manifest = JSON.parse(fs.readFileSync(path.join(root, 'manifest.json'), 'utf8'));
  assert.equal(manifest.manifest_version, 3);
  assert.equal(manifest.content_scripts, undefined, 'no always-on injection');
  assert.ok(manifest.permissions.includes('activeTab'));
  assert.ok(manifest.permissions.includes('scripting'));
  assert.ok(!manifest.host_permissions.some(p => p.includes('<all_urls>')));
  const popup = fs.readFileSync(path.join(root, 'popup.js'), 'utf8');
  assert.match(popup, /chrome\.scripting\.executeScript/);
  const content = fs.readFileSync(path.join(root, 'content.js'), 'utf8');
  assert.ok(!/verifaiAccessToken|Authorization|chrome\.storage\.session/.test(content));
});
