import { sha256Hex } from '../../_shared/hash';
import { getCachedJson, runRedisPipeline, setCachedJson } from '../../_shared/redis';
import {
  TINYFISH_CHOKEPOINT_PREFIX,
  TINYFISH_EVENT_PREFIX,
  TINYFISH_GROUNDING_PREFIX,
  TINYFISH_LAST_PREFETCH_KEY,
  TINYFISH_NEWS_PREFIX,
  TINYFISH_PREFETCH_CHOKEPOINT_LEASE_KEY,
  TINYFISH_PREFETCH_NEWS_LEASE_KEY,
  TINYFISH_RUN_PREFIX,
  TINYFISH_SETTINGS_KEY,
  TINYFISH_SHADOW_DIFF_PREFIX,
} from './constants';
import { buildTinyfishRuntimeSettings, type TinyfishSettingsPatch } from './settings';
import { getTinyfishProvider } from './tinyfish-provider';
import type {
  TinyfishMode,
  TinyfishRuntimeSettings,
  WebIntelEvent,
  WebIntelGoalRequest,
} from './types';

export interface SignalDiagnostics {
  mode: TinyfishMode;
  providerStatus: string;
  fallbackUsed: boolean;
  staleData: boolean;
  reason: string;
}

export interface GroundingEvidence {
  statement: string;
  source: string;
  sourceUrl: string;
  observedAt: string;
  confidence: number;
  quoteSpans: string[];
}

export interface GroundingVerification {
  status: 'skipped' | 'not_triggered' | 'verified' | 'unverified' | 'error';
  confidenceDelta: number;
  evidenceCount: number;
  topEvidence: GroundingEvidence[];
  diagnostics: SignalDiagnostics;
  riskScore: number;
  confidence: number;
}

export interface OfficialQueueObservation {
  status: 'ok' | 'unknown';
  vesselCount: number;
  avgWaitHours: number;
  restrictionSummary: string;
  observedAt: string;
  sourceUrl: string;
  confidence: number;
}

export interface NewsDeepExtract {
  status: 'ok' | 'unknown';
  fullTextAvailable: boolean;
  infraDamageMentioned: boolean;
  coordinates: Array<{ latitude: number; longitude: number }>;
  entities: string[];
  extractedAt: string;
  confidence: number;
  summary: string;
}

export interface CriticalNewsInput {
  title: string;
  link: string;
  source: string;
  threatLevel: string;
}

export interface ChokepointPrefetchInput {
  chokepointId: string;
  chokepointName: string;
  sourceUrl: string;
}

interface TinyfishRequestOptions {
  preferLive?: boolean;
}

interface CachedGroundingPayload {
  fetchedAt: number;
  status: GroundingVerification['status'];
  confidenceDelta: number;
  evidence: GroundingEvidence[];
}

interface CachedChokepointPayload {
  fetchedAt: number;
  observation: OfficialQueueObservation;
}

interface CachedNewsPayload {
  fetchedAt: number;
  deepExtract: NewsDeepExtract;
}

let settingsCache: { expiresAt: number; value: TinyfishRuntimeSettings } | null = null;

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === 'object' && !Array.isArray(value);
}

function toIso(value: unknown): string {
  if (typeof value === 'string') {
    const parsed = Date.parse(value);
    if (Number.isFinite(parsed)) return new Date(parsed).toISOString();
  }
  if (typeof value === 'number' && Number.isFinite(value)) {
    return new Date(value).toISOString();
  }
  return new Date().toISOString();
}

function toNumber(value: unknown, fallback = 0): number {
  const numeric = typeof value === 'number' ? value : Number(value);
  return Number.isFinite(numeric) ? numeric : fallback;
}

function toBoolean(value: unknown, fallback = false): boolean {
  if (typeof value === 'boolean') return value;
  if (typeof value === 'string') {
    if (value.toLowerCase() === 'true') return true;
    if (value.toLowerCase() === 'false') return false;
  }
  return fallback;
}

function clamp01(value: number): number {
  return Math.max(0, Math.min(1, value));
}

function normalizeStringArray(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value
    .map((entry) => (typeof entry === 'string' ? entry.trim() : ''))
    .filter((entry) => entry.length > 0);
}

function nowIso(): string {
  return new Date().toISOString();
}

