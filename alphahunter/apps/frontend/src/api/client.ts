/**
 * AlphaHunter API client.
 *
 * All requests go through the typed `request<T>()` helper which:
 *   - Prefixes every path with API_BASE (default "/api", overridable via VITE_API_BASE_URL)
 *   - Sets Content-Type: application/json
 *   - Throws an Error with the backend `detail` field on non-2xx responses
 *
 * Binary downloads use `requestBlob()` instead (no JSON parsing).
 * Query parameters are assembled with `createSearchParams()` which omits
 * null/undefined/empty-string values automatically.
 *
 * Sections
 * --------
 *   HTTP helpers          request, requestBlob, createSearchParams
 *   Type definitions      response shapes shared across page components
 *   API object            one method per backend endpoint, grouped by domain
 */
const DEFAULT_API_BASE = "/api";

function normalizeApiBase(url: string): string {
  return url.endsWith("/") ? url.slice(0, -1) : url;
}

const API_BASE = normalizeApiBase(import.meta.env.VITE_API_BASE_URL || DEFAULT_API_BASE);

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const errorPayload = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(errorPayload.detail || errorPayload.error?.message || `Request failed: ${response.status}`);
  }

  return response.json() as Promise<T>;
}

async function requestBlob(path: string): Promise<Blob> {
  const response = await fetch(`${API_BASE}${path}`);
  if (!response.ok) {
    const errorPayload = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(errorPayload.detail || `Request failed: ${response.status}`);
  }
  return response.blob();
}

function createSearchParams(params: Record<string, string | number | boolean | null | undefined>) {
  const searchParams = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === null || value === undefined || value === "") continue;
    searchParams.set(key, String(value));
  }
  const queryString = searchParams.toString();
  return queryString ? `?${queryString}` : "";
}

export interface ApiResponse<T> {
  success: boolean;
  data: T;
}

export interface ScanSummary {
  id: number;
  scan_run_id: string;
  triggered_by: string;
  status: string;
  started_at: string | null;
  completed_at: string | null;
  duration_secs: number | null;
  stocks_scanned: number;
  signals_found: number;
  error_message: string | null;
}

export interface Opportunity {
  decision_id: string;
  symbol: string;
  name: string;
  sector: string | null;
  action: string;
  confidence: number;
  entry_price: number | null;
  target_price: number | null;
  stop_loss: number | null;
  rr_ratio: number | null;
  price: number | null;
  signal_count: number;
  signals: string[];
  composite_score: number | null;
  reasoning: {
    llm_summary?: string;
    key_factors?: string[];
    risk_warnings?: string[];
  };
  scanned_at: string | null;
  decided_at: string | null;
}

export interface OpportunitiesResponse {
  scan_run_id: string | null;
  status: string;
  scanned_at: string | null;
  total: number;
  opportunities: Opportunity[];
}

export interface HealthSnapshot {
  status: string;
  database: string;
  version: string;
  latest_scan: ScanSummary | null;
  active_scan: ScanSummary | null;
  data_feeds: Record<string, string>;
  tinyfish: {
    provider?: string;
    last_prefetch_at?: string | null;
    last_prefetch_status?: string | null;
    source_status?: Record<string, { status: string; count?: number; freshness_minutes?: number | null }>;
    source_freshness_minutes?: Record<string, number>;
  };
}

export interface StockDetailResponse {
  stock: {
    symbol: string;
    name: string;
    sector: string | null;
    market_cap_cr: number | null;
    is_active: boolean;
  };
  meta: {
    scanned_at: string | null;
    backtest_lookback_years: string;
    backtest_outcome_days: string;
  } | null;
  decision: {
    decision_id: string;
    action: string;
    confidence: number;
    entry_price: number | null;
    target_price: number | null;
    stop_loss: number | null;
    rr_ratio: number | null;
    score_breakdown: {
      signal_score: number | null;
      backtest_score: number | null;
      composite_score: number | null;
    };
    decided_at: string;
    outcome_measured: boolean;
    outcome_return_pct: number | null;
    outcome_result: string | null;
  } | null;
  signals: {
    signal_count: number;
    composite_score: number | null;
    price: number | null;
    volume_today: number | null;
    volume_avg_20d: number | null;
    volume_ratio: number | null;
    items: Array<{
      key: string;
      label: string;
      triggered: boolean;
      strength: number | null;
      details: Record<string, unknown>;
    }>;
    diagnostics: Record<string, unknown>;
    extra_signals: Record<string, unknown>;
  } | null;
  reasoning: {
    llm_summary?: string;
    key_factors?: string[];
    risk_warnings?: string[];
  } | null;
  backtest: {
    matches: number | null;
    success_rate: number | null;
    avg_return_pct: number | null;
    worst_case_pct: number | null;
    best_case_pct: number | null;
    cases: Array<Record<string, unknown>>;
  } | null;
}

