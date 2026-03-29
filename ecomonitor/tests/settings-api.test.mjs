import assert from 'node:assert/strict';
import { afterEach, describe, it } from 'node:test';

import handler from '../api/settings.js';

const originalFetch = globalThis.fetch;
const originalEnv = {
  UPSTASH_REDIS_REST_URL: process.env.UPSTASH_REDIS_REST_URL,
  UPSTASH_REDIS_REST_TOKEN: process.env.UPSTASH_REDIS_REST_TOKEN,
  WORLDMONITOR_VALID_KEYS: process.env.WORLDMONITOR_VALID_KEYS,
};

afterEach(() => {
  globalThis.fetch = originalFetch;
  process.env.UPSTASH_REDIS_REST_URL = originalEnv.UPSTASH_REDIS_REST_URL;
  process.env.UPSTASH_REDIS_REST_TOKEN = originalEnv.UPSTASH_REDIS_REST_TOKEN;
  process.env.WORLDMONITOR_VALID_KEYS = originalEnv.WORLDMONITOR_VALID_KEYS;
});

describe('api/settings', () => {
  it('returns TinyFish defaults when no saved settings exist', async () => {
    process.env.UPSTASH_REDIS_REST_URL = 'https://redis.example';
    process.env.UPSTASH_REDIS_REST_TOKEN = 'token';
    process.env.WORLDMONITOR_VALID_KEYS = 'wm_test_key';

    globalThis.fetch = async (input) => {
      const url = String(input);
      if (url.includes('/get/')) {
        return new Response(JSON.stringify({ result: null }), { status: 200 });
      }
      throw new Error(`Unexpected fetch: ${url}`);
    };

    const req = new Request('https://api.worldmonitor.app/api/settings', {
      method: 'GET',
      headers: {
        Origin: 'https://worldmonitor.app',
        'X-WorldMonitor-Key': 'wm_test_key',
      },
    });
    const resp = await handler(req);
    const body = await resp.json();

    assert.equal(resp.status, 200);
    assert.equal(body.settings.tinyfish_mode, 'shadow');
    assert.equal(body.settings.tinyfish_timeout_secs, 20);
    assert.equal(body.settings.tinyfish_fail_open, true);
  });

  it('sanitizes PATCH payload and persists allowed keys only', async () => {
    process.env.UPSTASH_REDIS_REST_URL = 'https://redis.example';
    process.env.UPSTASH_REDIS_REST_TOKEN = 'token';
    process.env.WORLDMONITOR_VALID_KEYS = 'wm_test_key';

    const writes = [];
    globalThis.fetch = async (input, init = {}) => {
      const url = String(input);
      if (url.includes('/get/')) {
        return new Response(JSON.stringify({ result: JSON.stringify({
          tinyfish_mode: 'shadow',
          tinyfish_timeout_secs: 20,
        }) }), { status: 200 });
      }
      if (url === 'https://redis.example') {
        writes.push(JSON.parse(init.body));
        return new Response(JSON.stringify({ result: 'OK' }), { status: 200 });
      }
      throw new Error(`Unexpected fetch: ${url}`);
    };

    const req = new Request('https://api.worldmonitor.app/api/settings', {
      method: 'PATCH',
      headers: {
        Origin: 'https://worldmonitor.app',
        'Content-Type': 'application/json',
        'X-WorldMonitor-Key': 'wm_test_key',
      },
      body: JSON.stringify({
        tinyfish_mode: 'active',
        tinyfish_timeout_secs: 45,
        tinyfish_fail_open: 'false',
        invalid_key: 'ignored',
      }),
    });

    const resp = await handler(req);
    const body = await resp.json();

    assert.equal(resp.status, 200);
    assert.equal(body.settings.tinyfish_mode, 'active');
    assert.equal(body.settings.tinyfish_timeout_secs, 45);
    assert.equal(body.settings.tinyfish_fail_open, false);
    assert.ok(!('invalid_key' in body.settings));
    assert.equal(writes.length, 1);
  });
});
