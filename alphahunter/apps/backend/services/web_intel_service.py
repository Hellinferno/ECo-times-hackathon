from __future__ import annotations

from datetime import datetime, timedelta
import hashlib
from time import perf_counter
from typing import Any, Dict, Iterable, List, Optional

from loguru import logger
from sqlalchemy import desc
from sqlalchemy.orm import Session

from models.db import ExternalSignalEvent, WebFetchRun
from providers import GoalSpec, NormalizedSignalEvent, TinyFishProvider, WebIntelProvider
from utils.runtime_settings import get_runtime_settings, parse_int


SOURCE_CONFIG: Dict[str, Dict[str, Any]] = {
    "bulk_deal": {
        "url": "https://www.nseindia.com/report-detail/display-bulk-and-block-deals",
        "ttl_minutes": 360,
        "global": True,
    },
    "news_sentiment": {
        "url": "https://www.moneycontrol.com/news/business/markets/",
        "ttl_minutes": 180,
        "global": False,
    },
    "social_sentiment": {
        "url": "https://finance.yahoo.com",
        "ttl_minutes": 180,
        "global": False,
    },
    "insider_filing": {
        "url": "https://www.bseindia.com/corporates/insider_trading_new.aspx",
        "ttl_minutes": 720,
        "global": True,
    },
    "macro_indicator": {
        "url": "https://www.investing.com",
        "ttl_minutes": 60,
        "global": True,
    },
}


