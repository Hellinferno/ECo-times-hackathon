/**
 * Watchlist — tracked NSE names sorted by live signal heat.
 *
 * Sections:
 *   PageHeader      — title and description
 *   Metrics grid    — tracked count, active signals, highest conviction, latest update (4-up)
 *   Add a stock     — symbol input + add button (enforces 20-name server cap)
 *   Tracked names   — 2-col grid of watchlist item cards with remove action
 *
 * Sort order: names with active signals first, then by descending confidence.
 */
import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowUpRight, Plus, Trash2 } from "lucide-react";
import { api, type WatchlistEntry } from "./api/client";
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
import { formatDateTime, formatPercent } from "./lib/format";

export default function Watchlist() {
  const [symbol, setSymbol] = useState("");
  const [adding, setAdding] = useState(false);
  const [mutationError, setMutationError] = useState("");

  const { data: watchlist, loading, error: loadError, refresh } = useApiLoad(
    () => api.getWatchlist(),
    [],
  );
  const error = loadError || mutationError;

  const sortedItems = useMemo(() => {
    if (!watchlist) return [];
    return [...watchlist.items].sort((left, right) => {
      if (left.has_active_signal !== right.has_active_signal) {
        return left.has_active_signal ? -1 : 1;
      }
      return (right.latest_confidence ?? 0) - (left.latest_confidence ?? 0);
    });
  }, [watchlist]);

  const handleAdd = async () => {
    if (!symbol.trim()) return;
    setAdding(true);
    try {
      await api.addToWatchlist(symbol.trim().toUpperCase());
      setSymbol("");
      setMutationError("");
      refresh();
    } catch (watchlistError) {
      setMutationError(watchlistError instanceof Error ? watchlistError.message : "Unable to add stock.");
    } finally {
      setAdding(false);
    }
  };

  const handleRemove = async (item: WatchlistEntry) => {
    try {
      await api.removeFromWatchlist(item.symbol);
      setMutationError("");
      refresh();
    } catch (watchlistError) {
      setMutationError(watchlistError instanceof Error ? watchlistError.message : "Unable to remove stock.");
    }
  };

  if (loading) {
    return <LoadingState label="Loading watchlist..." />;
  }

  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="Watchlist"
        title="Track the names that deserve immediate attention."
        description="Pin up to twenty NSE names and sort them by live signal heat so your highest-priority ideas stay on top."
      />

      {error ? <ErrorState description={error} /> : null}

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard label="Tracked names" value={watchlist?.count ?? 0} detail={`of ${watchlist?.max_items ?? 20} max slots`} />
        <MetricCard label="Active signals" value={sortedItems.filter((item) => item.has_active_signal).length} detail="Names currently showing live signal activity." tone="positive" />
        <MetricCard label="Highest conviction" value={formatPercent(sortedItems[0]?.latest_confidence)} detail={sortedItems[0] ? `${sortedItems[0].symbol} leads the board.` : "Awaiting first tracked signal."} tone="warning" />
        <MetricCard label="Latest update" value={sortedItems[0]?.last_scanned_at ? formatDateTime(sortedItems[0].last_scanned_at) : "NA"} detail="Most recent scan time among tracked names." />
      </div>

      <Panel title="Add a stock" subtitle="The watchlist is single-user for this phase and capped at twenty names.">
        <div className="grid gap-4 lg:grid-cols-[1.2fr_auto]">
          <label className="space-y-2">
            <span className="text-sm font-medium text-white">Stock symbol</span>
            <input
              value={symbol}
              onChange={(event) => setSymbol(event.target.value.toUpperCase())}
              onKeyDown={(event) => {
                if (event.key === "Enter") {
                  void handleAdd();
                }
              }}
              className="terminal-input"
              placeholder="INFY"
            />
          </label>
          <div className="flex items-end">
            <Button onClick={() => void handleAdd()} disabled={adding || !symbol.trim()} className="w-full lg:w-auto">
              <Plus className="size-4" />
              {adding ? "Adding..." : "Add to watchlist"}
            </Button>
          </div>
        </div>
      </Panel>

      <Panel title="Tracked names" subtitle="Active signals float to the top so the board behaves like a true investor command list.">
        {sortedItems.length === 0 ? (
          <EmptyState
            title="Your watchlist is empty"
            description="Add a few names to start tracking live signal heat, confidence, and last scan recency."
          />
        ) : (
          <div className="grid gap-4 xl:grid-cols-2">
            {sortedItems.map((item) => (
              <article
                key={item.id}
                className="rounded-[28px] border border-white/8 bg-slate-950/60 p-5 transition hover:border-cyan-400/30"
              >
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="text-xs uppercase tracking-[0.24em] text-slate-500">{item.name}</p>
                    <h3 className="mt-2 text-2xl font-semibold text-white">{item.symbol}</h3>
                    <p className="mt-1 text-sm text-slate-400">{item.sector ?? "NSE coverage"}</p>
                  </div>
                  <StatusBadge label={item.latest_action ?? "idle"} tone={item.has_active_signal ? "positive" : "neutral"} />
                </div>

                <div className="mt-5 grid gap-3 md:grid-cols-3">
                  <MetricCard label="Confidence" value={formatPercent(item.latest_confidence)} detail="Latest decision score." />
                  <MetricCard label="Signals" value={item.latest_signal_count} detail="Triggered factors in the last scan." tone="warning" />
                  <MetricCard label="Last scan" value={item.last_scanned_at ? formatDateTime(item.last_scanned_at) : "NA"} detail="Refresh recency." />
                </div>

                <div className="mt-6 flex items-center justify-between">
                  <Link
                    to={`/stock/${item.symbol}`}
                    className="inline-flex items-center gap-2 text-sm font-medium text-cyan-200 hover:text-white"
                  >
                    Open stock detail
                    <ArrowUpRight className="size-4" />
                  </Link>
                  <button
                    type="button"
                    onClick={() => void handleRemove(item)}
                    className="inline-flex items-center gap-2 rounded-full border border-rose-500/20 px-3 py-1.5 text-sm text-rose-200 hover:bg-rose-500/8"
                  >
                    <Trash2 className="size-4" />
                    Remove
                  </button>
                </div>
              </article>
            ))}
          </div>
        )}
      </Panel>
    </div>
  );
}
