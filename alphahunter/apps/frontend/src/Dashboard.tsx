/**
 * Dashboard — investor command center.
 *
 * Sections:
 *   PageHeader        — title, run-scan CTA
 *   Metrics grid      — scan status, stocks scanned, signals, watchlist pulse (4-up)
 *   Top opportunities — latest 3 high-conviction ideas + Watchlist pulse (2-col)
 *   System pulse      — API health, data feed status, TinyFish sources
 *   Quick actions     — nav cards to scanner, history, settings
 *
 * Data loads on mount and re-fetches whenever `latestScan` status changes
 * (driven by the useScanCenter auto-poll).
 */
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Activity, ArrowRight, Radar, ShieldCheck, Waves } from "lucide-react";
import { api, type HealthSnapshot, type Opportunity, type WatchlistEntry } from "./api/client";
import { useScanCenter } from "./hooks/useScanCenter";
import {
  Button,
  EmptyState,
  ErrorState,
  LoadingState,
  MetricCard,
  PageHeader,
  Panel,
  StatusBadge,
} from "./components/ui";
import { formatCompactNumber, formatDateTime, formatPercent } from "./lib/format";

interface DashboardState {
  opportunities: Opportunity[];
  watchlist: WatchlistEntry[];
  health: HealthSnapshot | null;
}

function getFeedTone(status: string | null | undefined) {
  if (status === "ok" || status === "completed" || status === "fresh") return "positive" as const;
  if (status === "running") return "info" as const;
  if (status === "failed" || status === "missing" || status === "stale") return "danger" as const;
  return "warning" as const;
}

function getScanTone(status: string | null | undefined) {
  if (status === "completed") return "positive" as const;
  if (status === "running") return "info" as const;
  if (status === "failed") return "danger" as const;
  return "neutral" as const;
}

