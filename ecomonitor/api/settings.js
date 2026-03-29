import { getCorsHeaders, isDisallowedOrigin } from './_cors.js';
import { validateApiKey } from './_api-key.js';
import { jsonResponse } from './_json-response.js';
import { readJsonFromUpstash } from './_upstash-json.js';

export const config = { runtime: 'edge' };

const SETTINGS_KEY = 'wm:tinyfish:settings:v1';
const SETTINGS_TTL_SECONDS = 365 * 24 * 60 * 60;

const DEFAULTS = {
  tinyfish_mode: 'shadow',
  tinyfish_timeout_secs: 20,
  tinyfish_max_concurrency: 20,
  tinyfish_batch_size: 20,
  tinyfish_fail_open: true,
  grounding_lookback_hours: 6,
  chokepoint_lookback_minutes: 60,
  news_deep_extract_lookback_hours: 24,
  risk_trigger_threshold: 0.7,
  confidence_trigger_threshold: 0.65,
  min_observation_confidence: 0.5,
};

const ALLOWED_KEYS = new Set(Object.keys(DEFAULTS));
const VALID_MODES = new Set(['off', 'shadow', 'active']);

function asFiniteNumber(value, fallback, min, max) {
  const numeric = typeof value === 'number' ? value : Number(value);
  if (!Number.isFinite(numeric)) return fallback;
  let constrained = numeric;
  if (typeof min === 'number') constrained = Math.max(min, constrained);
  if (typeof max === 'number') constrained = Math.min(max, constrained);
  return constrained;
}

function asBoolean(value, fallback) {
  if (typeof value === 'boolean') return value;
  if (typeof value === 'string') {
    if (value.toLowerCase() === 'true') return true;
    if (value.toLowerCase() === 'false') return false;
  }
  return fallback;
}

function sanitizeSettings(input) {
  const candidate = (input && typeof input === 'object') ? input : {};
  const mode = typeof candidate.tinyfish_mode === 'string' ? candidate.tinyfish_mode : DEFAULTS.tinyfish_mode;

  return {
    tinyfish_mode: VALID_MODES.has(mode) ? mode : DEFAULTS.tinyfish_mode,
    tinyfish_timeout_secs: Math.floor(asFiniteNumber(candidate.tinyfish_timeout_secs, DEFAULTS.tinyfish_timeout_secs, 1, 120)),
    tinyfish_max_concurrency: Math.floor(asFiniteNumber(candidate.tinyfish_max_concurrency, DEFAULTS.tinyfish_max_concurrency, 1, 1000)),
    tinyfish_batch_size: Math.floor(asFiniteNumber(candidate.tinyfish_batch_size, DEFAULTS.tinyfish_batch_size, 1, 1000)),
    tinyfish_fail_open: asBoolean(candidate.tinyfish_fail_open, DEFAULTS.tinyfish_fail_open),
    grounding_lookback_hours: asFiniteNumber(candidate.grounding_lookback_hours, DEFAULTS.grounding_lookback_hours, 1, 72),
    chokepoint_lookback_minutes: asFiniteNumber(candidate.chokepoint_lookback_minutes, DEFAULTS.chokepoint_lookback_minutes, 5, 720),
    news_deep_extract_lookback_hours: asFiniteNumber(candidate.news_deep_extract_lookback_hours, DEFAULTS.news_deep_extract_lookback_hours, 1, 168),
    risk_trigger_threshold: asFiniteNumber(candidate.risk_trigger_threshold, DEFAULTS.risk_trigger_threshold, 0, 1),
    confidence_trigger_threshold: asFiniteNumber(candidate.confidence_trigger_threshold, DEFAULTS.confidence_trigger_threshold, 0, 1),
    min_observation_confidence: asFiniteNumber(candidate.min_observation_confidence, DEFAULTS.min_observation_confidence, 0, 1),
  };
}

function pickPatch(input) {
  if (!input || typeof input !== 'object') return {};
  const patch = {};
  for (const [key, value] of Object.entries(input)) {
    if (ALLOWED_KEYS.has(key)) patch[key] = value;
  }
  return patch;
}

async function writeSettings(settings) {
  const url = process.env.UPSTASH_REDIS_REST_URL;
  const token = process.env.UPSTASH_REDIS_REST_TOKEN;
  if (!url || !token) throw new Error('Redis not configured');

  const response = await fetch(url, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
    body: JSON.stringify(['SET', SETTINGS_KEY, JSON.stringify(settings), 'EX', SETTINGS_TTL_SECONDS]),
    signal: AbortSignal.timeout(4_000),
  });

  if (!response.ok) {
    throw new Error(`Redis HTTP ${response.status}`);
  }
}

export default async function handler(req) {
  if (isDisallowedOrigin(req)) {
    return new Response(JSON.stringify({ error: 'Origin not allowed' }), {
      status: 403,
      headers: { 'Content-Type': 'application/json' },
    });
  }

  const cors = getCorsHeaders(req, 'GET, PATCH, OPTIONS');
  if (req.method === 'OPTIONS') return new Response(null, { status: 204, headers: cors });

  const keyCheck = validateApiKey(req, { forceKey: true });
  if (!keyCheck.valid) {
    return jsonResponse({ error: keyCheck.error || 'Unauthorized' }, 401, cors);
  }

  const currentRaw = await readJsonFromUpstash(SETTINGS_KEY);
  const current = sanitizeSettings(currentRaw || DEFAULTS);

  if (req.method === 'GET') {
    return jsonResponse({ settings: current }, 200, {
      ...cors,
      'Cache-Control': 'no-store',
    });
  }

  if (req.method === 'PATCH') {
    let body;
    try {
      body = await req.json();
    } catch {
      return jsonResponse({ error: 'Invalid JSON body' }, 400, cors);
    }

    const patch = pickPatch(body);
    const merged = sanitizeSettings({ ...current, ...patch });

    try {
      await writeSettings(merged);
    } catch (error) {
      return jsonResponse(
        { error: error instanceof Error ? error.message : String(error) },
        503,
        cors,
      );
    }

    return jsonResponse(
      { settings: merged, updatedKeys: Object.keys(patch) },
      200,
      { ...cors, 'Cache-Control': 'no-store' },
    );
  }

  return jsonResponse({ error: 'Method not allowed' }, 405, cors);
}