function chunkArray<T>(items: T[], size: number): T[][] {
  const chunkSize = Math.max(1, Math.floor(size));
  const chunks: T[][] = [];
  for (let i = 0; i < items.length; i += chunkSize) {
    chunks.push(items.slice(i, i + chunkSize));
  }
  return chunks;
}

function extractGroundingRows(payload: unknown): Record<string, unknown>[] {
  if (Array.isArray(payload)) {
    return payload.filter((entry): entry is Record<string, unknown> => isRecord(entry));
  }
  if (isRecord(payload)) {
    const nested = payload.evidence ?? payload.items ?? payload.findings ?? payload.results;
    if (Array.isArray(nested)) {
      return nested.filter((entry): entry is Record<string, unknown> => isRecord(entry));
    }
    return [payload];
  }
  return [];
}

function extractGroundingEvidence(payload: unknown): GroundingEvidence[] {
  const rows = extractGroundingRows(payload);
  return rows
    .map((row) => ({
      statement: String(row.statement ?? row.finding ?? row.claim ?? row.summary ?? '').trim(),
      source: String(row.source ?? row.publisher ?? row.outlet ?? 'unknown').trim(),
      sourceUrl: String(row.source_url ?? row.sourceUrl ?? row.url ?? '').trim(),
      observedAt: toIso(row.observed_at ?? row.observedAt ?? row.timestamp ?? Date.now()),
      confidence: clamp01(toNumber(row.confidence, 0.5)),
      quoteSpans: normalizeStringArray(row.quote_spans ?? row.quoteSpans),
    }))
    .filter((entry) => entry.statement.length > 0);
}

function estimateRiskAndConfidence(query: string, geoContext: string): { riskScore: number; confidence: number } {
  const text = `${query} ${geoContext}`.toLowerCase();
  const highRiskTokens = [
    'port closure',
    'blockade',
    'military',
    'airstrike',
    'missile',
    'war',
    'terror',
    'sanction',
    'infrastructure damage',
    'explosion',
    'pipeline',
  ];
  const lowCertaintyTokens = ['unconfirmed', 'reportedly', 'rumor', 'possible', 'likely', 'might', 'may'];
  const riskHits = highRiskTokens.reduce((count, token) => count + (text.includes(token) ? 1 : 0), 0);
  const uncertaintyHits = lowCertaintyTokens.reduce((count, token) => count + (text.includes(token) ? 1 : 0), 0);

  const riskScore = clamp01(0.35 + (riskHits * 0.12));
  const confidence = clamp01(0.78 - (uncertaintyHits * 0.08) - Math.min(0.25, riskHits * 0.03));
  return { riskScore, confidence };
}

function normalizeCoordinates(value: unknown): Array<{ latitude: number; longitude: number }> {
  if (!Array.isArray(value)) return [];
  const result: Array<{ latitude: number; longitude: number }> = [];
  for (const entry of value) {
    if (!isRecord(entry)) continue;
    const latitude = toNumber(entry.latitude ?? entry.lat, Number.NaN);
    const longitude = toNumber(entry.longitude ?? entry.lon ?? entry.lng, Number.NaN);
    if (Number.isFinite(latitude) && Number.isFinite(longitude)) {
      result.push({ latitude, longitude });
    }
  }
  return result;
}

function parseChokepointObservation(
  payload: unknown,
  sourceUrl: string,
): OfficialQueueObservation | null {
  if (!isRecord(payload)) return null;
  const vesselCount = Math.max(0, Math.round(toNumber(payload.vessel_count ?? payload.vesselCount ?? payload.queue_vessels, Number.NaN)));
  const avgWaitHours = Math.max(0, toNumber(payload.avg_wait_hours ?? payload.avgWaitHours ?? payload.wait_hours, Number.NaN));
  const restrictionSummary = String(
    payload.restriction_summary
    ?? payload.restrictionSummary
    ?? payload.status_summary
    ?? payload.note
    ?? '',
  ).trim();
  const observedAt = toIso(payload.observed_at ?? payload.observedAt ?? payload.timestamp ?? Date.now());
  const confidence = clamp01(toNumber(payload.confidence, 0.5));

  if (!Number.isFinite(vesselCount) && !Number.isFinite(avgWaitHours) && restrictionSummary.length === 0) {
    return null;
  }

  return {
    status: 'ok',
    vesselCount: Number.isFinite(vesselCount) ? vesselCount : 0,
    avgWaitHours: Number.isFinite(avgWaitHours) ? avgWaitHours : 0,
    restrictionSummary,
    observedAt,
    sourceUrl,
    confidence,
  };
}

