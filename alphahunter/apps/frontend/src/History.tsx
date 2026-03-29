/**
 * History — audit trail for decisions and scan runs.
 *
 * Views (tab-switched):
 *   decisions   Summary metrics + filter bar + sortable decision log table
 *               Click any row to open DecisionReplayDrawer with full snapshot.
 *   scan runs   Archive table of every ScanRun record.
 *
 * Actions:
 *   Export CSV  — downloads filtered decisions as attachment via blob URL.
 *   Replay      — loads DecisionDetailResponse and opens the drawer overlay.
 */
import { useEffect, useMemo, useState } from "react";
import { Download, Eye, Filter } from "lucide-react";
import {
  api,
  type DecisionDetailResponse,
  type DecisionEntry,
  type ScanSummary,
} from "./api/client";
import { DecisionReplayDrawer } from "./components/DecisionReplayDrawer";
import {
  Button,
  EmptyState,
  ErrorState,
  LoadingState,
  MetricCard,
  PageHeader,
  Panel,
  SectionTabs,
  StatusBadge,
} from "./components/ui";
import {
  formatCurrency,
  formatDateTime,
  formatDuration,
  formatPercent,
  getActionTone,
} from "./lib/format";

type HistoryView = "decisions" | "scans";

interface FilterState {
  action: string;
  outcome: string;
  symbol: string;
  fromDate: string;
  toDate: string;
}

const initialFilters: FilterState = {
  action: "",
  outcome: "",
  symbol: "",
  fromDate: "",
  toDate: "",
};

