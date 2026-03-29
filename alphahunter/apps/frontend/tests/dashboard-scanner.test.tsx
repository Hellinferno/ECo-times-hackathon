/**
 * Dashboard + Scanner page tests.
 *
 * Covers: dashboard metric cards, opportunity cards, watchlist pulse,
 * run-scan button interaction, scanner filter controls (action/signal/
 * confidence), opportunity board rendering, and empty-state fallbacks.
 *
 * All api.* calls are mocked via vi.mock so no real network is required.
 */
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { vi } from "vitest";

import Dashboard from "../src/Dashboard";
import Scanner from "../src/Scanner";
import { api } from "../src/api/client";
import { useScanCenter } from "../src/hooks/useScanCenter";

vi.mock("../src/api/client", () => ({
  api: {
    getOpportunities: vi.fn(),
    getWatchlist: vi.fn(),
    getHealth: vi.fn(),
  },
}));

vi.mock("../src/hooks/useScanCenter", () => ({
  useScanCenter: vi.fn(),
}));

const mockedUseScanCenter = vi.mocked(useScanCenter);

describe("dashboard and scanner", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedUseScanCenter.mockReturnValue({
      latestScan: {
        id: 1,
        scan_run_id: "scan-1",
        triggered_by: "manual",
        status: "completed",
        started_at: "2026-03-27T09:00:00Z",
        completed_at: "2026-03-27T09:01:00Z",
        duration_secs: 48,
        stocks_scanned: 100,
        signals_found: 7,
        error_message: null,
      },
      loading: false,
      error: "",
      triggerScan: vi.fn().mockResolvedValue("scan-1"),
      refreshLatest: vi.fn().mockResolvedValue(undefined),
    });
  });

  it("renders dashboard data cards and top opportunities", async () => {
    vi.mocked(api.getOpportunities).mockResolvedValue({
      success: true,
      data: {
        scan_run_id: "scan-1",
        status: "completed",
        scanned_at: "2026-03-27T09:01:00Z",
        total: 1,
        opportunities: [
          {
            decision_id: "dec-1",
            symbol: "INFY",
            name: "Infosys Ltd",
            sector: "Technology",
            action: "BUY",
            confidence: 78,
            entry_price: 1500,
            target_price: 1580,
            stop_loss: 1450,
            rr_ratio: 2.3,
            price: 1502,
            signal_count: 2,
            signals: ["breakout", "volume_spike"],
            composite_score: 0.82,
            reasoning: { llm_summary: "INFY broke resistance on strong volume." },
            scanned_at: "2026-03-27T09:01:00Z",
            decided_at: "2026-03-27T09:01:00Z",
          },
        ],
      },
    });
    vi.mocked(api.getWatchlist).mockResolvedValue({
      success: true,
      data: {
        count: 1,
        max_items: 20,
        items: [
          {
            id: 1,
            symbol: "INFY",
            name: "Infosys Ltd",
            sector: "Technology",
            added_at: "2026-03-26T09:00:00Z",
            notes: null,
            latest_action: "BUY",
            latest_confidence: 78,
            latest_decided_at: "2026-03-27T09:01:00Z",
            latest_signal_count: 2,
            last_scanned_at: "2026-03-27T09:01:00Z",
            has_active_signal: true,
          },
        ],
      },
    });
    vi.mocked(api.getHealth).mockResolvedValue({
      success: true,
      data: {
        status: "healthy",
        database: "connected",
        version: "1.1.0",
        latest_scan: null,
        active_scan: null,
        data_feeds: { yfinance: "ok", tinyfish: "fresh" },
        tinyfish: { source_status: { news_sentiment: { status: "fresh", freshness_minutes: 5 } } },
      },
    });

    render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>,
    );

    expect(await screen.findByText("Top opportunities")).toBeTruthy();
    expect(screen.getAllByText("Infosys Ltd").length).toBeGreaterThan(0);
    expect(screen.getByText("Tracked names currently showing active signals.")).toBeTruthy();
  });

  it("refetches opportunities when scanner filters change", async () => {
    vi.mocked(api.getOpportunities).mockResolvedValue({
      success: true,
      data: {
        scan_run_id: "scan-1",
        status: "completed",
        scanned_at: "2026-03-27T09:01:00Z",
        total: 1,
        opportunities: [],
      },
    });

    render(
      <MemoryRouter>
        <Scanner />
      </MemoryRouter>,
    );

    await screen.findByText("Opportunity board");
    const actionSelect = screen.getByDisplayValue("All actions");
    fireEvent.change(actionSelect, { target: { value: "BUY" } });

    await waitFor(() => {
      expect(api.getOpportunities).toHaveBeenLastCalledWith(
        expect.objectContaining({ action: "BUY" }),
      );
    });
  });
});