function parseNewsDeepExtract(payload: unknown): NewsDeepExtract | null {
  if (!isRecord(payload)) return null;
  return {
    status: 'ok',
    fullTextAvailable: toBoolean(payload.full_text_available ?? payload.fullTextAvailable, false),
    infraDamageMentioned: toBoolean(payload.infra_damage_mentioned ?? payload.infraDamageMentioned, false),
    coordinates: normalizeCoordinates(payload.coordinates),
    entities: normalizeStringArray(payload.entities),
    extractedAt: toIso(payload.extracted_at ?? payload.extractedAt ?? Date.now()),
    confidence: clamp01(toNumber(payload.confidence, 0.5)),
    summary: String(payload.summary ?? payload.excerpt ?? '').trim(),
  };
}

function buildDiagnostics(
  mode: TinyfishMode,
  providerStatus: string,
  fallbackUsed: boolean,
  staleData: boolean,
  reason: string,
): SignalDiagnostics {
  return {
    mode,
    providerStatus,
    fallbackUsed,
    staleData,
    reason,
  };
}

async function getSettingsOverrides(): Promise<TinyfishSettingsPatch | null> {
  try {
    const raw = await getCachedJson(TINYFISH_SETTINGS_KEY, true);
    if (!isRecord(raw)) return null;
    return raw as TinyfishSettingsPatch;
  } catch {
    return null;
  }
}

export function invalidateTinyfishSettingsCache(): void {
  settingsCache = null;
}

export async function getTinyfishRuntimeSettings(forceRefresh = false): Promise<TinyfishRuntimeSettings> {
  const now = Date.now();
  if (!forceRefresh && settingsCache && settingsCache.expiresAt > now) {
    return settingsCache.value;
  }

  const overrides = await getSettingsOverrides();
  const value = buildTinyfishRuntimeSettings(overrides);
  settingsCache = {
    value,
    expiresAt: now + 30_000,
  };
  return value;
}

async function persistEvents(events: WebIntelEvent[], ttlSeconds: number): Promise<void> {
  if (events.length === 0) return;
  await Promise.all(events.map((event) => {
    const key = `${TINYFISH_EVENT_PREFIX}:${event.dedupeHash}`;
    return setCachedJson(key, event, ttlSeconds);
  }));
}

async function persistRunSummary(
  domain: string,
  payload: Record<string, unknown>,
  ttlSeconds = 7 * 24 * 3600,
  options: { markAsPrefetch?: boolean } = {},
): Promise<void> {
  const runId = `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
  const runKey = `${TINYFISH_RUN_PREFIX}:${runId}`;
  const runPayload = {
    runId,
    domain,
    createdAt: nowIso(),
    ...payload,
  };
  const commands: Array<Array<string | number>> = [
    ['SET', runKey, JSON.stringify(runPayload), 'EX', ttlSeconds],
  ];
  if (options.markAsPrefetch) {
    commands.push(['SET', TINYFISH_LAST_PREFETCH_KEY, JSON.stringify(runPayload), 'EX', ttlSeconds]);
  }
  await runRedisPipeline(commands, true);
}

async function acquirePrefetchLease(key: string, intervalSeconds: number): Promise<boolean> {
  const ttl = Math.max(30, Math.floor(intervalSeconds));
  const leaseValue = `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
  const [result] = await runRedisPipeline(
    [['SET', key, leaseValue, 'NX', 'EX', ttl]],
    true,
  );
  return result?.result === 'OK';
}

export async function persistShadowDiff(
  requestId: string,
  payload: Record<string, unknown>,
): Promise<void> {
  const key = `${TINYFISH_SHADOW_DIFF_PREFIX}:${requestId}`;
  await setCachedJson(key, {
    requestId,
    createdAt: nowIso(),
    ...payload,
  }, 14 * 24 * 3600);
}

