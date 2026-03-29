"""Web intelligence providers — abstract interface and concrete implementations.

Exports:
  WebIntelProvider       Abstract base class — implement run_goal_batch().
  GoalSpec               Dataclass describing one natural-language browser goal.
  NormalizedSignalEvent  Dataclass for the canonical event shape returned by all providers.
  TinyFishProvider       Concrete provider that calls the TinyFish SSE run-goal API.
  NSEProvider            Direct NSE bulk/block deal fetcher (zero API key required).
"""
from .web_intel_provider import GoalSpec, NormalizedSignalEvent, WebIntelProvider
from .tinyfish_provider import TinyFishProvider
from .nse_provider import NSEProvider

__all__ = [
    "GoalSpec",
    "NormalizedSignalEvent",
    "WebIntelProvider",
    "TinyFishProvider",
    "NSEProvider",
]
