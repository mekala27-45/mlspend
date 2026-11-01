const test = require('node:test');
const assert = require('node:assert/strict');
const {baseURL, probe} = require('../web/api.js');

test('hosted API uses same origin; Pages requires explicit configuration', () => {
  assert.equal(baseURL({hostname:'demo.vercel.app',origin:'https://demo.vercel.app'}), 'https://demo.vercel.app');
  assert.equal(baseURL({hostname:'mekala27-45.github.io'}), null);
  assert.equal(baseURL({}, 'https://api.example.test/'), 'https://api.example.test');
});

test('cold service receives two GETs and recovers from first 503', async () => {
  let calls = 0;
  const ready = await probe('https://api.example.test', async (_url, options) => {
    assert.equal(options.method, undefined);
    calls++;
    return {ok:calls === 2, json:async () => ({status:'ready'})};
  });
  assert.equal(ready, true);
  assert.equal(calls, 2);
});

test('missing configuration and unavailable database never report ready', async () => {
  assert.equal(await probe(null, () => {throw Error('must not call')}), false);
  let calls = 0;
  assert.equal(await probe('https://api.example.test', async () => {
    calls++;
    return {ok:true, json:async () => ({status:'configuration_required'})};
  }), false);
  assert.equal(calls, 2);
});
