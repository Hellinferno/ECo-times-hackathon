"""DeterministicValuationEngine — DCF, Comps, and LBO model runner.

All three models produce bear / base / bull scenario outputs so the UI can
show a range rather than a point estimate.

  DCF   — discounted free-cash-flow with fade-adjusted growth and terminal value
  Comps — sector EV/EBITDA multiple band applied to the latest EBITDA
  LBO   — leveraged buyout with annual debt schedule, IRR, and MOIC

Public API
----------
  ValuationContext      — workspace / company inputs supplied by the caller
  DeterministicValuationEngine.build_defaults(context)  → assumption dict
  DeterministicValuationEngine.run(model_type, assumptions, context) → result
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any


# ── Numeric helpers ────────────────────────────────────────────────────────────

def _to_float(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return default


def _to_float_list(values: Any, fallback: list[float]) -> list[float]:
    if not isinstance(values, list):
        return fallback
    parsed = [_to_float(value, math.nan) for value in values]
    cleaned = [value for value in parsed if not math.isnan(value)]
    return cleaned if cleaned else fallback


def _discount(value: float, rate: float, period: int) -> float:
    return value / ((1 + rate) ** max(period, 1))


def _irr(cashflows: list[float]) -> float:
    low = -0.95
    high = 2.0

    def npv(rate: float) -> float:
        total = 0.0
        for index, cashflow in enumerate(cashflows):
            total += cashflow / ((1 + rate) ** index)
        return total

    low_npv = npv(low)
    high_npv = npv(high)
    if low_npv * high_npv > 0:
        return 0.0

    midpoint = 0.0
    for _ in range(120):
        midpoint = (low + high) / 2
        mid_npv = npv(midpoint)
        if abs(mid_npv) < 1e-6:
            return midpoint
        if low_npv * mid_npv <= 0:
            high = midpoint
            high_npv = mid_npv
        else:
            low = midpoint
            low_npv = mid_npv
    return midpoint


# ── Data types ─────────────────────────────────────────────────────────────────

@dataclass
class ValuationContext:
    workspace_type: str
    company_name: str
    industry: str
    current_market_cap: float | None = None
    current_price: float | None = None


# ── Engine ─────────────────────────────────────────────────────────────────────

class DeterministicValuationEngine:
    SECTOR_MULTIPLES = {
        "technology": (12.0, 16.0, 20.0),
        "it services": (12.0, 16.0, 19.0),
        "software": (13.0, 18.0, 22.0),
        "consumer": (8.0, 11.0, 14.0),
        "energy": (6.0, 8.0, 10.0),
        "industrials": (7.0, 9.5, 12.0),
        "financial": (7.0, 9.0, 11.0),
        "default": (7.0, 10.0, 13.0),
    }

    def build_defaults(self, context: ValuationContext) -> dict[str, Any]:
        market_cap = _to_float(context.current_market_cap, 10000.0)
        quick_revenue = max(market_cap * 0.55, 2500.0)
        base_margin = 0.22 if "tech" in context.industry.lower() else 0.17
        shares = max(market_cap / max(_to_float(context.current_price, 100.0), 1.0), 50.0)

        return {
            "historical_revenues": [
                round(quick_revenue * 0.73, 2),
                round(quick_revenue * 0.84, 2),
                round(quick_revenue * 0.94, 2),
                round(quick_revenue, 2),
            ],
            "historical_ebitda_margins": [
                round(base_margin - 0.04, 4),
                round(base_margin - 0.02, 4),
                round(base_margin - 0.01, 4),
                round(base_margin, 4),
            ],
            "tax_rate": 0.25,
            "wacc": 0.115 if context.workspace_type == "public_equity" else 0.13,
            "terminal_growth_rate": 0.03 if context.workspace_type == "public_equity" else 0.025,
            "projection_years": 5,
            "net_debt": round(market_cap * 0.08, 2),
            "shares_outstanding": round(shares, 2),
            "entry_ebitda": round(quick_revenue * base_margin, 2),
            "entry_ev_ebitda": self._resolve_multiple_band(context.industry)[1],
            "equity_contribution_pct": 0.45,
            "hold_years": 5,
            "exit_ev_ebitda": self._resolve_multiple_band(context.industry)[1] - 0.5,
            "revenue_growth_rates": [0.11, 0.1, 0.09, 0.08, 0.07],
            "ebitda_margins": [round(base_margin + delta, 4) for delta in (0.0, 0.01, 0.015, 0.02, 0.025)],
            "notes": "Auto-generated defaults from market context and sector template.",
        }

    def run(self, model_type: str, assumptions: dict[str, Any], context: ValuationContext) -> dict[str, Any]:
        merged = {**self.build_defaults(context), **(assumptions or {})}
        normalized_model_type = (model_type or "dcf").strip().lower()

        if normalized_model_type == "lbo":
            return self._run_lbo(merged, context)
        if normalized_model_type == "comps":
            return self._run_comps(merged, context)
        return self._run_dcf(merged, context)

    def _resolve_multiple_band(self, industry: str) -> tuple[float, float, float]:
        needle = (industry or "").lower()
        for key, band in self.SECTOR_MULTIPLES.items():
            if key != "default" and key in needle:
                return band
        return self.SECTOR_MULTIPLES["default"]

    def _run_dcf(self, assumptions: dict[str, Any], context: ValuationContext) -> dict[str, Any]:
        revenues = _to_float_list(assumptions.get("historical_revenues"), [3000.0, 3400.0, 3800.0, 4200.0])
        margins = _to_float_list(assumptions.get("historical_ebitda_margins"), [0.14, 0.16, 0.17, 0.18])
        latest_revenue = revenues[-1]
        latest_margin = margins[-1]
        projection_years = int(max(3, min(7, _to_float(assumptions.get("projection_years"), 5))))
        wacc = max(0.08, min(0.18, _to_float(assumptions.get("wacc"), 0.115)))
        terminal_growth = max(0.01, min(wacc - 0.01, _to_float(assumptions.get("terminal_growth_rate"), 0.03)))
        net_debt = _to_float(assumptions.get("net_debt"), 0.0)
        shares = max(_to_float(assumptions.get("shares_outstanding"), 1.0), 1.0)

        growth_base = max(-0.02, min(0.18, (revenues[-1] / revenues[0]) ** (1 / max(len(revenues) - 1, 1)) - 1))
        scenarios = {
            "bear": {"growth": growth_base * 0.7, "margin": max(latest_margin - 0.02, 0.06)},
            "base": {"growth": growth_base, "margin": latest_margin},
            "bull": {"growth": growth_base * 1.2, "margin": min(latest_margin + 0.02, 0.34)},
        }

        scenario_outputs: dict[str, Any] = {}
        warnings: list[str] = []

        for name, scenario in scenarios.items():
            current_revenue = latest_revenue
            discounted_fcfs = 0.0
            cashflows: list[dict[str, float]] = []
            for year in range(1, projection_years + 1):
                fade = 1 - ((year - 1) / max(projection_years, 1)) * 0.35
                growth = scenario["growth"] * fade
                current_revenue = current_revenue * (1 + growth)
                ebitda = current_revenue * scenario["margin"]
                da = current_revenue * 0.04
                ebit = ebitda - da
                nopat = ebit * (1 - _to_float(assumptions.get("tax_rate"), 0.25))
                capex = current_revenue * 0.04
                wc_drag = current_revenue * 0.015
                fcf = nopat + da - capex - wc_drag
                discounted = _discount(fcf, wacc, year)
                discounted_fcfs += discounted
                cashflows.append(
                    {
                        "year": year,
                        "revenue": round(current_revenue, 2),
                        "ebitda": round(ebitda, 2),
                        "fcf": round(fcf, 2),
                        "discounted_fcf": round(discounted, 2),
                    }
                )

            terminal_fcf = cashflows[-1]["fcf"] * (1 + terminal_growth)
            terminal_value = terminal_fcf / max(wacc - terminal_growth, 0.01)
            discounted_terminal = _discount(terminal_value, wacc, projection_years)
            enterprise_value = discounted_fcfs + discounted_terminal
            equity_value = enterprise_value - net_debt
            implied_share_price = equity_value / shares
            tv_share = discounted_terminal / max(enterprise_value, 1.0)
            if tv_share > 0.78 and name == "base":
                warnings.append("Terminal value dominates the base case. Review projection depth and growth assumptions.")

            scenario_outputs[name] = {
                "enterprise_value": round(enterprise_value, 2),
                "equity_value": round(equity_value, 2),
                "implied_share_price": round(implied_share_price, 2),
                "terminal_value_share": round(tv_share, 3),
                "cashflows": cashflows,
            }

        return {
            "model_type": "dcf",
            "status": "completed",
            "summary": {
                "headline_value": scenario_outputs["base"]["implied_share_price"],
                "headline_metric": "Implied share price",
                "confidence_band": "Moderate conviction" if context.workspace_type == "public_equity" else "Analyst workup",
            },
            "inputs": assumptions,
            "result": {
                "wacc": round(wacc, 4),
                "terminal_growth_rate": round(terminal_growth, 4),
                "projection_years": projection_years,
                "scenarios": scenario_outputs,
            },
            "warnings": warnings,
        }

    def _run_comps(self, assumptions: dict[str, Any], context: ValuationContext) -> dict[str, Any]:
        revenue = _to_float_list(assumptions.get("historical_revenues"), [3000.0])[-1]
        margin = _to_float_list(assumptions.get("historical_ebitda_margins"), [0.18])[-1]
        ebitda = revenue * margin
        shares = max(_to_float(assumptions.get("shares_outstanding"), 1.0), 1.0)
        net_debt = _to_float(assumptions.get("net_debt"), 0.0)
        bear, base, bull = self._resolve_multiple_band(context.industry)

        def build_case(multiple: float) -> dict[str, float]:
            enterprise_value = ebitda * multiple
            equity_value = enterprise_value - net_debt
            return {
                "ev_ebitda": multiple,
                "enterprise_value": round(enterprise_value, 2),
                "equity_value": round(equity_value, 2),
                "implied_share_price": round(equity_value / shares, 2),
            }

        return {
            "model_type": "comps",
            "status": "completed",
            "summary": {
                "headline_value": build_case(base)["implied_share_price"],
                "headline_metric": "Comparable share price",
                "confidence_band": "Sector band estimate",
            },
            "inputs": assumptions,
            "result": {
                "industry": context.industry,
                "latest_ebitda": round(ebitda, 2),
                "multiple_band": {"bear": bear, "base": base, "bull": bull},
                "scenarios": {
                    "bear": build_case(bear),
                    "base": build_case(base),
                    "bull": build_case(bull),
                },
            },
            "warnings": [],
        }

    def _run_lbo(self, assumptions: dict[str, Any], context: ValuationContext) -> dict[str, Any]:
        entry_ebitda = max(_to_float(assumptions.get("entry_ebitda"), 500.0), 1.0)
        entry_multiple = max(_to_float(assumptions.get("entry_ev_ebitda"), 8.0), 4.0)
        equity_contribution = max(0.2, min(0.8, _to_float(assumptions.get("equity_contribution_pct"), 0.45)))
        hold_years = int(max(3, min(7, _to_float(assumptions.get("hold_years"), 5))))
        exit_multiple = max(4.0, _to_float(assumptions.get("exit_ev_ebitda"), entry_multiple - 0.5))
        growth_rates = _to_float_list(assumptions.get("revenue_growth_rates"), [0.08, 0.08, 0.07, 0.07, 0.06])
        margins = _to_float_list(assumptions.get("ebitda_margins"), [0.18, 0.19, 0.2, 0.205, 0.21])

        entry_ev = entry_ebitda * entry_multiple
        entry_equity = entry_ev * equity_contribution
        entry_debt = entry_ev - entry_equity
        remaining_debt = entry_debt
        ebitda = entry_ebitda
        cashflows = [-entry_equity]
        debt_schedule: list[dict[str, float]] = []
        warnings: list[str] = []

        for year in range(hold_years):
            growth = growth_rates[min(year, len(growth_rates) - 1)]
            margin = margins[min(year, len(margins) - 1)]
            ebitda = ebitda * (1 + growth) * (1 + (margin - margins[0]) * 0.35)
            interest = remaining_debt * 0.08
            amortization = min(remaining_debt, entry_debt * 0.12)
            free_cash = max(ebitda * 0.52 - interest - amortization, 0.0)
            remaining_debt = max(remaining_debt - amortization - free_cash * 0.35, 0.0)
            debt_schedule.append(
                {
                    "year": year + 1,
                    "ebitda": round(ebitda, 2),
                    "interest": round(interest, 2),
                    "amortization": round(amortization, 2),
                    "closing_debt": round(remaining_debt, 2),
                }
            )

        exit_ev = ebitda * exit_multiple
        exit_equity = max(exit_ev - remaining_debt, 0.0)
        cashflows.extend([0.0] * (hold_years - 1))
        cashflows.append(exit_equity)
        irr = _irr(cashflows)
        moic = exit_equity / max(entry_equity, 1.0)

        if irr < 0.12:
            warnings.append("Base-case LBO IRR is below a typical sponsor return hurdle.")

        return {
            "model_type": "lbo",
            "status": "completed",
            "summary": {
                "headline_value": round(irr * 100, 2),
                "headline_metric": "Sponsor IRR %",
                "confidence_band": "Leveraged case",
            },
            "inputs": assumptions,
            "result": {
                "entry_ev": round(entry_ev, 2),
                "entry_equity": round(entry_equity, 2),
                "exit_ev": round(exit_ev, 2),
                "exit_equity": round(exit_equity, 2),
                "irr_pct": round(irr * 100, 2),
                "moic": round(moic, 2),
                "debt_schedule": debt_schedule,
            },
            "warnings": warnings,
        }


valuation_engine = DeterministicValuationEngine()
