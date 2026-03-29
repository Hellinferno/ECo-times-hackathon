/**
 * Alerts — signal-triggered notification inbox.
 *
 * Sections:
 *   PageHeader     — title, read/unread filter tabs, mark-all-read, clear-read CTAs
 *   Metrics grid   — unread count, read count, visible count, latest confidence (4-up)
 *   Alert stream   — scrollable list of alert cards with drill-through to stock detail
 *
 * Actions:
 *   Mark all read  — POST /api/alerts/read-all then refresh
 *   Clear read     — DELETE /api/alerts/read then refresh
 */
import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Bell, CheckCheck, Trash2 } from "lucide-react";
import { api, type AlertEntry } from "./api/client";
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
import { formatDateTime, formatPercent, getActionTone } from "./lib/format";

type AlertFilter = "all" | "unread";

export default function Alerts() {
  const [filter, setFilter] = useState<AlertFilter>("all");
  const [mutationError, setMutationError] = useState("");

  const { data: alerts, loading, error: loadError, refresh } = useApiLoad(
    () => api.getAlerts({ unread_only: filter === "unread", limit: 80 }),
    [filter],
  );
  const error = loadError || mutationError;

  const readCount = useMemo(() => alerts?.alerts.filter((alert) => alert.is_read).length ?? 0, [alerts]);

  const markAllRead = async () => {
    try {
      await api.markAlertsRead();
      refresh();
      setMutationError("");
    } catch (alertError) {
      setMutationError(alertError instanceof Error ? alertError.message : "Unable to mark alerts as read.");
    }
  };

  const clearRead = async () => {
    try {
      await api.clearReadAlerts();
      refresh();
      setMutationError("");
    } catch (alertError) {
      setMutationError(alertError instanceof Error ? alertError.message : "Unable to clear read alerts.");
    }
  };

  if (loading) {
    return <LoadingState label="Loading alert center..." />;
  }

  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="Alert center"
        title="Review timely alerts without losing context."
        description="AlphaHunter keeps alert volume focused: unread count, mark-as-read controls, and direct drill-through into the matching stock detail."
        actions={
          <div className="flex flex-wrap items-center gap-3">
            <div className="inline-flex rounded-2xl border border-white/8 bg-slate-950/70 p-1">
              <button
                type="button"
                onClick={() => setFilter("all")}
                className={`rounded-2xl px-4 py-2 text-sm ${filter === "all" ? "bg-cyan-400/12 text-white" : "text-slate-400 hover:text-white"}`}
              >
                All
              </button>
              <button
                type="button"
                onClick={() => setFilter("unread")}
                className={`rounded-2xl px-4 py-2 text-sm ${filter === "unread" ? "bg-cyan-400/12 text-white" : "text-slate-400 hover:text-white"}`}
              >
                Unread
              </button>
            </div>
            <Button variant="secondary" onClick={() => void markAllRead()} disabled={!alerts?.unread_count}>
              <CheckCheck className="size-4" />
              Mark all read
            </Button>
            <Button variant="danger" onClick={() => void clearRead()} disabled={readCount === 0}>
              <Trash2 className="size-4" />
              Clear read
            </Button>
          </div>
        }
      />

      {error ? <ErrorState description={error} /> : null}

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard label="Unread" value={alerts?.unread_count ?? 0} detail="Alerts still needing review." tone="warning" />
        <MetricCard label="Read" value={readCount} detail="Already triaged in this inbox." />
        <MetricCard label="Visible" value={alerts?.alerts.length ?? 0} detail={`Filter: ${filter}`} tone="positive" />
        <MetricCard label="Latest confidence" value={formatPercent(alerts?.alerts[0]?.confidence)} detail={alerts?.alerts[0]?.symbol ? `${alerts.alerts[0].symbol} is the freshest alert.` : "No alert confidence available."} />
      </div>

      <Panel title="Alert stream" subtitle="Alerts stay compact, readable, and directly connected to the underlying stock detail.">
        {!alerts?.alerts.length ? (
          <EmptyState
            title="No alerts in this view"
            description="When the engine detects high-confidence activity, the alert center will show it here."
          />
        ) : (
          <div className="space-y-3">
            {alerts.alerts.map((alert: AlertEntry) => (
              <article
                key={alert.id}
                className={`rounded-[28px] border p-5 transition ${
                  alert.is_read
                    ? "border-white/8 bg-slate-950/45"
                    : "border-cyan-400/20 bg-cyan-400/6"
                }`}
              >
                <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-3">
                      <Bell className="size-4 text-cyan-200" />
                      <Link to={`/stock/${alert.symbol}`} className="text-lg font-semibold text-white hover:text-cyan-100">
                        {alert.symbol}
                      </Link>
                      {alert.action ? (
                        <StatusBadge
                          label={alert.action}
                          tone={getActionTone(alert.action)}
                        />
                      ) : null}
                      <StatusBadge label={alert.is_read ? "Read" : "Unread"} tone={alert.is_read ? "neutral" : "info"} />
                    </div>
                    <p className="mt-3 text-sm text-slate-300">{alert.message}</p>
                    <div className="mt-3 flex flex-wrap items-center gap-3 text-xs text-slate-500">
                      <span>{formatDateTime(alert.created_at)}</span>
                      <span>{alert.alert_type}</span>
                      <span>{formatPercent(alert.confidence)}</span>
                    </div>
                  </div>
                  <Link to={`/stock/${alert.symbol}`}>
                    <Button variant="ghost">Open detail</Button>
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
