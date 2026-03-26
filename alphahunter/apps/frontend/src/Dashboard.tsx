import { useState, useEffect, useCallback } from "react";
import { Link } from "react-router-dom";
import { api } from "./api/client";
import type { Opportunity } from "./api/client";
import {
  PlayCircle,
  LayoutDashboard,
  ChevronRight,
  Filter,
} from "lucide-react";

export default function Dashboard() {
  const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
  const [loading, setLoading] = useState(false);
  const [running, setRunning] = useState(false);
  const [actionFilter, setActionFilter] = useState("");

  const fetchOpportunities = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.getOpportunities();
      if (res.success) setOpportunities(res.data);
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    fetchOpportunities();
  }, [fetchOpportunities]);

  const triggerScan = async () => {
    setRunning(true);
    try {
      const res = await api.triggerScan();
      if (res.success) {
        // Poll for completion
        const pollInterval = setInterval(async () => {
          try {
            const scanRes = await api.getScanHistory(1);
            const latest = scanRes.data[0];
            if (latest && latest.status !== "running") {
              clearInterval(pollInterval);
              fetchOpportunities();
              setRunning(false);
            }
          } catch {
            clearInterval(pollInterval);
            setRunning(false);
          }
        }, 3000);
      } else {
        setRunning(false);
      }
    } catch (e: any) {
      alert(e.message || "Scan failed");
      setRunning(false);
    }
  };

  const filtered = actionFilter
    ? opportunities.filter((o) => o.action === actionFilter)
    : opportunities;

  return (
    <div className="space-y-6">
      <header className="flex flex-col md:flex-row justify-between md:items-center gap-4 bg-gray-800 p-6 rounded-xl shadow-lg border border-gray-700">
        <div>
          <p className="text-gray-400 mt-1">Autonomous Opportunity Engine</p>
        </div>
        <button
          onClick={triggerScan}
          disabled={running}
          className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold px-6 py-3 rounded-lg transition-all disabled:opacity-50 shadow-lg shadow-emerald-900/20"
        >
          <PlayCircle size={20} />
          {running ? "Scanning Market..." : "Trigger Market Scan"}
        </button>
      </header>

      <div className="bg-gray-800 p-6 rounded-xl shadow-lg border border-gray-700">
        <div className="flex items-center justify-between mb-6 border-b border-gray-700 pb-4">
          <h2 className="text-xl font-bold flex items-center gap-2">
            <LayoutDashboard className="text-blue-400" />
            Active Opportunities
          </h2>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <Filter size={14} className="text-gray-400" />
              <select
                value={actionFilter}
                onChange={(e) => setActionFilter(e.target.value)}
                aria-label="Filter by action"
                className="bg-gray-900 border border-gray-700 rounded-lg px-2 py-1 text-xs text-white focus:outline-none"
              >
                <option value="">All</option>
                <option value="BUY">BUY</option>
                <option value="WATCH">WATCH</option>
                <option value="AVOID">AVOID</option>
              </select>
            </div>
            <span className="text-sm bg-gray-700 px-3 py-1 rounded-full text-gray-300 font-mono">
              {filtered.length} Items
            </span>
          </div>
        </div>

        {loading ? (
          <div className="flex flex-col items-center justify-center py-20 text-gray-400">
            <div className="w-10 h-10 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mb-4" />
            <p className="font-semibold">Loading opportunities...</p>
          </div>
        ) : filtered.length === 0 ? (
          <div className="text-center py-20 bg-gray-900/50 rounded-lg border border-dashed border-gray-700">
            <p className="text-gray-400 font-medium">
              No active opportunities found.
            </p>
            <p className="text-sm text-gray-500 mt-2">
              Trigger a new market scan to analyze NSE stocks across all
              algorithms.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filtered.map((opp) => (
              <Link
                to={`/stock/${opp.symbol}`}
                key={opp.decision_id}
                className="block group"
              >
                <div className="bg-gray-900 border border-gray-700 hover:border-blue-500 rounded-xl p-5 transition-all shadow-md group-hover:shadow-blue-900/20 h-full flex flex-col relative overflow-hidden">
                  <div
                    className={`absolute top-0 left-0 w-full h-1 ${
                      opp.action === "BUY"
                        ? "bg-green-500"
                        : opp.action === "WATCH"
                        ? "bg-yellow-500"
                        : "bg-red-500"
                    }`}
                  />

                  <div className="flex justify-between items-start mb-4 mt-1">
                    <h3 className="text-2xl font-black tracking-tight text-white group-hover:text-blue-400 transition-colors">
                      {opp.symbol}
                    </h3>
                    <span
                      className={`px-3 py-1 text-xs font-black tracking-wider rounded-lg ${
                        opp.action === "BUY"
                          ? "bg-green-900/50 text-green-400 border border-green-800"
                          : opp.action === "WATCH"
                          ? "bg-yellow-900/50 text-yellow-400 border border-yellow-800"
                          : "bg-red-900/50 text-red-400 border border-red-800"
                      }`}
                    >
                      {opp.action}
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-4 text-sm mb-4">
                    <div className="bg-gray-800 p-3 rounded-lg border border-gray-700">
                      <span className="block text-gray-400 text-xs font-medium uppercase tracking-wider mb-1">
                        Entry
                      </span>
                      <span className="font-mono text-white text-lg">
                        ₹{opp.entry_price}
                      </span>
                    </div>
                    <div className="bg-gray-800 p-3 rounded-lg border border-gray-700 text-right">
                      <span className="block text-gray-400 text-xs font-medium uppercase tracking-wider mb-1">
                        Confidence
                      </span>
                      <span className="block font-mono text-white text-lg">
                        {opp.confidence}%
                      </span>
                    </div>
                    <div className="bg-green-900/20 p-3 rounded-lg border border-green-900/50">
                      <span className="block text-green-500/70 text-xs font-medium uppercase tracking-wider mb-1">
                        Target
                      </span>
                      <span className="font-mono text-green-400 text-lg">
                        ₹{opp.target}
                      </span>
                    </div>
                    <div className="bg-red-900/20 p-3 rounded-lg border border-red-900/50 text-right">
                      <span className="block text-red-500/70 text-xs font-medium uppercase tracking-wider mb-1">
                        Stop Loss
                      </span>
                      <span className="block font-mono text-red-400 text-lg">
                        ₹{opp.stop_loss}
                      </span>
                    </div>
                  </div>

                  <div className="pt-3 border-t border-gray-800 mt-auto">
                    <p className="text-sm text-gray-400 line-clamp-2 leading-relaxed">
                      {opp.reasoning?.llm_summary ||
                        "No rationale available."}
                    </p>
                    <div className="flex items-center text-blue-400 mt-3 text-sm font-semibold opacity-0 group-hover:opacity-100 transition-opacity">
                      View Analysis{" "}
                      <ChevronRight size={16} className="ml-1" />
                    </div>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
