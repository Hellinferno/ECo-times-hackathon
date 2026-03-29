/**
 * Shared UI primitives used across all pages.
 *
 * Components
 * ----------
 * Layout      — Panel, PageHeader
 * Data display — MetricCard, StatusBadge
 * Actions     — Button
 * Feedback    — EmptyState, LoadingState, ErrorState
 * Navigation  — SectionTabs
 * Forms       — FieldLabel
 */
import type { ReactNode } from "react";
import { AlertTriangle, LoaderCircle } from "lucide-react";
import { cx } from "../lib/utils";

// ── Layout ────────────────────────────────────────────────────────────────────

export function Panel({
  title,
  subtitle,
  actions,
  children,
  className,
}: {
  title?: string;
  subtitle?: string;
  actions?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section className={cx("panel-card", className)}>
      {(title || subtitle || actions) && (
        <header className="mb-5 flex flex-col gap-4 border-b border-white/6 pb-4 md:flex-row md:items-end md:justify-between">
          <div>
            {title ? <h2 className="text-lg font-semibold text-white">{title}</h2> : null}
            {subtitle ? <p className="mt-1 text-sm text-slate-400">{subtitle}</p> : null}
          </div>
          {actions ? <div className="flex flex-wrap items-center gap-2">{actions}</div> : null}
        </header>
      )}
      {children}
    </section>
  );
}

export function PageHeader({
  eyebrow,
  title,
  description,
  actions,
}: {
  eyebrow?: string;
  title: string;
  description?: string;
  actions?: ReactNode;
}) {
  return (
    <div className="mb-8 flex flex-col gap-5 xl:flex-row xl:items-end xl:justify-between">
      <div className="max-w-3xl">
        {eyebrow ? (
          <p className="mb-2 text-xs font-semibold uppercase tracking-[0.28em] text-cyan-300/70">
            {eyebrow}
          </p>
        ) : null}
        <h1 className="text-3xl font-semibold tracking-tight text-white md:text-4xl">{title}</h1>
        {description ? (
          <p className="mt-3 max-w-2xl text-sm text-slate-300 md:text-base">{description}</p>
        ) : null}
      </div>
      {actions ? <div className="flex flex-wrap items-center gap-3">{actions}</div> : null}
    </div>
  );
}

// ── Data display ───────────────────────────────────────────────────────────────

export function MetricCard({
  label,
  value,
  detail,
  tone = "neutral",
}: {
  label: string;
  value: ReactNode;
  detail?: ReactNode;
  tone?: "neutral" | "positive" | "warning" | "danger" | "info";
}) {
  return (
    <div className={cx("metric-card", `metric-card-${tone}`)}>
      <span className="text-[11px] uppercase tracking-[0.28em] text-slate-400">{label}</span>
      <strong className="mt-3 block text-2xl font-semibold text-white">{value}</strong>
      {detail ? <p className="mt-2 text-sm text-slate-300">{detail}</p> : null}
    </div>
  );
}

export function StatusBadge({
  label,
  tone,
}: {
  label: string;
  tone: "neutral" | "positive" | "warning" | "danger" | "info";
}) {
  return <span className={cx("status-badge", `status-badge-${tone}`)}>{label}</span>;
}

// ── Actions ───────────────────────────────────────────────────────────────────

export function Button({
  children,
  onClick,
  type = "button",
  disabled,
  variant = "primary",
  className,
}: {
  children: ReactNode;
  onClick?: () => void;
  type?: "button" | "submit";
  disabled?: boolean;
  variant?: "primary" | "secondary" | "ghost" | "danger";
  className?: string;
}) {
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={cx("button-base", `button-${variant}`, className)}
    >
      {children}
    </button>
  );
}

// ── Feedback ──────────────────────────────────────────────────────────────────

export function EmptyState({
  title,
  description,
  action,
}: {
  title: string;
  description: string;
  action?: ReactNode;
}) {
  return (
    <div className="rounded-3xl border border-dashed border-white/10 bg-slate-950/50 px-6 py-12 text-center">
      <p className="text-lg font-medium text-white">{title}</p>
      <p className="mx-auto mt-2 max-w-xl text-sm text-slate-400">{description}</p>
      {action ? <div className="mt-5">{action}</div> : null}
    </div>
  );
}

export function LoadingState({ label = "Loading intelligence..." }: { label?: string }) {
  return (
    <div className="flex min-h-[220px] flex-col items-center justify-center gap-3 text-center text-slate-300">
      <LoaderCircle className="size-8 animate-spin text-cyan-300" />
      <p className="text-sm">{label}</p>
    </div>
  );
}

export function ErrorState({
  title = "Something went wrong",
  description,
  action,
}: {
  title?: string;
  description: string;
  action?: ReactNode;
}) {
  return (
    <div className="rounded-3xl border border-rose-500/20 bg-rose-500/6 px-6 py-10 text-center">
      <AlertTriangle className="mx-auto size-8 text-rose-300" />
      <p className="mt-3 text-lg font-medium text-white">{title}</p>
      <p className="mx-auto mt-2 max-w-xl text-sm text-rose-100/75">{description}</p>
      {action ? <div className="mt-5">{action}</div> : null}
    </div>
  );
}

// ── Navigation ────────────────────────────────────────────────────────────────

export function SectionTabs<T extends string>({
  value,
  onChange,
  tabs,
}: {
  value: T;
  onChange: (next: T) => void;
  tabs: Array<{ value: T; label: string }>;
}) {
  return (
    <div className="inline-flex flex-wrap gap-2 rounded-2xl border border-white/8 bg-slate-950/70 p-1">
      {tabs.map((tab) => (
        <button
          key={tab.value}
          type="button"
          onClick={() => onChange(tab.value)}
          className={cx(
            "rounded-2xl px-4 py-2 text-sm font-medium transition",
            value === tab.value
              ? "bg-cyan-400/15 text-cyan-200 shadow-[0_0_0_1px_rgba(103,232,249,0.25)_inset]"
              : "text-slate-400 hover:bg-white/5 hover:text-white",
          )}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}

// ── Forms ─────────────────────────────────────────────────────────────────────

export function FieldLabel({
  label,
  hint,
}: {
  label: string;
  hint?: string;
}) {
  return (
    <div>
      <p className="text-sm font-medium text-white">{label}</p>
      {hint ? <p className="mt-1 text-xs text-slate-400">{hint}</p> : null}
    </div>
  );
}
