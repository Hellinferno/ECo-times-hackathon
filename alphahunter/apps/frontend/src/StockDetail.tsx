/**
 * StockDetail — deep-dive intelligence page for a single NSE stock.
 *
 * Tabs:
 *   overview    AI reasoning narrative + confidence score breakdown
 *   signals     Signal stack cards with strength and diagnostics JSON
 *   backtest    Historical pattern match summary + methodology note + case table
 *   trade plan  Entry / target / stop-loss metrics + execution notes
 *   chart       6-month Recharts price + volume with signal markers and level lines
 *
 * Data: stock detail loads on mount; chart loads lazily on first visit to the
 * chart tab. Watchlist status is loaded alongside the detail via Promise.all.
 */
import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  ArrowLeft,
  BarChart3,
  BookOpen,
  CandlestickChart,
  ShieldAlert,
  Sparkles,
  Star,
  Target,
  TrendingUp,
} from "lucide-react";
import {
  Area,
  Bar,
  CartesianGrid,
  ComposedChart,
  Legend,
  ReferenceDot,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  api,
  type StockChartResponse,
  type StockDetailResponse,
} from "./api/client";
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
  formatConfidenceBand,
  formatCurrency,
  formatDate,
  formatDateTime,
  formatPercent,
} from "./lib/format";

type DetailTab = "overview" | "signals" | "backtest" | "trade" | "chart";

function getCaseNumber(record: Record<string, unknown>, key: string) {
  const value = record[key];
  if (typeof value === "number") return value;
  if (typeof value === "string") {
    const parsed = Number(value);
    return Number.isNaN(parsed) ? null : parsed;
  }
  return null;
}

function getCaseText(record: Record<string, unknown>, key: string) {
  const value = record[key];
  return typeof value === "string" ? value : null;
}

