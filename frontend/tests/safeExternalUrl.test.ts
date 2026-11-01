import assert from 'node:assert/strict';
import { test } from 'node:test';
import { safeExternalUrl } from '../src/utils/safeExternalUrl.ts';

test('external evidence links must use an absolute HTTP(S) URL', () => {
  assert.equal(safeExternalUrl('https://example.org/claim?q=1'), 'https://example.org/claim?q=1');
  assert.equal(safeExternalUrl('http://example.org/source'), 'http://example.org/source');
  for (const unsafe of [
    'javascript:alert(1)',
    'data:text/html,<script>alert(1)</script>',
    'file:///etc/passwd',
    '//example.org/path',
    '/relative/source',
    'https://name:password@example.org/',
    'http://user@example.org/',
    '',
  ]) {
    assert.equal(safeExternalUrl(unsafe), undefined, unsafe);
  }
  assert.equal(safeExternalUrl(), undefined);
});

test('URL parser rejects deceptive malformed URL strings', () => {
  assert.equal(safeExternalUrl('https://'), undefined);
  assert.equal(safeExternalUrl(' \\u0000javascript:alert(1)'), undefined);
});
