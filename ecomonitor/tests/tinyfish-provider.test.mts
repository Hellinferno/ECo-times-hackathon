import assert from 'node:assert/strict';
import { afterEach, describe, it } from 'node:test';

import {
  TinyfishWebIntelProvider,
  getNewsDeepExtractWithTinyfish,
  invalidateTinyfishSettingsCache,
  verifyGroundingWithTinyfish,
} from '../server/worldmonitor/_web-intel/index.ts';
import type { WebIntelGoalRequest } from '../server/worldmonitor/_web-intel/types.ts';

const originalFetch = globalThis.fetch;
const originalEnv = {
  MINO_API_KEY: process.env.MINO_API_KEY,
  TINYFISH_MODE: process.env.TINYFISH_MODE,
  TINYFISH_TIMEOUT_SECS: process.env.TINYFISH_TIMEOUT_SECS,
};

afterEach(() => {
  globalThis.fetch = originalFetch;
  process.env.MINO_API_KEY = originalEnv.MINO_API_KEY;
  process.env.TINYFISH_MODE = originalEnv.TINYFISH_MODE;
  process.env.TINYFISH_TIMEOUT_SECS = originalEnv.TINYFISH_TIMEOUT_SECS;
  invalidateTinyfishSettingsCache();
});

describe('TinyfishWebIntelProvider', () => {
  it('parses SSE final payload and returns normalized success', async () => {
    process.env.MINO_API_KEY = 'test-key';
    globalThis.fetch = async () => new Response(
      'event: message\ndata: {"result":{"evidence":[{"statement":"Confirmed closure"}]}}\n\n',
      { status: 200, headers: { 'Content-Type': 'text/event-stream' } },
    );

    const provider = new TinyfishWebIntelProvider();
    const request: WebIntelGoalRequest = {
      requestId: 'req-1',
      domain: 'intelligence_grounding',
      eventType: 'grounding_evidence',
      subjectId: 'subject-1',
      url: 'https://example.com',
      goal: 'Extract evidence',
    };

    const [result] = await provider.runGoalBatch([request], { maxRetries: 0 });
    assert.equal(result.status, 'success');
    assert.equal(result.normalizedEvents.length, 1);
    assert.equal(result.normalizedEvents[0]!.type, 'grounding_evidence');
  });

  it('retries once on failure and succeeds on the next attempt', async () => {
    process.env.MINO_API_KEY = 'test-key';
    let calls = 0;
    globalThis.fetch = async () => {
      calls += 1;
      if (calls === 1) throw new Error('connect timeout');
      return new Response('data: {"result":{"ok":true}}\n\n', {
        status: 200,
        headers: { 'Content-Type': 'text/event-stream' },
      });
    };

    const provider = new TinyfishWebIntelProvider();
    const [result] = await provider.runGoalBatch([{
      requestId: 'req-2',
      domain: 'news_deep_extract',
      eventType: 'news_deep_extract',
      subjectId: 'subject-2',
      url: 'https://example.com/article',
      goal: 'Extract structured output',
    }], { maxRetries: 1 });

    assert.equal(calls, 2);
    assert.equal(result.status, 'success');
  });

  it('returns invalid_payload when SSE stream has no usable final data', async () => {
    process.env.MINO_API_KEY = 'test-key';
    globalThis.fetch = async () => new Response('event: ping\ndata: [DONE]\n\n', {
      status: 200,
      headers: { 'Content-Type': 'text/event-stream' },
    });

    const provider = new TinyfishWebIntelProvider();
    const [result] = await provider.runGoalBatch([{
      requestId: 'req-3',
      domain: 'supply_chain_chokepoint',
      eventType: 'chokepoint_observation',
      subjectId: 'suez',
      url: 'https://example.com/port',
      goal: 'Extract queue metrics',
    }], { maxRetries: 0 });

    assert.equal(result.status, 'invalid_payload');
  });
});

describe('TinyFish service integration', () => {
  it('verifies grounding in active mode and returns evidence diagnostics', async () => {
    process.env.MINO_API_KEY = 'test-key';
    process.env.TINYFISH_MODE = 'active';
    process.env.TINYFISH_TIMEOUT_SECS = '2';
    invalidateTinyfishSettingsCache();

    globalThis.fetch = async () => new Response(
      'data: {"result":{"evidence":[{"statement":"Port access restricted","source":"Gov Notice","source_url":"https://example.com/gov","observed_at":"2026-03-27T10:00:00Z","confidence":0.88,"quote_spans":["restricted to military traffic"]}]}}\n\n',
      { status: 200, headers: { 'Content-Type': 'text/event-stream' } },
    );

    const verification = await verifyGroundingWithTinyfish({
      requestId: 'verify-1',
      query: 'Unconfirmed reports of military closure at the port',
      geoContext: 'Possible blockade near key maritime chokepoint',
    });

    assert.equal(verification.status, 'verified');
    assert.equal(verification.evidenceCount, 1);
    assert.equal(verification.diagnostics.mode, 'active');
    assert.ok(verification.confidenceDelta > 0);
  });

  it('skips deep extraction when item is not critical', async () => {
    process.env.MINO_API_KEY = 'test-key';
    process.env.TINYFISH_MODE = 'active';
    invalidateTinyfishSettingsCache();

    let calls = 0;
    globalThis.fetch = async () => {
      calls += 1;
      return new Response('{}', { status: 200 });
    };

    const { deepExtract, diagnostics } = await getNewsDeepExtractWithTinyfish({
      title: 'Routine logistics update',
      link: 'https://example.com/news',
      source: 'Example',
      threatLevel: 'THREAT_LEVEL_HIGH',
    });

    assert.equal(calls, 0);
    assert.equal(deepExtract.status, 'unknown');
    assert.equal(diagnostics.reason, 'not_critical');
  });

  it('returns unknown without live fetch when preferLive=false and cache is missing', async () => {
    process.env.MINO_API_KEY = 'test-key';
    process.env.TINYFISH_MODE = 'active';
    invalidateTinyfishSettingsCache();

    let calls = 0;
    globalThis.fetch = async () => {
      calls += 1;
      return new Response('{}', { status: 200 });
    };

    const { deepExtract, diagnostics } = await getNewsDeepExtractWithTinyfish({
      title: 'Critical disruption report',
      link: 'https://example.com/critical',
      source: 'Example',
      threatLevel: 'THREAT_LEVEL_CRITICAL',
    }, { preferLive: false });

    assert.equal(calls, 0);
    assert.equal(deepExtract.status, 'unknown');
    assert.equal(diagnostics.reason, 'cache_miss_no_live_fetch');
  });
});
