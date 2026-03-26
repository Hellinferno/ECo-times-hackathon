import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { api } from "./api/client";
import type { StockDetail as StockDetailType } from "./api/client";
import {
  ArrowLeft,
  Target,
  ShieldAlert,
  Zap,
  TrendingUp,
  BarChart3,
  Brain,
  FileText,
  Star,
} from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";

type Tab = "overview" | "signals" | "backtest" | "trade";

export default function StockDetail() {
  const { symbol } = useParams<{ symbol: string }>();
  const [data, setData] = useState<StockDetailType | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [tab, setTab] = useState<Tab>("overview");
  const [inWatchlist, setInWatchlist] = useState(false);

  useEffect(() => {
    if (!symbol) return;
    setLoading(true);
    api
      .getStockDetail(symbol)
      .then((res) => setData(res.data))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [symbol]);

  // Check watchlist
  useEffect(() => {
    api
      .getWatchlist()
      .then((res) => {
        if (res.data.some((w) => w.symbol === symbol?.toUpperCase())) {
          setInWatchlist(true);
        }
      })
      .catch(() => {});
  }, [symbol]);

  const toggleWatchlist = async () => {
    if (!symbol) return;
    try {
      if (inWatchlist) {
        await api.removeFromWatchlist(symbol);
        setInWatchlist(false);
      } else {
        await api.addToWatchlist(symbol);
        setInWatchlist(true);
      }
    } catch (e: any) {
      console.error(e);
    }
  };

  if (loading)
    return (
      <div className="flex justify-center py-20">
        <div className="w-10 h-10 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  if (error)
    return <div className="text-center py-20 text-red-400">{error}</div>;
  if (!data)
    return <div className="text-center py-20 text-gray-400">Not found.</div>;

  const { stock, decision, signals, reasoning, backtest } = data;

  const tabs: { key: Tab; label: string; icon: any }[] = [
    { key: "overview", label: "Overview", icon: FileText },
    { key: "signals", label: "Signals", icon: BarChart3 },
    { key: "backtest", label: "Backtest", icon: TrendingUp },
    { key: "trade", label: "Trade Plan", icon: Target },
  ];

  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-12">
      <div className="flex items-center justify-between">
        <Link
          to="/"
          className="inline-flex items-center text-gray-400 hover:text-white transition-colors"
        >
          <ArrowLeft size={20} className="mr-2" /> Back
        </Link>
        <button
          onClick={toggleWatchlist}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            inWatchlist
              ? "bg-yellow-900/50 text-yellow-400 border border-yellow-800"
              : "bg-gray-700 text-gray-300 hover:bg-gray-600"
          }`}
        >
          <Star size={16} fill={inWatchlist ? "currentColor" : "none"} />
          {inWatchlist ? "In Watchlist" : "Add to Watchlist"}
        </button>
      </div>

      {/* Header */}
      <div className="bg-gray-800 p-6 rounded-xl border border-gray-700">
        <div className="flex flex-col md:flex-row justify-between md:items-center gap-4">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-4xl font-black text-white">{stock.symbol}</h1>
              {decision && (
                <span
                  className={`px-3 py-1 text-sm font-black tracking-wider rounded-lg ${
                    decision.action === "BUY"
                      ? "bg-green-900/50 text-green-400 border border-green-800"
                      : decision.action === "WATCH"
                      ? "bg-yellow-900/50 text-yellow-400 border border-yellow-800"
                      : "bg-red-900/50 text-red-400 border border-red-800"
                  }`}
                >
                  {decision.action}
                </span>
              )}
            </div>
            <p className="text-gray-400 mt-1">{stock.name}</p>
            {stock.sector && (
              <span className="text-xs bg-gray-700 text-gray-300 px-2 py-0.5 rounded mt-1 inline-block">
                {stock.sector}
              </span>
            )}
          </div>
          {decision && (
            <div className="flex gap-4">
              <div className="text-center bg-gray-900 px-6 py-3 rounded-lg border border-gray-700">
                <span className="block text-gray-500 text-xs font-bold uppercase tracking-wider">
                  Confidence
                </span>
                <span className="text-2xl font-mono font-black text-blue-400">
                  {decision.confidence}%
                </span>
              </div>
              {decision.rr_ratio && (
                <div className="text-center bg-gray-900 px-6 py-3 rounded-lg border border-gray-700">
                  <span className="block text-gray-500 text-xs font-bold uppercase tracking-wider">
                    R:R
                  </span>
                  <span className="text-2xl font-mono font-black text-purple-400">
                    {decision.rr_ratio}x
                  </span>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-gray-800 p-1 rounded-lg border border-gray-700">
        {tabs.map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            onClick={() => setTab(key)}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-md text-sm font-medium transition-colors flex-1 justify-center ${
              tab === key
                ? "bg-gray-700 text-white shadow"
                : "text-gray-400 hover:text-white"
            }`}
          >
            <Icon size={16} />
            {label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="bg-gray-800 p-6 rounded-xl border border-gray-700">
        {tab === "overview" && (
          <OverviewTab decision={decision} reasoning={reasoning} />
        )}
        {tab === "signals" && <SignalsTab signals={signals} />}
        {tab === "backtest" && <BacktestTab backtest={backtest} />}
        {tab === "trade" && <TradeTab decision={decision} />}
      </div>
    </div>
  );
}

