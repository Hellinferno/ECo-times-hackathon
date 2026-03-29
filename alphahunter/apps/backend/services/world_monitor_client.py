"""WorldMonitorClient — typed HTTP client for the WorldMonitor sidecar.

Wraps the four economic/market endpoints with per-call error handling.
All methods return None on timeout or non-200 response so callers can
decide whether to use a fallback.

Note: MacroIntelligenceService (macro_service.py) is the higher-level
facade that caches and merges these signals; use that for application code.
"""
from __future__ import annotations

from typing import Any

import requests

from config import settings


class WorldMonitorClient:
    def __init__(self, base_url: str | None = None):
        self.base_url = (base_url or settings.WORLDMONITOR_API_URL or "").rstrip("/")
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": "AlphaHunter/1.0"})

    @property
    def available(self) -> bool:
        return bool(self.base_url)

    def _get(self, path: str, timeout: float = 10.0) -> dict[str, Any] | None:
        if not self.available:
            return None
        try:
            response = self._session.get(f"{self.base_url}{path}", timeout=timeout)
            response.raise_for_status()
            return response.json()
        except Exception:
            return None

    def get_macro_signals(self) -> dict[str, Any] | None:
        return self._get("/api/economic/v1/getMacroSignals")

    def get_fear_greed_index(self) -> dict[str, Any] | None:
        return self._get("/api/market/v1/getFearGreedIndex")

    def get_sector_summary(self) -> dict[str, Any] | None:
        return self._get("/api/market/v1/getSectorSummary")

    def get_risk_scores(self) -> dict[str, Any] | None:
        return self._get("/api/risk/v1/getRiskScores")

    def get_market_regime(self) -> dict[str, Any] | None:
        return self._get("/api/market/v1/getMarketRegime")

    def get_country_risk(self, country_code: str | None = None) -> dict[str, Any] | None:
        if country_code:
            return self._get(f"/api/risk/v1/getCountryRisk?country={country_code}")
        return self._get("/api/risk/v1/getCountryRisk")

    def get_supply_chain_risk(self, sector: str | None = None) -> dict[str, Any] | None:
        if sector:
            return self._get(f"/api/risk/v1/getSupplyChainRisk?sector={sector}")
        return self._get("/api/risk/v1/getSupplyChainRisk")

    def get_full_context(
        self,
        symbol: str | None = None,
        sector: str | None = None,
        country_code: str | None = None,
    ) -> dict[str, Any]:
        if not self.available:
            return self._fallback_context(symbol, sector)

        macro = self.get_macro_signals()
        fear_greed = self.get_fear_greed_index()
        sectors = self.get_sector_summary()
        risks = self.get_risk_scores()
        regime = self.get_market_regime()

        if not any([macro, fear_greed, sectors, risks, regime]):
            return self._fallback_context(symbol, sector)

        verdict = "Neutral"
        if isinstance(macro, dict):
            signals = macro.get("signals", {})
            verdict = signals.get("verdict") or verdict

        fear_greed_value = None
        if isinstance(fear_greed, dict):
            fear_greed_value = fear_greed.get("data", {}).get("value")

        sector_row = None
        if isinstance(sectors, dict) and sector:
            sector_list = sectors.get("sectors") or sectors.get("data") or []
            if isinstance(sector_list, list):
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

        strategic_risks = []
        if isinstance(risks, dict):
            strategic_risks = risks.get("strategicRisks", [])[:4]

        regime_data = None
        if isinstance(regime, dict):
            regime_data = regime.get("data", {}) or regime

        return {
            "available": True,
            "source": "worldmonitor",
            "symbol": symbol,
            "sector": sector,
            "country_code": country_code,
            "market_regime": verdict,
            "fear_greed": fear_greed_value,
            "sector_snapshot": sector_row,
            "strategic_risks": strategic_risks,
            "regime": regime_data,
            "notes": [
                "Live macro context from WorldMonitor.",
                "If a feed goes stale, the UI should fall back gracefully.",
            ],
        }

    def _fallback_context(
        self,
        symbol: str | None = None,
        sector: str | None = None,
    ) -> dict[str, Any]:
        return {
            "available": False,
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
            "regime": None,
            "notes": [
                "WorldMonitor is offline or not configured.",
                "AlphaHunter is showing neutral macro guidance.",
            ],
        }


world_monitor_client = WorldMonitorClient()
