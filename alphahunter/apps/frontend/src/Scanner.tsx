/**
 * Scanner — ranked opportunity board with live filters.
 *
 * Sections:
 *   PageHeader        — title, run-scan + reset-filters CTAs
 *   Metrics grid      — latest scan status, results, actionable count, threshold (4-up)
 *   Filter bar        — action, signal, minimum-confidence sliders
 *   Opportunity board — 2-col grid of ranked opportunity cards
 *
 * Filters re-trigger a fresh API fetch on every change (controlled inputs).
 * useScanCenter provides scan status and the triggerScan action.
 */
import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Filter, Radar, RefreshCw, Search } from "lucide-react";
import { api, type Opportunity } from "./api/client";
import { useScanCenter } from "./hooks/useScanCenter";
import { useApiLoad } from "./hooks/useApiLoad";
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
import {
  formatConfidenceBand,
  formatCurrency,
  formatDateTime,
  formatPercent,
  formatSignalLabel,
  getActionTone,
} from "./lib/format";

type ActionFilter = "" | "BUY" | "WATCH" | "AVOID";
type SignalFilter = "" | "breakout" | "volume_spike" | "bulk_deal";

export default function Scanner() {
  const { latestScan, triggerScan } = useScanCenter();
  const [actionFilter, setActionFilter] = useState<ActionFilter>("");
  const [signalFilter, setSignalFilter] = useState<SignalFilter>("");
  const [sectorFilter, setSectorFilter] = useState("");
  const [sectors, setSectors] = useState<string[]>([]);
  const [minConfidence, setMinConfidence] = useState(0);
  useEffect(() => {
    api.getSectors().then((resp) => setSectors(resp.data)).catch(() => {/* sectors optional */});
  }, []);

  const { data: oppData, loading, error } = useApiLoad(
    () => api.getOpportunities({
      action: actionFilter || undefined,
      signal: signalFilter || undefined,
      sector: sectorFilter || undefined,
      min_confidence: minConfidence || undefined,
      limit: 18,
    }),
    [actionFilter, signalFilter, sectorFilter, minConfidence, latestScan?.completed_at, latestScan?.status],
  );

  const opportunities: Opportunity[] = oppData?.opportunities ?? [];
  const total = oppData?.total ?? 0;

  const actionableCount = useMemo(
    () => opportunities.filter((opportunity) => opportunity.action !== "AVOID").length,
    [opportunities],
  );

  const clearFilters = () => {
    setActionFilter("");
    setSignalFilter("");
    setSectorFilter("");
    setMinConfidence(0);
  };

  const handleRunScan = async () => {
    try {
      await triggerScan();
      setError("");
    } catch (triggerError) {
      setError(triggerError instanceof Error ? triggerError.message : "Unable to trigger scan.");
    }
  };

  if (loading) {
    return <LoadingState label="Loading scanner..." />;
  }

  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="Scanner"
        title="Scan, filter, and rank live opportunities."
        description="The scanner turns the latest scan run into an investor-ready opportunity board with action, signal, and conviction filters."
        actions={
          <>
            <Button onClick={handleRunScan}>
              <Radar className="size-4" />
              Run scan
            </Button>
            <Button variant="secondary" onClick={clearFilters}>
              Reset filters
            </Button>
          </>
        }
      />

      {error ? <ErrorState description={error} /> : null}

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          label="Latest scan"
          value={latestScan?.status ?? "idle"}
          detail={latestScan?.completed_at ? formatDateTime(latestScan.completed_at) : "No completed scan yet"}
        />
        <MetricCard
          label="Results"
          value={total}
          detail="Total matching names after filters."
          tone="positive"
        />
        <MetricCard
          label="Actionable"
          value={actionableCount}
          detail="BUY and WATCH names in the current board."
          tone="warning"
        />
        <MetricCard
          label="Threshold"
          value={minConfidence ? formatPercent(minConfidence) : "Any"}
          detail={formatConfidenceBand(minConfidence)}
        />
      </div>

      <Panel
        title="Filter bar"
        subtitle="Slice the ranked board by decision action, signal family, and minimum conviction."
      >
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-[1fr_1fr_1fr_1.3fr_auto]">
          <label className="space-y-2">
            <span className="flex items-center gap-2 text-sm font-medium text-white">
              <Filter className="size-4 text-cyan-200" />
              Action
            </span>
            <select
              value={actionFilter}
              onChange={(event) => setActionFilter(event.target.value as ActionFilter)}
              className="terminal-select"
            >
              <option value="">All actions</option>
              <option value="BUY">BUY</option>
              <option value="WATCH">WATCH</option>
              <option value="AVOID">AVOID</option>
            </select>
          </label>

          <label className="space-y-2">
            <span className="flex items-center gap-2 text-sm font-medium text-white">
              <Search className="size-4 text-cyan-200" />
              Signal
            </span>
            <select
              value={signalFilter}
              onChange={(event) => setSignalFilter(event.target.value as SignalFilter)}
              className="terminal-select"
            >
              <option value="">All signals</option>
              <option value="breakout">Breakout</option>
              <option value="volume_spike">Volume spike</option>
              <option value="bulk_deal">Bulk deal</option>
            </select>
          </label>

          <label className="space-y-2">
            <span className="flex items-center gap-2 text-sm font-medium text-white">
              <Filter className="size-4 text-cyan-200" />
              Sector
            </span>
            <select
              value={sectorFilter}
              onChange={(event) => setSectorFilter(event.target.value)}
              className="terminal-select"
            >
              <option value="">All sectors</option>
              {sectors.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </label>

          <label className="space-y-2">
            <span className="text-sm font-medium text-white">Minimum confidence</span>
            <div className="rounded-[24px] border border-white/8 bg-slate-950/70 px-4 py-3">
              <input
                type="range"
                min={0}
                max={100}
                step={5}
                value={minConfidence}
                onChange={(event) => setMinConfidence(Number(event.target.value))}
                className="w-full accent-cyan-300"
              />
              <div className="mt-2 flex items-center justify-between text-xs text-slate-400">
                <span>0%</span>
                <span>{minConfidence}%</span>
                <span>100%</span>
              </div>
            </div>
          </label>

          <div className="flex items-end">
            <Button variant="secondary" onClick={clearFilters} className="w-full">
              <RefreshCw className="size-4" />
              Clear filters
            </Button>
          </div>
        </div>
      </Panel>

      <Panel title="Opportunity board" subtitle="Ranked opportunities from the latest reference scan run.">
        {opportunities.length === 0 ? (
          <EmptyState
            title="No names match the active filters"
            description="Relax one of the filters or trigger a fresh scan to repopulate the board."
            action={<Button onClick={clearFilters}>Reset filters</Button>}
          />
        ) : (
          <div className="grid gap-4 xl:grid-cols-2">
            {opportunities.map((opportunity) => (
              <article
                key={opportunity.decision_id}
                className="rounded-[28px] border border-white/8 bg-slate-950/60 p-5 transition hover:border-cyan-400/30"
              >
                <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                  <div>
                    <p className="text-xs uppercase tracking-[0.24em] text-slate-500">{opportunity.name}</p>
                    <div className="mt-2 flex items-center gap-3">
                      <h3 className="text-2xl font-semibold text-white">{opportunity.symbol}</h3>
                      <StatusBadge
                        label={opportunity.action}
                        tone={getActionTone(opportunity.action)}
                      />
                    </div>
                    <p className="mt-3 text-sm text-slate-300">
                      {opportunity.reasoning.llm_summary || "No fresh AI reasoning available for this scan row."}
                    </p>
                  </div>
                  <div className="grid min-w-[180px] grid-cols-2 gap-3">
                    <div className="rounded-2xl border border-white/8 bg-slate-900/70 px-3 py-3">
                      <p className="text-[11px] uppercase tracking-[0.18em] text-slate-500">Entry</p>
                      <p className="mt-2 text-sm font-medium text-white">{formatCurrency(opportunity.entry_price)}</p>
                    </div>
                    <div className="rounded-2xl border border-white/8 bg-slate-900/70 px-3 py-3">
                      <p className="text-[11px] uppercase tracking-[0.18em] text-slate-500">Confidence</p>
                      <p className="mt-2 text-sm font-medium text-white">{formatPercent(opportunity.confidence)}</p>
                    </div>
                    <div className="rounded-2xl border border-white/8 bg-slate-900/70 px-3 py-3">
                      <p className="text-[11px] uppercase tracking-[0.18em] text-slate-500">Target</p>
                      <p className="mt-2 text-sm font-medium text-emerald-300">{formatCurrency(opportunity.target_price)}</p>
                    </div>
                    <div className="rounded-2xl border border-white/8 bg-slate-900/70 px-3 py-3">
                      <p className="text-[11px] uppercase tracking-[0.18em] text-slate-500">Stop</p>
                      <p className="mt-2 text-sm font-medium text-rose-300">{formatCurrency(opportunity.stop_loss)}</p>
                    </div>
                  </div>
                </div>

                <div className="mt-5 flex flex-wrap gap-2">
                  {opportunity.signals.map((signal) => (
                    <span
                      key={signal}
                      className="rounded-full border border-cyan-400/15 bg-cyan-400/8 px-3 py-1 text-xs font-medium text-cyan-100"
                    >
                      {formatSignalLabel(signal)}
                    </span>
                  ))}
                </div>

                <div className="mt-6 flex items-center justify-between">
                  <p className="text-sm text-slate-400">
                    Last scanned {opportunity.scanned_at ? formatDateTime(opportunity.scanned_at) : "NA"}
                  </p>
                  <Link
                    to={`/stock/${opportunity.symbol}`}
                    className="text-sm font-medium text-cyan-200 hover:text-white"
                  >
                    Open detail
                  </Link>
                </div>
              </article>
            ))}
          </div>
        )}
      </Panel>
    </div>
  );
}
