from __future__ import annotations

from typing import Any

from models import ExtractionValidationCheck, ExtractionValidatorReport


class ExtractionValidator:
    @staticmethod
    def _to_number(value: Any) -> float | None:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        try:
            return float(str(value).replace(",", "").strip())
        except (TypeError, ValueError):
            return None

    @classmethod
    def validate(
        cls,
        *,
        llm_data: dict[str, Any],
        audit_trail: list[dict[str, Any]],
        auditor_status: str,
        triangulation_result: dict[str, Any],
        has_uploaded_documents: bool,
        fallback_mode: bool,
        company_context: dict[str, Any],
        extraction_mode: str,
    ) -> ExtractionValidatorReport:
        if not has_uploaded_documents and not llm_data:
            return ExtractionValidatorReport(
                status="skipped",
                summary="No uploaded documents were available for extraction validation.",
                source_summary={
                    "has_uploaded_documents": False,
                    "extraction_mode": extraction_mode or "none",
                },
            )

        issues: list[str] = []
        warnings: list[str] = []
        checks: list[ExtractionValidationCheck] = []

        def add_check(
            name: str,
            passed: bool,
            details: str,
            *,
            blocking: bool = False,
            observed_value: Any = None,
        ) -> None:
            checks.append(
                ExtractionValidationCheck(
                    name=name,
                    passed=passed,
                    blocking=blocking,
                    details=details,
                    observed_value=observed_value,
                )
            )
            if not passed:
                target = issues if blocking else warnings
                target.append(f"{name}: {details}")

        revenues = llm_data.get("historical_revenues")
        margins = llm_data.get("historical_ebitda_margins")
        borrowings = cls._to_number(llm_data.get("total_borrowings"))
        lease_liabilities = cls._to_number(llm_data.get("lease_liabilities")) or 0.0
        ccps_liability = cls._to_number(llm_data.get("ccps_liability")) or 0.0
        cash = cls._to_number(llm_data.get("cash_and_equivalents"))
        net_debt = cls._to_number(llm_data.get("net_debt"))
        reporting_unit = str(llm_data.get("reporting_unit") or "").strip().lower()

        has_core_revenues = (
            isinstance(revenues, list)
            and len(revenues) >= 3
            and all(isinstance(v, (int, float)) and v > 0 for v in revenues)
        )
        add_check(
            "historical_revenues",
            has_core_revenues,
            "Expected at least 3 positive annual revenue values.",
            blocking=has_uploaded_documents,
            observed_value=revenues,
        )

        has_core_margins = (
            isinstance(margins, list)
            and len(margins) >= 3
            and all(isinstance(v, (int, float)) and -1.0 < v < 1.0 for v in margins)
        )
        add_check(
            "historical_ebitda_margins",
            has_core_margins,
            "Expected at least 3 EBITDA margins in decimal form between -1 and 1.",
            blocking=has_uploaded_documents,
            observed_value=margins,
        )

        has_debt_cash = borrowings is not None and cash is not None
        add_check(
            "debt_and_cash_fields",
            has_debt_cash,
            "Both total_borrowings and cash_and_equivalents should be extracted.",
            blocking=has_uploaded_documents,
            observed_value={
                "total_borrowings": borrowings,
                "cash_and_equivalents": cash,
            },
        )

        audit_by_field = {entry.get("field"): entry for entry in audit_trail or []}
        strong_core_support = 0
        citation_failures: list[str] = []
        for field_name in (
            "historical_revenues",
            "historical_ebitda_margins",
            "total_borrowings",
            "cash_and_equivalents",
        ):
            entry = audit_by_field.get(field_name) or {}
            confidence = float(entry.get("confidence", 0.0) or 0.0)
            citation = str(entry.get("source_citation", "") or "")
            is_strong = confidence >= (0.70 if "historical" in field_name else 0.65) and len(citation.strip()) >= 8
            strong_core_support += 1 if is_strong else 0
            if not is_strong:
                citation_failures.append(field_name)

        add_check(
            "citation_strength",
            strong_core_support >= 2,
            "Too few core fields have strong citation support.",
            blocking=has_uploaded_documents and not fallback_mode,
            observed_value={
                "strong_core_support": strong_core_support,
                "weak_fields": citation_failures,
            },
        )

        add_check(
            "reporting_unit_present",
            bool(reporting_unit),
            "Reporting unit should be captured for normalization and auditability.",
            blocking=has_uploaded_documents and extraction_mode != "structured_spreadsheet",
            observed_value=reporting_unit,
        )

        if has_debt_cash and net_debt is not None:
            derived_net_debt = (borrowings or 0.0) + lease_liabilities + ccps_liability - (cash or 0.0)
            delta = abs(derived_net_debt - net_debt)
            tolerance = max(abs(derived_net_debt) * 0.10, 50_000_000.0)
            add_check(
                "net_debt_reconciliation",
                delta <= tolerance,
                f"net_debt mismatch vs derived debt-cash bridge (delta={delta:,.0f}, tolerance={tolerance:,.0f}).",
                blocking=has_uploaded_documents,
                observed_value={
                    "derived_net_debt": derived_net_debt,
                    "reported_net_debt": net_debt,
                    "delta": delta,
                },
            )
        else:
            add_check(
                "net_debt_reconciliation",
                False,
                "Could not run net-debt reconciliation due to missing fields.",
                blocking=has_uploaded_documents,
            )

        if isinstance(revenues, list) and len(revenues) >= 2 and all(isinstance(v, (int, float)) and v > 0 for v in revenues):
            rounded = {round(float(v), -7) for v in revenues}
            add_check(
                "revenue_variability",
                len(rounded) > 1,
                "Extracted revenues appear flat or duplicated across years.",
                blocking=has_uploaded_documents,
                observed_value=revenues,
            )

            latest_revenue = float(revenues[-1])
            add_check(
                "revenue_scale_plausibility",
                500_000_000 <= latest_revenue <= 10_000_000_000_000,
                "Latest revenue is outside the expected INR scale bounds.",
                blocking=has_uploaded_documents,
                observed_value=latest_revenue,
            )

        tri_verdict = str(triangulation_result.get("overall_verdict") or "unknown").lower()
        tri_results = triangulation_result.get("results", []) or []
        tri_critical_failures = [
            result for result in tri_results if not result.get("passed", True) and result.get("severity") == "critical"
        ]
        add_check(
            "triangulation",
            tri_verdict != "halt" and not tri_critical_failures,
            f"Triangulation verdict is {tri_verdict}.",
            blocking=has_uploaded_documents,
            observed_value={
                "overall_verdict": tri_verdict,
                "critical_failures": len(tri_critical_failures),
            },
        )

        normalized_auditor_status = str(auditor_status or "").lower()
        add_check(
            "auditor_status",
            normalized_auditor_status != "rejected",
            f"Auditor status is {auditor_status or 'unknown'}.",
            blocking=has_uploaded_documents,
            observed_value=auditor_status,
        )

        if extraction_mode == "structured_spreadsheet":
            structured_citations_ok = all(
                ("row" in str(entry.get("source_citation", "")).lower() or "|" in str(entry.get("source_citation", "")))
                for entry in audit_trail[: min(len(audit_trail), 5)]
            )
            add_check(
                "structured_spreadsheet_crosscheck",
                structured_citations_ok,
                "Structured spreadsheet extraction should retain sheet/row level citations.",
                blocking=has_uploaded_documents,
            )

        is_private = bool(company_context.get("is_private_company")) if isinstance(company_context, dict) else False
        shares = cls._to_number(llm_data.get("shares_outstanding"))
        diluted = cls._to_number(llm_data.get("diluted_shares_outstanding"))
        if not is_private:
            add_check(
                "share_count_presence",
                (shares is not None) or (diluted is not None),
                "Public company context should have shares_outstanding or diluted_shares_outstanding.",
                blocking=False,
                observed_value={"shares_outstanding": shares, "diluted": diluted},
            )

        if has_uploaded_documents and not llm_data:
            add_check(
                "document_extraction_available",
                False,
                "Documents were uploaded but no validated extraction payload was produced.",
                blocking=True,
            )

        if has_uploaded_documents and fallback_mode:
            add_check(
                "fallback_mode",
                False,
                "Deterministic fallback was used instead of document-grounded extraction.",
                blocking=True,
            )

        status = "failed" if issues else "passed"
        return ExtractionValidatorReport(
            status=status,
            summary=(
                "Extraction validator passed."
                if status == "passed"
                else "Extraction validator failed due to blocking data quality issues."
            ),
            blocking_issues=issues,
            warnings=warnings,
            checks=checks,
            source_summary={
                "has_uploaded_documents": has_uploaded_documents,
                "extraction_mode": extraction_mode,
                "auditor_status": auditor_status,
                "triangulation_verdict": tri_verdict,
            },
        )
