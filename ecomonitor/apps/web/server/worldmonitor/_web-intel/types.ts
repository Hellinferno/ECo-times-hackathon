export type TinyfishMode = 'off' | 'shadow' | 'active';

export type WebIntelDomain =
  | 'intelligence_grounding'
  | 'supply_chain_chokepoint'
  | 'news_deep_extract'
  | 'sanctions_monitor';

export type WebIntelEventType =
  | 'grounding_evidence'
  | 'chokepoint_observation'
  | 'news_deep_extract'
  | 'sanctions_notice';

export interface WebIntelEvent {
  id: string;
  type: WebIntelEventType;
  subjectId: string;
  eventTime: string;
  source: string;
  confidence: number;
  freshnessSecs: number;
  dedupeHash: string;
  payload: Record<string, unknown>;
}

export type WebIntelGoalStatus =
  | 'success'
  | 'timeout'
  | 'error'
  | 'invalid_payload'
  | 'skipped';

export interface WebIntelGoalRequest {
  requestId: string;
  domain: WebIntelDomain;
  eventType: WebIntelEventType;
  subjectId: string;
  url: string;
  goal: string;
  expectedSchema?: Record<string, unknown>;
  locale?: string;
  timeoutMs?: number;
  metadata?: Record<string, unknown>;
  normalize?: (payload: unknown, request: WebIntelGoalRequest) => Promise<WebIntelEvent[] | null> | WebIntelEvent[] | null;
}

export interface WebIntelGoalResult {
  requestId: string;
  status: WebIntelGoalStatus;
  startedAt: string;
  durationMs: number;
  rawFinalPayload: unknown;
  normalizedEvents: WebIntelEvent[];
  error: string;
}

export interface WebIntelBatchOptions {
  timeoutMs?: number;
  maxRetries?: number;
  maxConcurrency?: number;
}

export type ProviderHealthStatus = 'healthy' | 'degraded' | 'down';

export interface WebIntelProviderHealth {
  provider: string;
  status: ProviderHealthStatus;
  successCount: number;
  errorCount: number;
  lastRunAt: string;
  lastLatencyMs: number;
  lastError: string;
  capacity: string;
}

export interface WebIntelProvider {
  runGoalBatch(
    requests: WebIntelGoalRequest[],
    options?: WebIntelBatchOptions,
  ): Promise<WebIntelGoalResult[]>;
  health(): WebIntelProviderHealth;
}

export interface TinyfishRuntimeSettings {
  mode: TinyfishMode;
  timeoutSecs: number;
  maxConcurrency: number;
  batchSize: number;
  failOpen: boolean;
  groundingLookbackHours: number;
  chokepointLookbackMinutes: number;
  newsDeepExtractLookbackHours: number;
  riskTriggerThreshold: number;
  confidenceTriggerThreshold: number;
  minObservationConfidence: number;
}