export async function verifyGroundingWithTinyfish(input: {
  requestId: string;
  query: string;
  geoContext: string;
}): Promise<GroundingVerification> {
  const settings = await getTinyfishRuntimeSettings();
  const provider = getTinyfishProvider();
  const providerHealth = provider.health();
  const { riskScore, confidence } = estimateRiskAndConfidence(input.query, input.geoContext);

  if (settings.mode === 'off') {
    return {
      status: 'skipped',
      confidenceDelta: 0,
      evidenceCount: 0,
      topEvidence: [],
      diagnostics: buildDiagnostics(settings.mode, providerHealth.status, false, false, 'mode_off'),
      riskScore,
      confidence,
    };
  }

  if (riskScore < settings.riskTriggerThreshold || confidence >= settings.confidenceTriggerThreshold) {
    return {
      status: 'not_triggered',
      confidenceDelta: 0,
      evidenceCount: 0,
      topEvidence: [],
      diagnostics: buildDiagnostics(settings.mode, providerHealth.status, false, false, 'threshold_not_met'),
      riskScore,
      confidence,
    };
  }

  const hash = await sha256Hex(`${input.query.trim().toLowerCase()}|${input.geoContext.trim().toLowerCase()}`);
  const cacheKey = `${TINYFISH_GROUNDING_PREFIX}:${hash.slice(0, 24)}`;
  const cacheTtlSeconds = Math.round(settings.groundingLookbackHours * 3600);
  const maxAgeMs = settings.groundingLookbackHours * 60 * 60 * 1000;

  const cached = await getCachedJson(cacheKey) as CachedGroundingPayload | null;
  if (cached && Date.now() - cached.fetchedAt <= maxAgeMs) {
    return {
      status: cached.status,
      confidenceDelta: cached.confidenceDelta,
      evidenceCount: cached.evidence.length,
      topEvidence: cached.evidence.slice(0, 3),
      diagnostics: buildDiagnostics(settings.mode, provider.health().status, false, false, 'cache_hit'),
      riskScore,
      confidence,
    };
  }

  const request: WebIntelGoalRequest = {
    requestId: input.requestId,
    domain: 'intelligence_grounding',
    eventType: 'grounding_evidence',
    subjectId: hash.slice(0, 16),
    url: 'https://www.google.com',
    goal: [
      'Verify this geopolitical claim using current web sources and return JSON.',
      `Query: ${input.query}`,
      `Geo context: ${input.geoContext}`,
      'Output schema: {"evidence":[{"statement":string,"source":string,"source_url":string,"observed_at":ISO8601,"confidence":0..1,"quote_spans":[string]}]}',
    ].join('\n'),
    expectedSchema: {
      evidence: [{
        statement: 'string',
        source: 'string',
        source_url: 'string',
        observed_at: 'string',
        confidence: 'number',
        quote_spans: ['string'],
      }],
    },
    normalize: async (payload, req) => {
      const evidence = extractGroundingEvidence(payload);
      if (evidence.length === 0) return [];
      const nowMs = Date.now();
      return evidence.map((item, idx) => {
        const observedMs = Date.parse(item.observedAt);
        const freshnessSecs = Number.isFinite(observedMs) ? Math.max(0, Math.round((nowMs - observedMs) / 1000)) : 0;
        return {
          id: `${req.requestId}-${idx + 1}`,
          type: 'grounding_evidence',
          subjectId: req.subjectId,
          eventTime: item.observedAt,
          source: item.sourceUrl || item.source,
          confidence: clamp01(item.confidence),
          freshnessSecs,
          dedupeHash: '',
          payload: {
            statement: item.statement,
            source: item.source,
            sourceUrl: item.sourceUrl,
            observedAt: item.observedAt,
            confidence: item.confidence,
            quoteSpans: item.quoteSpans,
          },
        };
      });
    },
  };

  const startedMs = Date.now();
  const [resultRaw] = await provider.runGoalBatch([request], {
    timeoutMs: settings.timeoutSecs * 1000,
    maxRetries: 2,
    maxConcurrency: 1,
  });
  const result = resultRaw ?? {
    requestId: request.requestId,
    status: 'error',
    startedAt: nowIso(),
    durationMs: 0,
    rawFinalPayload: null,
    normalizedEvents: [],
    error: 'TinyFish did not return a result',
  };
  const durationMs = Date.now() - startedMs;

  let verification: GroundingVerification;
  if (result.status === 'success') {
    const evidence = result.normalizedEvents.map((event) => ({
      statement: String(event.payload.statement ?? ''),
      source: String(event.payload.source ?? ''),
      sourceUrl: String(event.payload.sourceUrl ?? ''),
      observedAt: toIso(event.payload.observedAt ?? event.eventTime),
      confidence: clamp01(toNumber(event.payload.confidence, event.confidence)),
      quoteSpans: normalizeStringArray(event.payload.quoteSpans),
    }));
    const avgConfidence = evidence.length === 0
      ? 0
      : (evidence.reduce((sum, entry) => sum + entry.confidence, 0) / evidence.length);
    const confidenceDelta = evidence.length === 0
      ? 0
      : clamp01(Math.min(0.25, 0.05 + (avgConfidence * 0.2) + (Math.min(3, evidence.length) * 0.03)));

    verification = {
      status: evidence.length > 0 ? 'verified' : 'unverified',
      confidenceDelta,
      evidenceCount: evidence.length,
      topEvidence: evidence.slice(0, 3),
      diagnostics: buildDiagnostics(settings.mode, provider.health().status, false, false, evidence.length > 0 ? 'verified' : 'no_evidence'),
      riskScore,
      confidence,
    };

    await setCachedJson(cacheKey, {
      fetchedAt: Date.now(),
      status: verification.status,
      confidenceDelta: verification.confidenceDelta,
      evidence,
    } satisfies CachedGroundingPayload, cacheTtlSeconds);
    await persistEvents(result.normalizedEvents, cacheTtlSeconds);
  } else {
    verification = {
      status: 'error',
      confidenceDelta: 0,
      evidenceCount: 0,
      topEvidence: [],
      diagnostics: buildDiagnostics(settings.mode, provider.health().status, true, false, result.error || result.status),
      riskScore,
      confidence,
    };
  }

  await persistRunSummary('intelligence_grounding', {
    requestId: input.requestId,
    durationMs,
    status: verification.status,
    evidenceCount: verification.evidenceCount,
    providerStatus: provider.health().status,
  }).catch(() => {});

  return verification;
}