export interface StockChartResponse {
  symbol: string;
  period: string;
  interval: string;
  ohlcv: Array<{
    date: string;
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
  }>;
  signal_markers: Array<{
    date: string;
    type: string;
    return_pct: number | null;
    profitable: boolean;
  }>;
  resistance_level: number | null;
  support_level: number | null;
  target_price: number | null;
}

// Workspace Types
export interface CompanySummary {
  id: string;
  symbol: string | null;
  name: string;
  sector: string | null;
  listing_status: string;
  exchange: string | null;
  country: string;
  market_cap: number | null;
  workspace_count?: number;
}

export interface WorkspaceSummary {
  id: string;
  company_id: string;
  workspace_type: string;
  title: string;
  stage: string;
  owner_id: string;
  source_symbol: string | null;
  source_decision_id: string | null;
  created_at: string;
  updated_at: string;
  health_summary: Record<string, unknown> | null;
  company?: CompanySummary;
}

export interface WorkspaceDetailResponse {
  workspace: WorkspaceSummary;
  documents: DocumentSummary[];
  agent_runs: AgentRunSummary[];
  valuations: ValuationRunSummary[];
  outputs: OutputSummary[];
  tasks: TaskSummary[];
  default_valuation_inputs: Record<string, unknown>;
}

export interface DocumentSummary {
  id: string;
  workspace_id: string;
  filename: string;
  file_type: string;
  file_size_bytes: number;
  category: string | null;
  classification: string;
  parse_status: string;
  rag_status: string;
  text_preview: string | null;
  uploaded_at: string;
}

export interface AgentRunSummary {
  id: string;
  workspace_id: string;
  agent_type: string;
  task_name: string;
  status: string;
  parameters: Record<string, unknown>;
  summary: string | null;
  confidence: number | null;
  error_message: string | null;
  created_at: string;
  completed_at: string | null;
}

export interface ValuationRunSummary {
  id: string;
  workspace_id: string;
  model_type: string;
  status: string;
  headline_value: string | number | null;
  headline_metric: string | null;
  warnings: string[];
  created_at: string;
  completed_at: string | null;
  assumptions: Record<string, unknown>;
  result_summary: Record<string, unknown>;
}

export interface OutputSummary {
  id: string;
  workspace_id: string;
  source_run_id: string | null;
  source_kind: string;
  output_type: string;
  review_status: string;
  version: number;
  title: string;
  preview_markdown: string | null;
  created_at: string;
}

export interface TaskSummary {
  id: string;
  title: string;
  status: string;
  priority: string;
  owner_label: string;
  description: string | null;
  due_at: string | null;
  created_at: string;
}

export interface MacroContext {
  available: boolean;
  source: string;
  symbol: string | null;
  sector: string | null;
  market_regime: string;
  fear_greed: number | null;
  sector_snapshot: Record<string, unknown> | null;
  strategic_risks: Array<{ name: string; severity: string }>;
  notes: string[];
}

// Continue with existing types
export interface DecisionEntry {
  decision_id: string;
  symbol: string;
  name: string;
  sector: string | null;
  action: string;
  confidence: number;
  entry_price: number | null;
  target_price: number | null;
  stop_loss: number | null;
  rr_ratio: number | null;
  decided_at: string | null;
  outcome_measured: boolean;
  outcome_return_pct: number | null;
  outcome_result: string | null;
  outcome_exit_price: number | null;
  outcome_measured_at: string | null;
}

