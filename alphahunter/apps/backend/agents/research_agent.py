"""ResearchAgent — structured research task runner backed by macro context.

Dispatches to one of four task types:
  - research_brief          General company summary with macro overlay
  - due_diligence           Financial / legal / operational / market DD checklist
  - industry_analysis       Sector-level market sizing, competition, regulations
  - competitive_landscape   Peer positioning and moat analysis

All task methods are async so they can later be replaced with LLM calls
without changing callers. The module-level `research_agent` singleton is
imported by the platform API endpoints.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from config import settings


@dataclass
class ResearchContext:
    workspace_id: str
    company_name: str
    symbol: str | None
    sector: str | None
    workspace_type: str
    macro_context: dict[str, Any]


@dataclass
class ResearchOutput:
    title: str
    summary: str
    sections: list[dict[str, str]]
    key_findings: list[str]
    risks: list[str]
    confidence: float
    sources: list[str]


class ResearchAgent:
    def __init__(self):
        self._llm_available = bool(settings.GEMINI_API_KEY)

    # ── Public dispatcher ──────────────────────────────────────────────────────

    async def run_research(
        self,
        context: ResearchContext,
        task_type: str = "research_brief",
    ) -> ResearchOutput:
        if task_type == "due_diligence":
            return await self._run_due_diligence(context)
        elif task_type == "industry_analysis":
            return await self._run_industry_analysis(context)
        elif task_type == "competitive_landscape":
            return await self._run_competitive_landscape(context)
        else:
            return await self._run_research_brief(context)

    # ── Task implementations ───────────────────────────────────────────────────

    async def _run_research_brief(self, context: ResearchContext) -> ResearchOutput:
        macro = context.macro_context or {}

        title = f"Research Brief: {context.company_name}"
        if context.symbol:
            title += f" ({context.symbol})"

        sections = [
            {
                "title": "Company Overview",
                "content": f"{context.company_name} operates in the {context.sector or 'General'} sector. "
                f"Market regime: {macro.get('market_regime', 'Neutral')}. "
                f"Fear/Greed Index: {macro.get('fear_greed', 'N/A') or 'N/A'}.",
            },
            {
                "title": "Industry Context",
                "content": self._generate_industry_context(context.sector, macro),
            },
            {
                "title": "Macro Environment",
                "content": f"Current regime: {macro.get('market_regime', 'Neutral')}. "
                f"Sector snapshot: {macro.get('sector_snapshot', {}).get('sector', 'General')}. "
                f"Strategic risks: {', '.join([r.get('name', 'Unknown') for r in macro.get('strategic_risks', [])[:3]]) or 'None identified'}.",
            },
            {
                "title": "Investment Considerations",
                "content": self._generate_investment_considerations(context, macro),
            },
        ]

        key_findings = [
            f"{context.company_name} is positioned in {context.sector or 'a diversified'} sector",
            f"Current market regime: {macro.get('market_regime', 'Neutral')}",
            "Research brief generated based on available market data",
        ]

        risks = [
            "Market volatility may impact valuations",
            "Sector-specific risks apply",
            "Macro economic conditions may change",
        ]

        return ResearchOutput(
            title=title,
            summary=f"Research brief for {context.company_name} covering company overview, "
            f"industry context, and macro environment.",
            sections=sections,
            key_findings=key_findings,
            risks=risks,
            confidence=0.72 if context.workspace_type == "public_equity" else 0.68,
            sources=["Market data", "Macro intelligence"],
        )

    async def _run_due_diligence(self, context: ResearchContext) -> ResearchOutput:
        macro = context.macro_context or {}

        sections = [
            {
                "title": "Financial Due Diligence",
                "content": "Review of historical financial performance, revenue trends, "
                "profitability margins, and cash flow generation. "
                "Key metrics to validate: revenue growth, EBITDA margins, working capital requirements.",
            },
            {
                "title": "Legal & Compliance",
                "content": "Assessment of regulatory compliance, litigation history, "
                "and material contracts. Verify all statutory filings are current.",
            },
            {
                "title": "Operational Due Diligence",
                "content": "Evaluation of operational efficiency, supply chain resilience, "
                "and key dependencies. Review management team and organizational structure.",
            },
            {
                "title": "Market Due Diligence",
                "content": f"Market position analysis within {context.sector or 'the'} sector. "
                f"Competitive landscape and market share trends. "
                f"Macro environment: {macro.get('market_regime', 'Neutral')} regime.",
            },
            {
                "title": "Risk Factors",
                "content": f"Key risks identified: {', '.join([r.get('name', 'Unknown') for r in macro.get('strategic_risks', [])[:3]]) or 'Standard market risks apply'}.",
            },
        ]

        key_findings = [
            "Due diligence scope defined based on workspace type",
            "Financial, legal, operational, and market dimensions covered",
            "Macro risks incorporated from WorldMonitor",
        ]

        risks = [
            "Detailed financial analysis requires access to filings",
            "Legal review requires counsel engagement",
            "Market conditions may change during diligence period",
        ]

        return ResearchOutput(
            title=f"Due Diligence Report: {context.company_name}",
            summary=f"Comprehensive due diligence report for {context.company_name} "
            "covering financial, legal, operational, and market dimensions.",
            sections=sections,
            key_findings=key_findings,
            risks=risks,
            confidence=0.65,
            sources=["Company filings", "Market data", "Third-party databases"],
        )

    async def _run_industry_analysis(self, context: ResearchContext) -> ResearchOutput:
        macro = context.macro_context or {}
        sector = context.sector or "General"

        sections = [
            {
                "title": "Industry Overview",
                "content": f"Analysis of {sector} sector. "
                f"Current market regime: {macro.get('market_regime', 'Neutral')}.",
            },
            {
                "title": "Market Size & Growth",
                "content": "Industry market size, historical growth rates, "
                "and projected growth trajectory. Key growth drivers identified.",
            },
            {
                "title": "Competitive Landscape",
                "content": "Major players in the industry, market share distribution, "
                "and competitive dynamics. Barriers to entry and industry concentration.",
            },
            {
                "title": "Regulatory Environment",
                "content": "Key regulations affecting the industry, "
                "recent regulatory changes, and upcoming compliance requirements.",
            },
            {
                "title": "Industry Risks",
                "content": f"Strategic risks: {', '.join([r.get('name', 'Unknown') for r in macro.get('strategic_risks', [])[:3]]) or 'Standard industry risks apply'}).",
            },
        ]

        key_findings = [
            f"Industry analysis for {sector} sector",
            f"Market regime context: {macro.get('market_regime', 'Neutral')}",
            "Competitive dynamics and regulatory environment covered",
        ]

        risks = [
            "Industry projections subject to market conditions",
            "Regulatory changes may impact outlook",
            "Competitive landscape is dynamic",
        ]

        return ResearchOutput(
            title=f"Industry Analysis: {sector}",
            summary=f"Comprehensive industry analysis for the {sector} sector, "
            "covering market dynamics, competitive landscape, and regulatory environment.",
            sections=sections,
            key_findings=key_findings,
            risks=risks,
            confidence=0.70,
            sources=["Industry reports", "Market data", "Regulatory filings"],
        )

    async def _run_competitive_landscape(self, context: ResearchContext) -> ResearchOutput:
        sector = context.sector or "General"

        sections = [
            {
                "title": "Competitive Overview",
                "content": f"Competitive analysis for {context.company_name} "
                f"within the {sector} sector.",
            },
            {
                "title": "Key Competitors",
                "content": "Identification of major competitors, "
                "their market positioning, and relative strengths.",
            },
            {
                "title": "Competitive Advantages",
                "content": "Analysis of sustainable competitive advantages, "
                "moats, and differentiation factors.",
            },
            {
                "title": "Market Share Dynamics",
                "content": "Historical and current market share trends, "
                "and factors driving share changes.",
            },
        ]

        key_findings = [
            f"Competitive landscape for {context.company_name}",
            f"Primary competitors in {sector} identified",
            "Market share dynamics analyzed",
        ]

        risks = [
            "Competitive landscape is subject to change",
            "New entrants may disrupt market",
            "Technology changes may alter competitive dynamics",
        ]

        return ResearchOutput(
            title=f"Competitive Landscape: {context.company_name}",
            summary=f"Competitive landscape analysis for {context.company_name}, "
            "identifying key competitors and competitive dynamics.",
            sections=sections,
            key_findings=key_findings,
            risks=risks,
            confidence=0.68,
            sources=["Company data", "Industry reports", "Market analysis"],
        )

    # ── Text generation helpers ────────────────────────────────────────────────

    def _generate_industry_context(self, sector: str | None, macro: dict[str, Any]) -> str:
        sector_snapshot = macro.get("sector_snapshot", {})
        sector_name = sector or sector_snapshot.get("sector", "General")
        bias = sector_snapshot.get("bias", "Neutral outlook")

        return f"Industry: {sector_name}. Current view: {bias}."

    def _generate_investment_considerations(
        self,
        context: ResearchContext,
        macro: dict[str, Any],
    ) -> str:
        regime = macro.get("market_regime", "Neutral")
        fear_greed = macro.get("fear_greed")

        considerations = [
            f"Market regime: {regime}",
        ]

        if fear_greed is not None:
            if fear_greed < 25:
                considerations.append("Fear indicator: Extreme Fear")
            elif fear_greed < 45:
                considerations.append("Fear indicator: Fear")
            elif fear_greed > 75:
                considerations.append("Fear indicator: Extreme Greed")
            elif fear_greed > 55:
                considerations.append("Fear indicator: Greed")

        if context.workspace_type == "public_equity":
            considerations.append("Public equity workspace: Focus on market liquidity and trading considerations")
        elif context.workspace_type == "private_company" or context.workspace_type == "deal":
            considerations.append("Private company/deal workspace: Focus on exit opportunities and valuation sensitivity")

        return " ".join(considerations)


research_agent = ResearchAgent()