export async function getChokepointObservationWithTinyfish(input: {
  chokepointId: string;
  chokepointName: string;
  sourceUrl: string;
}, options: TinyfishRequestOptions = {}): Promise<{ observation: OfficialQueueObservation; diagnostics: SignalDiagnostics }> {
  const preferLive = options.preferLive ?? true;
  const settings = await getTinyfishRuntimeSettings();
  const provider = getTinyfishProvider();
  const providerStatus = provider.health().status;
  const unknown: OfficialQueueObservation = {
    status: 'unknown',
    vesselCount: 0,
    avgWaitHours: 0,
    restrictionSummary: '',
    observedAt: nowIso(),
    sourceUrl: input.sourceUrl,
    confidence: 0,
  };

  if (settings.mode === 'off') {
    return {
      observation: unknown,
      diagnostics: buildDiagnostics(settings.mode, providerStatus, false, false, 'mode_off'),
    };
  }

  const cacheKey = `${TINYFISH_CHOKEPOINT_PREFIX}:${input.chokepointId}`;
  const maxAgeMs = settings.chokepointLookbackMinutes * 60 * 1000;
  const cacheTtlSeconds = Math.round((settings.chokepointLookbackMinutes + 5) * 60);

  const cached = await getCachedJson(cacheKey) as CachedChokepointPayload | null;
  if (cached && Date.now() - cached.fetchedAt <= maxAgeMs) {
    return {
      observation: cached.observation,
      diagnostics: buildDiagnostics(settings.mode, providerStatus, false, false, 'cache_hit'),
    };
  }

  if (!preferLive) {
    if (cached?.observation && settings.failOpen) {
      return {
        observation: cached.observation,
        diagnostics: buildDiagnostics(settings.mode, providerStatus, true, true, 'stale_fallback'),
      };
    }
    return {
      observation: unknown,
      diagnostics: buildDiagnostics(settings.mode, providerStatus, true, false, 'cache_miss_no_live_fetch'),
    };
  }

  const requestId = `chokepoint-${input.chokepointId}-${Date.now()}`;
  const request: WebIntelGoalRequest = {
    requestId,
    domain: 'supply_chain_chokepoint',
    eventType: 'chokepoint_observation',
    subjectId: input.chokepointId,
    url: input.sourceUrl,
    goal: [
      `Extract latest vessel queue for ${input.chokepointName}.`,
      'Return JSON only with fields:',
      '{"vessel_count":number,"avg_wait_hours":number,"restriction_summary":string,"observed_at":ISO8601,"confidence":0..1}',
    ].join('\n'),
    expectedSchema: {
      vessel_count: 'number',
      avg_wait_hours: 'number',
      restriction_summary: 'string',
      observed_at: 'string',
      confidence: 'number',
    },
    normalize: async (payload, req) => {
      const observation = parseChokepointObservation(payload, req.url);
      if (!observation) return [];
      return [{
        id: req.requestId,
        type: 'chokepoint_observation',
        subjectId: req.subjectId,
        eventTime: observation.observedAt,
        source: req.url,
        confidence: observation.confidence,
        freshnessSecs: 0,
        dedupeHash: '',
        payload: observation as unknown as Record<string, unknown>,
      }];
    },
  };

  const startedMs = Date.now();
  const [resultRaw] = await provider.runGoalBatch([request], {
    timeoutMs: settings.timeoutSecs * 1000,
    maxRetries: 2,
    maxConcurrency: 1,
  });
  const result = resultRaw ?? {
    requestId,
    status: 'error',
    startedAt: nowIso(),
    durationMs: 0,
    rawFinalPayload: null,
    normalizedEvents: [],
    error: 'TinyFish did not return a result',
  };
  const durationMs = Date.now() - startedMs;

  if (result.status === 'success' && result.normalizedEvents.length > 0) {
    const first = result.normalizedEvents[0];
    if (!first) {
      return {
        observation: unknown,
        diagnostics: buildDiagnostics(settings.mode, provider.health().status, true, false, 'missing_event_payload'),
      };
    }
    const observation = parseChokepointObservation(first.payload, input.sourceUrl);
    if (observation && observation.confidence >= settings.minObservationConfidence) {
      await setCachedJson(cacheKey, {
        fetchedAt: Date.now(),
        observation,
      } satisfies CachedChokepointPayload, cacheTtlSeconds);
      await persistEvents(result.normalizedEvents, cacheTtlSeconds);
      await persistRunSummary('supply_chain_chokepoint', {
        chokepointId: input.chokepointId,
        durationMs,
        status: 'ok',
        confidence: observation.confidence,
      }).catch(() => {});
      return {
        observation,
        diagnostics: buildDiagnostics(settings.mode, provider.health().status, false, false, 'live_fetch'),
      };
    }
  }

  const staleFallback = cached?.observation;
  await persistRunSummary('supply_chain_chokepoint', {
    chokepointId: input.chokepointId,
    durationMs,
    status: 'fallback',
    error: result.error || result.status,
  }).catch(() => {});

  if (staleFallback && settings.failOpen) {
    return {
      observation: staleFallback,
      diagnostics: buildDiagnostics(settings.mode, provider.health().status, true, true, 'stale_fallback'),
    };
  }

  return {
    observation: unknown,
    diagnostics: buildDiagnostics(settings.mode, provider.health().status, true, false, result.error || result.status),
  };
}