function OverviewTab({ decision, reasoning }: { decision: any; reasoning: any }) {
  if (!decision) {
    return (
      <div className="text-center py-10 text-gray-400">
        No analysis available yet. Run a scan to generate insights.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-bold flex items-center gap-2 mb-4">
          <Brain size={20} className="text-emerald-400" /> AI Reasoning
        </h3>
        <p className="text-gray-300 leading-relaxed">
          {reasoning?.llm_summary || "No reasoning available."}
        </p>
        {reasoning?.key_factors && (
          <div className="mt-4">
            <h4 className="text-sm font-semibold text-gray-400 mb-2">
              Key Factors:
            </h4>
            <ul className="list-disc pl-5 text-sm text-emerald-400/80 space-y-1">
              {reasoning.key_factors.map((f: string, i: number) => (
                <li key={i}>{f}</li>
              ))}
            </ul>
          </div>
        )}
        {reasoning?.risk_warnings && (
          <div className="mt-4 pt-4 border-t border-gray-700">
            <h4 className="text-sm font-semibold text-gray-400 mb-2">
              Risk Warnings:
            </h4>
            <ul className="list-disc pl-5 text-sm text-red-400/80 space-y-1">
              {reasoning.risk_warnings.map((f: string, i: number) => (
                <li key={i}>{f}</li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {decision.outcome_measured && (
        <div className="bg-gray-900 p-5 rounded-xl border border-gray-700">
          <h3 className="text-lg font-bold mb-3">Outcome (T+5)</h3>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <span className="text-gray-400 text-sm">Result</span>
              <p
                className={`text-xl font-bold ${
                  decision.outcome_result === "WIN"
                    ? "text-green-400"
                    : "text-red-400"
                }`}
              >
                {decision.outcome_result}
              </p>
            </div>
            <div>
              <span className="text-gray-400 text-sm">Return</span>
              <p
                className={`text-xl font-bold ${
                  (decision.outcome_return_pct || 0) >= 0
                    ? "text-green-400"
                    : "text-red-400"
                }`}
              >
                {decision.outcome_return_pct
                  ? `${decision.outcome_return_pct > 0 ? "+" : ""}${decision.outcome_return_pct}%`
                  : "-"}
              </p>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-3 gap-4">
        <div className="bg-gray-900 p-4 rounded-xl border border-gray-700 text-center">
          <span className="text-gray-400 text-xs font-bold uppercase">
            Signal Score
          </span>
          <p className="text-xl font-mono font-bold text-blue-400 mt-1">
            {decision.score_signal
              ? (decision.score_signal * 100).toFixed(1)
              : "-"}
            %
          </p>
        </div>
        <div className="bg-gray-900 p-4 rounded-xl border border-gray-700 text-center">
          <span className="text-gray-400 text-xs font-bold uppercase">
            Backtest Score
          </span>
          <p className="text-xl font-mono font-bold text-purple-400 mt-1">
            {decision.score_backtest
              ? (decision.score_backtest * 100).toFixed(1)
              : "-"}
            %
          </p>
        </div>
        <div className="bg-gray-900 p-4 rounded-xl border border-gray-700 text-center">
          <span className="text-gray-400 text-xs font-bold uppercase">
            Composite
          </span>
          <p className="text-xl font-mono font-bold text-emerald-400 mt-1">
            {decision.score_composite
              ? (decision.score_composite * 100).toFixed(1)
              : "-"}
            %
          </p>
        </div>
      </div>
    </div>
  );
}

function SignalsTab({ signals }: { signals: any }) {
  if (!signals) {
    return (
      <div className="text-center py-10 text-gray-400">
        No signal data available.
      </div>
    );
  }

  const signalItems = [
    {
      name: "Breakout",
      active: signals.breakout,
      details: signals.breakout_details,
      color: "blue",
    },
    {
      name: "Volume Spike",
      active: signals.volume_spike,
      details: signals.volume_spike_details,
      color: "purple",
    },
    {
      name: "Bulk Deal",
      active: signals.bulk_deal,
      details: signals.bulk_deal_details,
      color: "emerald",
    },
  ];

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {signalItems.map((s) => (
          <div
            key={s.name}
            className={`p-5 rounded-xl border ${
              s.active
                ? `bg-${s.color}-900/20 border-${s.color}-800`
                : "bg-gray-900 border-gray-700"
            }`}
          >
            <div className="flex justify-between items-center mb-3">
              <span className="font-bold text-white">{s.name}</span>
              <span
                className={`px-2 py-0.5 text-xs font-bold rounded ${
                  s.active
                    ? "bg-green-900/50 text-green-400"
                    : "bg-gray-700 text-gray-500"
                }`}
              >
                {s.active ? "TRIGGERED" : "INACTIVE"}
              </span>
            </div>
            {s.active && s.details && (
              <div className="text-sm text-gray-400 space-y-1">
                {Object.entries(s.details).map(([k, v]) => (
                  <div key={k} className="flex justify-between">
                    <span>{k.replace(/_/g, " ")}</span>
                    <span className="text-white font-mono">
                      {typeof v === "number" ? Number(v).toFixed(2) : String(v)}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="bg-gray-900 p-5 rounded-xl border border-gray-700">
        <div className="grid grid-cols-4 gap-4 text-center">
          <div>
            <span className="text-gray-400 text-xs font-bold uppercase">
              Signals Active
            </span>
            <p className="text-2xl font-bold text-white">
              {signals.signal_count}/3
            </p>
          </div>
          <div>
            <span className="text-gray-400 text-xs font-bold uppercase">
              Price
            </span>
            <p className="text-2xl font-mono text-white">
              {signals.price ? `₹${signals.price}` : "-"}
            </p>
          </div>
          <div>
            <span className="text-gray-400 text-xs font-bold uppercase">
              Volume Ratio
            </span>
            <p className="text-2xl font-mono text-white">
              {signals.volume_ratio ? `${signals.volume_ratio}x` : "-"}
            </p>
          </div>
          <div>
            <span className="text-gray-400 text-xs font-bold uppercase">
              Composite
            </span>
            <p className="text-2xl font-mono text-emerald-400">
              {signals.composite_score
                ? `${(signals.composite_score * 100).toFixed(1)}%`
                : "-"}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

function BacktestTab({ backtest }: { backtest: any }) {
  if (!backtest || !backtest.matches) {
    return (
      <div className="text-center py-10 text-gray-400">
        No backtest data available. Historical pattern matching requires
        sufficient data.
      </div>
    );
  }

  const chartData = [
    { name: "Success Rate", value: backtest.success_rate || 0, fill: "#34d399" },
    { name: "Avg Return", value: Math.abs(backtest.avg_return || 0), fill: "#60a5fa" },
    { name: "Best Case", value: Math.abs(backtest.best_case || 0), fill: "#a78bfa" },
    {
      name: "Worst Case",
      value: Math.abs(backtest.worst_case || 0),
      fill: "#f87171",
    },
  ];

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-gray-900 p-4 rounded-xl border border-gray-700 text-center">
          <span className="text-gray-400 text-xs font-bold uppercase">
            Matches
          </span>
          <p className="text-2xl font-bold text-white">{backtest.matches}</p>
        </div>
        <div className="bg-gray-900 p-4 rounded-xl border border-green-900/30 text-center">
          <span className="text-gray-400 text-xs font-bold uppercase">
            Success Rate
          </span>
          <p className="text-2xl font-bold text-green-400">
            {backtest.success_rate ? `${backtest.success_rate}%` : "-"}
          </p>
        </div>
        <div className="bg-gray-900 p-4 rounded-xl border border-blue-900/30 text-center">
          <span className="text-gray-400 text-xs font-bold uppercase">
            Avg Return
          </span>
          <p className="text-2xl font-bold text-blue-400">
            {backtest.avg_return != null
              ? `${backtest.avg_return > 0 ? "+" : ""}${backtest.avg_return}%`
              : "-"}
          </p>
        </div>
        <div className="bg-gray-900 p-4 rounded-xl border border-gray-700 text-center">
          <span className="text-gray-400 text-xs font-bold uppercase">
            Range
          </span>
          <p className="text-sm font-mono mt-1">
            <span className="text-red-400">
              {backtest.worst_case != null ? `${backtest.worst_case}%` : "-"}
            </span>{" "}
            to{" "}
            <span className="text-green-400">
              {backtest.best_case != null ? `+${backtest.best_case}%` : "-"}
            </span>
          </p>
        </div>
      </div>

      <div className="bg-gray-900 p-5 rounded-xl border border-gray-700">
        <h4 className="text-sm font-bold text-gray-400 mb-4 uppercase">
          Backtest Metrics
        </h4>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis dataKey="name" tick={{ fill: "#9ca3af", fontSize: 12 }} />
            <YAxis tick={{ fill: "#9ca3af", fontSize: 12 }} />
            <Tooltip
              contentStyle={{
                backgroundColor: "#1f2937",
                border: "1px solid #374151",
                borderRadius: "8px",
              }}
            />
            <Bar dataKey="value" radius={[4, 4, 0, 0]}>
              {chartData.map((entry, i) => (
                <Cell key={i} fill={entry.fill} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {backtest.cases && backtest.cases.length > 0 && (
        <div className="bg-gray-900 p-5 rounded-xl border border-gray-700">
          <h4 className="text-sm font-bold text-gray-400 mb-4 uppercase">
            Historical Cases
          </h4>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="text-gray-400 text-xs uppercase border-b border-gray-700">
                <tr>
                  <th className="px-3 py-2">Date</th>
                  <th className="px-3 py-2">Entry</th>
                  <th className="px-3 py-2">Exit (T+5)</th>
                  <th className="px-3 py-2">Return</th>
                </tr>
              </thead>
              <tbody>
                {backtest.cases.map((c: any, i: number) => (
                  <tr key={i} className="border-b border-gray-800">
                    <td className="px-3 py-2 font-mono text-gray-300">
                      {c.date || "-"}
                    </td>
                    <td className="px-3 py-2 font-mono">
                      ₹{c.entry_price || "-"}
                    </td>
                    <td className="px-3 py-2 font-mono">
                      ₹{c.exit_price || "-"}
                    </td>
                    <td
                      className={`px-3 py-2 font-mono font-bold ${
                        (c.return_pct || 0) >= 0
                          ? "text-green-400"
                          : "text-red-400"
                      }`}
                    >
                      {c.return_pct != null
                        ? `${c.return_pct > 0 ? "+" : ""}${c.return_pct}%`
                        : "-"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

function TradeTab({ decision }: { decision: any }) {
  if (!decision || !decision.entry_price) {
    return (
      <div className="text-center py-10 text-gray-400">
        No trade plan available for this stock.
      </div>
    );
  }

  const risk = decision.entry_price - (decision.stop_loss || 0);
  const reward = (decision.target_price || 0) - decision.entry_price;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-gray-900 p-5 rounded-xl border border-gray-700 flex items-start gap-4">
          <div className="bg-blue-900/30 p-3 rounded-lg">
            <Zap className="text-blue-400" size={24} />
          </div>
          <div>
            <p className="text-gray-500 text-sm font-medium">Entry Price</p>
            <p className="text-2xl font-mono text-white">
              ₹{decision.entry_price}
            </p>
          </div>
        </div>
        <div className="bg-gray-900 p-5 rounded-xl border border-green-900/30 flex items-start gap-4">
          <div className="bg-green-900/30 p-3 rounded-lg">
            <Target className="text-green-400" size={24} />
          </div>
          <div>
            <p className="text-green-500/70 text-sm font-medium">
              Target Price
            </p>
            <p className="text-2xl font-mono text-green-400">
              ₹{decision.target_price}
            </p>
          </div>
        </div>
        <div className="bg-gray-900 p-5 rounded-xl border border-red-900/30 flex items-start gap-4">
          <div className="bg-red-900/30 p-3 rounded-lg">
            <ShieldAlert className="text-red-400" size={24} />
          </div>
          <div>
            <p className="text-red-500/70 text-sm font-medium">Stop Loss</p>
            <p className="text-2xl font-mono text-red-400">
              ₹{decision.stop_loss}
            </p>
          </div>
        </div>
      </div>

      <div className="bg-gray-900 p-5 rounded-xl border border-gray-700">
        <h4 className="text-sm font-bold text-gray-400 mb-4 uppercase">
          Risk/Reward Analysis
        </h4>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <span className="text-gray-400 text-xs font-bold uppercase">
              Risk (₹)
            </span>
            <p className="text-xl font-mono text-red-400">
              ₹{risk.toFixed(2)}
            </p>
          </div>
          <div className="text-center">
            <span className="text-gray-400 text-xs font-bold uppercase">
              Reward (₹)
            </span>
            <p className="text-xl font-mono text-green-400">
              ₹{reward.toFixed(2)}
            </p>
          </div>
          <div className="text-center">
            <span className="text-gray-400 text-xs font-bold uppercase">
              R:R Ratio
            </span>
            <p className="text-xl font-mono text-purple-400">
              {decision.rr_ratio}x
            </p>
          </div>
          <div className="text-center">
            <span className="text-gray-400 text-xs font-bold uppercase">
              Confidence
            </span>
            <p className="text-xl font-mono text-blue-400">
              {decision.confidence}%
            </p>
          </div>
        </div>

        {/* Visual risk/reward bar */}
        <div className="mt-6">
          <div className="flex items-center gap-2 text-xs text-gray-400 mb-2">
            <span>Stop Loss</span>
            <div className="flex-1" />
            <span>Entry</span>
            <div className="flex-1" />
            <span>Target</span>
          </div>
          <div className="flex h-4 rounded-full overflow-hidden">
            <div
              className="bg-red-500/60"
              style={{ flex: risk }}
            />
            <div className="w-1 bg-white" />
            <div
              className="bg-green-500/60"
              style={{ flex: reward }}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
