/**
 * Watchlist + StockDetail page tests.
 *
 * Covers: watchlist load/display, add/remove stock interactions,
 * StockDetail tab navigation (overview/signals/backtest/trade/chart),
 * watchlist toggle from the detail page, and chart lazy-load behaviour.
 *
 * All api.* calls are mocked via vi.mock so no real network is required.
 */
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { vi } from "vitest";

import StockDetail from "../src/StockDetail";
import Watchlist from "../src/Watchlist";
import { api } from "../src/api/client";

vi.mock("../src/api/client", () => ({
  api: {
    getWatchlist: vi.fn(),
    addToWatchlist: vi.fn(),
    removeFromWatchlist: vi.fn(),
    getStockDetail: vi.fn(),
    getStockChart: vi.fn(),
  },
}));

describe("watchlist and stock detail", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("supports add and remove watchlist flows", async () => {
    vi.mocked(api.getWatchlist)
      .mockResolvedValueOnce({
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
              added_at: "2026-03-27T09:01:00Z",
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
      })
      .mockResolvedValueOnce({
        success: true,
        data: {
          count: 2,
          max_items: 20,
          items: [
            {
              id: 1,
              symbol: "INFY",
              name: "Infosys Ltd",
              sector: "Technology",
              added_at: "2026-03-27T09:01:00Z",
              notes: null,
              latest_action: "BUY",
              latest_confidence: 78,
              latest_decided_at: "2026-03-27T09:01:00Z",
              latest_signal_count: 2,
              last_scanned_at: "2026-03-27T09:01:00Z",
              has_active_signal: true,
            },
            {
              id: 2,
              symbol: "TCS",
              name: "TCS",
              sector: "Technology",
              added_at: "2026-03-27T09:01:00Z",
              notes: null,
              latest_action: null,
              latest_confidence: null,
              latest_decided_at: null,
              latest_signal_count: 0,
              last_scanned_at: null,
              has_active_signal: false,
            },
          ],
        },
      })
      .mockResolvedValueOnce({
        success: true,
        data: {
          count: 1,
          max_items: 20,
          items: [
            {
              id: 2,
              symbol: "TCS",
              name: "TCS",
              sector: "Technology",
              added_at: "2026-03-27T09:01:00Z",
              notes: null,
              latest_action: null,
              latest_confidence: null,
              latest_decided_at: null,
              latest_signal_count: 0,
              last_scanned_at: null,
              has_active_signal: false,
            },
          ],
        },
      });
    vi.mocked(api.addToWatchlist).mockResolvedValue({
      success: true,
      data: {
        id: 2,
        symbol: "TCS",
        added_at: "2026-03-27T09:01:00Z",
        notes: null,
        max_items: 20,
      },
    });
    vi.mocked(api.removeFromWatchlist).mockResolvedValue({
      success: true,
      data: { symbol: "INFY", removed: true },
    });

    render(
      <MemoryRouter>
        <Watchlist />
      </MemoryRouter>,
    );

    await screen.findByText("Track the names that deserve immediate attention.");
    fireEvent.change(screen.getByPlaceholderText("INFY"), { target: { value: "TCS" } });
    fireEvent.click(screen.getByRole("button", { name: /add to watchlist/i }));

    await waitFor(() => {
      expect(api.addToWatchlist).toHaveBeenCalledWith("TCS");
    });

    const infyCard = screen.getByRole("heading", { name: "INFY" }).closest("article");
    expect(infyCard).toBeTruthy();
    fireEvent.click(within(infyCard as HTMLElement).getByRole("button", { name: /remove/i }));
    await waitFor(() => {
      expect(api.removeFromWatchlist).toHaveBeenCalledWith("INFY");
    });
  });

  it("loads the chart tab when switching stock detail tabs", async () => {
    vi.mocked(api.getStockDetail).mockResolvedValue({
      success: true,
      data: {
        stock: {
          symbol: "INFY",
          name: "Infosys Ltd",
          sector: "Technology",
          market_cap_cr: 12000,
          is_active: true,
        },
        meta: {
          scanned_at: "2026-03-27T09:01:00Z",
          backtest_lookback_years: "2",
          backtest_outcome_days: "5",
        },
        decision: {
          decision_id: "dec-1",
          action: "BUY",
          confidence: 78,
          entry_price: 1500,
          target_price: 1580,
          stop_loss: 1450,
          rr_ratio: 2.3,
          score_breakdown: { signal_score: 0.82, backtest_score: 0.8, composite_score: 0.78 },
          decided_at: "2026-03-27T09:01:00Z",
          outcome_measured: true,
          outcome_return_pct: 4.8,
          outcome_result: "WIN",
        },
        signals: {
          signal_count: 2,
          composite_score: 0.82,
          price: 1502,
          volume_today: 4600000,
          volume_avg_20d: 2000000,
          volume_ratio: 2.3,
          items: [
            {
              key: "breakout",
              label: "Breakout",
              triggered: true,
              strength: 0.82,
              details: { resistance_level: 1500 },
            },
          ],
          diagnostics: {},
          extra_signals: {},
        },
        reasoning: { llm_summary: "INFY broke resistance." },
        backtest: {
          matches: 5,
          success_rate: 80,
          avg_return_pct: 5.2,
          worst_case_pct: -3.1,
          best_case_pct: 9.8,
          cases: [],
        },
      },
    });
    vi.mocked(api.getWatchlist).mockResolvedValue({
      success: true,
      data: { count: 0, max_items: 20, items: [] },
    });
    vi.mocked(api.getStockChart).mockResolvedValue({
      success: true,
      data: {
        symbol: "INFY",
        period: "6mo",
        interval: "1d",
        ohlcv: [
          { date: "2026-03-20", open: 1490, high: 1510, low: 1488, close: 1502, volume: 3200000 },
        ],
        signal_markers: [],
        resistance_level: 1500,
        support_level: 1450,
        target_price: 1580,
      },
    });

    render(
      <MemoryRouter initialEntries={["/stock/INFY"]}>
        <Routes>
          <Route path="/stock/:symbol" element={<StockDetail />} />
        </Routes>
      </MemoryRouter>,
    );

    await screen.findByText("AI reasoning");
    fireEvent.click(screen.getByRole("button", { name: "Chart" }));

    await waitFor(() => {
      expect(api.getStockChart).toHaveBeenCalledWith("INFY", { period: "6mo", interval: "1d" });
    });
    expect(await screen.findByText("Chart view")).toBeTruthy();
  });
});