export async function getNewsDeepExtractWithTinyfish(item: CriticalNewsInput, options: TinyfishRequestOptions = {}): Promise<{
  deepExtract: NewsDeepExtract;
  diagnostics: SignalDiagnostics;
}> {
  const preferLive = options.preferLive ?? true;
  const settings = await getTinyfishRuntimeSettings();
  const provider = getTinyfishProvider();
  const providerStatus = provider.health().status;
  const unknown: NewsDeepExtract = {
    status: 'unknown',
    fullTextAvailable: false,
    infraDamageMentioned: false,
    coordinates: [],
    entities: [],
    extractedAt: nowIso(),
    confidence: 0,
    summary: '',
  };

  if (settings.mode === 'off') {
    return {
      deepExtract: unknown,
      diagnostics: buildDiagnostics(settings.mode, providerStatus, false, false, 'mode_off'),
    };
  }

  if (item.threatLevel !== 'THREAT_LEVEL_CRITICAL') {
    return {
      deepExtract: unknown,
      diagnostics: buildDiagnostics(settings.mode, providerStatus, false, false, 'not_critical'),
    };
  }

  const articleHash = (await sha256Hex(item.link.toLowerCase().trim())).slice(0, 24);
  const cacheKey = `${TINYFISH_NEWS_PREFIX}:${articleHash}`;
  const maxAgeMs = settings.newsDeepExtractLookbackHours * 60 * 60 * 1000;
  const cacheTtlSeconds = Math.round(settings.newsDeepExtractLookbackHours * 3600);

  const cached = await getCachedJson(cacheKey) as CachedNewsPayload | null;
  if (cached && Date.now() - cached.fetchedAt <= maxAgeMs) {
    return {
      deepExtract: cached.deepExtract,
      diagnostics: buildDiagnostics(settings.mode, providerStatus, false, false, 'cache_hit'),
    };
  }

  if (!preferLive) {
    if (cached?.deepExtract && settings.failOpen) {
      return {
        deepExtract: cached.deepExtract,
        diagnostics: buildDiagnostics(settings.mode, providerStatus, true, true, 'stale_fallback'),
      };
    }
    return {
      deepExtract: unknown,
      diagnostics: buildDiagnostics(settings.mode, providerStatus, true, false, 'cache_miss_no_live_fetch'),
    };
  }

  const request: WebIntelGoalRequest = {
    requestId: `news-${articleHash}-${Date.now()}`,
    domain: 'news_deep_extract',
    eventType: 'news_deep_extract',
    subjectId: articleHash,
    url: item.link,
    goal: [
      'Read this article and return structured infrastructure-impact extraction.',
      `Title: ${item.title}`,
      'Return JSON only:',
      '{"full_text_available":boolean,"infra_damage_mentioned":boolean,"coordinates":[{"latitude":number,"longitude":number}],"entities":[string],"summary":string,"extracted_at":ISO8601,"confidence":0..1}',
    ].join('\n'),
    expectedSchema: {
      full_text_available: 'boolean',
      infra_damage_mentioned: 'boolean',
      coordinates: [{ latitude: 'number', longitude: 'number' }],
      entities: ['string'],
      summary: 'string',
      extracted_at: 'string',
      confidence: 'number',
    },
    normalize: async (payload, req) => {
      const deepExtract = parseNewsDeepExtract(payload);
      if (!deepExtract) return [];
      return [{
        id: req.requestId,
        type: 'news_deep_extract',
        subjectId: req.subjectId,
        eventTime: deepExtract.extractedAt,
        source: req.url,
        confidence: deepExtract.confidence,
        freshnessSecs: 0,
        dedupeHash: '',
        payload: deepExtract as unknown as Record<string, unknown>,
      }];
    },
  };

  const startedMs = Date.now();
  const [resultRaw] = await provider.runGoalBatch([request], {
    timeoutMs: settings.timeoutSecs * 1000,
    maxRetries: 2,
    maxConcurrency: 1,
  });
  const result = resultRaw ?? {
    requestId: request.requestId,
    status: 'error',
    startedAt: nowIso(),
    durationMs: 0,
    rawFinalPayload: null,
    normalizedEvents: [],
    error: 'TinyFish did not return a result',
  };
  const durationMs = Date.now() - startedMs;

  if (result.status === 'success' && result.normalizedEvents.length > 0) {
    const firstEvent = result.normalizedEvents[0];
    const deepExtract = firstEvent ? parseNewsDeepExtract(firstEvent.payload) : null;
    if (deepExtract) {
      await setCachedJson(cacheKey, {
        fetchedAt: Date.now(),
        deepExtract,
      } satisfies CachedNewsPayload, cacheTtlSeconds);
      await persistEvents(result.normalizedEvents, cacheTtlSeconds);
      await persistRunSummary('news_deep_extract', {
        articleHash,
        durationMs,
        status: 'ok',
        confidence: deepExtract.confidence,
      }).catch(() => {});
      return {
        deepExtract,
        diagnostics: buildDiagnostics(settings.mode, provider.health().status, false, false, 'live_fetch'),
      };
    }
  }

  await persistRunSummary('news_deep_extract', {
    articleHash,
    durationMs,
    status: 'fallback',
    error: result.error || result.status,
  }).catch(() => {});

  if (cached?.deepExtract && settings.failOpen) {
    return {
      deepExtract: cached.deepExtract,
      diagnostics: buildDiagnostics(settings.mode, provider.health().status, true, true, 'stale_fallback'),
    };
  }

  return {
    deepExtract: unknown,
    diagnostics: buildDiagnostics(settings.mode, provider.health().status, true, false, result.error || result.status),
  };
}

