"""ExcelWriter — in-memory Excel model generator for valuation outputs.

Produces formatted workbooks (DCF, LBO, Comps) as BytesIO objects so they
can be streamed directly as HTTP attachments without writing to disk.

Sheets produced per model:
  DCF   — Assumptions, Projections, Scenarios, Summary
  LBO   — Assumptions, Debt Schedule, Returns
  Comps — Peer multiples, Derived values, Summary
"""
from __future__ import annotations

import io
from datetime import datetime
from typing import Any


class ExcelWriter:
    def __init__(self):
        self._workbook = None
        self._sheets = {}

    def create_dcf_model(
        self,
        company_name: str,
        assumptions: dict[str, Any],
        results: dict[str, Any],
        output_path: str | None = None,
    ) -> bytes:
        try:
            import openpyxl
            from openpyxl import Workbook
            from openpyxl.styles import Alignment, Font, PatternFill
            from openpyxl.utils import get_column_letter
        except ImportError:
            return self._create_fallback_dcf(company_name, assumptions, results)

        wb = Workbook()
        ws_summary = wb.active
        ws_summary.title = "Summary"

        header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF")
        accent_fill = PatternFill(start_color="D6DCE4", end_color="D6DCE4", fill_type="solid")

        ws_summary["A1"] = f"{company_name} - DCF Valuation"
        ws_summary["A1"].font = Font(bold=True, size=14)
        ws_summary.merge_cells("A1:D1")

        ws_summary["A3"] = "Valuation Summary"
        ws_summary["A3"].font = Font(bold=True, size=12)

        scenarios = results.get("result", {}).get("scenarios", {})
        row = 4
        for scenario_name, scenario_data in scenarios.items():
            ws_summary[f"A{row}"] = f"{scenario_name.upper()} Case"
            ws_summary[f"A{row}"].font = Font(bold=True)
            row += 1

            ws_summary[f"A{row}"] = "Enterprise Value"
            ws_summary[f"B{row}"] = scenario_data.get("enterprise_value", 0)
            row += 1

            ws_summary[f"A{row}"] = "Equity Value"
            ws_summary[f"B{row}"] = scenario_data.get("equity_value", 0)
            row += 1

            ws_summary[f"A{row}"] = "Implied Share Price"
            ws_summary[f"B{row}"] = scenario_data.get("implied_share_price", 0)
            row += 1

            ws_summary[f"A{row}"] = "Terminal Value Share"
            ws_summary[f"B{row}"] = scenario_data.get("terminal_value_share", 0)
            row += 2

        ws_summary["A16"] = "Key Assumptions"
        ws_summary["A16"].font = Font(bold=True, size=12)
        row = 17

        for key, value in assumptions.items():
            if isinstance(value, list):
                continue
            ws_summary[f"A{row}"] = key.replace("_", " ").title()
            ws_summary[f"B{row}"] = str(value)
            row += 1

        if scenarios.get("base", {}).get("cashflows"):
            ws_cf = wb.create_sheet("Cash Flows")
            ws_cf["A1"] = "Year"
            ws_cf["B1"] = "Revenue"
            ws_cf["C1"] = "EBITDA"
            ws_cf["D1"] = "FCF"
            ws_cf["E1"] = "Discounted FCF"

            for col in ["A", "B", "C", "D", "E"]:
                ws_cf[f"{col}1"].fill = header_fill
                ws_cf[f"{col}1"].font = header_font

            cashflows = scenarios["base"]["cashflows"]
            for idx, cf in enumerate(cashflows, start=2):
                ws_cf[f"A{idx}"] = cf.get("year", "")
                ws_cf[f"B{idx}"] = cf.get("revenue", "")
                ws_cf[f"C{idx}"] = cf.get("ebitda", "")
                ws_cf[f"D{idx}"] = cf.get("fcf", "")
                ws_cf[f"E{idx}"] = cf.get("discounted_fcf", "")

            for col in range(1, 6):
                ws_cf.column_dimensions[get_column_letter(col)].width = 15

        for col in range(1, 5):
            ws_summary.column_dimensions[get_column_letter(col)].width = 20

        if output_path:
            wb.save(output_path)

        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        return buffer.getvalue()

    def create_lbo_model(
        self,
        company_name: str,
        assumptions: dict[str, Any],
        results: dict[str, Any],
        output_path: str | None = None,
    ) -> bytes:
        try:
            import openpyxl
            from openpyxl import Workbook
            from openpyxl.styles import Alignment, Font, PatternFill
            from openpyxl.utils import get_column_letter
        except ImportError:
            return self._create_fallback_lbo(company_name, assumptions, results)

        wb = Workbook()
        ws_summary = wb.active
        ws_summary.title = "LBO Summary"

        header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF")

        ws_summary["A1"] = f"{company_name} - LBO Analysis"
        ws_summary["A1"].font = Font(bold=True, size=14)
        ws_summary.merge_cells("A1:D1")

        ws_summary["A3"] = "Investment Returns"
        ws_summary["A3"].font = Font(bold=True, size=12)

        result = results.get("result", {})
        row = 4

        metrics = [
            ("Entry EV", result.get("entry_ev")),
            ("Entry Equity", result.get("entry_equity")),
            ("Exit EV", result.get("exit_ev")),
            ("Exit Equity", result.get("exit_equity")),
            ("IRR", f"{result.get('irr_pct', 0)}%"),
            ("MOIC", result.get("moic")),
        ]

        for label, value in metrics:
            ws_summary[f"A{row}"] = label
            ws_summary[f"B{row}"] = value
            row += 1

        row += 1
        ws_summary[f"A{row}"] = "Key Assumptions"
        ws_summary[f"A{row}"].font = Font(bold=True, size=12)
        row += 1

        key_assumptions = [
            ("Equity Contribution %", assumptions.get("equity_contribution_pct")),
            ("Hold Years", assumptions.get("hold_years")),
            ("Entry Multiple", assumptions.get("entry_ev_ebitda")),
            ("Exit Multiple", assumptions.get("exit_ev_ebitda")),
        ]

        for label, value in key_assumptions:
            ws_summary[f"A{row}"] = label
            ws_summary[f"B{row}"] = value
            row += 1

        if result.get("debt_schedule"):
            ws_debt = wb.create_sheet("Debt Schedule")
            ws_debt["A1"] = "Year"
            ws_debt["B1"] = "EBITDA"
            ws_debt["C1"] = "Interest"
            ws_debt["D1"] = "Amortization"
            ws_debt["E1"] = "Closing Debt"

            for col in ["A", "B", "C", "D", "E"]:
                ws_debt[f"{col}1"].fill = header_fill
                ws_debt[f"{col}1"].font = header_font

            debt_schedule = result["debt_schedule"]
            for idx, period in enumerate(debt_schedule, start=2):
                ws_debt[f"A{idx}"] = period.get("year", "")
                ws_debt[f"B{idx}"] = period.get("ebitda", "")
                ws_debt[f"C{idx}"] = period.get("interest", "")
                ws_debt[f"D{idx}"] = period.get("amortization", "")
                ws_debt[f"E{idx}"] = period.get("closing_debt", "")

            for col in range(1, 6):
                ws_debt.column_dimensions[get_column_letter(col)].width = 15

        for col in range(1, 3):
            ws_summary.column_dimensions[get_column_letter(col)].width = 20

        if output_path:
            wb.save(output_path)

        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        return buffer.getvalue()

    def create_comps_model(
        self,
        company_name: str,
        assumptions: dict[str, Any],
        results: dict[str, Any],
        output_path: str | None = None,
    ) -> bytes:
        try:
            import openpyxl
            from openpyxl import Workbook
            from openpyxl.styles import Font, PatternFill
            from openpyxl.utils import get_column_letter
        except ImportError:
            return self._create_fallback_comps(company_name, assumptions, results)

        wb = Workbook()
        ws = wb.active
        ws.title = "Comps Analysis"

        header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF")

        ws["A1"] = f"{company_name} - Comparable Companies Analysis"
        ws["A1"].font = Font(bold=True, size=14)
        ws.merge_cells("A1:E1")

        ws["A3"] = "Valuation Summary"
        ws["A3"].font = Font(bold=True, size=12)

        result = results.get("result", {})
        scenarios = result.get("scenarios", {})
        row = 4

        for scenario_name, scenario_data in scenarios.items():
            ws[f"A{row}"] = f"{scenario_name.upper()} Case"
            ws[f"A{row}"].font = Font(bold=True)
            row += 1

            ws[f"A{row}"] = "EV/EBITDA Multiple"
            ws[f"B{row}"] = scenario_data.get("ev_ebitda", "")
            row += 1

            ws[f"A{row}"] = "Enterprise Value"
            ws[f"B{row}"] = scenario_data.get("enterprise_value", "")
            row += 1

            ws[f"A{row}"] = "Equity Value"
            ws[f"B{row}"] = scenario_data.get("equity_value", "")
            row += 1

            ws[f"A{row}"] = "Implied Share Price"
            ws[f"B{row}"] = scenario_data.get("implied_share_price", "")
            row += 2

        ws[f"A{row}"] = "Industry"
        ws[f"B{row}"] = result.get("industry", "")
        row += 1

        ws[f"A{row}"] = "Latest EBITDA"
        ws[f"B{row}"] = result.get("latest_ebitda", "")
        row += 1

        multiple_band = result.get("multiple_band", {})
        ws[f"A{row}"] = "Multiple Band"
        ws[f"B{row}"] = f"Bear: {multiple_band.get('bear', '')}, Base: {multiple_band.get('base', '')}, Bull: {multiple_band.get('bull', '')}"

        for col in range(1, 6):
            ws.column_dimensions[get_column_letter(col)].width = 25

        if output_path:
            wb.save(output_path)

        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        return buffer.getvalue()

    def _create_fallback_dcf(
        self,
        company_name: str,
        assumptions: dict[str, Any],
        results: dict[str, Any],
    ) -> bytes:
        content = f"""
{company_name} - DCF Valuation Model
Generated: {datetime.utcnow().isoformat()}

SUMMARY
-------
"""
        scenarios = results.get("result", {}).get("scenarios", {})
        for scenario_name, data in scenarios.items():
            content += f"""
{scenario_name.upper()} CASE
Enterprise Value: {data.get('enterprise_value', 0)}
Equity Value: {data.get('equity_value', 0)}
Implied Share Price: {data.get('implied_share_price', 0)}
"""
        return content.encode("utf-8")

    def _create_fallback_lbo(
        self,
        company_name: str,
        assumptions: dict[str, Any],
        results: dict[str, Any],
    ) -> bytes:
        content = f"""
{company_name} - LBO Analysis
Generated: {datetime.utcnow().isoformat()}

INVESTMENT RETURNS
------------------
"""
        result = results.get("result", {})
        content += f"""
Entry EV: {result.get('entry_ev', 0)}
Entry Equity: {result.get('entry_equity', 0)}
Exit EV: {result.get('exit_ev', 0)}
Exit Equity: {result.get('exit_equity', 0)}
IRR: {result.get('irr_pct', 0)}%
MOIC: {result.get('moic', 0)}
"""
        return content.encode("utf-8")

    def _create_fallback_comps(
        self,
        company_name: str,
        assumptions: dict[str, Any],
        results: dict[str, Any],
    ) -> bytes:
        content = f"""
{company_name} - Comps Analysis
Generated: {datetime.utcnow().isoformat()}

VALUATION SUMMARY
-----------------
"""
        result = results.get("result", {})
        scenarios = result.get("scenarios", {})
        for scenario_name, data in scenarios.items():
            content += f"""
{scenario_name.upper()} Case:
EV/EBITDA: {data.get('ev_ebitda', 0)}
Enterprise Value: {data.get('enterprise_value', 0)}
Equity Value: {data.get('equity_value', 0)}
Implied Share Price: {data.get('implied_share_price', 0)}
"""
        return content.encode("utf-8")


excel_writer = ExcelWriter()
