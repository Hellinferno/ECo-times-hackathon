"""Web intelligence provider interface and shared data types.

Defines the abstract WebIntelProvider contract so concrete implementations
(e.g. TinyFishProvider) can be swapped in tests or replaced at runtime.

Supported event types (SUPPORTED_EVENT_TYPES):
  bulk_deal | news_sentiment | social_sentiment | insider_filing | macro_indicator
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional


# ── Constants ─────────────────────────────────────────────────────────────────

SUPPORTED_EVENT_TYPES = {
    "bulk_deal",
    "news_sentiment",
    "social_sentiment",
    "insider_filing",
    "macro_indicator",
}


# ── Data types ────────────────────────────────────────────────────────────────


@dataclass
class GoalSpec:
    source_type: str
    url: str
    goal: str
    symbol: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NormalizedSignalEvent:
    symbol: str
    event_type: str
    event_time: datetime
    source: str
    payload_json: Dict[str, Any]
    strength: Optional[Decimal] = None
    sentiment: Optional[Decimal] = None
    confidence: Optional[Decimal] = None
    expires_at: Optional[datetime] = None
    dedupe_hash: str = ""

    def as_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "event_type": self.event_type,
            "event_time": self.event_time,
            "source": self.source,
            "payload_json": self.payload_json,
            "strength": self.strength,
            "sentiment": self.sentiment,
            "confidence": self.confidence,
            "expires_at": self.expires_at,
            "dedupe_hash": self.dedupe_hash,
        }


# ── Abstract provider ─────────────────────────────────────────────────────────


class WebIntelProvider(ABC):
    @abstractmethod
    def run_goal_batch(
        self,
        goals: List[GoalSpec],
        timeout_secs: int = 20,
        max_concurrency: int = 20,
    ) -> List[NormalizedSignalEvent]:
        """Execute multiple natural-language browser goals and return normalized events."""
        raise NotImplementedError
