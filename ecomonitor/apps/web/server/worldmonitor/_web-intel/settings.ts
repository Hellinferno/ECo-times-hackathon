import type { TinyfishRuntimeSettings, TinyfishMode } from './types';
import {
  TINYFISH_DEFAULT_BATCH_SIZE,
  TINYFISH_DEFAULT_CHOKEPOINT_LOOKBACK_MINUTES,
  TINYFISH_DEFAULT_CONFIDENCE_TRIGGER_THRESHOLD,
  TINYFISH_DEFAULT_FAIL_OPEN,
  TINYFISH_DEFAULT_GROUNDING_LOOKBACK_HOURS,
  TINYFISH_DEFAULT_MAX_CONCURRENCY,
  TINYFISH_DEFAULT_MIN_OBSERVATION_CONFIDENCE,
  TINYFISH_DEFAULT_MODE,
  TINYFISH_DEFAULT_NEWS_LOOKBACK_HOURS,
  TINYFISH_DEFAULT_RISK_TRIGGER_THRESHOLD,
  TINYFISH_DEFAULT_TIMEOUT_SECS,
} from './constants';

const VALID_MODES = new Set<TinyfishMode>(['off', 'shadow', 'active']);

function asFiniteNumber(value: unknown, fallback: number, min?: number, max?: number): number {
  const numeric = typeof value === 'number' ? value : Number(value);
  if (!Number.isFinite(numeric)) return fallback;
  let constrained = numeric;
  if (typeof min === 'number') constrained = Math.max(min, constrained);
  if (typeof max === 'number') constrained = Math.min(max, constrained);
  return constrained;
}

function asBoolean(value: unknown, fallback: boolean): boolean {
  if (typeof value === 'boolean') return value;
  if (typeof value === 'string') {
    if (value.toLowerCase() === 'true') return true;
    if (value.toLowerCase() === 'false') return false;
  }
  return fallback;
}

function asMode(value: unknown, fallback: TinyfishMode): TinyfishMode {
  if (typeof value !== 'string') return fallback;
  return VALID_MODES.has(value as TinyfishMode) ? (value as TinyfishMode) : fallback;
}

export interface TinyfishSettingsPatch {
  tinyfish_mode?: unknown;
  tinyfish_timeout_secs?: unknown;
  tinyfish_max_concurrency?: unknown;
  tinyfish_batch_size?: unknown;
  tinyfish_fail_open?: unknown;
  grounding_lookback_hours?: unknown;
  chokepoint_lookback_minutes?: unknown;
  news_deep_extract_lookback_hours?: unknown;
  risk_trigger_threshold?: unknown;
  confidence_trigger_threshold?: unknown;
  min_observation_confidence?: unknown;
}

function fromEnv(): TinyfishSettingsPatch {
  return {
    tinyfish_mode: process.env.TINYFISH_MODE,
    tinyfish_timeout_secs: process.env.TINYFISH_TIMEOUT_SECS,
    tinyfish_max_concurrency: process.env.TINYFISH_MAX_CONCURRENCY,
    tinyfish_batch_size: process.env.TINYFISH_BATCH_SIZE,
    tinyfish_fail_open: process.env.TINYFISH_FAIL_OPEN,
    grounding_lookback_hours: process.env.GROUNDING_LOOKBACK_HOURS,
    chokepoint_lookback_minutes: process.env.CHOKEPOINT_LOOKBACK_MINUTES,
    news_deep_extract_lookback_hours: process.env.NEWS_DEEP_EXTRACT_LOOKBACK_HOURS,
    risk_trigger_threshold: process.env.TINYFISH_RISK_TRIGGER_THRESHOLD,
    confidence_trigger_threshold: process.env.TINYFISH_CONFIDENCE_TRIGGER_THRESHOLD,
    min_observation_confidence: process.env.TINYFISH_MIN_OBSERVATION_CONFIDENCE,
  };
}

export function buildTinyfishRuntimeSettings(overrides?: TinyfishSettingsPatch | null): TinyfishRuntimeSettings {
  const base = fromEnv();
  const merged: TinyfishSettingsPatch = {
    ...base,
    ...(overrides ?? {}),
  };

  return {
    mode: asMode(merged.tinyfish_mode, TINYFISH_DEFAULT_MODE as TinyfishMode),
    timeoutSecs: asFiniteNumber(merged.tinyfish_timeout_secs, TINYFISH_DEFAULT_TIMEOUT_SECS, 1, 120),
    maxConcurrency: Math.floor(asFiniteNumber(merged.tinyfish_max_concurrency, TINYFISH_DEFAULT_MAX_CONCURRENCY, 1, 1000)),
    batchSize: Math.floor(asFiniteNumber(merged.tinyfish_batch_size, TINYFISH_DEFAULT_BATCH_SIZE, 1, 1000)),
    failOpen: asBoolean(merged.tinyfish_fail_open, TINYFISH_DEFAULT_FAIL_OPEN),
    groundingLookbackHours: asFiniteNumber(merged.grounding_lookback_hours, TINYFISH_DEFAULT_GROUNDING_LOOKBACK_HOURS, 1, 72),
    chokepointLookbackMinutes: asFiniteNumber(merged.chokepoint_lookback_minutes, TINYFISH_DEFAULT_CHOKEPOINT_LOOKBACK_MINUTES, 5, 720),
    newsDeepExtractLookbackHours: asFiniteNumber(merged.news_deep_extract_lookback_hours, TINYFISH_DEFAULT_NEWS_LOOKBACK_HOURS, 1, 168),
    riskTriggerThreshold: asFiniteNumber(merged.risk_trigger_threshold, TINYFISH_DEFAULT_RISK_TRIGGER_THRESHOLD, 0, 1),
    confidenceTriggerThreshold: asFiniteNumber(merged.confidence_trigger_threshold, TINYFISH_DEFAULT_CONFIDENCE_TRIGGER_THRESHOLD, 0, 1),
    minObservationConfidence: asFiniteNumber(merged.min_observation_confidence, TINYFISH_DEFAULT_MIN_OBSERVATION_CONFIDENCE, 0, 1),
  };
}
