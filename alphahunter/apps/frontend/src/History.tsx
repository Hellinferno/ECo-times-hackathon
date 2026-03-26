import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { api } from "./api/client";
import type { DecisionEntry, ScanRun } from "./api/client";
import {
  History as HistoryIcon,
  CheckCircle2,
  ServerCrash,
  TrendingUp,
  TrendingDown,
  Filter,
} from "lucide-react";

type View = "decisions" | "scans";

export default function History() {
  const [view, setView] = useState<View>("decisions");
  const [decisions, setDecisions] = useState<DecisionEntry[]>([]);
  const [scans, setScans] = useState<ScanRun[]>([]);
  const [trackRecord, setTrackRecord] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [actionFilter, setActionFilter] = useState("");

  useEffect(() => {
    setLoading(true);
    if (view === "decisions") {
      api
        .getDecisionHistory(actionFilter || undefined)
        .then((res) => {
          setDecisions(res.data.decisions);
          setTrackRecord(res.data.track_record);
        })
        .catch(console.error)
        .finally(() => setLoading(false));
    } else {
      api
        .getScanHistory()
        .then((res) => setScans(res.data))
        .catch(console.error)
        .finally(() => setLoading(false));
    }
  }, [view, actionFilter]);

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-black text-white flex items-center gap-2">
          <HistoryIcon className="text-blue-400" size={24} />
          History
        </h1>
        <div className="flex gap-2">
          <div className="flex bg-gray-800 rounded-lg p-0.5 border border-gray-700">
            <button
              onClick={() => setView("decisions")}
              className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
                view === "decisions"
                  ? "bg-gray-700 text-white"
                  : "text-gray-400 hover:text-white"
              }`}
            >
              Decisions
            </button>
            <button
              onClick={() => setView("scans")}
              className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
                view === "scans"
                  ? "bg-gray-700 text-white"
                  : "text-gray-400 hover:text-white"
              }`}
            >
              Scan Runs
            </button>
          </div>
        </div>
      </div>

      {/* Track record summary */}
      {view === "decisions" && trackRecord && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <div className="bg-gray-800 p-4 rounded-xl border border-gray-700 text-center">
            <span className="text-gray-400 text-xs font-bold uppercase">
              Total
            </span>
            <p className="text-xl font-bold text-white">
              {trackRecord.total_decisions}
            </p>
          </div>
          <div className="bg-gray-800 p-4 rounded-xl border border-gray-700 text-center">
            <span className="text-gray-400 text-xs font-bold uppercase">
              Measured
            </span>
            <p className="text-xl font-bold text-white">
              {trackRecord.measured}
            </p>
          </div>
          <div className="bg-gray-800 p-4 rounded-xl border border-gray-700 text-center">
            <span className="text-gray-400 text-xs font-bold uppercase">
              Wins
            </span>
            <p className="text-xl font-bold text-green-400">
              {trackRecord.wins}
            </p>
          </div>
          <div className="bg-gray-800 p-4 rounded-xl border border-green-900/30 text-center">
            <span className="text-gray-400 text-xs font-bold uppercase">
              Win Rate
            </span>
            <p className="text-xl font-bold text-green-400">
              {trackRecord.win_rate != null ? `${trackRecord.win_rate}%` : "-"}
            </p>
          </div>
          <div className="bg-gray-800 p-4 rounded-xl border border-blue-900/30 text-center">
            <span className="text-gray-400 text-xs font-bold uppercase">
              Avg Return
            </span>
            <p className="text-xl font-bold text-blue-400">
              {trackRecord.avg_return_pct != null
                ? `${trackRecord.avg_return_pct > 0 ? "+" : ""}${trackRecord.avg_return_pct}%`
                : "-"}
            </p>
          </div>
        </div>
      )}

      {/* Filter for decisions */}
      {view === "decisions" && (
        <div className="flex items-center gap-2">
          <Filter size={16} className="text-gray-400" />
          <select
            value={actionFilter}
            onChange={(e) => setActionFilter(e.target.value)}
            aria-label="Filter by action"
            className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:border-blue-500"
          >
            <option value="">All Actions</option>
            <option value="BUY">BUY</option>
            <option value="WATCH">WATCH</option>
            <option value="AVOID">AVOID</option>
          </select>
        </div>
      )}

      {/* Content */}
      <div className="bg-gray-800 rounded-xl shadow-lg border border-gray-700 overflow-hidden">
        {loading ? (
          <div className="flex justify-center py-10">
            <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : view === "decisions" ? (
          <DecisionTable decisions={decisions} />
        ) : (
          <ScanTable scans={scans} />
        )}
      </div>
    </div>
  );
}

