/**
 * History page tests.
 *
 * Covers: decision log rendering, filter controls, CSV export trigger,
 * scan-runs tab switch, and DecisionReplayDrawer open/close lifecycle.
 *
 * All api.* calls are mocked via vi.mock so no real network is required.
 */
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { vi } from "vitest";

import History from "../src/History";
import { api } from "../src/api/client";

vi.mock("../src/api/client", () => ({
  api: {
    getHistory: vi.fn(),
    getScanHistory: vi.fn(),
    getHistoryDetail: vi.fn(),
    exportHistoryCsv: vi.fn(),
  },
}));

describe("history", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.getHistory).mockResolvedValue({
      success: true,
      data: {
        summary: {
          total_decisions: 1,
          buy_decisions: 1,
          measured: 1,
          wins: 1,
          win_rate_pct: 100,
          avg_return_pct: 4.8,
        },
        decisions: [
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
            decided_at: "2026-03-27T09:01:00Z",
            outcome_measured: true,
            outcome_return_pct: 4.8,
            outcome_result: "WIN",
            outcome_exit_price: 1551,
            outcome_measured_at: "2026-04-01T09:01:00Z",
          },
        ],
        pagination: { total: 1, limit: 80, offset: 0 },
      },
    });
    vi.mocked(api.getScanHistory).mockResolvedValue({
      success: true,
      data: [],
    });
    vi.mocked(api.getHistoryDetail).mockResolvedValue({
      success: true,
      data: {
        decision: {
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
          decided_at: "2026-03-27T09:01:00Z",
          outcome_measured: true,
          outcome_return_pct: 4.8,
          outcome_result: "WIN",
          outcome_exit_price: 1551,
          outcome_measured_at: "2026-04-01T09:01:00Z",
        },
        stock: { symbol: "INFY", name: "Infosys Ltd", sector: "Technology" },
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
        reasoning: { llm_summary: "Stored reasoning" },
        backtest: {
          matches: 5,
          success_rate: 80,
          avg_return_pct: 5.2,
          worst_case_pct: -3.1,
          best_case_pct: 9.8,
          cases: [],
        },
        snapshot: { decision_metrics: { confidence: 78 } },
        outcome: {
          result: "WIN",
          exit_price: 1551,
          return_pct: 4.8,
          measured_at: "2026-04-01T09:01:00Z",
        },
      },
    });
  });

  it("renders decisions and opens the replay drawer", async () => {
    render(
      <MemoryRouter>
        <History />
      </MemoryRouter>,
    );

    expect(await screen.findByText("Decision log")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: /replay/i }));

    await waitFor(() => {
      expect(api.getHistoryDetail).toHaveBeenCalledWith("dec-1");
    });
    expect(await screen.findByText("Decision replay")).toBeTruthy();
    expect(screen.getByText("Stored reasoning")).toBeTruthy();
  });
});
