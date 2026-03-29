import { CHROME_UA } from '../../_shared/constants';
import { sha256Hex } from '../../_shared/hash';
import { runRedisPipeline } from '../../_shared/redis';
import {
  TINYFISH_ENDPOINT_DEFAULT,
  TINYFISH_PROVIDER_HEALTH_KEY,
  TINYFISH_RETRY_DELAYS_MS,
  TINYFISH_RETRY_JITTER,
} from './constants';
import type {
  WebIntelBatchOptions,
  WebIntelEvent,
  WebIntelGoalRequest,
  WebIntelGoalResult,
  WebIntelProvider,
  WebIntelProviderHealth,
} from './types';

interface ProviderStats {
  successCount: number;
  errorCount: number;
  lastRunAt: string;
  lastLatencyMs: number;
  lastError: string;
}

function nowIso(): string {
  return new Date().toISOString();
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === 'object' && !Array.isArray(value);
}

function stableStringify(value: unknown): string {
  if (value === null || typeof value !== 'object') return JSON.stringify(value);
  if (Array.isArray(value)) return `[${value.map((entry) => stableStringify(entry)).join(',')}]`;
  const entries = Object.entries(value as Record<string, unknown>).sort(([a], [b]) => a.localeCompare(b));
  return `{${entries.map(([key, val]) => `${JSON.stringify(key)}:${stableStringify(val)}`).join(',')}}`;
}

function parseSseDataEntries(rawText: string): string[] {
  const lines = rawText.split(/\r?\n/);
  const entries: string[] = [];
  let current: string[] = [];

  for (const rawLine of lines) {
    const line = rawLine.trimEnd();
    if (line.length === 0) {
      if (current.length > 0) {
        entries.push(current.join('\n'));
        current = [];
      }
      continue;
    }
    if (line.startsWith('data:')) {
      current.push(line.slice(5).trimStart());
    }
  }

  if (current.length > 0) {
    entries.push(current.join('\n'));
  }

  return entries;
}

function decodeSseEntry(rawEntry: string): unknown {
  const trimmed = rawEntry.trim();
  if (!trimmed || trimmed === '[DONE]') return null;
  try {
    return JSON.parse(trimmed);
  } catch {
    return trimmed;
  }
}

function selectFinalPayload(decodedEntries: unknown[]): unknown {
  for (let i = decodedEntries.length - 1; i >= 0; i -= 1) {
    const candidate = decodedEntries[i];
    if (isRecord(candidate)) {
      if (candidate.final !== undefined) return candidate.final;
      if (candidate.result !== undefined) return candidate.result;
      if (candidate.data !== undefined) return candidate.data;
      if (candidate.payload !== undefined) return candidate.payload;
      return candidate;
    }
    if (candidate != null) return candidate;
  }
  return null;
}

function deriveHealthStatus(stats: ProviderStats): WebIntelProviderHealth['status'] {
  const total = stats.successCount + stats.errorCount;
  if (total === 0) return 'degraded';
  if (stats.successCount === 0 && stats.errorCount > 0) return 'down';
  const errorRatio = stats.errorCount / total;
  return errorRatio > 0.5 ? 'degraded' : 'healthy';
}

function toErrorMessage(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}

export class TinyfishWebIntelProvider implements WebIntelProvider {
  private readonly endpoint: string;

  private readonly apiKey: string;

  private stats: ProviderStats = {
    successCount: 0,
    errorCount: 0,
    lastRunAt: '',
    lastLatencyMs: 0,
    lastError: '',
  };

  constructor() {
    this.endpoint = process.env.TINYFISH_ENDPOINT || TINYFISH_ENDPOINT_DEFAULT;
    this.apiKey = process.env.MINO_API_KEY || process.env.TINYFISH_API_KEY || '';
  }

  public health(): WebIntelProviderHealth {
    const status = deriveHealthStatus(this.stats);
    return {
      provider: 'tinyfish',
      status,
      successCount: this.stats.successCount,
      errorCount: this.stats.errorCount,
      lastRunAt: this.stats.lastRunAt,
      lastLatencyMs: this.stats.lastLatencyMs,
      lastError: this.stats.lastError,
      capacity: 'batch-run-sse',
    };
  }

  public async runGoalBatch(
    requests: WebIntelGoalRequest[],
    options: WebIntelBatchOptions = {},
  ): Promise<WebIntelGoalResult[]> {
    if (requests.length === 0) return [];

    const maxConcurrency = Math.max(1, Math.floor(options.maxConcurrency ?? 4));
    const queueIndex = { value: 0 };
    const results: WebIntelGoalResult[] = new Array(requests.length);

    const workers = Array.from({ length: Math.min(maxConcurrency, requests.length) }, async () => {
      while (true) {
        const idx = queueIndex.value;
        queueIndex.value += 1;
        if (idx >= requests.length) return;
        const request = requests[idx];
        if (!request) continue;
        results[idx] = await this.runGoal(request, options);
      }
    });

    await Promise.all(workers);
    await this.persistHealth().catch(() => {});
    return results;
  }