function DecisionTable({ decisions }: { decisions: DecisionEntry[] }) {
  if (decisions.length === 0) {
    return (
      <div className="text-center py-10 text-gray-400">
        No decisions recorded yet.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-sm text-gray-300">
        <thead className="bg-gray-900 text-gray-400 uppercase text-xs">
          <tr>
            <th className="px-4 py-3">Stock</th>
            <th className="px-4 py-3">Action</th>
            <th className="px-4 py-3">Confidence</th>
            <th className="px-4 py-3">Entry</th>
            <th className="px-4 py-3">Target</th>
            <th className="px-4 py-3">SL</th>
            <th className="px-4 py-3">Date</th>
            <th className="px-4 py-3">Outcome</th>
          </tr>
        </thead>
        <tbody>
          {decisions.map((d) => (
            <tr
              key={d.decision_id}
              className="border-b border-gray-700/50 hover:bg-gray-700/30 transition-colors"
            >
              <td className="px-4 py-3">
                <Link
                  to={`/stock/${d.symbol}`}
                  className="font-bold text-white hover:text-blue-400 transition-colors"
                >
                  {d.symbol}
                </Link>
              </td>
              <td className="px-4 py-3">
                <span
                  className={`px-2 py-0.5 text-xs font-bold rounded ${
                    d.action === "BUY"
                      ? "bg-green-900/50 text-green-400"
                      : d.action === "WATCH"
                      ? "bg-yellow-900/50 text-yellow-400"
                      : "bg-red-900/50 text-red-400"
                  }`}
                >
                  {d.action}
                </span>
              </td>
              <td className="px-4 py-3 font-mono text-blue-400">
                {d.confidence}%
              </td>
              <td className="px-4 py-3 font-mono">
                {d.entry_price ? `₹${d.entry_price}` : "-"}
              </td>
              <td className="px-4 py-3 font-mono text-green-400">
                {d.target_price ? `₹${d.target_price}` : "-"}
              </td>
              <td className="px-4 py-3 font-mono text-red-400">
                {d.stop_loss ? `₹${d.stop_loss}` : "-"}
              </td>
              <td className="px-4 py-3 text-xs text-gray-400">
                {new Date(d.decided_at).toLocaleString()}
              </td>
              <td className="px-4 py-3">
                {d.outcome_measured ? (
                  <div className="flex items-center gap-1">
                    {d.outcome_result === "WIN" ? (
                      <TrendingUp size={14} className="text-green-400" />
                    ) : (
                      <TrendingDown size={14} className="text-red-400" />
                    )}
                    <span
                      className={`font-mono text-xs font-bold ${
                        d.outcome_result === "WIN"
                          ? "text-green-400"
                          : "text-red-400"
                      }`}
                    >
                      {d.outcome_return_pct != null
                        ? `${d.outcome_return_pct > 0 ? "+" : ""}${d.outcome_return_pct}%`
                        : d.outcome_result}
                    </span>
                  </div>
                ) : (
                  <span className="text-gray-500 text-xs">Pending</span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ScanTable({ scans }: { scans: ScanRun[] }) {
  if (scans.length === 0) {
    return (
      <div className="text-center py-10 text-gray-400">
        No scans have been run yet.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-sm text-gray-300">
        <thead className="bg-gray-900 text-gray-400 uppercase text-xs">
          <tr>
            <th className="px-4 py-3">Status</th>
            <th className="px-4 py-3">Started At</th>
            <th className="px-4 py-3">Duration</th>
            <th className="px-4 py-3">Triggered By</th>
            <th className="px-4 py-3">Stocks Scanned</th>
            <th className="px-4 py-3">Signals Found</th>
          </tr>
        </thead>
        <tbody>
          {scans.map((run, idx) => (
            <tr
              key={run.id}
              className={`border-b border-gray-700/50 ${
                idx % 2 === 0 ? "bg-gray-800/50" : "bg-gray-800"
              }`}
            >
              <td className="px-4 py-4 font-medium flex items-center gap-2">
                {run.status === "completed" ? (
                  <CheckCircle2 className="text-emerald-500" size={16} />
                ) : (
                  <ServerCrash className="text-red-500" size={16} />
                )}
                <span
                  className={
                    run.status === "completed"
                      ? "text-emerald-400"
                      : "text-red-400"
                  }
                >
                  {run.status}
                </span>
              </td>
              <td className="px-4 py-4 font-mono">
                {new Date(run.started_at).toLocaleString()}
              </td>
              <td className="px-4 py-4">
                {run.duration_secs
                  ? `${Number(run.duration_secs).toFixed(2)}s`
                  : "-"}
              </td>
              <td className="px-4 py-4">{run.triggered_by}</td>
              <td className="px-4 py-4">{run.stocks_scanned}</td>
              <td className="px-4 py-4 font-bold text-white">
                {run.signals_found}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