class WebIntelService:
    def __init__(self, db: Session, provider: Optional[WebIntelProvider] = None):
        self.db = db
        self.provider = provider or TinyFishProvider()

    def is_cache_stale(self, stale_after_minutes: int = 5) -> bool:
        latest_success = (
            self.db.query(WebFetchRun)
            .filter(WebFetchRun.status.in_(["completed", "partial"]))
            .order_by(desc(WebFetchRun.started_at))
            .first()
        )
        if not latest_success:
            return True
        return latest_success.started_at < datetime.utcnow() - timedelta(minutes=stale_after_minutes)

    def prefetch_if_stale(self, symbols: List[str]) -> Dict[str, Any]:
        if not self.is_cache_stale(5):
            return {"skipped": True, "reason": "fresh_cache"}
        return self.prefetch(symbols=symbols, force=False)

    def prefetch(self, symbols: List[str], force: bool = False) -> Dict[str, Any]:
        symbols = sorted({s.upper() for s in symbols if s})
        if not symbols:
            return {"skipped": True, "reason": "no_symbols"}

        settings = get_runtime_settings(self.db)
        if not force and not self.is_cache_stale(5):
            return {"skipped": True, "reason": "fresh_cache"}

        self._purge_expired_events()
        timeout_secs = parse_int(settings, "tinyfish_timeout_secs", 20)
        max_concurrency = parse_int(settings, "tinyfish_max_concurrency", 20)
        batch_size = parse_int(settings, "tinyfish_batch_size", 20)

        collector_order = [
            "bulk_deal",
            "insider_filing",
            "macro_indicator",
            "news_sentiment",
            "social_sentiment",
        ]
        summary: Dict[str, Any] = {"sources": {}}
        for source_type in collector_order:
            goals = self._build_goals(source_type, symbols, settings)
            source_summary = self._collect_source(
                source_type=source_type,
                symbols=symbols,
                goals=goals,
                timeout_secs=timeout_secs,
                max_concurrency=max_concurrency,
                batch_size=batch_size,
            )
            summary["sources"][source_type] = source_summary

        return summary

    def get_health_snapshot(self) -> Dict[str, Any]:
        latest = (
            self.db.query(WebFetchRun)
            .order_by(desc(WebFetchRun.started_at))
            .first()
        )
        source_status: Dict[str, str] = {}
        freshness: Dict[str, Optional[float]] = {}
        for source_type in SOURCE_CONFIG:
            source_run = (
                self.db.query(WebFetchRun)
                .filter(WebFetchRun.source_type == source_type)
                .order_by(desc(WebFetchRun.started_at))
                .first()
            )
            if not source_run:
                source_status[source_type] = "missing"
                freshness[source_type] = None
                continue
            source_status[source_type] = source_run.status
            freshness[source_type] = round(
                (datetime.utcnow() - source_run.started_at).total_seconds() / 60.0, 2
            )

        return {
            "provider": "tinyfish" if getattr(self.provider, "api_key", None) else "disabled",
            "last_prefetch_at": latest.started_at.isoformat() if latest else None,
            "last_prefetch_status": latest.status if latest else "missing",
            "source_status": source_status,
            "source_freshness_minutes": freshness,
        }

    def _collect_source(
        self,
        source_type: str,
        symbols: List[str],
        goals: List[GoalSpec],
        timeout_secs: int,
        max_concurrency: int,
        batch_size: int,
    ) -> Dict[str, Any]:
        run = WebFetchRun(
            source_type=source_type,
            status="running",
            symbols_count=len(goals),
            success_count=0,
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)

        started = perf_counter()
        errors: List[str] = []
        success_goals = 0
        events: List[NormalizedSignalEvent] = []

        if not goals:
            run.status = "completed"
            run.completed_at = datetime.utcnow()
            run.duration_ms = int((perf_counter() - started) * 1000)
            self.db.commit()
            return {
                "status": run.status,
                "goals": 0,
                "success_goals": 0,
                "events_saved": 0,
            }

        source_batch_size = batch_size if not SOURCE_CONFIG[source_type]["global"] else len(goals)
        for goal_chunk in self._chunk(goals, max(1, source_batch_size)):
            try:
                chunk_events = self.provider.run_goal_batch(
                    goals=goal_chunk,
                    timeout_secs=timeout_secs,
                    max_concurrency=max_concurrency,
                )
                events.extend(chunk_events)
                success_goals += len(goal_chunk)
            except Exception as exc:
                logger.warning(f"Web intel source '{source_type}' chunk failed: {exc}")
                errors.append(str(exc))

        saved_count = self._persist_events(source_type, symbols, events)
        run.success_count = success_goals
        run.duration_ms = int((perf_counter() - started) * 1000)
        run.completed_at = datetime.utcnow()

        if success_goals == len(goals) and not errors:
            run.status = "completed"
        elif success_goals > 0:
            run.status = "partial"
        else:
            run.status = "failed"
        run.error_summary = " | ".join(errors[:5]) if errors else None
        self.db.commit()

        return {
            "status": run.status,
            "goals": len(goals),
            "success_goals": success_goals,
            "events_saved": saved_count,
            "duration_ms": run.duration_ms,
        }

    def _persist_events(
        self,
        source_type: str,
        symbols: List[str],
        events: List[NormalizedSignalEvent],
    ) -> int:
        ttl_minutes = SOURCE_CONFIG[source_type]["ttl_minutes"]
        now = datetime.utcnow()
        saved = 0

        for event in events:
            candidates = [event]
            if source_type == "macro_indicator" and event.symbol == "__GLOBAL__":
                candidates = [
                    NormalizedSignalEvent(
                        symbol=symbol,
                        event_type=event.event_type,
                        event_time=event.event_time,
                        source=event.source,
                        payload_json=event.payload_json,
                        strength=event.strength,
                        sentiment=event.sentiment,
                        confidence=event.confidence,
                        expires_at=event.expires_at,
                        dedupe_hash=self._derive_symbol_hash(event.dedupe_hash, symbol),
                    )
                    for symbol in symbols
                ]

            for candidate in candidates:
                exists = (
                    self.db.query(ExternalSignalEvent)
                    .filter(ExternalSignalEvent.dedupe_hash == candidate.dedupe_hash)
                    .first()
                )
                if exists:
                    continue
                row = ExternalSignalEvent(
                    symbol=candidate.symbol,
                    event_type=candidate.event_type,
                    event_time=candidate.event_time,
                    source=candidate.source,
                    payload_json=candidate.payload_json,
                    strength=candidate.strength,
                    sentiment=candidate.sentiment,
                    confidence=candidate.confidence,
                    expires_at=candidate.expires_at or (now + timedelta(minutes=ttl_minutes)),
                    dedupe_hash=candidate.dedupe_hash,
                )
                self.db.add(row)
                saved += 1

        if saved > 0:
            self.db.commit()
        return saved

    def _build_goals(self, source_type: str, symbols: List[str], settings: Dict[str, str]) -> List[GoalSpec]:
        config = SOURCE_CONFIG[source_type]
        if config["global"]:
            return [self._build_global_goal(source_type, symbols, config["url"], settings)]

        goals = []
        for symbol in symbols:
            goals.append(self._build_symbol_goal(source_type, symbol, config["url"], settings))
        return goals

    def _build_global_goal(
        self,
        source_type: str,
        symbols: List[str],
        url: str,
        settings: Dict[str, str],
    ) -> GoalSpec:
        if source_type == "bulk_deal":
            goal = (
                "Extract all NSE/BSE bulk and block deals for the last 24 hours and return JSON array "
                "with symbol, client_name, deal_type, quantity, price, and event_time."
            )
        elif source_type == "insider_filing":
            lookback_days = parse_int(settings, "insider_lookback_days", 5)
            goal = (
                f"Extract insider-trading or promoter-holding changes in last {lookback_days} days. "
                "Return JSON array with symbol, filing_score (0-1), filing_type, summary, confidence, and event_time."
            )
        else:
            lookback_minutes = parse_int(settings, "macro_lookback_minutes", 60)
            goal = (
                f"Extract macro indicators relevant to Indian equities updated in the last {lookback_minutes} minutes. "
                "Return JSON array with symbol (or __GLOBAL__), score (0-1), indicator, and event_time."
            )
        return GoalSpec(
            source_type=source_type,
            url=url,
            goal=goal,
            symbol="__GLOBAL__",
            metadata={"symbols": symbols},
        )

    def _build_symbol_goal(
        self,
        source_type: str,
        symbol: str,
        url: str,
        settings: Dict[str, str],
    ) -> GoalSpec:
        if source_type == "news_sentiment":
            lookback = parse_int(settings, "news_lookback_hours", 6)
            goal = (
                f"Collect market news for {symbol} from last {lookback} hours and return JSON array with "
                "symbol, sentiment (-1 to 1), confidence (0-1), headline, source, and event_time."
            )
        else:
            lookback = parse_int(settings, "social_lookback_hours", 6)
            goal = (
                f"Summarize social buzz for {symbol} over last {lookback} hours using public and aggregator signals. "
                "Return JSON array with symbol, mention_zscore, positive_ratio, sentiment, confidence, and event_time."
            )

        return GoalSpec(
            source_type=source_type,
            url=url,
            goal=goal,
            symbol=symbol,
        )

    def _purge_expired_events(self) -> None:
        now = datetime.utcnow()
        self.db.query(ExternalSignalEvent).filter(ExternalSignalEvent.expires_at < now).delete(synchronize_session=False)
        self.db.commit()

    def _chunk(self, items: List[Any], size: int) -> Iterable[List[Any]]:
        for idx in range(0, len(items), size):
            yield items[idx : idx + size]

    def _derive_symbol_hash(self, base_hash: str, symbol: str) -> str:
        seed = f"{base_hash}:{symbol}"
        return hashlib.sha256(seed.encode("utf-8")).hexdigest()