  private async runGoal(
    request: WebIntelGoalRequest,
    options: WebIntelBatchOptions,
  ): Promise<WebIntelGoalResult> {
    const startedAtMs = Date.now();
    const startedAt = new Date(startedAtMs).toISOString();

    if (!this.apiKey) {
      const result: WebIntelGoalResult = {
        requestId: request.requestId,
        status: 'skipped',
        startedAt,
        durationMs: Date.now() - startedAtMs,
        rawFinalPayload: null,
        normalizedEvents: [],
        error: 'TinyFish API key is not configured',
      };
      this.recordError(result.error, result.durationMs);
      return result;
    }

    const timeoutMs = Math.max(1_000, Math.floor(request.timeoutMs ?? options.timeoutMs ?? 20_000));
    const maxRetries = Math.max(0, Math.floor(options.maxRetries ?? 2));

    let attempt = 0;
    while (attempt <= maxRetries) {
      try {
        const response = await fetch(this.endpoint, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'text/event-stream, application/json',
            'User-Agent': CHROME_UA,
            'X-API-Key': this.apiKey,
          },
          body: JSON.stringify({
            url: request.url,
            goal: request.goal,
            locale: request.locale || 'en',
            expected_schema: request.expectedSchema ?? undefined,
            metadata: request.metadata ?? undefined,
          }),
          signal: AbortSignal.timeout(timeoutMs),
        });

        if (!response.ok) {
          throw new Error(`TinyFish HTTP ${response.status}`);
        }

        const rawResponse = await response.text();
        const decodedEntries = parseSseDataEntries(rawResponse).map(decodeSseEntry).filter((entry) => entry !== null);
        const finalPayload = selectFinalPayload(decodedEntries);
        if (finalPayload === null || finalPayload === undefined) {
          const invalidResult: WebIntelGoalResult = {
            requestId: request.requestId,
            status: 'invalid_payload',
            startedAt,
            durationMs: Date.now() - startedAtMs,
            rawFinalPayload: null,
            normalizedEvents: [],
            error: 'TinyFish returned no final SSE payload',
          };
          this.recordError(invalidResult.error, invalidResult.durationMs);
          return invalidResult;
        }

        const normalizedEvents = await this.normalizeEvents(request, finalPayload);
        const result: WebIntelGoalResult = {
          requestId: request.requestId,
          status: 'success',
          startedAt,
          durationMs: Date.now() - startedAtMs,
          rawFinalPayload: finalPayload,
          normalizedEvents,
          error: '',
        };

        this.recordSuccess(result.durationMs);
        return result;
      } catch (error) {
        const isLastAttempt = attempt >= maxRetries;
        if (isLastAttempt) {
          const msg = toErrorMessage(error);
          const result: WebIntelGoalResult = {
            requestId: request.requestId,
            status: /timeout/i.test(msg) ? 'timeout' : 'error',
            startedAt,
            durationMs: Date.now() - startedAtMs,
            rawFinalPayload: null,
            normalizedEvents: [],
            error: msg,
          };
          this.recordError(result.error, result.durationMs);
          return result;
        }

        const delayMs = TINYFISH_RETRY_DELAYS_MS[Math.min(attempt, TINYFISH_RETRY_DELAYS_MS.length - 1)]!;
        const jitterMultiplier = 1 + (Math.random() * TINYFISH_RETRY_JITTER);
        await sleep(Math.round(delayMs * jitterMultiplier));
      }

      attempt += 1;
    }

    const fallback: WebIntelGoalResult = {
      requestId: request.requestId,
      status: 'error',
      startedAt,
      durationMs: Date.now() - startedAtMs,
      rawFinalPayload: null,
      normalizedEvents: [],
      error: 'TinyFish request failed',
    };
    this.recordError(fallback.error, fallback.durationMs);
    return fallback;
  }

  private async normalizeEvents(
    request: WebIntelGoalRequest,
    payload: unknown,
  ): Promise<WebIntelEvent[]> {
    const normalized = request.normalize ? await request.normalize(payload, request) : null;
    const materialized = Array.isArray(normalized) && normalized.length > 0
      ? normalized
      : [{
        id: request.requestId,
        type: request.eventType,
        subjectId: request.subjectId,
        eventTime: nowIso(),
        source: request.url,
        confidence: 0.5,
        freshnessSecs: 0,
        dedupeHash: '',
        payload: isRecord(payload) ? payload : { value: payload as unknown },
      }];

    const withHashes: WebIntelEvent[] = [];
    for (const event of materialized) {
      const payloadSignature = stableStringify(event.payload);
      const dedupeHash = event.dedupeHash || await sha256Hex(
        `${event.type}|${event.subjectId}|${event.source}|${payloadSignature}`,
      );
      withHashes.push({
        ...event,
        dedupeHash,
        id: event.id || dedupeHash.slice(0, 24),
        eventTime: event.eventTime || nowIso(),
      });
    }
    return withHashes;
  }

  private recordSuccess(latencyMs: number): void {
    this.stats.successCount += 1;
    this.stats.lastLatencyMs = latencyMs;
    this.stats.lastRunAt = nowIso();
    this.stats.lastError = '';
  }

  private recordError(message: string, latencyMs: number): void {
    this.stats.errorCount += 1;
    this.stats.lastLatencyMs = latencyMs;
    this.stats.lastRunAt = nowIso();
    this.stats.lastError = message;
  }

  private async persistHealth(): Promise<void> {
    const payload = this.health();
    await runRedisPipeline(
      [['SET', TINYFISH_PROVIDER_HEALTH_KEY, JSON.stringify(payload), 'EX', 86_400]],
      true,
    );
  }
}

let singleton: TinyfishWebIntelProvider | null = null;

export function getTinyfishProvider(): TinyfishWebIntelProvider {
  if (!singleton) singleton = new TinyfishWebIntelProvider();
  return singleton;
}
