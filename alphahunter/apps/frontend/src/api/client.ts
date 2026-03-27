const DEFAULT_API_BASE = "/api";

function normalizeApiBase(url: string): string {
  return url.endsWith("/") ? url.slice(0, -1) : url;
}

const API_BASE = normalizeApiBase(
  import.meta.env.VITE_API_BASE_URL || DEFAULT_API_BASE,
);

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Request failed: ${res.status}`);
  }
  return res.json();
}

export const api = {
  // Opportunities
  getOpportunities: (limit = 20) =>
    request<ApiResponse<Opportunity[]>>(`/opportunities?limit=${limit}`),

  getOpportunityDetail: (decisionId: string) =>
    request<ApiResponse<OpportunityDetail>>(`/opportunities/${decisionId}`),

  // Scan
  triggerScan: () =>
    request<ApiResponse<ScanTriggerResult>>("/scan", { method: "POST" }),

  // History
  getDecisionHistory: (action?: string, limit = 50) => {
    const params = new URLSearchParams({ limit: String(limit) });
    if (action) params.set("action", action);
    return request<ApiResponse<DecisionHistoryResponse>>(`/history?${params}`);
  },

  getScanHistory: (limit = 50) =>
    request<ApiResponse<ScanRun[]>>(`/history/scans?limit=${limit}`),

  // Stock detail
  getStockDetail: (symbol: string) =>
    request<ApiResponse<StockDetail>>(`/stock/${symbol}`),

  // Watchlist
  getWatchlist: () => request<ApiResponse<WatchlistEntry[]>>("/watchlist"),

  addToWatchlist: (symbol: string, notes?: string) =>
    request<ApiResponse<WatchlistEntry>>(`/watchlist/${symbol}`, {
      method: "POST",
      body: notes ? JSON.stringify({ notes }) : undefined,
    }),

  removeFromWatchlist: (symbol: string) =>
    request<ApiResponse<{ symbol: string; removed: boolean }>>(`/watchlist/${symbol}`, {
      method: "DELETE",
    }),

  // Alerts
  getAlerts: (unreadOnly = false, limit = 50) =>
    request<ApiResponse<AlertEntry[]>>(`/alerts?unread_only=${unreadOnly}&limit=${limit}`),

  markAlertsRead: (alertIds?: number[]) =>
    request<ApiResponse<{ marked_read: number }>>("/alerts/mark-read", {
      method: "POST",
      body: JSON.stringify(alertIds || null),
    }),

  // Settings
  getSettings: () => request<ApiResponse<Record<string, string>>>("/settings"),

  updateSettings: (updates: Record<string, string>) =>
    request<ApiResponse<{ updated: string[] }>>("/settings", {
      method: "PATCH",
      body: JSON.stringify(updates),
    }),
};

// Type definitions inline for convenience
interface ApiResponse<T> {
  success: boolean;
  data: T;
}

interface Opportunity {
  decision_id: string;
  symbol: string;
  action: string;
  confidence: number;
  entry_price: number;
  target: number;
  stop_loss: number;
  rr_ratio: number;
  reasoning: { llm_summary?: string; key_factors?: string[]; risk_warnings?: string[] };
  timestamp: string;
}

interface OpportunityDetail {
  decision: {
    decision_id: string;
    symbol: string;
    action: string;
    confidence: number;
    entry_price: number;
    target: number;
    stop_loss: number;
    rr_ratio: number;
    score_signal: number;
    score_backtest: number;
    score_composite: number;
    timestamp: string;
    snapshot: any;
  };
  signals: {
    breakout: boolean;
    volume: boolean;
    bulk: boolean;
    breakout_details: any;
    volume_details: any;
    bulk_details: any;
  };
  reasoning: { llm_summary?: string; key_factors?: string[]; risk_warnings?: string[] };
}

interface ScanTriggerResult {
  scan_run_id: string;
  status: string;
  started_at: string;
  stocks_queued: number;
}

interface ScanRun {
  id: number;
  run_id: string;
  triggered_by: string;
  status: string;
  started_at: string;
  completed_at: string | null;
  duration_secs: number | null;
  stocks_scanned: number;
  signals_found: number;
}

interface DecisionHistoryResponse {
  decisions: DecisionEntry[];
  track_record: {
    total_decisions: number;
    measured: number;
    wins: number;
    win_rate: number | null;
    avg_return_pct: number | null;
  };
}

interface DecisionEntry {
  decision_id: string;
  symbol: string;
  action: string;
  confidence: number;
  entry_price: number | null;
  target_price: number | null;
  stop_loss: number | null;
  rr_ratio: number | null;
  decided_at: string;
  outcome_measured: boolean;
  outcome_return_pct: number | null;
  outcome_result: string | null;
}

interface StockDetail {
  stock: {
    symbol: string;
    name: string;
    sector: string | null;
    market_cap_cr: number | null;
    is_active: boolean;
  };
  decision: {
    decision_id: string;
    action: string;
    confidence: number;
    entry_price: number | null;
    target_price: number | null;
    stop_loss: number | null;
    rr_ratio: number | null;
    score_signal: number | null;
    score_backtest: number | null;
    score_composite: number | null;
    decided_at: string;
    outcome_measured: boolean;
    outcome_return_pct: number | null;
    outcome_result: string | null;
  } | null;
  signals: {
    breakout: boolean;
    volume_spike: boolean;
    bulk_deal: boolean;
    signal_count: number;
    composite_score: number | null;
    price: number | null;
    volume_today: number | null;
    volume_avg_20d: number | null;
    volume_ratio: number | null;
    breakout_details: any;
    volume_spike_details: any;
    bulk_deal_details: any;
  } | null;
  reasoning: { llm_summary?: string; key_factors?: string[]; risk_warnings?: string[] };
  backtest: {
    matches: number | null;
    success_rate: number | null;
    avg_return: number | null;
    worst_case: number | null;
    best_case: number | null;
    cases: any;
  } | null;
}

interface WatchlistEntry {
  id: number;
  symbol: string;
  added_at: string;
  notes: string | null;
  latest_action: string | null;
  latest_confidence: number | null;
  latest_decided_at: string | null;
}

interface AlertEntry {
  id: number;
  alert_id: string;
  symbol: string;
  alert_type: string;
  message: string;
  confidence: number | null;
  action: string | null;
  is_read: boolean;
  created_at: string;
}

export type {
  ApiResponse,
  Opportunity,
  OpportunityDetail,
  ScanTriggerResult,
  ScanRun,
  DecisionHistoryResponse,
  DecisionEntry,
  StockDetail,
  WatchlistEntry,
  AlertEntry,
};
