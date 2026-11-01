'use strict';
(function (root) {
  function baseURL(location, configured) {
    if (configured) return configured.replace(/\/$/, '');
    if (['127.0.0.1', 'localhost'].includes(location.hostname)) {
      return location.port === '4173' ? 'http://127.0.0.1:8000' : location.origin;
    }
    return location.hostname.endsWith('.vercel.app') ? location.origin : null;
  }
  async function probe(base, request = fetch) {
    if (!base) return false;
    for (let attempt = 0; attempt < 2; attempt++) {
      try {
        const response = await request(base + '/health', {signal: AbortSignal.timeout(12000)});
        if (response.ok && (await response.json()).status === 'ready') return true;
      } catch (_) { /* A second GET tolerates a sleeping API. */ }
    }
    return false;
  }
  async function createEstimate(base, data, request = fetch) {
    if (!await probe(base, request)) return {state: 'unavailable'};
    // A timed-out POST may already have committed. Never retry it automatically.
    try {
      const response = await request(base + '/v1/estimate', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data),
        signal: AbortSignal.timeout(15000)
      });
      const result = await response.json();
      if (!response.ok) return {state: 'rejected', message: result.detail || 'Request failed'};
      if (!result.id) return {state: 'unknown'};
      return {state: 'saved', result, requestCost: response.headers.get('X-Shadow-Cost-USD')};
    } catch (_) {
      return {state: 'unknown'};
    }
  }
  const api = {baseURL, probe, createEstimate};
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.MLSpendAPI = api;
})(typeof window !== 'undefined' ? window : globalThis);
