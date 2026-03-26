import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { api } from "./api/client";
import type { WatchlistEntry } from "./api/client";
import { Star, Trash2, Plus, ExternalLink } from "lucide-react";

export default function Watchlist() {
  const [items, setItems] = useState<WatchlistEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [addSymbol, setAddSymbol] = useState("");
  const [adding, setAdding] = useState(false);
  const [error, setError] = useState("");

  const fetchWatchlist = () => {
    api
      .getWatchlist()
      .then((res) => setItems(res.data))
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchWatchlist();
  }, []);

  const handleAdd = async () => {
    if (!addSymbol.trim()) return;
    setAdding(true);
    setError("");
    try {
      await api.addToWatchlist(addSymbol.trim());
      setAddSymbol("");
      fetchWatchlist();
    } catch (e: any) {
      setError(e.message);
    }
    setAdding(false);
  };

  const handleRemove = async (symbol: string) => {
    try {
      await api.removeFromWatchlist(symbol);
      setItems((prev) => prev.filter((i) => i.symbol !== symbol));
    } catch (e: any) {
      console.error(e);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-black text-white flex items-center gap-2">
          <Star className="text-yellow-400" size={24} />
          Watchlist
        </h1>
        <span className="text-sm bg-gray-700 px-3 py-1 rounded-full text-gray-300 font-mono">
          {items.length} stocks
        </span>
      </div>

      {/* Add stock form */}
      <div className="bg-gray-800 p-4 rounded-xl border border-gray-700 flex gap-3">
        <input
          type="text"
          value={addSymbol}
          onChange={(e) => setAddSymbol(e.target.value.toUpperCase())}
          onKeyDown={(e) => e.key === "Enter" && handleAdd()}
          placeholder="Enter stock symbol (e.g., INFY)"
          className="flex-1 bg-gray-900 border border-gray-700 rounded-lg px-4 py-2.5 text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
        />
        <button
          onClick={handleAdd}
          disabled={adding || !addSymbol.trim()}
          className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold px-5 py-2.5 rounded-lg transition-all disabled:opacity-50"
        >
          <Plus size={18} />
          Add
        </button>
      </div>
      {error && <p className="text-red-400 text-sm">{error}</p>}

      {/* Watchlist table */}
      <div className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden">
        {loading ? (
          <div className="flex justify-center py-10">
            <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : items.length === 0 ? (
          <div className="text-center py-16 text-gray-400">
            <Star size={40} className="mx-auto mb-3 opacity-30" />
            <p className="font-medium">Your watchlist is empty</p>
            <p className="text-sm mt-1">
              Add stocks above to track them
            </p>
          </div>
        ) : (
          <table className="w-full text-left text-sm">
            <thead className="bg-gray-900 text-gray-400 uppercase text-xs">
              <tr>
                <th className="px-5 py-3">Symbol</th>
                <th className="px-5 py-3">Latest Action</th>
                <th className="px-5 py-3">Confidence</th>
                <th className="px-5 py-3">Last Analyzed</th>
                <th className="px-5 py-3">Added</th>
                <th className="px-5 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr
                  key={item.id}
                  className="border-t border-gray-700/50 hover:bg-gray-700/30 transition-colors"
                >
                  <td className="px-5 py-4">
                    <Link
                      to={`/stock/${item.symbol}`}
                      className="font-bold text-white hover:text-blue-400 transition-colors"
                    >
                      {item.symbol}
                    </Link>
                  </td>
                  <td className="px-5 py-4">
                    {item.latest_action ? (
                      <span
                        className={`px-2 py-0.5 text-xs font-bold rounded ${
                          item.latest_action === "BUY"
                            ? "bg-green-900/50 text-green-400"
                            : item.latest_action === "WATCH"
                            ? "bg-yellow-900/50 text-yellow-400"
                            : "bg-red-900/50 text-red-400"
                        }`}
                      >
                        {item.latest_action}
                      </span>
                    ) : (
                      <span className="text-gray-500">-</span>
                    )}
                  </td>
                  <td className="px-5 py-4 font-mono">
                    {item.latest_confidence != null ? (
                      <span className="text-blue-400">
                        {item.latest_confidence}%
                      </span>
                    ) : (
                      <span className="text-gray-500">-</span>
                    )}
                  </td>
                  <td className="px-5 py-4 text-gray-400 text-xs">
                    {item.latest_decided_at
                      ? new Date(item.latest_decided_at).toLocaleString()
                      : "-"}
                  </td>
                  <td className="px-5 py-4 text-gray-400 text-xs">
                    {new Date(item.added_at).toLocaleDateString()}
                  </td>
                  <td className="px-5 py-4 text-right">
                    <div className="flex items-center gap-2 justify-end">
                      <Link
                        to={`/stock/${item.symbol}`}
                        className="text-gray-400 hover:text-blue-400 transition-colors p-1"
                        title="View detail"
                      >
                        <ExternalLink size={16} />
                      </Link>
                      <button
                        onClick={() => handleRemove(item.symbol)}
                        className="text-gray-400 hover:text-red-400 transition-colors p-1"
                        title="Remove"
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
