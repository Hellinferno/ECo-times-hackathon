/**
 * Layout — persistent application shell shared by all pages.
 *
 * Structure:
 *   Background  — radial-gradient + dot-grid fixed canvas (pointer-events: none)
 *   Sidebar     — sticky left nav with logo, scan status card, nav links, footer tip (lg+)
 *   Top header  — scan status badge, stocks/signals summary, run-scan CTA
 *   <Outlet />  — page content area
 *   Mobile nav  — fixed bottom bar (hidden on lg+) with 6-col icon grid
 *
 * Behaviour:
 *   - useScanCenter drives scan status badge in both sidebar and top header.
 *   - Alert badge polls GET /api/alerts every 15 s; shows unread count on the
 *     Alerts nav item.
 */
import { useEffect, useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import {
  Activity,
  Bell,
  BookCopy,
  BookOpen,
  CandlestickChart,
  Gauge,
  Radar,
  Settings,
  Star,
  TrendingUp,
  FileText,
} from "lucide-react";
import { api } from "../api/client";
import { useScanCenter } from "../hooks/useScanCenter";
import { Button, StatusBadge } from "./ui";
import { cx } from "../lib/utils";

const navigation = [
  { to: "/", label: "Dashboard", icon: Gauge },
  { to: "/scanner", label: "Scanner", icon: Radar },
  { to: "/workspaces", label: "Workspaces", icon: BookOpen },
  { to: "/valuation-lab", label: "Valuation Lab", icon: TrendingUp },
  { to: "/outputs", label: "Outputs", icon: FileText },
  { to: "/history", label: "History", icon: BookCopy },
  { to: "/watchlist", label: "Watchlist", icon: Star },
  { to: "/alerts", label: "Alerts", icon: Bell },
  { to: "/settings", label: "Settings", icon: Settings },
];

function getScanTone(status: string | null | undefined) {
  if (status === "completed") return "positive" as const;
  if (status === "running") return "info" as const;
  if (status === "failed") return "danger" as const;
  return "neutral" as const;
}

export default function Layout() {
  const { latestScan, triggerScan } = useScanCenter();
  const [unreadAlerts, setUnreadAlerts] = useState(0);

  useEffect(() => {
    let cancelled = false;

    const loadBadge = async () => {
      try {
        const response = await api.getAlerts({ limit: 1 });
        if (!cancelled) {
          setUnreadAlerts(response.data.unread_count);
        }
      } catch {
        if (!cancelled) {
          setUnreadAlerts(0);
        }
      }
    };

    void loadBadge();
    const intervalId = window.setInterval(() => {
      void loadBadge();
    }, 15000);

    return () => {
      cancelled = true;
      window.clearInterval(intervalId);
    };
  }, []);

  return (
    <div className="min-h-screen bg-[var(--app-bg)] text-white">
      <div className="pointer-events-none fixed inset-0 -z-10 overflow-hidden">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,_rgba(34,211,238,0.16),_transparent_32%),radial-gradient(circle_at_top_right,_rgba(16,185,129,0.12),_transparent_28%),linear-gradient(180deg,_rgba(15,23,42,0.2),_rgba(2,6,23,0.9))]" />
        <div className="absolute inset-0 bg-[linear-gradient(rgba(148,163,184,0.04)_1px,transparent_1px),linear-gradient(90deg,rgba(148,163,184,0.04)_1px,transparent_1px)] bg-[size:90px_90px] opacity-35" />
      </div>

      <div className="mx-auto flex min-h-screen max-w-[1600px] gap-6 px-4 pb-24 pt-4 md:px-6 lg:px-8 lg:pb-8">
        <aside className="hidden w-72 shrink-0 lg:block">
          <div className="sticky top-4 flex h-[calc(100vh-2rem)] flex-col rounded-[32px] border border-white/8 bg-slate-950/85 p-6 shadow-[0_24px_80px_rgba(2,6,23,0.55)] backdrop-blur">
            <div className="mb-8 flex items-center gap-3">
              <div className="flex size-12 items-center justify-center rounded-2xl border border-cyan-400/20 bg-cyan-400/10 text-cyan-200">
                <CandlestickChart className="size-6" />
              </div>
              <div>
                <p className="text-xs uppercase tracking-[0.3em] text-cyan-300/70">AlphaHunter</p>
                <h1 className="mt-1 text-xl font-semibold tracking-tight">Decision Terminal</h1>
              </div>
            </div>

            <div className="rounded-[28px] border border-white/8 bg-white/4 p-4">
              <p className="text-xs uppercase tracking-[0.28em] text-slate-400">Market engine</p>
              <div className="mt-3 flex items-center justify-between gap-3">
                <div>
                  <p className="text-sm text-slate-300">Latest scan</p>
                  <p className="mt-1 text-lg font-medium text-white">
                    {latestScan?.signals_found ?? 0} signals
                  </p>
                </div>
                <StatusBadge
                  label={latestScan?.status ?? "idle"}
                  tone={getScanTone(latestScan?.status)}
                />
              </div>
              <p className="mt-3 text-xs text-slate-400">
                Premium, investor-first intelligence for NSE opportunity review.
              </p>
            </div>

            <nav className="mt-6 flex-1 space-y-2">
              {navigation.map(({ to, label, icon: Icon }) => (
                <NavLink
                  key={to}
                  to={to}
                  end={to === "/"}
                  className={({ isActive }) =>
                    cx(
                      "group flex items-center justify-between rounded-2xl px-4 py-3 text-sm transition",
                      isActive
                        ? "bg-cyan-400/12 text-white shadow-[0_0_0_1px_rgba(103,232,249,0.2)_inset]"
                        : "text-slate-400 hover:bg-white/5 hover:text-white",
                    )
                  }
                >
                  <span className="flex items-center gap-3">
                    <Icon className="size-4" />
                    {label}
                  </span>
                  {label === "Alerts" && unreadAlerts > 0 ? (
                    <span className="rounded-full bg-cyan-400 px-2 py-0.5 text-[11px] font-semibold text-slate-950">
                      {unreadAlerts}
                    </span>
                  ) : null}
                </NavLink>
              ))}
            </nav>

            <div className="rounded-[28px] border border-white/8 bg-slate-900/70 p-4">
              <div className="flex items-center gap-2 text-slate-300">
                <Activity className="size-4 text-emerald-300" />
                <span className="text-sm font-medium">Investor-first expansion</span>
              </div>
              <p className="mt-2 text-xs leading-relaxed text-slate-400">
                Dashboard, scanner, replay history, and charting now share one cohesive terminal shell.
              </p>
            </div>
          </div>
        </aside>

        <div className="min-w-0 flex-1">
          <header className="mb-6 flex flex-col gap-4 rounded-[28px] border border-white/8 bg-slate-950/75 px-5 py-4 shadow-[0_18px_60px_rgba(2,6,23,0.4)] backdrop-blur md:flex-row md:items-center md:justify-between">
            <div>
              <p className="text-xs uppercase tracking-[0.28em] text-slate-500">AlphaHunter OS</p>
              <div className="mt-2 flex flex-wrap items-center gap-3">
                <StatusBadge
                  label={latestScan?.status ?? "idle"}
                  tone={getScanTone(latestScan?.status)}
                />
                <span className="text-sm text-slate-300">
                  {latestScan
                    ? `${latestScan.stocks_scanned} stocks scanned, ${latestScan.signals_found} signals`
                    : "No scan has completed yet."}
                </span>
              </div>
            </div>
            <div className="flex flex-wrap items-center gap-3">
              <Button onClick={() => void triggerScan()}>
                Run market scan
              </Button>
            </div>
          </header>

          <main className="pb-12">
            <Outlet />
          </main>
        </div>
      </div>

      <nav className="fixed inset-x-3 bottom-3 z-40 rounded-[28px] border border-white/10 bg-slate-950/88 p-2 shadow-[0_24px_60px_rgba(2,6,23,0.55)] backdrop-blur lg:hidden">
        <div className="grid grid-cols-6 gap-1">
          {navigation.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === "/"}
              className={({ isActive }) =>
                cx(
                  "relative flex flex-col items-center gap-1 rounded-2xl px-2 py-2 text-[11px] text-slate-400 transition",
                  isActive ? "bg-cyan-400/12 text-white" : "hover:bg-white/5 hover:text-white",
                )
              }
            >
              <Icon className="size-4" />
              <span>{label}</span>
              {label === "Alerts" && unreadAlerts > 0 ? (
                <span className="absolute right-2 top-1 rounded-full bg-cyan-400 px-1.5 text-[10px] font-semibold text-slate-950">
                  {unreadAlerts}
                </span>
              ) : null}
            </NavLink>
          ))}
        </div>
      </nav>
    </div>
  );
}
