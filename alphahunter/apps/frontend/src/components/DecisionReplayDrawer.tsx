/**
 * DecisionReplayDrawer — slide-in panel that replays a saved decision.
 *
 * Sections (top → bottom):
 *   Drawer header     — symbol, name, close button
 *   Metrics grid      — action, confidence, outcome, return (4-up)
 *   Trade plan panel  — entry / target / stop-loss
 *   Reasoning panel   — LLM narrative + key factors
 *   Signal snapshot   — triggered signals with diagnostics JSON
 *   Backtest snapshot — historical match stats
 *
 * Accessibility: Escape key closes the drawer; focus is trapped on open.
 */
import { useEffect, useRef } from "react";
import { X } from "lucide-react";
import type { DecisionDetailResponse } from "../api/client";
import {
  formatConfidenceBand,
  formatCurrency,
  formatDateTime,
  formatPercent,
  formatSignalLabel,
  getActionTone,
} from "../lib/format";
import { Button, MetricCard, Panel, StatusBadge } from "./ui";

export function DecisionReplayDrawer({
  detail,
  onClose,
}: {
  detail: DecisionDetailResponse;
  onClose: () => void;
}) {
  const drawerRef = useRef<HTMLElement>(null);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handleKeyDown);
    drawerRef.current?.focus();
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  return (
    <>
      <button type="button" className="drawer-backdrop" onClick={onClose} aria-label="Close replay drawer" />
      <aside ref={drawerRef} className="drawer-panel" role="dialog" aria-modal="true" tabIndex={-1}>
        {/* ── Drawer header ── */}
        <div className="mb-5 flex items-start justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-[0.24em] text-slate-500">Decision replay</p>
            <h2 className="mt-2 text-3xl font-semibold text-white">{detail.stock.symbol}</h2>
            <p className="mt-1 text-sm text-slate-400">{detail.stock.name}</p>
          </div>
          <Button variant="ghost" onClick={onClose}>
            <X className="size-4" />
            Close
          </Button>
        </div>

        {/* ── Metrics grid ── */}
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <MetricCard label="Action" value={<StatusBadge label={detail.decision.action} tone={getActionTone(detail.decision.action)} />} />
          <MetricCard label="Confidence" value={formatPercent(detail.decision.confidence)} detail={formatConfidenceBand(detail.decision.confidence)} />
          <MetricCard label="Outcome" value={detail.outcome.result ?? "Pending"} detail={detail.outcome.measured_at ? formatDateTime(detail.outcome.measured_at) : "Still open"} />
          <MetricCard label="Return" value={formatPercent(detail.outcome.return_pct, true)} detail={detail.decision.outcome_measured ? "Measured at T+5" : "Awaiting measurement"} tone={detail.outcome.return_pct != null && detail.outcome.return_pct >= 0 ? "positive" : "danger"} />
        </div>

        {/* ── Trade plan + Reasoning ── */}
        <div className="mt-6 grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
          <Panel title="Trade plan" subtitle="Frozen recommendation values stored with the original decision.">
            <div className="grid gap-4 md:grid-cols-3">
              <MetricCard label="Entry" value={formatCurrency(detail.decision.entry_price)} />
              <MetricCard label="Target" value={formatCurrency(detail.decision.target_price)} tone="positive" />
              <MetricCard label="Stop loss" value={formatCurrency(detail.decision.stop_loss)} tone="danger" />
            </div>
          </Panel>

          <Panel title="Reasoning" subtitle="Snapshot of the narrative recorded for the decision.">
            <p className="text-sm leading-7 text-slate-300">
              {detail.reasoning?.llm_summary || "No stored reasoning narrative for this decision."}
            </p>
            {detail.reasoning?.key_factors?.length ? (
              <ul className="mt-4 space-y-2 text-sm text-slate-300">
                {detail.reasoning.key_factors.map((factor) => (
                  <li key={factor} className="rounded-2xl border border-white/8 bg-slate-950/70 px-3 py-2">
                    {factor}
                  </li>
                ))}
              </ul>
            ) : null}
          </Panel>
        </div>

        {/* ── Signal snapshot + Backtest ── */}
        <div className="mt-6 grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
          <Panel title="Signal snapshot" subtitle="Triggered signal families and captured diagnostics.">
            {detail.signals?.items?.length ? (
              <div className="space-y-3">
                {detail.signals.items.map((signal) => (
                  <div key={signal.key} className="rounded-2xl border border-white/8 bg-slate-950/60 p-4">
                    <div className="flex items-center justify-between gap-3">
                      <p className="text-sm font-medium text-white">{signal.label}</p>
                      <StatusBadge label={signal.triggered ? "Triggered" : "Inactive"} tone={signal.triggered ? "positive" : "neutral"} />
                    </div>
                    <p className="mt-3 text-xs uppercase tracking-[0.18em] text-slate-500">
                      {formatSignalLabel(signal.key)}
                    </p>
                    <pre className="mt-3 overflow-x-auto rounded-2xl bg-slate-950 p-3 text-xs text-slate-300">
                      {JSON.stringify(signal.details, null, 2)}
                    </pre>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-slate-400">No signal snapshot was stored for this decision.</p>
            )}
          </Panel>

          <Panel title="Backtest snapshot" subtitle="Historical context captured at decision time.">
            <div className="grid gap-4 md:grid-cols-2">
              <MetricCard label="Matches" value={detail.backtest?.matches ?? "NA"} />
              <MetricCard label="Success rate" value={formatPercent(detail.backtest?.success_rate)} />
              <MetricCard label="Avg return" value={formatPercent(detail.backtest?.avg_return_pct, true)} tone="positive" />
              <MetricCard label="Worst case" value={formatPercent(detail.backtest?.worst_case_pct, true)} tone="danger" />
            </div>
          </Panel>
        </div>
      </aside>
    </>
  );
}
