const test = require('node:test');
const assert = require('node:assert/strict');
const {baseURL, probe, createEstimate} = require('../web/api.js');

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

test('a lost POST response has unknown persistence and is never retried', async () => {
  let posts = 0;
  const result = await createEstimate('https://api.example.test', {}, async (_url, options) => {
    if (options.method === 'POST') {
      posts++;
      throw new Error('response lost after database commit');
    }
    return {ok: true, json: async () => ({status: 'ready'})};
  });
  assert.equal(result.state, 'unknown');
  assert.equal(posts, 1);
});

test('an unavailable service is never sent an estimate', async () => {
  let posts = 0;
  const result = await createEstimate('https://api.example.test', {}, async (_url, options) => {
    if (options.method === 'POST') posts++;
    return {ok: false, json: async () => ({})};
  });
  assert.equal(result.state, 'unavailable');
  assert.equal(posts, 0);
});

test('saved estimates retain their identifier and measured request cost', async () => {
  const input = {price_id: 'azure-t4', days: 30};
  const result = await createEstimate('https://api.example.test', input, async (_url, options) => {
    if (options.method !== 'POST') return {ok: true, json: async () => ({status: 'ready'})};
    assert.deepEqual(JSON.parse(options.body), input);
    return {ok: true, json: async () => ({id: 'persisted-id', shadow_cost_usd: '378.72'}), headers: {get: () => '0.000001'}};
  });
  assert.equal(result.state, 'saved');
  assert.equal(result.result.id, 'persisted-id');
  assert.equal(result.requestCost, '0.000001');
});