export default function StockDetail() {
  const { symbol } = useParams<{ symbol: string }>();
  const [detail, setDetail] = useState<StockDetailResponse | null>(null);
  const [chart, setChart] = useState<StockChartResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [chartLoading, setChartLoading] = useState(false);
  const [error, setError] = useState("");
  const [tab, setTab] = useState<DetailTab>("overview");
  const [inWatchlist, setInWatchlist] = useState(false);

  useEffect(() => {
    if (!symbol) return;
    let cancelled = false;

    const loadDetail = async () => {
      try {
        const [detailResponse, watchlistResponse] = await Promise.all([
          api.getStockDetail(symbol),
          api.getWatchlist(),
        ]);
        if (cancelled) return;
        setDetail(detailResponse.data);
        setInWatchlist(
          watchlistResponse.data.items.some(
            (item) => item.symbol.toUpperCase() === symbol.toUpperCase(),
          ),
        );
        setError("");
      } catch (detailError) {
        if (cancelled) return;
        setError(detailError instanceof Error ? detailError.message : "Unable to load stock detail.");
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    void loadDetail();

    return () => {
      cancelled = true;
    };
  }, [symbol]);

  useEffect(() => {
    if (!symbol || tab !== "chart" || chart) return;
    let cancelled = false;

    const loadChart = async () => {
      setChartLoading(true);
      try {
        const response = await api.getStockChart(symbol, { period: "6mo", interval: "1d" });
        if (!cancelled) {
          setChart(response.data);
          setError("");
        }
      } catch (chartError) {
        if (!cancelled) {
          setError(chartError instanceof Error ? chartError.message : "Unable to load chart.");
        }
      } finally {
        if (!cancelled) {
          setChartLoading(false);
        }
      }
    };

    void loadChart();

    return () => {
      cancelled = true;
    };
  }, [chart, symbol, tab]);

  const handleWatchlistToggle = async () => {
    if (!symbol) return;
    try {
      if (inWatchlist) {
        await api.removeFromWatchlist(symbol);
        setInWatchlist(false);
      } else {
        await api.addToWatchlist(symbol);
        setInWatchlist(true);
      }
      setError("");
    } catch (watchlistError) {
      setError(watchlistError instanceof Error ? watchlistError.message : "Unable to update watchlist.");
    }
  };

  const currentPrice = detail?.signals?.price ?? detail?.decision?.entry_price ?? null;
  const riskPerShare = useMemo(() => {
    if (!detail?.decision?.entry_price || !detail.decision.stop_loss) return null;
    return detail.decision.entry_price - detail.decision.stop_loss;
  }, [detail?.decision?.entry_price, detail?.decision?.stop_loss]);
  const rewardPerShare = useMemo(() => {
    if (!detail?.decision?.entry_price || !detail.decision.target_price) return null;
    return detail.decision.target_price - detail.decision.entry_price;
  }, [detail?.decision?.entry_price, detail?.decision?.target_price]);

  if (loading) {
    return <LoadingState label="Loading stock intelligence..." />;
  }

  if (error && !detail) {
    return <ErrorState description={error} />;
  }

  if (!detail || !symbol) {
    return (
      <EmptyState
        title="Stock not found"
        description="The requested stock is not available in the AlphaHunter universe."
        action={
          <Link to="/scanner">
            <Button variant="secondary">Return to scanner</Button>
          </Link>
        }
      />
    );
  }

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-center gap-3">
        <Link to="/scanner" className="inline-flex items-center gap-2 text-sm text-slate-400 hover:text-white">
          <ArrowLeft className="size-4" />
          Back to scanner
        </Link>
        <StatusBadge
          label={detail.decision?.action ?? "Unscored"}
          tone={
            detail.decision?.action === "BUY"
              ? "positive"
              : detail.decision?.action === "WATCH"
                ? "warning"
                : detail.decision?.action === "AVOID"
                  ? "danger"
                  : "neutral"
          }
        />
      </div>

      <PageHeader
        eyebrow="Stock detail"
        title={`${detail.stock.symbol} - ${detail.stock.name}`}
        description={
          detail.meta?.scanned_at
            ? `Latest analysis recorded ${formatDateTime(detail.meta.scanned_at)}.`
            : "No completed scan is available for this stock yet."
        }
        actions={
          <Button variant={inWatchlist ? "secondary" : "primary"} onClick={() => void handleWatchlistToggle()}>
            <Star className="size-4" />
            {inWatchlist ? "In watchlist" : "Add to watchlist"}
          </Button>
        }
      />

      {error ? <ErrorState description={error} /> : null}

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          label="Current price"
          value={formatCurrency(currentPrice)}
          detail={detail.stock.sector ?? "NSE equity"}
        />
        <MetricCard
          label="Confidence"
          value={formatPercent(detail.decision?.confidence)}
          detail={formatConfidenceBand(detail.decision?.confidence)}
          tone="positive"
        />
        <MetricCard
          label="Signal count"
          value={detail.signals?.signal_count ?? 0}
          detail="Triggered signal families in the latest analysis."
          tone="warning"
        />
        <MetricCard
          label="Backtest success"
          value={formatPercent(detail.backtest?.success_rate)}
          detail={`${detail.backtest?.matches ?? 0} matching historical cases`}
        />
      </div>

      <SectionTabs
        value={tab}
        onChange={setTab}
        tabs={[
          { value: "overview", label: "Overview" },
          { value: "signals", label: "Signals" },
          { value: "backtest", label: "Backtest" },
          { value: "trade", label: "Trade plan" },
          { value: "chart", label: "Chart" },
        ]}
      />

      {tab === "overview" ? (
        <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
          <Panel title="AI reasoning" subtitle="A concise narrative grounded in the signal and backtest data.">
            <div className="space-y-4">
              <div className="flex items-center gap-3 text-cyan-200">
                <Sparkles className="size-5" />
                <span className="text-sm font-medium">Current recommendation narrative</span>
              </div>
              <p className="text-sm leading-7 text-slate-300">
                {detail.reasoning?.llm_summary || "No reasoning is available yet for this stock."}
              </p>
              {detail.reasoning?.key_factors?.length ? (
                <div className="grid gap-3 md:grid-cols-2">
                  {detail.reasoning.key_factors.map((factor) => (
                    <div
                      key={factor}
                      className="rounded-[24px] border border-white/8 bg-slate-950/70 px-4 py-3 text-sm text-slate-200"
                    >
                      {factor}
                    </div>
                  ))}
                </div>
              ) : null}
              {detail.reasoning?.risk_warnings?.length ? (
                <div className="rounded-[24px] border border-rose-500/20 bg-rose-500/6 p-4">
                  <p className="text-sm font-medium text-white">Risk warnings</p>
                  <ul className="mt-3 space-y-2 text-sm text-rose-100/85">
                    {detail.reasoning.risk_warnings.map((warning) => (
                      <li key={warning}>{warning}</li>
                    ))}
                  </ul>
                </div>
              ) : null}
            </div>
          </Panel>

          <Panel title="Confidence explainer" subtitle="How the recommendation was assembled from component scores.">
            <div className="grid gap-4">
              <MetricCard
                label="Signal score"
                value={formatPercent(detail.decision?.score_breakdown.signal_score != null ? detail.decision.score_breakdown.signal_score * 100 : null)}
                detail="Relative strength of the current triggered signals."
              />
              <MetricCard
                label="Backtest score"
                value={formatPercent(detail.decision?.score_breakdown.backtest_score != null ? detail.decision.score_breakdown.backtest_score * 100 : null)}
                detail="Historical pattern quality from similar setups."
              />
              <MetricCard
                label="Composite score"
                value={formatPercent(detail.decision?.score_breakdown.composite_score != null ? detail.decision.score_breakdown.composite_score * 100 : null)}
                detail="Blended final score used by the decision engine."
                tone="positive"
              />
              <div className="rounded-[24px] border border-white/8 bg-slate-950/70 p-4 text-sm text-slate-300">
                <p className="font-medium text-white">Interpretation guide</p>
                <p className="mt-2">Above 70% means high conviction, 50-69% means watch closely, below 50% means the setup lacks enough evidence.</p>
              </div>
            </div>
          </Panel>
        </div>
      ) : null}

      {tab === "signals" ? (
        <div className="space-y-6">
          <Panel title="Signal stack" subtitle="Each signal shows trigger state, captured detail, and strength.">
            {!detail.signals?.items.length ? (
              <EmptyState
                title="No signal details available"
                description="Run a new scan to repopulate the signal layer for this stock."
              />
            ) : (
              <div className="grid gap-4 xl:grid-cols-3">
                {detail.signals.items.map((signal) => (
                  <article
                    key={signal.key}
                    className="rounded-[28px] border border-white/8 bg-slate-950/60 p-5"
                  >
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <p className="text-sm font-medium text-white">{signal.label}</p>
                        <p className="mt-1 text-xs uppercase tracking-[0.18em] text-slate-500">{signal.key.replace(/_/g, " ")}</p>
                      </div>
                      <StatusBadge label={signal.triggered ? "Triggered" : "Inactive"} tone={signal.triggered ? "positive" : "neutral"} />
                    </div>
                    <div className="mt-4 rounded-[24px] border border-white/8 bg-slate-950/80 px-4 py-3">
                      <p className="text-[11px] uppercase tracking-[0.18em] text-slate-500">Strength</p>
                      <p className="mt-2 text-lg font-semibold text-white">{signal.strength != null ? signal.strength.toFixed(2) : "NA"}</p>
                    </div>
                    <pre className="mt-4 overflow-x-auto rounded-[24px] bg-slate-950 p-4 text-xs text-slate-300">
                      {JSON.stringify(signal.details, null, 2)}
                    </pre>
                  </article>
                ))}
              </div>
            )}
          </Panel>

          <Panel title="Diagnostics" subtitle="Operational context captured with the signal evaluation.">
            <pre className="overflow-x-auto rounded-[28px] bg-slate-950 p-4 text-xs text-slate-300">
              {JSON.stringify(detail.signals?.diagnostics ?? {}, null, 2)}
            </pre>
          </Panel>
        </div>
      ) : null}

      {tab === "backtest" ? (
        <div className="space-y-6">
          <Panel title="Backtest summary" subtitle="Historical pattern matching for comparable signal setups.">
            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
              <MetricCard label="Matches" value={detail.backtest?.matches ?? 0} detail="Comparable historical setups found." />
              <MetricCard label="Success rate" value={formatPercent(detail.backtest?.success_rate)} detail="Profitable match ratio." tone="positive" />
              <MetricCard label="Average return" value={formatPercent(detail.backtest?.avg_return_pct, true)} detail="Mean T+5 return." tone="warning" />
              <MetricCard label="Worst case" value={formatPercent(detail.backtest?.worst_case_pct, true)} detail="Historical downside bound." tone="danger" />
            </div>
          </Panel>

          <Panel title="Methodology note" subtitle="How AlphaHunter produces the historical replay summary.">
            <div className="rounded-[28px] border border-white/8 bg-slate-950/60 p-5 text-sm leading-7 text-slate-300">
              AlphaHunter looks back {detail.meta?.backtest_lookback_years ?? "2"} years for similar signal combinations and measures results over {detail.meta?.backtest_outcome_days ?? "5"} trading days. The panel is intended to build trust, not promise future performance.
            </div>
          </Panel>

          <Panel title="Historical cases" subtitle="Recent historical matches with their recorded returns.">
            {!detail.backtest?.cases.length ? (
              <EmptyState
                title="No backtest cases available"
                description="This stock does not currently have enough historical pattern matches for a reliable backtest table."
              />
            ) : (
              <div className="overflow-x-auto">
                <table className="terminal-table">
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Entry</th>
                      <th>Exit</th>
                      <th>Return</th>
                    </tr>
                  </thead>
                  <tbody>
                    {detail.backtest.cases.map((caseItem, index) => {
                      const caseDate = getCaseText(caseItem, "date");
                      const entryPrice = getCaseNumber(caseItem, "entry_price");
                      const exitPrice = getCaseNumber(caseItem, "exit_price");
                      const returnPct = getCaseNumber(caseItem, "return_pct");

                      return (
                        <tr key={`${caseDate ?? "case"}-${index}`}>
                          <td>{caseDate ? formatDate(caseDate) : "NA"}</td>
                          <td>{formatCurrency(entryPrice)}</td>
                          <td>{formatCurrency(exitPrice)}</td>
                          <td className={returnPct != null && returnPct >= 0 ? "text-emerald-300" : "text-rose-300"}>
                            {formatPercent(returnPct, true)}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </Panel>
        </div>
      ) : null}

      {tab === "trade" ? (
        <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
          <Panel title="Trade plan" subtitle="Trade-ready output generated by the decision engine.">
            <div className="grid gap-4 md:grid-cols-3">
              <MetricCard label="Entry price" value={formatCurrency(detail.decision?.entry_price)} />
              <MetricCard label="Target price" value={formatCurrency(detail.decision?.target_price)} tone="positive" />
              <MetricCard label="Stop loss" value={formatCurrency(detail.decision?.stop_loss)} tone="danger" />
            </div>
            <div className="mt-6 grid gap-4 md:grid-cols-3">
              <MetricCard label="Risk per share" value={formatCurrency(riskPerShare)} detail="Entry minus stop loss." tone="danger" />
              <MetricCard label="Reward per share" value={formatCurrency(rewardPerShare)} detail="Target minus entry." tone="positive" />
              <MetricCard label="R:R ratio" value={detail.decision?.rr_ratio != null ? `${detail.decision.rr_ratio.toFixed(2)}x` : "NA"} detail="Targeted payoff ratio." />
            </div>
          </Panel>

          <Panel title="Execution notes" subtitle="Context to keep the trade plan disciplined.">
            <div className="space-y-4">
              <div className="rounded-[24px] border border-white/8 bg-slate-950/65 p-4">
                <div className="flex items-center gap-3 text-slate-200">
                  <Target className="size-5 text-emerald-300" />
                  <span className="font-medium">Profit objective</span>
                </div>
                <p className="mt-3 text-sm leading-7 text-slate-300">
                  The target is based on the decision engine output and should be reviewed against the chart tab before live execution.
                </p>
              </div>
              <div className="rounded-[24px] border border-white/8 bg-slate-950/65 p-4">
                <div className="flex items-center gap-3 text-slate-200">
                  <ShieldAlert className="size-5 text-rose-300" />
                  <span className="font-medium">Risk guardrail</span>
                </div>
                <p className="mt-3 text-sm leading-7 text-slate-300">
                  The stop loss is the discipline point. A trade with low conviction or weak historical support should be sized conservatively.
                </p>
              </div>
            </div>
          </Panel>
        </div>
      ) : null}

      {tab === "chart" ? (
        <Panel title="Chart view" subtitle="Six-month price context with volume and stored signal markers.">
          {chartLoading ? (
            <LoadingState label="Loading price chart..." />
          ) : !chart?.ohlcv.length ? (
            <EmptyState
              title="Chart data unavailable"
              description="AlphaHunter could not fetch chart data for this symbol right now."
            />
          ) : (
            <div className="space-y-6">
              <div className="grid gap-4 md:grid-cols-3">
                <MetricCard label="Resistance" value={formatCurrency(chart.resistance_level)} detail="Latest breakout reference level." />
                <MetricCard label="Support / stop" value={formatCurrency(chart.support_level)} detail="Current downside guardrail." tone="danger" />
                <MetricCard label="Target" value={formatCurrency(chart.target_price)} detail="Decision engine target." tone="positive" />
              </div>
              <div className="h-[420px] w-full rounded-[28px] border border-white/8 bg-slate-950/80 p-4">
                <ResponsiveContainer width="100%" height="100%">
                  <ComposedChart data={chart.ohlcv}>
                    <CartesianGrid stroke="rgba(148, 163, 184, 0.12)" strokeDasharray="3 3" />
                    <XAxis dataKey="date" tick={{ fill: "#94a3b8", fontSize: 11 }} />
                    <YAxis yAxisId="price" tick={{ fill: "#94a3b8", fontSize: 11 }} />
                    <YAxis yAxisId="volume" orientation="right" tick={{ fill: "#64748b", fontSize: 11 }} />
                    <Tooltip
                      contentStyle={{
                        borderRadius: "16px",
                        border: "1px solid rgba(148, 163, 184, 0.15)",
                        backgroundColor: "rgba(2, 6, 23, 0.95)",
                        color: "#f8fafc",
                      }}
                    />
                    <Legend />
                    <Bar yAxisId="volume" dataKey="volume" fill="rgba(103, 232, 249, 0.18)" name="Volume" barSize={8} />
                    <Area
                      yAxisId="price"
                      type="monotone"
                      dataKey="close"
                      stroke="#67e8f9"
                      fill="rgba(34, 211, 238, 0.14)"
                      name="Close"
                      strokeWidth={2}
                    />
                    {chart.resistance_level != null ? (
                      <ReferenceLine yAxisId="price" y={chart.resistance_level} stroke="#fbbf24" strokeDasharray="4 4" label="Resistance" />
                    ) : null}
                    {chart.support_level != null ? (
                      <ReferenceLine yAxisId="price" y={chart.support_level} stroke="#fb7185" strokeDasharray="4 4" label="Support" />
                    ) : null}
                    {chart.target_price != null ? (
                      <ReferenceLine yAxisId="price" y={chart.target_price} stroke="#34d399" strokeDasharray="4 4" label="Target" />
                    ) : null}
                    {chart.signal_markers.map((marker) => (
                      <ReferenceDot
                        key={`${marker.date}-${marker.type}`}
                        yAxisId="price"
                        x={marker.date}
                        y={chart.ohlcv.find((point) => point.date === marker.date)?.close}
                        r={5}
                        fill={marker.profitable ? "#34d399" : "#fb7185"}
                        stroke="transparent"
                      />
                    ))}
                  </ComposedChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}
        </Panel>
      ) : null}

      <Panel title="Research links" subtitle="Follow-up routes for deeper product context.">
        <div className="flex flex-wrap gap-3">
          <Link to="/history">
            <Button variant="secondary">
              <BookOpen className="size-4" />
              Open audit history
            </Button>
          </Link>
          <Link to="/scanner">
            <Button variant="secondary">
              <BarChart3 className="size-4" />
              Return to scanner
            </Button>
          </Link>
          <Button variant="secondary" onClick={() => setTab("chart")}>
            <CandlestickChart className="size-4" />
            Jump to chart
          </Button>
          <Link to={`/workspaces?create=true&symbol=${symbol}`}>
            <Button variant="secondary">
              <BookOpen className="size-4" />
              Create Workspace
            </Button>
          </Link>
          <Link to={`/valuation-lab?workspace=${symbol}`}>
            <Button variant="secondary">
              <TrendingUp className="size-4" />
              Run Valuation
            </Button>
          </Link>
        </div>
      </Panel>
    </div>
  );
}
