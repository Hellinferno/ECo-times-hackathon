/**
 * Formatting utilities for the AlphaHunter terminal UI.
 *
 * All functions return "NA" (not "null", not "–") when the value is missing
 * or invalid so that table cells always render something consistent.
 */

// ── Locale formatter instances (created once, reused per call) ─────────────────

const currencyFormatter = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  maximumFractionDigits: 2,
});

const compactNumberFormatter = new Intl.NumberFormat("en-IN", {
  notation: "compact",
  maximumFractionDigits: 1,
});

const percentFormatter = new Intl.NumberFormat("en-IN", {
  maximumFractionDigits: 1,
});

const dateFormatter = new Intl.DateTimeFormat("en-IN", {
  day: "2-digit",
  month: "short",
  year: "numeric",
});

const dateTimeFormatter = new Intl.DateTimeFormat("en-IN", {
  day: "2-digit",
  month: "short",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
});

// ── Exported formatters ────────────────────────────────────────────────────────

export function formatCurrency(value: number | null | undefined) {
  if (value == null || Number.isNaN(value)) return "NA";
  return currencyFormatter.format(value);
}

export function formatPercent(value: number | null | undefined, withSign = false) {
  if (value == null || Number.isNaN(value)) return "NA";
  const formatted = `${percentFormatter.format(value)}%`;
  if (!withSign || value === 0) return formatted;
  return `${value > 0 ? "+" : ""}${formatted}`;
}

export function formatCompactNumber(value: number | null | undefined) {
  if (value == null || Number.isNaN(value)) return "NA";
  return compactNumberFormatter.format(value);
}

export function formatDate(value: string | null | undefined) {
  if (!value) return "NA";
  return dateFormatter.format(new Date(value));
}

export function formatDateTime(value: string | null | undefined) {
  if (!value) return "NA";
  return dateTimeFormatter.format(new Date(value));
}

export function formatDuration(seconds: number | null | undefined) {
  if (seconds == null || Number.isNaN(seconds)) return "NA";
  if (seconds < 60) return `${seconds.toFixed(1)}s`;
  const minutes = Math.floor(seconds / 60);
  const remainder = Math.round(seconds % 60);
  return `${minutes}m ${remainder}s`;
}

// ── Domain-specific labels ─────────────────────────────────────────────────────

/** Returns a human-readable conviction label from a 0–100 confidence score. */
export function formatConfidenceBand(value: number | null | undefined) {
  if (value == null) return "Unscored";
  if (value >= 70) return "High conviction";
  if (value >= 50) return "Watch closely";
  return "Low conviction";
}

/** Converts a snake_case signal key to Title Case (e.g. "bulk_deal" → "Bulk Deal"). */
export function formatSignalLabel(signal: string) {
  return signal
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

/** Maps a decision action string to the StatusBadge tone prop. */
export function getActionTone(action: string): "positive" | "warning" | "danger" {
  if (action === "BUY") return "positive";
  if (action === "WATCH") return "warning";
  return "danger";
}