export default function History() {
  const [view, setView] = useState<HistoryView>("decisions");
  const [filters, setFilters] = useState<FilterState>(initialFilters);
  const [decisions, setDecisions] = useState<DecisionEntry[]>([]);
  const [scans, setScans] = useState<ScanSummary[]>([]);
  const [summary, setSummary] = useState<{
    total_decisions: number;
    buy_decisions: number;
    measured: number;
    wins: number;
    win_rate_pct: number | null;
    avg_return_pct: number | null;
  } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedDecision, setSelectedDecision] = useState<DecisionDetailResponse | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;

    const loadHistory = async () => {
      try {
        if (view === "decisions") {
          const response = await api.getHistory({
            action: filters.action || undefined,
            outcome: filters.outcome || undefined,
            symbol: filters.symbol || undefined,
            from_date: filters.fromDate || undefined,
            to_date: filters.toDate || undefined,
            limit: 80,
          });
          if (cancelled) return;
          setDecisions(response.data.decisions);
          setSummary(response.data.summary);
        } else {
          const response = await api.getScanHistory(60);
          if (cancelled) return;
          setScans(response.data);
        }
        setError("");
      } catch (historyError) {
        if (cancelled) return;
        setError(historyError instanceof Error ? historyError.message : "Unable to load history.");
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    void loadHistory();

    return () => {
      cancelled = true;
    };
  }, [filters.action, filters.fromDate, filters.outcome, filters.symbol, filters.toDate, view]);

  const measuredShare = useMemo(() => {
    if (!summary || summary.total_decisions === 0) return "NA";
    return formatPercent((summary.measured / summary.total_decisions) * 100);
  }, [summary]);

  const handleExport = async () => {
    try {
      const blob = await api.exportHistoryCsv({
        action: filters.action || undefined,
        outcome: filters.outcome || undefined,
        symbol: filters.symbol || undefined,
        from_date: filters.fromDate || undefined,
        to_date: filters.toDate || undefined,
      });
      const url = window.URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `alphahunter_decisions_${new Date().toISOString().slice(0, 10)}.csv`;
      anchor.click();
      window.URL.revokeObjectURL(url);
    } catch (exportError) {
      setError(exportError instanceof Error ? exportError.message : "Unable to export history.");
    }
  };

  const openDecision = async (decisionId: string) => {
    setDetailLoading(true);
    try {
      const response = await api.getHistoryDetail(decisionId);
      setSelectedDecision(response.data);
    } catch (detailError) {
      setError(detailError instanceof Error ? detailError.message : "Unable to load decision detail.");
    } finally {
      setDetailLoading(false);
    }
  };

  if (loading) {
    return <LoadingState label="Loading history..." />;
  }

  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="Audit trail"
        title="Review outcomes, replay decisions, and export conviction history."
        description="History gives investors a trust layer: a filtered decision log, scan-run archive, replay detail, and CSV export for deeper review."
        actions={
          <>
            <SectionTabs
              value={view}
              onChange={setView}
              tabs={[
                { value: "decisions", label: "Decisions" },
                { value: "scans", label: "Scan runs" },
              ]}
            />
            {view === "decisions" ? (
              <Button variant="secondary" onClick={() => void handleExport()}>
                <Download className="size-4" />
                Export CSV
              </Button>
            ) : null}
          </>
        }
      />

      {error ? <ErrorState description={error} /> : null}

      {view === "decisions" && summary ? (
        <>
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <MetricCard label="Total decisions" value={summary.total_decisions} detail="Filtered recommendation count." />
            <MetricCard label="Win rate" value={formatPercent(summary.win_rate_pct)} detail={`${summary.wins} winning calls`} tone="positive" />
            <MetricCard label="Avg return" value={formatPercent(summary.avg_return_pct, true)} detail="Measured outcomes only." tone="warning" />
            <MetricCard label="Measured share" value={measuredShare} detail={`${summary.measured} measured outcomes`} />
          </div>

          <Panel title="Decision filters" subtitle="Narrow the audit trail by action, outcome, symbol, or date range.">
            <div className="grid gap-4 lg:grid-cols-[1fr_1fr_1.2fr_1fr_1fr]">
              <label className="space-y-2">
                <span className="flex items-center gap-2 text-sm font-medium text-white">
                  <Filter className="size-4 text-cyan-200" />
                  Action
                </span>
                <select
                  value={filters.action}
                  onChange={(event) => setFilters((current) => ({ ...current, action: event.target.value }))}
                  className="terminal-select"
                >
                  <option value="">All actions</option>
                  <option value="BUY">BUY</option>
                  <option value="WATCH">WATCH</option>
                  <option value="AVOID">AVOID</option>
                </select>
              </label>
              <label className="space-y-2">
                <span className="text-sm font-medium text-white">Outcome</span>
                <select
                  value={filters.outcome}
                  onChange={(event) => setFilters((current) => ({ ...current, outcome: event.target.value }))}
                  className="terminal-select"
                >
                  <option value="">All outcomes</option>
                  <option value="profit">Profit</option>
                  <option value="loss">Loss</option>
                  <option value="pending">Pending</option>
                </select>
              </label>
              <label className="space-y-2">
                <span className="text-sm font-medium text-white">Symbol</span>
                <input
                  value={filters.symbol}
                  onChange={(event) => setFilters((current) => ({ ...current, symbol: event.target.value.toUpperCase() }))}
                  className="terminal-input"
                  placeholder="INFY"
                />
              </label>
              <label className="space-y-2">
                <span className="text-sm font-medium text-white">From date</span>
                <input
                  type="date"
                  value={filters.fromDate}
                  onChange={(event) => setFilters((current) => ({ ...current, fromDate: event.target.value }))}
                  className="terminal-input"
                />
              </label>
              <label className="space-y-2">
                <span className="text-sm font-medium text-white">To date</span>
                <input
                  type="date"
                  value={filters.toDate}
                  onChange={(event) => setFilters((current) => ({ ...current, toDate: event.target.value }))}
                  className="terminal-input"
                />
              </label>
            </div>
          </Panel>

          <Panel title="Decision log" subtitle="Click any row to replay the full stored snapshot.">
            {decisions.length === 0 ? (
              <EmptyState
                title="No decision history matches the filters"
                description="Try a broader date range or clear one of the filters to restore the audit trail."
                action={<Button onClick={() => setFilters(initialFilters)}>Reset filters</Button>}
              />
            ) : (
              <div className="overflow-x-auto">
                <table className="terminal-table">
                  <thead>
                    <tr>
                      <th>Stock</th>
                      <th>Action</th>
                      <th>Confidence</th>
                      <th>Entry</th>
                      <th>Target</th>
                      <th>Outcome</th>
                      <th>Decided</th>
                      <th />
                    </tr>
                  </thead>
                  <tbody>
                    {decisions.map((decision) => (
                      <tr key={decision.decision_id}>
                        <td>
                          <div>
                            <p className="font-medium text-white">{decision.symbol}</p>
                            <p className="text-xs text-slate-500">{decision.name}</p>
                          </div>
                        </td>
                        <td>
                          <StatusBadge
                            label={decision.action}
                            tone={getActionTone(decision.action)}
                          />
                        </td>
                        <td>{formatPercent(decision.confidence)}</td>
                        <td>{formatCurrency(decision.entry_price)}</td>
                        <td>{formatCurrency(decision.target_price)}</td>
                        <td>
                          {decision.outcome_measured ? (
                            <span className={decision.outcome_return_pct != null && decision.outcome_return_pct >= 0 ? "text-emerald-300" : "text-rose-300"}>
                              {formatPercent(decision.outcome_return_pct, true)}
                            </span>
                          ) : (
                            <span className="text-slate-500">Pending</span>
                          )}
                        </td>
                        <td>{formatDateTime(decision.decided_at)}</td>
                        <td>
                          <button
                            type="button"
                            onClick={() => void openDecision(decision.decision_id)}
                            className="inline-flex items-center gap-2 rounded-full border border-white/8 px-3 py-1 text-sm text-cyan-200 hover:border-cyan-400/30 hover:text-white"
                          >
                            <Eye className="size-4" />
                            Replay
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Panel>
        </>
      ) : null}

      {view === "scans" ? (
        <Panel title="Scan run archive" subtitle="Recent scan runs with duration, coverage, and signal yield.">
          {scans.length === 0 ? (
            <EmptyState
              title="No scans recorded yet"
              description="Trigger a market scan from the dashboard or scanner to begin building the audit archive."
            />
          ) : (
            <div className="overflow-x-auto">
              <table className="terminal-table">
                <thead>
                  <tr>
                    <th>Status</th>
                    <th>Started</th>
                    <th>Completed</th>
                    <th>Duration</th>
                    <th>Triggered by</th>
                    <th>Stocks</th>
                    <th>Signals</th>
                  </tr>
                </thead>
                <tbody>
                  {scans.map((scan) => (
                    <tr key={scan.scan_run_id}>
                      <td>
                        <StatusBadge
                          label={scan.status}
                          tone={
                            scan.status === "completed"
                              ? "positive"
                              : scan.status === "running"
                                ? "info"
                                : "danger"
                          }
                        />
                      </td>
                      <td>{formatDateTime(scan.started_at)}</td>
                      <td>{formatDateTime(scan.completed_at)}</td>
                      <td>{formatDuration(scan.duration_secs)}</td>
                      <td>{scan.triggered_by}</td>
                      <td>{scan.stocks_scanned}</td>
                      <td>{scan.signals_found}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Panel>
      ) : null}

      {detailLoading ? <LoadingState label="Loading decision replay..." /> : null}
      {selectedDecision ? (
        <DecisionReplayDrawer detail={selectedDecision} onClose={() => setSelectedDecision(null)} />
      ) : null}
    </div>
  );
}