export async function prefetchChokepointObservations(
  targets: ChokepointPrefetchInput[],
): Promise<{ scheduled: boolean; processed: number; successCount: number; fallbackCount: number }> {
  const settings = await getTinyfishRuntimeSettings();
  if (settings.mode === 'off' || targets.length === 0) {
    return { scheduled: false, processed: 0, successCount: 0, fallbackCount: 0 };
  }

  const leaseAcquired = await acquirePrefetchLease(
    TINYFISH_PREFETCH_CHOKEPOINT_LEASE_KEY,
    settings.chokepointLookbackMinutes * 60,
  );
  if (!leaseAcquired) {
    return { scheduled: false, processed: 0, successCount: 0, fallbackCount: 0 };
  }

  const deduped = Array.from(new Map(
    targets
      .filter((target) => target.sourceUrl.length > 0)
      .map((target) => [`${target.chokepointId}:${target.sourceUrl}`, target] as const),
  ).values());

  const startedMs = Date.now();
  let successCount = 0;
  let fallbackCount = 0;
  const batchSize = Math.max(1, Math.min(settings.batchSize, settings.maxConcurrency));

  for (const batch of chunkArray(deduped, batchSize)) {
    const settled = await Promise.allSettled(batch.map((target) => getChokepointObservationWithTinyfish(target, {
      preferLive: true,
    })));
    for (const result of settled) {
      if (result.status === 'fulfilled' && result.value.observation.status === 'ok') {
        successCount += 1;
      } else {
        fallbackCount += 1;
      }
    }
  }

  await persistRunSummary('supply_chain_chokepoint_prefetch', {
    status: 'completed',
    symbolsCount: deduped.length,
    successCount,
    fallbackCount,
    durationMs: Date.now() - startedMs,
  }, undefined, { markAsPrefetch: true }).catch(() => {});

  return {
    scheduled: true,
    processed: deduped.length,
    successCount,
    fallbackCount,
  };
}

