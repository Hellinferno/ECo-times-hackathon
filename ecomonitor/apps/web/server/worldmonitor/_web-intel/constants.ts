export const TINYFISH_ENDPOINT_DEFAULT = 'https://mino.ai/v1/automation/run-sse';

export const TINYFISH_SETTINGS_KEY = 'wm:tinyfish:settings:v1';
export const TINYFISH_PROVIDER_HEALTH_KEY = 'wm:tinyfish:provider-health';
export const TINYFISH_LAST_PREFETCH_KEY = 'wm:tinyfish:last-prefetch-metrics';

export const TINYFISH_GROUNDING_PREFIX = 'wm:tinyfish:grounding';
export const TINYFISH_CHOKEPOINT_PREFIX = 'wm:tinyfish:chokepoint';
export const TINYFISH_NEWS_PREFIX = 'wm:tinyfish:news';
export const TINYFISH_EVENT_PREFIX = 'wm:tinyfish:event';
export const TINYFISH_RUN_PREFIX = 'wm:tinyfish:run';
export const TINYFISH_SHADOW_DIFF_PREFIX = 'wm:tinyfish:shadow_diff';
export const TINYFISH_PREFETCH_GROUNDING_LEASE_KEY = 'wm:tinyfish:prefetch:grounding:lease';
export const TINYFISH_PREFETCH_CHOKEPOINT_LEASE_KEY = 'wm:tinyfish:prefetch:chokepoint:lease';
export const TINYFISH_PREFETCH_NEWS_LEASE_KEY = 'wm:tinyfish:prefetch:news:lease';

export const TINYFISH_DEFAULT_TIMEOUT_SECS = 20;
export const TINYFISH_DEFAULT_MAX_CONCURRENCY = 20;
export const TINYFISH_DEFAULT_BATCH_SIZE = 20;
export const TINYFISH_DEFAULT_FAIL_OPEN = true;
export const TINYFISH_DEFAULT_MODE = 'shadow';

export const TINYFISH_DEFAULT_GROUNDING_LOOKBACK_HOURS = 6;
export const TINYFISH_DEFAULT_CHOKEPOINT_LOOKBACK_MINUTES = 60;
export const TINYFISH_DEFAULT_NEWS_LOOKBACK_HOURS = 24;

export const TINYFISH_DEFAULT_RISK_TRIGGER_THRESHOLD = 0.7;
export const TINYFISH_DEFAULT_CONFIDENCE_TRIGGER_THRESHOLD = 0.65;
export const TINYFISH_DEFAULT_MIN_OBSERVATION_CONFIDENCE = 0.5;

export const TINYFISH_RETRY_DELAYS_MS = [500, 1500] as const;
export const TINYFISH_RETRY_JITTER = 0.2;