export interface DecisionHistoryResponse {
  summary: {
    total_decisions: number;
    buy_decisions: number;
    measured: number;
    wins: number;
    win_rate_pct: number | null;
    avg_return_pct: number | null;
  };
  decisions: DecisionEntry[];
  pagination: {
    total: number;
    limit: number;
    offset: number;
  };
}

export interface DecisionDetailResponse {
  decision: DecisionEntry;
  stock: {
    symbol: string;
    name: string;
    sector: string | null;
  };
  signals: StockDetailResponse["signals"];
  reasoning: StockDetailResponse["reasoning"];
  backtest: StockDetailResponse["backtest"];
  snapshot: Record<string, unknown>;
  outcome: {
    result: string | null;
    exit_price: number | null;
    return_pct: number | null;
    measured_at: string | null;
  };
}

export interface WatchlistEntry {
  id: number;
  symbol: string;
  name: string;
  sector: string | null;
  added_at: string;
  notes: string | null;
  latest_action: string | null;
  latest_confidence: number | null;
  latest_decided_at: string | null;
  latest_signal_count: number;
  last_scanned_at: string | null;
  has_active_signal: boolean;
}

export interface WatchlistResponse {
  count: number;
  max_items: number;
  items: WatchlistEntry[];
}

export interface AlertEntry {
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

export interface AlertsResponse {
  unread_count: number;
  alerts: AlertEntry[];
}

export interface SettingsResponse {
  [key: string]: string;
}

export const api = {
  getLatestScan: () => request<ApiResponse<ScanSummary | null>>("/scan/latest"),
  getScanStatus: (scanRunId: string) =>
    request<ApiResponse<ScanSummary>>(`/scan/${scanRunId}/status`),
  triggerScan: () =>
    request<
      ApiResponse<{
        scan_run_id: string;
        status: string;
        started_at: string;
        stocks_queued: number;
      }>
    >("/scan", { method: "POST" }),
  getSectors: () =>
    request<ApiResponse<string[]>>("/opportunities/sectors"),
  getOpportunities: (params?: {
    action?: string;
    signal?: string;
    sector?: string;
    min_confidence?: number;
    limit?: number;
    offset?: number;
  }) => request<ApiResponse<OpportunitiesResponse>>(`/opportunities${createSearchParams(params ?? {})}`),
  getStockDetail: (symbol: string) =>
    request<ApiResponse<StockDetailResponse>>(`/stock/${symbol}`),
  getStockChart: (symbol: string, params?: { period?: string; interval?: string }) =>
    request<ApiResponse<StockChartResponse>>(`/stock/${symbol}/chart${createSearchParams(params ?? {})}`),
  getHistory: (params?: {
    action?: string;
    outcome?: string;
    symbol?: string;
    from_date?: string;
    to_date?: string;
    limit?: number;
    offset?: number;
  }) => request<ApiResponse<DecisionHistoryResponse>>(`/history${createSearchParams(params ?? {})}`),
  getHistoryDetail: (decisionId: string) =>
    request<ApiResponse<DecisionDetailResponse>>(`/history/${decisionId}`),
  exportHistoryCsv: (params?: {
    action?: string;
    outcome?: string;
    symbol?: string;
    from_date?: string;
    to_date?: string;
  }) => requestBlob(`/history/export${createSearchParams(params ?? {})}`),
  getScanHistory: (limit = 50) =>
    request<ApiResponse<ScanSummary[]>>(`/history/scans${createSearchParams({ limit })}`),
  getWatchlist: () =>
    request<ApiResponse<WatchlistResponse>>("/watchlist"),
  addToWatchlist: (symbol: string, notes?: string) =>
    request<ApiResponse<{ id: number; symbol: string; added_at: string; notes: string | null; max_items: number }>>(
      `/watchlist/${symbol}`,
      {
        method: "POST",
        body: notes ? JSON.stringify({ notes }) : undefined,
      },
    ),
  removeFromWatchlist: (symbol: string) =>
    request<ApiResponse<{ symbol: string; removed: boolean }>>(`/watchlist/${symbol}`, {
      method: "DELETE",
    }),
  getAlerts: (params?: { unread_only?: boolean; limit?: number }) =>
    request<ApiResponse<AlertsResponse>>(`/alerts${createSearchParams(params ?? {})}`),
  markAlertsRead: (alertIds?: number[]) =>
    request<ApiResponse<{ marked_read: number }>>("/alerts/mark-read", {
      method: "POST",
      body: JSON.stringify(alertIds ?? null),
    }),
  clearReadAlerts: () =>
    request<ApiResponse<{ cleared: number }>>("/alerts/read", {
      method: "DELETE",
    }),
  getSettings: () => request<ApiResponse<SettingsResponse>>("/settings"),
  updateSettings: (updates: Record<string, string>) =>
    request<ApiResponse<{ updated: string[] }>>("/settings", {
      method: "PATCH",
      body: JSON.stringify(updates),
    }),
  getHealth: () => request<ApiResponse<HealthSnapshot>>("/health/"),

  // Workspace Types
  getWorkspaces: (params?: { workspace_type?: string; stage?: string }) =>
    request<ApiResponse<{ workspaces: WorkspaceSummary[] }>>(`/workspaces${createSearchParams(params ?? {})}`),
  createWorkspace: (payload: { title?: string; workspace_type?: string; symbol?: string; company_id?: string }) =>
    request<ApiResponse<WorkspaceSummary>>("/workspaces", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  createWorkspaceFromOpportunity: (payload: { symbol: string; title?: string; source_decision_id?: string }) =>
    request<ApiResponse<WorkspaceSummary>>("/workspaces/from-opportunity", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  getWorkspaceDetail: (workspaceId: string) =>
    request<ApiResponse<WorkspaceDetailResponse>>(`/workspaces/${workspaceId}`),

  // Valuation Types
  getValuations: (params?: { workspace_id?: string }) =>
    request<ApiResponse<{ valuations: ValuationRunSummary[] }>>(`/valuations${createSearchParams(params ?? {})}`),
  runValuation: (payload: { workspace_id: string; model_type: string; assumptions?: Record<string, unknown> }) =>
    request<ApiResponse<ValuationRunSummary>>("/valuations/run", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  getValuation: (valuationId: string) =>
    request<ApiResponse<ValuationRunSummary>>(`/valuations/${valuationId}`),
  promoteValuation: (valuationId: string, payload: { title?: string; output_type?: string }) =>
    request<ApiResponse<OutputSummary>>(`/valuations/${valuationId}/promote`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  // Output Types
  getOutputs: () =>
    request<ApiResponse<{ outputs: OutputSummary[] }>>("/outputs"),
  downloadOutput: (workspaceId: string, outputId: string) =>
    requestBlob(`/workspaces/${workspaceId}/outputs/${outputId}/download`),
  reviewOutput: (workspaceId: string, outputId: string, payload: { review_status: string }) =>
    request<ApiResponse<OutputSummary>>(`/workspaces/${workspaceId}/outputs/${outputId}/review`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),

  // Company Types
  getCompanies: (params?: { q?: string; limit?: number }) =>
    request<ApiResponse<{ companies: CompanySummary[] }>>(`/companies${createSearchParams(params ?? {})}`),
  createCompany: (payload: { name: string; symbol?: string; sector?: string; listing_status?: string }) =>
    request<ApiResponse<CompanySummary>>("/companies", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  // Task Types
  createTask: (workspaceId: string, payload: { title: string; status?: string; priority?: string; owner_label?: string }) =>
    request<ApiResponse<TaskSummary>>(`/workspaces/${workspaceId}/tasks`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  updateTask: (workspaceId: string, taskId: string, payload: { status?: string; priority?: string; description?: string }) =>
    request<ApiResponse<TaskSummary>>(`/workspaces/${workspaceId}/tasks/${taskId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),

  // Macro Context
  getMacroContext: (params?: { workspace_id?: string; symbol?: string; sector?: string }) =>
    request<ApiResponse<MacroContext>>(`/macro/context${createSearchParams(params ?? {})}`),
};