export default function Dashboard() {
  const { latestScan, loading: scanLoading, error: scanError, triggerScan } = useScanCenter();
  const [state, setState] = useState<DashboardState>({
    opportunities: [],
    watchlist: [],
    health: null,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    const loadDashboard = async () => {
      try {
        const [opportunitiesResponse, watchlistResponse, healthResponse] = await Promise.all([
          api.getOpportunities({ limit: 3 }),
          api.getWatchlist(),
          api.getHealth(),
        ]);

        if (cancelled) return;

        const sortedWatchlist = [...watchlistResponse.data.items].sort((left, right) => {
          if (left.has_active_signal !== right.has_active_signal) {
            return left.has_active_signal ? -1 : 1;
          }
          return (right.latest_confidence ?? 0) - (left.latest_confidence ?? 0);
        });

        setState({
          opportunities: opportunitiesResponse.data.opportunities,
          watchlist: sortedWatchlist.slice(0, 4),
          health: healthResponse.data,
        });
        setError("");
      } catch (dashboardError) {
        if (cancelled) return;
        setError(dashboardError instanceof Error ? dashboardError.message : "Unable to load dashboard.");
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    void loadDashboard();

    return () => {
      cancelled = true;
    };
  }, [latestScan?.completed_at, latestScan?.status]);

  const handleRunScan = async () => {
    try {
      await triggerScan();
      setError("");
    } catch (triggerError) {
      setError(triggerError instanceof Error ? triggerError.message : "Unable to trigger scan.");
    }
  };

  if (loading && scanLoading) {
    return <LoadingState label="Loading dashboard pulse..." />;
  }

  if (error && !state.health) {
    return (
      <ErrorState
        description={error}
        action={<Button onClick={() => window.location.reload()}>Reload dashboard</Button>}
      />
    );
  }

  const activeSignals = state.opportunities.filter((opportunity) => opportunity.action !== "AVOID").length;

  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="Investor command center"
        title="Read the market before the market reads you."
        description="AlphaHunter turns NSE scans into trade-ready intelligence with ranked opportunities, watchlist pulse, and lightweight system health in one terminal-grade workspace."
        actions={
          <>
            <Button onClick={handleRunScan}>Run scan now</Button>
            <Link to="/scanner">
              <Button variant="secondary">Open scanner</Button>
            </Link>
          </>
        }
      />

      {scanError ? <ErrorState title="Scan monitor warning" description={scanError} /> : null}

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          label="Latest status"
          value={<StatusBadge label={latestScan?.status ?? "idle"} tone={getScanTone(latestScan?.status)} />}
          detail={latestScan?.completed_at ? `Completed ${formatDateTime(latestScan.completed_at)}` : "Waiting for the first completed run."}
          tone="neutral"
        />
        <MetricCard
          label="Stocks scanned"
          value={formatCompactNumber(latestScan?.stocks_scanned ?? 0)}
          detail="Universe scanned in the latest run."
          tone="info"
        />
        <MetricCard
          label="Signals found"
          value={formatCompactNumber(latestScan?.signals_found ?? 0)}
          detail={`${activeSignals} actionable names in the top view.`}
          tone="positive"
        />
        <MetricCard
          label="Watchlist pulse"
          value={formatCompactNumber(state.watchlist.filter((item) => item.has_active_signal).length)}
          detail="Tracked names currently showing active signals."
          tone="warning"
        />
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.6fr_1fr]">
        <Panel
          title="Top opportunities"
          subtitle="Highest-conviction ideas from the latest reference scan."
          actions={
            <Link to="/scanner" className="text-sm font-medium text-cyan-200 hover:text-white">
              View full scanner
            </Link>
          }
        >
          {state.opportunities.length === 0 ? (
            <EmptyState
              title="No current opportunities"
              description="Run a market scan to populate the terminal with ranked trade ideas and signal-backed reasoning."
              action={<Button onClick={handleRunScan}>Scan the market</Button>}
            />
          ) : (
            <div className="grid gap-4 lg:grid-cols-3">
              {state.opportunities.map((opportunity) => (
                <article
                  key={opportunity.decision_id}
                  className="rounded-[28px] border border-white/8 bg-slate-950/60 p-5"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="text-sm text-slate-400">{opportunity.name}</p>
                      <h3 className="mt-2 text-2xl font-semibold text-white">{opportunity.symbol}</h3>
                    </div>
                    <StatusBadge
                      label={opportunity.action}
                      tone={getFeedTone(
                        opportunity.action === "BUY"
                          ? "completed"
                          : opportunity.action === "WATCH"
                            ? "idle"
                            : "failed",
                      )}
                    />
                  </div>
                  <p className="mt-4 text-sm text-slate-300">
                    {opportunity.reasoning.llm_summary || "Signal-backed opportunity awaiting fresh narrative."}
                  </p>
                  <div className="mt-5 flex items-center justify-between text-sm text-slate-400">
                    <span>{opportunity.signal_count} active signals</span>
                    <span>{formatPercent(opportunity.confidence)}</span>
                  </div>
                  <Link
                    to={`/stock/${opportunity.symbol}`}
                    className="mt-6 inline-flex items-center gap-2 text-sm font-medium text-cyan-200 hover:text-white"
                  >
                    Open stock detail
                    <ArrowRight className="size-4" />
                  </Link>
                </article>
              ))}
            </div>
          )}
        </Panel>

        <Panel title="Watchlist pulse" subtitle="Tracked names sorted by current signal heat.">
          {state.watchlist.length === 0 ? (
            <EmptyState
              title="No watchlist names yet"
              description="Add NSE names to your watchlist to see signal heat and recency directly on the dashboard."
              action={
                <Link to="/watchlist">
                  <Button variant="secondary">Open watchlist</Button>
                </Link>
              }
            />
          ) : (
            <div className="space-y-3">
              {state.watchlist.map((item) => (
                <Link
                  key={item.id}
                  to={`/stock/${item.symbol}`}
                  className="flex items-center justify-between rounded-3xl border border-white/8 bg-slate-950/60 px-4 py-3 transition hover:border-cyan-400/30 hover:bg-slate-950"
                >
                  <div>
                    <p className="text-xs uppercase tracking-[0.22em] text-slate-500">{item.name}</p>
                    <p className="mt-1 text-lg font-semibold text-white">{item.symbol}</p>
                  </div>
                  <div className="text-right">
                    <StatusBadge
                      label={item.latest_action ?? "idle"}
                      tone={item.has_active_signal ? "positive" : "neutral"}
                    />
                    <p className="mt-2 text-xs text-slate-400">
                      {item.last_scanned_at ? formatDateTime(item.last_scanned_at) : "No scan yet"}
                    </p>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </Panel>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <Panel title="System pulse" subtitle="Compact health view for feeds and scan infrastructure.">
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
            <MetricCard
              label="API health"
              value={state.health?.status ?? "Unknown"}
              detail={`Database ${state.health?.database ?? "unknown"}`}
              tone="positive"
            />
            <MetricCard
              label="YFinance feed"
              value={state.health?.data_feeds.yfinance ?? "Unknown"}
              detail="Primary market data source."
              tone="neutral"
            />
            <MetricCard
              label="TinyFish"
              value={state.health?.data_feeds.tinyfish ?? "Unknown"}
              detail="External signal enrichment freshness."
              tone={getFeedTone(state.health?.data_feeds.tinyfish)}
            />
          </div>
          <div className="mt-5 grid gap-3">
            {Object.entries(state.health?.tinyfish.source_status ?? {}).map(([source, status]) => (
              <div
                key={source}
                className="flex items-center justify-between rounded-2xl border border-white/8 bg-slate-950/55 px-4 py-3"
              >
                <div className="flex items-center gap-3">
                  <Activity className="size-4 text-cyan-200" />
                  <span className="text-sm font-medium text-white">{source.replace(/_/g, " ")}</span>
                </div>
                <div className="flex items-center gap-3 text-sm text-slate-400">
                  <StatusBadge label={status.status} tone={getFeedTone(status.status)} />
                  <span>{status.freshness_minutes != null ? `${status.freshness_minutes}m` : "NA"}</span>
                </div>
              </div>
            ))}
          </div>
        </Panel>

        <Panel title="Quick actions" subtitle="Fast paths for the most common investor workflows.">
          <div className="grid gap-4">
            <Link
              to="/scanner"
              className="rounded-[28px] border border-white/8 bg-slate-950/60 p-5 transition hover:border-cyan-400/30"
            >
              <div className="flex items-center gap-3">
                <Radar className="size-5 text-cyan-200" />
                <div>
                  <p className="text-lg font-semibold text-white">Open scanner</p>
                  <p className="text-sm text-slate-400">Filter ranked opportunities by action, signal, and conviction.</p>
                </div>
              </div>
            </Link>
            <Link
              to="/history"
              className="rounded-[28px] border border-white/8 bg-slate-950/60 p-5 transition hover:border-cyan-400/30"
            >
              <div className="flex items-center gap-3">
                <Waves className="size-5 text-cyan-200" />
                <div>
                  <p className="text-lg font-semibold text-white">Review track record</p>
                  <p className="text-sm text-slate-400">Inspect past calls, replay frozen snapshots, and export decision history.</p>
                </div>
              </div>
            </Link>
            <Link
              to="/settings"
              className="rounded-[28px] border border-white/8 bg-slate-950/60 p-5 transition hover:border-cyan-400/30"
            >
              <div className="flex items-center gap-3">
                <ShieldCheck className="size-5 text-cyan-200" />
                <div>
                  <p className="text-lg font-semibold text-white">Tune the engine</p>
                  <p className="text-sm text-slate-400">Adjust thresholds, cadence, and pipeline preferences without leaving the terminal.</p>
                </div>
              </div>
            </Link>
          </div>
        </Panel>
      </div>
    </div>
  );
}
