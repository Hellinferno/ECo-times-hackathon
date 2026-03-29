"""MacroIntelligenceService — WorldMonitor macro context client.

Fetches four signals from the WorldMonitor sidecar:
  - getMacroSignals      → market regime verdict (Bullish / Bearish / Neutral)
  - getFearGreedIndex    → 0–100 fear/greed value
  - getSectorSummary     → per-sector bias snapshot
  - getRiskScores        → strategic risk list

Falls back to a neutral context dict when the sidecar is unavailable.
The module-level `macro_service` singleton is imported by platform API endpoints.
"""
from __future__ import annotations

from typing import Any

import requests

from config import settings


class MacroIntelligenceService:
    def __init__(self, base_url: str | None = None):
        self.base_url = (base_url if base_url is not None else settings.WORLDMONITOR_API_URL or "").rstrip("/")

    @property
    def enabled(self) -> bool:
        return bool(self.base_url)

    def _request(self, path: str) -> dict[str, Any] | None:
        if not self.enabled:
            return None
        try:
            response = requests.get(f"{self.base_url}{path}", timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception:
            return None

    def get_context(self, symbol: str | None = None, sector: str | None = None) -> dict[str, Any]:
        if not self.enabled:
            return self._fallback_context(symbol=symbol, sector=sector, live=False)

        macro = self._request("/api/economic/v1/getMacroSignals")
        fear_greed = self._request("/api/market/v1/getFearGreedIndex")
        sectors = self._request("/api/market/v1/getSectorSummary")
        risks = self._request("/api/risk/v1/getRiskScores")

        if not any([macro, fear_greed, sectors, risks]):
            return self._fallback_context(symbol=symbol, sector=sector, live=False)

        verdict = (
            macro.get("signals", {}).get("verdict")
            if isinstance(macro, dict)
            else None
        ) or "Neutral"
        fear_greed_value = (
            fear_greed.get("data", {}).get("value")
            if isinstance(fear_greed, dict)
            else None
        )
        sector_row = None
        if isinstance(sectors, dict):
            sector_list = sectors.get("sectors") or sectors.get("data") or []
            if isinstance(sector_list, list) and sector:
                sector_lower = sector.lower()
                sector_row = next(
                    (
                        item
                        for item in sector_list
                        if sector_lower in str(item.get("sector", "")).lower()
                        or sector_lower in str(item.get("name", "")).lower()
                    ),
                    None,
                )

        strategic_risks = risks.get("strategicRisks", []) if isinstance(risks, dict) else []

        return {
            "available": True,
            "source": "worldmonitor",
            "symbol": symbol,
            "sector": sector,
            "market_regime": verdict,
            "fear_greed": fear_greed_value,
            "sector_snapshot": sector_row,
            "strategic_risks": strategic_risks[:4],
            "notes": [
                "Live macro context is being used to frame valuation and decision confidence.",
                "If a feed goes stale, the UI should fall back gracefully to neutral guidance.",
            ],
        }

    def _fallback_context(self, symbol: str | None, sector: str | None, live: bool) -> dict[str, Any]:
        return {
            "available": live,
            "source": "fallback",
            "symbol": symbol,
            "sector": sector,
            "market_regime": "Neutral",
            "fear_greed": None,
            "sector_snapshot": {
                "sector": sector or "General market",
                "bias": "Awaiting live macro feed",
            },
            "strategic_risks": [],
            "notes": [
                "WorldMonitor is offline or not configured.",
                "AlphaHunter is showing neutral macro guidance until the sidecar is available.",
            ],
        }


macro_service = MacroIntelligenceService()