export async function prefetchCriticalNewsDeepExtracts(
  items: CriticalNewsInput[],
): Promise<{ scheduled: boolean; processed: number; successCount: number; fallbackCount: number }> {
  const settings = await getTinyfishRuntimeSettings();
  if (settings.mode === 'off' || items.length === 0) {
    return { scheduled: false, processed: 0, successCount: 0, fallbackCount: 0 };
  }

  const leaseAcquired = await acquirePrefetchLease(
    TINYFISH_PREFETCH_NEWS_LEASE_KEY,
    5 * 60,
  );
  if (!leaseAcquired) {
    return { scheduled: false, processed: 0, successCount: 0, fallbackCount: 0 };
  }

  const deduped = Array.from(new Map(
    items
      .filter((item) => item.threatLevel === 'THREAT_LEVEL_CRITICAL' && item.link.length > 0)
      .map((item) => [item.link, item] as const),
  ).values());

  const startedMs = Date.now();
  let successCount = 0;
  let fallbackCount = 0;
  const batchSize = Math.max(1, Math.min(settings.batchSize, settings.maxConcurrency));

  for (const batch of chunkArray(deduped, batchSize)) {
    const settled = await Promise.allSettled(batch.map((item) => getNewsDeepExtractWithTinyfish(item, {
      preferLive: true,
    })));
    for (const result of settled) {
      if (result.status === 'fulfilled' && result.value.deepExtract.status === 'ok') {
        successCount += 1;
      } else {
        fallbackCount += 1;
      }
    }
  }

  await persistRunSummary('news_deep_extract_prefetch', {
    status: 'completed',
    symbolsCount: deduped.length,
    successCount,
    fallbackCount,
    durationMs: Date.now() - startedMs,
  }, undefined, { markAsPrefetch: true }).catch(() => {});

  return {
    scheduled: true,
    processed: deduped.length,
    successCount,
    fallbackCount,
  };
}
