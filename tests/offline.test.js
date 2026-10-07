const { test } = require('node:test');
const assert = require('node:assert/strict');
const { allowOfflineRequest } = require('../desktop/offline');
test('offline window permits only its exact loopback origin and local data', () => {
  const origin = 'http://127.0.0.1:12345';
  assert.equal(allowOfflineRequest(origin + '/assets/icon.js', origin), true);
  for (const url of ['https://github.com/', 'http://127.0.0.1:9999/', 'http://localhost:12345/', 'ws://127.0.0.1:12345/', 'file:///C:/test'])
    assert.equal(allowOfflineRequest(url, origin), false);
  assert.equal(allowOfflineRequest('blob:' + origin + '/export', origin), true);
});
